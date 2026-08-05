from dataclasses import dataclass
from typing import Any, Final, Literal, Protocol, overload

import requests

from pydatajud.client_modules.movements_delta import (
    MovementDeltaMode,
    MovementDeltaResult,
    build_movements_delta_batch_request,
    build_movements_delta_request,
    build_movements_status_batch_request,
    build_movements_status_request,
    extract_movements_delta_result,
    extract_movements_delta_results,
    validate_cutoff_iso,
    validate_movements_delta_mode,
)
from pydatajud.exceptions import (
    DataJudAuthenticationError,
    DataJudInvalidResponseError,
    DataJudProcessNotFoundError,
    DataJudRequestError,
)
from pydatajud.resolver import (
    format_cnj_process_number,
    normalize_cnj_process_number,
    resolve_datajud_search_url,
)

DEFAULT_TIMEOUT: Final = 30.0
DataJudResponse = dict[str, Any]
DataJudRawBatchResponse = list[DataJudResponse]
MovementDeltaBatchResult = dict[str, MovementDeltaResult]


class _ResponseLike(Protocol):
    status_code: int
    text: str

    def json(self) -> Any: ...

    def raise_for_status(self) -> None: ...


class _SessionLike(Protocol):
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> _ResponseLike: ...


@dataclass(frozen=True)
class DataJudResult:
    """Structured result returned by process searches."""

    endpoint: str
    total_hits: int
    raw_hits: list[dict[str, Any]]
    movimentos: list[dict[str, Any]]


DataJudBatchResponse = list[DataJudResult]


