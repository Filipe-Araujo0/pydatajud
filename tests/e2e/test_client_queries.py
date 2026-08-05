from __future__ import annotations

from typing import Any

import pytest

from pydatajud import DataJudClient

pytestmark = pytest.mark.e2e


def _configured_process(e2e_cases: dict[str, Any], key: str) -> str:
    process = e2e_cases.get(key)
    if not isinstance(process, str) or not process:
        pytest.skip(f"Configure DATAJUD_E2E_{key.upper()} for this E2E case")
    return process


def _configured_processes(
    e2e_cases: dict[str, Any], key: str, minimum: int = 1
) -> list[str]:
    raw_processes = e2e_cases.get(key, [])
    if not isinstance(raw_processes, list):
        pytest.fail(f"{key} fixture must be a list")
    processes = [process for process in raw_processes if isinstance(process, str)]
    if len(processes) < minimum:
        pytest.skip(f"Configure DATAJUD_E2E_{key.upper()} for this E2E case")
    return processes


def test_e2e_single_process_contract(
    e2e_client: DataJudClient, e2e_cases: dict[str, Any]
) -> None:
    process_number = _configured_process(e2e_cases, "single_process")
    result = e2e_client.search_by_process_number(
        process_number, size=5, raise_not_found=False
    )

    assert result.endpoint.startswith("https://api-publica.datajud.cnj.jus.br/")
    assert result.total_hits >= 0
    assert isinstance(result.raw_hits, list)
    assert isinstance(result.movimentos, list)


def test_e2e_batch_groups_by_endpoint(
    e2e_client: DataJudClient, e2e_cases: dict[str, Any]
) -> None:
    processes = _configured_processes(e2e_cases, "batch_processes", minimum=2)

    result = e2e_client.search_by_process_numbers(
        processes, size=5, raise_not_found=False
    )

    assert isinstance(result, list)
    assert len(result) >= 2
    for partial in result:
        assert partial.endpoint.startswith("https://api-publica.datajud.cnj.jus.br/")
        assert partial.total_hits >= 0
        assert isinstance(partial.raw_hits, list)
