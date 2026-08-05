from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, cast

from pydatajud.exceptions import DataJudInvalidResponseError
from pydatajud.resolver import normalize_cnj_process_number

DataJudResponse = dict[str, Any]
MovementDeltaMode = Literal["status", "movements"]


@dataclass(frozen=True)
class MovementDeltaResult:
    """Typed status and optional movements for one process."""

    process_number: str
    found: bool
    has_new_movements: bool
    movements: list[dict[str, Any]] | None


MOVEMENTS_FIELD = "movimentos_delta"
STATUS_FIELD = "movimentos_delta_status"

DELTA_SCRIPT_SOURCE = "\n".join(
    [
        "def out = [];",
        "def src = params['_source'];",
        "def arr = src.containsKey('movimentos') ? src['movimentos'] : [];",
        "for (m in arr) {",
        "  if (m.containsKey('dataHora') && m['dataHora'] != null &&",
        "      m['dataHora'].compareTo(params.cutoff) > 0) {",
        "    out.add(m);",
        "  }",
        "}",
        "return out;",
    ]
)

DELTA_BATCH_SCRIPT_SOURCE = "\n".join(
    [
        "def out = [];",
        "def src = params['_source'];",
        "def np = src.containsKey('numeroProcesso') ? src['numeroProcesso'] : null;",
        "if (np == null || !params.cutoffs.containsKey(np)) return out;",
        "def cutoff = params.cutoffs[np];",
        "def arr = src.containsKey('movimentos') ? src['movimentos'] : [];",
        "for (m in arr) {",
        "  if (m.containsKey('dataHora') && m['dataHora'] != null &&",
        "      m['dataHora'].compareTo(cutoff) > 0) {",
        "    out.add(m);",
        "  }",
        "}",
        "return out;",
    ]
)

STATUS_SCRIPT_SOURCE = "\n".join(
    [
        "def src = params['_source'];",
        "def arr = src.containsKey('movimentos') ? src['movimentos'] : [];",
        "for (m in arr) {",
        "  if (m.containsKey('dataHora') && m['dataHora'] != null &&",
        "      m['dataHora'].compareTo(params.cutoff) > 0) return true;",
        "}",
        "return false;",
    ]
)

STATUS_BATCH_SCRIPT_SOURCE = "\n".join(
    [
        "def src = params['_source'];",
        "def np = src.containsKey('numeroProcesso') ? src['numeroProcesso'] : null;",
        "if (np == null || !params.cutoffs.containsKey(np)) return false;",
        "def cutoff = params.cutoffs[np];",
        "def arr = src.containsKey('movimentos') ? src['movimentos'] : [];",
        "for (m in arr) {",
        "  if (m.containsKey('dataHora') && m['dataHora'] != null &&",
        "      m['dataHora'].compareTo(cutoff) > 0) return true;",
        "}",
        "return false;",
    ]
)


