from dataclasses import dataclass
from typing import Any, Final, Protocol

import requests

from pydatajud.exceptions import (
    DataJudAuthenticationError,
    DataJudInvalidResponseError,
    DataJudProcessNotFoundError,
    DataJudRequestError,
)
from pydatajud.resolver import normalize_cnj_process_number, resolve_datajud_search_url

DEFAULT_TIMEOUT: Final = 30.0


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
    endpoint: str
    total_hits: int
    raw_hits: list[dict[str, Any]]
    movimentos: list[dict[str, Any]]


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
        if size <= 0:
            raise ValueError("size deve ser maior que zero")

        normalized_process_number = normalize_cnj_process_number(process_number)
        endpoint = resolve_datajud_search_url(process_number)

        try:
            resp = self.session.post(
                endpoint,
                headers={
                    "Authorization": f"APIKey {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "size": size,
                    "query": {"match": {"numeroProcesso": normalized_process_number}},
                },
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
            raise DataJudRequestError(
                f"DataJud retornou HTTP {resp.status_code}: {resp.text[:500]}"
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

        movimentos: list[dict[str, Any]] = []
        for hit in hits:
            source = hit.get("_source", {})
            if not isinstance(source, dict):
                continue
            hit_movs = source.get("movimentos", [])
            if isinstance(hit_movs, list):
                movimentos.extend([m for m in hit_movs if isinstance(m, dict)])

        return DataJudResult(
            endpoint=endpoint,
            total_hits=_extract_total_hits(payload),
            raw_hits=hits,
            movimentos=movimentos,
        )


def _extract_hits(payload: dict[str, Any]) -> list[dict[str, Any]]:
    hits_obj = payload.get("hits", {})
    if not isinstance(hits_obj, dict):
        raise DataJudInvalidResponseError("Resposta não contém hits como objeto.")

    hits = hits_obj.get("hits", [])
    if not isinstance(hits, list):
        raise DataJudInvalidResponseError("Resposta não contém hits.hits como lista.")
    return [hit for hit in hits if isinstance(hit, dict)]


def _extract_total_hits(payload: dict[str, Any]) -> int:
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