class DataJudClient:
    def __init__(
        self,
        api_key: str,
        timeout: float = DEFAULT_TIMEOUT,
        session: _SessionLike | None = None,
    ):
        if not api_key.strip():
            raise ValueError("api_key não pode estar vazia")
        self.api_key = api_key
        self.timeout = timeout
        self.session = session or requests.Session()

    def search_by_process_number(
        self,
        process_number: str,
        size: int = 10,
        raise_not_found: bool = True,
    ) -> DataJudResult:
        normalized_process_number = normalize_cnj_process_number(process_number)
        endpoint = resolve_datajud_search_url(process_number)
        query = {"match": {"numeroProcesso": normalized_process_number}}
        body = {"size": size, "query": query}
        payload = self._search(endpoint, body, raise_not_found=raise_not_found)
        return _build_result(endpoint, payload)

    def search_by_process_numbers(
        self,
        process_numbers: list[str],
        size: int = 100,
        raise_not_found: bool = True,
    ) -> DataJudBatchResponse:
        if not process_numbers:
            raise ValueError("process_numbers não pode estar vazia")
        normalized_process_numbers = [
            normalize_cnj_process_number(process_number)
            for process_number in process_numbers
        ]
        grouped_by_endpoint: dict[str, list[str]] = {}
        for process_number, normalized_process_number in zip(
            process_numbers, normalized_process_numbers, strict=True
        ):
            endpoint = resolve_datajud_search_url(process_number)
            grouped_by_endpoint.setdefault(endpoint, []).append(
                normalized_process_number
            )

        partial_results: DataJudBatchResponse = []
        for endpoint, endpoint_process_numbers in grouped_by_endpoint.items():
            endpoint_process_numbers = list(dict.fromkeys(endpoint_process_numbers))
            query = {
                "bool": {
                    "should": [
                        {"match": {"numeroProcesso": process_number}}
                        for process_number in endpoint_process_numbers
                    ],
                    "minimum_should_match": 1,
                }
            }
            payload = self._search(
                endpoint,
                {"size": max(size, len(endpoint_process_numbers)), "query": query},
                raise_not_found=False,
            )
            partial_results.append(_build_result(endpoint, payload))

        has_hits = any(result.raw_hits for result in partial_results)
        if raise_not_found and not has_hits:
            raise DataJudProcessNotFoundError(
                "Nenhum processo encontrado nos endpoints DataJud consultados."
            )

        return partial_results

    @overload
    def search_movements_delta(
        self,
        process_number: str,
        cutoff_iso: str,
        mode: MovementDeltaMode = "status",
        size: int = 1,
        *,
        raw: Literal[False] = False,
        raise_not_found: bool = False,
    ) -> MovementDeltaResult: ...

    @overload
    def search_movements_delta(
        self,
        process_number: str,
        cutoff_iso: str,
        mode: MovementDeltaMode = "status",
        size: int = 1,
        *,
        raw: Literal[True],
        raise_not_found: bool = False,
    ) -> DataJudResponse: ...

    @overload
    def search_movements_delta(
        self,
        process_number: str,
        cutoff_iso: str,
        mode: MovementDeltaMode = "status",
        size: int = 1,
        *,
        raw: bool,
        raise_not_found: bool = False,
    ) -> MovementDeltaResult | DataJudResponse: ...

    def search_movements_delta(
        self,
        process_number: str,
        cutoff_iso: str,
        mode: MovementDeltaMode = "status",
        size: int = 1,
        *,
        raw: bool = False,
        raise_not_found: bool = False,
    ) -> MovementDeltaResult | DataJudResponse:
        """Check or return new movements using one public interface.

        Use ``mode="status"`` when only the verification result is needed and
        ``mode="movements"`` when the new movement objects will be processed,
        persisted, or sent to another integration. Set ``raw`` to ``True`` to
        receive the original DataJud payload instead of the typed result.
        """
        validated_mode = validate_movements_delta_mode(mode)
        normalized_process_number = normalize_cnj_process_number(process_number)
        formatted_process_number = format_cnj_process_number(process_number)
        normalized_cutoff = validate_cutoff_iso(cutoff_iso)
        endpoint = resolve_datajud_search_url(process_number)
        if validated_mode == "status":
            body = build_movements_status_request(
                normalized_process_number=normalized_process_number,
                cutoff_iso=normalized_cutoff,
                size=size,
            )
        else:
            body = build_movements_delta_request(
                normalized_process_number=normalized_process_number,
                cutoff_iso=normalized_cutoff,
                size=size,
            )
        payload = self._search(endpoint, body, raise_not_found=False)
        if raw:
            if raise_not_found and not _extract_hits(payload):
                raise DataJudProcessNotFoundError(
                    f"Processo não encontrado no endpoint {endpoint}."
                )
            return payload

        result = extract_movements_delta_result(
            payload,
            process_number=formatted_process_number,
            mode=validated_mode,
        )
        if raise_not_found and not result.found:
            raise DataJudProcessNotFoundError(
                f"Processo não encontrado no endpoint {endpoint}."
            )
        return result

    @overload
    def search_movements_delta_batch(
        self,
        cutoffs_by_process: dict[str, str],
        mode: MovementDeltaMode = "status",
        size: int = 100,
        *,
        raw: Literal[False] = False,
        raise_not_found: bool = False,
    ) -> MovementDeltaBatchResult: ...

    @overload
    def search_movements_delta_batch(
        self,
        cutoffs_by_process: dict[str, str],
        mode: MovementDeltaMode = "status",
        size: int = 100,
        *,
        raw: Literal[True],
        raise_not_found: bool = False,
    ) -> DataJudRawBatchResponse: ...

    @overload
    def search_movements_delta_batch(
        self,
        cutoffs_by_process: dict[str, str],
        mode: MovementDeltaMode = "status",
        size: int = 100,
        *,
        raw: bool,
        raise_not_found: bool = False,
    ) -> MovementDeltaBatchResult | DataJudRawBatchResponse: ...

    def search_movements_delta_batch(
        self,
        cutoffs_by_process: dict[str, str],
        mode: MovementDeltaMode = "status",
        size: int = 100,
        *,
        raw: bool = False,
        raise_not_found: bool = False,
    ) -> MovementDeltaBatchResult | DataJudRawBatchResponse:
        """Check or return new movements for multiple processes.

        The client groups processes by DataJud endpoint. ``mode="status"``
        keeps movement arrays out of the HTTP response, while
        ``mode="movements"`` includes the new movement objects. Typed results
        preserve an explicit status for every requested process, including
        missing processes.
        """
        validated_mode = validate_movements_delta_mode(mode)
        if not cutoffs_by_process:
            raise ValueError("cutoffs_by_process não pode estar vazio")
        if not isinstance(size, int) or size <= 0:
            raise ValueError("size deve ser maior que zero")

        grouped_by_endpoint: dict[str, dict[str, str]] = {}
        canonical_by_endpoint: dict[str, dict[str, str]] = {}
        results: MovementDeltaBatchResult = {}
        for process_number, cutoff_iso in cutoffs_by_process.items():
            normalized_process_number = normalize_cnj_process_number(process_number)
            formatted_process_number = format_cnj_process_number(process_number)
            normalized_cutoff = validate_cutoff_iso(cutoff_iso)
            endpoint = resolve_datajud_search_url(process_number)
            grouped_by_endpoint.setdefault(endpoint, {})[normalized_process_number] = (
                normalized_cutoff
            )
            canonical_by_endpoint.setdefault(endpoint, {})[
                normalized_process_number
            ] = formatted_process_number
            results[formatted_process_number] = MovementDeltaResult(
                process_number=formatted_process_number,
                found=False,
                has_new_movements=False,
                movements=None,
            )

        partial_results: DataJudRawBatchResponse = []
        for endpoint, endpoint_cutoffs in grouped_by_endpoint.items():
            endpoint_process_numbers = list(endpoint_cutoffs)
            if validated_mode == "status":
                body = build_movements_status_batch_request(
                    normalized_process_numbers=endpoint_process_numbers,
                    cutoffs_by_process=endpoint_cutoffs,
                    size=max(size, len(endpoint_process_numbers)),
                )
            else:
                body = build_movements_delta_batch_request(
                    normalized_process_numbers=endpoint_process_numbers,
                    cutoffs_by_process=endpoint_cutoffs,
                    size=max(size, len(endpoint_process_numbers)),
                )
            partial_results.append(
                self._search(
                    endpoint,
                    body,
                    raise_not_found=False,
                )
            )

        if raw:
            if raise_not_found and not any(
                _extract_hits(result) for result in partial_results
            ):
                raise DataJudProcessNotFoundError(
                    "Nenhum processo encontrado nos endpoints DataJud consultados."
                )
            return partial_results

        for (_endpoint, process_numbers_by_normalized), partial_result in zip(
            canonical_by_endpoint.items(), partial_results, strict=True
        ):
            endpoint_results = extract_movements_delta_results(
                partial_result,
                process_numbers_by_normalized=process_numbers_by_normalized,
                mode=validated_mode,
            )
            results.update(endpoint_results)

        if raise_not_found and any(not result.found for result in results.values()):
            raise DataJudProcessNotFoundError(
                "Um ou mais processos não foram encontrados nos endpoints DataJud."
            )
        return results

    def _search(
        self,
        endpoint: str,
        body: dict[str, Any],
        raise_not_found: bool,
    ) -> DataJudResponse:
        size = body.get("size")
        if not isinstance(size, int) or size <= 0:
            raise ValueError("size deve ser maior que zero")

        try:
            resp = self.session.post(
                endpoint,
                headers={
                    "Authorization": f"APIKey {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=body,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise DataJudRequestError(f"Falha ao consultar DataJud: {exc}") from exc

        if resp.status_code in {401, 403}:
            raise DataJudAuthenticationError(
                "A API do DataJud rejeitou a autenticação. Verifique a API key."
            )

        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            response_text = resp.text[:500].replace(self.api_key, "[REDACTED]")
            raise DataJudRequestError(
                f"DataJud retornou HTTP {resp.status_code}: {response_text}"
            ) from exc

        try:
            payload = resp.json()
        except ValueError as exc:
            raise DataJudInvalidResponseError(
                "DataJud retornou uma resposta que não é JSON válido."
            ) from exc

        if not isinstance(payload, dict):
            raise DataJudInvalidResponseError(
                "DataJud retornou JSON em formato inesperado."
            )

        hits = _extract_hits(payload)
        if not hits and raise_not_found:
            raise DataJudProcessNotFoundError(
                f"Processo não encontrado no endpoint {endpoint}."
            )
        return payload


def _extract_hits(payload: dict[str, Any]) -> list[dict[str, Any]]:
    hits_obj = payload.get("hits", {})
    if not isinstance(hits_obj, dict):
        raise DataJudInvalidResponseError("Resposta não contém hits como objeto.")

    hits = hits_obj.get("hits", [])
    if not isinstance(hits, list):
        raise DataJudInvalidResponseError("Resposta não contém hits.hits como lista.")
    return [hit for hit in hits if isinstance(hit, dict)]


def _build_result(endpoint: str, payload: DataJudResponse) -> DataJudResult:
    hits = _extract_hits(payload)
    movimentos: list[dict[str, Any]] = []
    for hit in hits:
        source = hit.get("_source", {})
        if not isinstance(source, dict):
            continue
        hit_movements = source.get("movimentos", [])
        if isinstance(hit_movements, list):
            movimentos.extend(
                movement for movement in hit_movements if isinstance(movement, dict)
            )

    return DataJudResult(
        endpoint=endpoint,
        total_hits=_extract_total_hits(payload),
        raw_hits=hits,
        movimentos=movimentos,
    )


def _extract_total_hits(payload: DataJudResponse) -> int:
    hits_obj = payload.get("hits", {})
    if not isinstance(hits_obj, dict):
        return 0

    total = hits_obj.get("total", 0)
    if isinstance(total, int):
        return total
    if isinstance(total, dict):
        value = total.get("value", 0)
        if isinstance(value, int):
            return value
    return 0