def validate_cutoff_iso(cutoff_iso: str) -> str:
    if not isinstance(cutoff_iso, str) or not cutoff_iso.strip():
        raise ValueError("cutoff_iso deve ser um timestamp UTC ISO-8601")

    try:
        parsed = datetime.fromisoformat(cutoff_iso.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("cutoff_iso deve ser um timestamp UTC ISO-8601") from exc

    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("cutoff_iso deve ser um timestamp UTC ISO-8601 com timezone")

    return (
        parsed.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def validate_movements_delta_mode(mode: str) -> MovementDeltaMode:
    if mode not in {"status", "movements"}:
        raise ValueError("mode deve ser 'status' ou 'movements'")
    return cast(MovementDeltaMode, mode)


def build_movements_delta_request(
    *,
    normalized_process_number: str,
    cutoff_iso: str,
    size: int,
) -> dict[str, Any]:
    return {
        "size": size,
        "_source": ["numeroProcesso"],
        "query": {"match": {"numeroProcesso": normalized_process_number}},
        "script_fields": {
            "movimentos_delta": {
                "script": {
                    "lang": "painless",
                    "source": DELTA_SCRIPT_SOURCE,
                    "params": {"cutoff": cutoff_iso},
                }
            }
        },
    }


def build_movements_delta_batch_request(
    *,
    normalized_process_numbers: list[str],
    cutoffs_by_process: dict[str, str],
    size: int,
) -> dict[str, Any]:
    return {
        "size": size,
        "_source": ["numeroProcesso"],
        "query": {"terms": {"numeroProcesso": normalized_process_numbers}},
        "script_fields": {
            "movimentos_delta": {
                "script": {
                    "lang": "painless",
                    "source": DELTA_BATCH_SCRIPT_SOURCE,
                    "params": {"cutoffs": cutoffs_by_process},
                }
            }
        },
    }


def build_movements_status_request(
    *,
    normalized_process_number: str,
    cutoff_iso: str,
    size: int,
) -> dict[str, Any]:
    return {
        "size": size,
        "_source": ["numeroProcesso"],
        "query": {"match": {"numeroProcesso": normalized_process_number}},
        "script_fields": {
            STATUS_FIELD: {
                "script": {
                    "lang": "painless",
                    "source": STATUS_SCRIPT_SOURCE,
                    "params": {"cutoff": cutoff_iso},
                }
            }
        },
    }


def build_movements_status_batch_request(
    *,
    normalized_process_numbers: list[str],
    cutoffs_by_process: dict[str, str],
    size: int,
) -> dict[str, Any]:
    return {
        "size": size,
        "_source": ["numeroProcesso"],
        "query": {"terms": {"numeroProcesso": normalized_process_numbers}},
        "script_fields": {
            STATUS_FIELD: {
                "script": {
                    "lang": "painless",
                    "source": STATUS_BATCH_SCRIPT_SOURCE,
                    "params": {"cutoffs": cutoffs_by_process},
                }
            }
        },
    }


def extract_movements_delta_result(
    payload: DataJudResponse,
    *,
    process_number: str,
    mode: MovementDeltaMode,
) -> MovementDeltaResult:
    hits = _extract_hits(payload)
    if not hits:
        return MovementDeltaResult(
            process_number=process_number,
            found=False,
            has_new_movements=False,
            movements=None,
        )
    return _extract_result_from_hit(hits[0], process_number=process_number, mode=mode)


def extract_movements_delta_results(
    payload: DataJudResponse,
    *,
    process_numbers_by_normalized: dict[str, str],
    mode: MovementDeltaMode,
) -> dict[str, MovementDeltaResult]:
    results = {
        process_number: MovementDeltaResult(
            process_number=process_number,
            found=False,
            has_new_movements=False,
            movements=None,
        )
        for process_number in process_numbers_by_normalized.values()
    }

    for hit in _extract_hits(payload):
        source = hit.get("_source", {})
        if not isinstance(source, dict):
            raise DataJudInvalidResponseError(
                "Resposta delta não contém _source como objeto."
            )
        raw_process_number = source.get("numeroProcesso")
        if not isinstance(raw_process_number, str):
            raise DataJudInvalidResponseError(
                "Resposta delta não contém _source.numeroProcesso."
            )
        normalized = normalize_cnj_process_number(raw_process_number)
        process_number = process_numbers_by_normalized.get(normalized)
        if process_number is None:
            continue
        results[process_number] = _extract_result_from_hit(
            hit,
            process_number=process_number,
            mode=mode,
        )
    return results


def extract_movements_delta(payload: DataJudResponse) -> list[dict[str, Any]]:
    deltas: list[dict[str, Any]] = []
    for hit in _extract_hits(payload):
        if not isinstance(hit, dict):
            continue
        source = hit.get("_source", {})
        np = source.get("numeroProcesso") if isinstance(source, dict) else None
        result = _extract_result_from_hit(
            hit,
            process_number=str(np) if np is not None else "",
            mode="movements",
        )
        for mov in result.movements or []:
            item = dict(mov)
            if np is not None:
                item["numeroProcesso"] = np
            deltas.append(item)
    return deltas


def _extract_hits(payload: DataJudResponse) -> list[dict[str, Any]]:
    hits_obj = payload.get("hits", {})
    if not isinstance(hits_obj, dict):
        raise DataJudInvalidResponseError("Resposta delta não contém hits como objeto.")
    hits = hits_obj.get("hits", [])
    if not isinstance(hits, list):
        raise DataJudInvalidResponseError(
            "Resposta delta não contém hits.hits como lista."
        )
    return [hit for hit in hits if isinstance(hit, dict)]


def _extract_result_from_hit(
    hit: dict[str, Any],
    *,
    process_number: str,
    mode: MovementDeltaMode,
) -> MovementDeltaResult:
    fields = hit.get("fields")
    if not isinstance(fields, dict):
        if mode == "movements":
            return MovementDeltaResult(
                process_number=process_number,
                found=True,
                has_new_movements=False,
                movements=[],
            )
        raise DataJudInvalidResponseError(
            "Resposta delta não contém fields como objeto."
        )

    if mode == "status":
        raw_status = fields.get(STATUS_FIELD)
        if isinstance(raw_status, list) and len(raw_status) == 1:
            raw_status = raw_status[0]
        if not isinstance(raw_status, bool):
            raise DataJudInvalidResponseError(
                "Resposta delta não contém status booleano válido."
            )
        return MovementDeltaResult(
            process_number=process_number,
            found=True,
            has_new_movements=raw_status,
            movements=None,
        )

    raw_delta = fields.get(MOVEMENTS_FIELD)
    if (
        isinstance(raw_delta, list)
        and len(raw_delta) == 1
        and isinstance(raw_delta[0], list)
    ):
        raw_delta = raw_delta[0]
    if not isinstance(raw_delta, list) or not all(
        isinstance(movement, dict) for movement in raw_delta
    ):
        raise DataJudInvalidResponseError(
            "Resposta delta não contém lista de movimentações válida."
        )
    movements = [dict(movement) for movement in raw_delta]
    if process_number:
        for movement in movements:
            movement.setdefault("numeroProcesso", process_number)
    return MovementDeltaResult(
        process_number=process_number,
        found=True,
        has_new_movements=bool(movements),
        movements=movements,
    )
