from __future__ import annotations

from typing import Any

import pytest

from pydatajud import DataJudClient

pytestmark = pytest.mark.e2e


def _hits(payload: dict[str, Any]) -> list[dict[str, Any]]:
    hits_obj = payload.get("hits", {})
    assert isinstance(hits_obj, dict)
    raw_hits = hits_obj.get("hits", [])
    assert isinstance(raw_hits, list)
    return [item for item in raw_hits if isinstance(item, dict)]


def _delta_processes(e2e_cases: dict[str, Any], minimum: int = 1) -> list[str]:
    raw_processes = e2e_cases.get("delta_processes", [])
    if not isinstance(raw_processes, list):
        pytest.fail("delta_processes fixture must be a list")
    processes = [process for process in raw_processes if isinstance(process, str)]
    if len(processes) < minimum:
        pytest.skip("Configure DATAJUD_E2E_DELTA_PROCESSES for this E2E case")
    return processes


def test_e2e_movements_delta_extract(
    e2e_client: DataJudClient, e2e_cases: dict[str, Any]
) -> None:
    process_number = _delta_processes(e2e_cases)[0]
    result = e2e_client.search_movements_delta(
        process_number,
        cutoff_iso="2020-01-01T00:00:00.000Z",
        mode="movements",
        size=1,
    )

    assert result.found
    assert result.has_new_movements
    assert result.movements
    assert all(isinstance(movement, dict) for movement in result.movements)
    assert all("numeroProcesso" in movement for movement in result.movements)


def test_e2e_delta_status_avoids_movement_transfer(
    e2e_client: DataJudClient, e2e_cases: dict[str, Any]
) -> None:
    process_number = _delta_processes(e2e_cases)[0]

    status = e2e_client.search_movements_delta(
        process_number,
        cutoff_iso="2020-01-01T00:00:00.000Z",
        mode="status",
    )

    assert status.found
    assert status.has_new_movements
    assert status.movements is None

    future = e2e_client.search_movements_delta(
        process_number,
        cutoff_iso="2999-01-01T00:00:00.000Z",
        mode="status",
    )
    assert future.found
    assert not future.has_new_movements
    assert future.movements is None


def test_e2e_delta_cutoff_is_strictly_greater(
    e2e_client: DataJudClient, e2e_cases: dict[str, Any]
) -> None:
    process_number = _delta_processes(e2e_cases)[0]

    initial = e2e_client.search_movements_delta(
        process_number,
        cutoff_iso="2020-01-01T00:00:00.000Z",
        mode="movements",
    )
    assert initial.movements
    timestamps: list[str] = []
    for movement in initial.movements:
        timestamp = movement.get("dataHora")
        if isinstance(timestamp, str):
            timestamps.append(timestamp)
    assert timestamps
    latest = max(timestamps)

    result = e2e_client.search_movements_delta(
        process_number,
        cutoff_iso=latest,
        mode="movements",
    )

    assert result.found
    assert all(
        movement.get("dataHora", "") > latest for movement in result.movements or []
    )


def test_e2e_delta_batch_returns_status_per_process(
    e2e_client: DataJudClient, e2e_cases: dict[str, Any]
) -> None:
    delta_processes = _delta_processes(e2e_cases, minimum=2)

    result = e2e_client.search_movements_delta_batch(
        dict.fromkeys(delta_processes[:2], "2020-01-01T00:00:00.000Z"),
        mode="status",
    )

    assert set(result) == set(delta_processes[:2])
    assert all(item.found for item in result.values())
    assert all(item.movements is None for item in result.values())


def test_e2e_delta_raw_mode_preserves_api_payload(
    e2e_client: DataJudClient, e2e_cases: dict[str, Any]
) -> None:
    process_number = _delta_processes(e2e_cases)[0]

    raw = e2e_client.search_movements_delta(
        process_number,
        cutoff_iso="2020-01-01T00:00:00.000Z",
        mode="status",
        raw=True,
    )

    assert "hits" in raw
    hits = _hits(raw)
    assert hits
    assert "_source" in hits[0]
    assert "movimentos" not in hits[0]["_source"]


def test_e2e_delta_distinguishes_not_found(
    e2e_client: DataJudClient, e2e_cases: dict[str, Any]
) -> None:
    process_number = e2e_cases["not_found_process"]
    if not isinstance(process_number, str) or not process_number:
        pytest.skip("Configure DATAJUD_E2E_NOT_FOUND_PROCESS for this E2E case")

    result = e2e_client.search_movements_delta(
        process_number,
        cutoff_iso="2020-01-01T00:00:00.000Z",
        mode="status",
    )

    assert not result.found
    assert not result.has_new_movements
    assert result.movements is None
