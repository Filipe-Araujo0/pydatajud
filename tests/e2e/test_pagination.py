from __future__ import annotations

from typing import Any

import pytest

from pydatajud import (
    DataJudClient,
    DataJudRequestError,
    normalize_cnj_process_number,
    resolve_datajud_search_url,
)

pytestmark = pytest.mark.e2e


def _hits(payload: dict[str, Any]) -> list[dict[str, Any]]:
    hits_obj = payload.get("hits", {})
    assert isinstance(hits_obj, dict)
    raw_hits = hits_obj.get("hits", [])
    assert isinstance(raw_hits, list)
    return [item for item in raw_hits if isinstance(item, dict)]


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


def test_e2e_process_level_search_after_pagination(
    e2e_api_key: str,
    e2e_cases: dict[str, Any],
) -> None:
    processes = _configured_processes(e2e_cases, "pagination_processes", minimum=2)

    p1 = processes[0]
    p2 = processes[1]
    n1 = normalize_cnj_process_number(p1)
    n2 = normalize_cnj_process_number(p2)

    endpoint = resolve_datajud_search_url(p1)
    client = DataJudClient(api_key=e2e_api_key, timeout=60.0)

    body_page_1 = {
        "size": 1,
        "query": {"terms": {"numeroProcesso": [n1, n2]}},
        "sort": [{"numeroProcesso.keyword": "asc"}],
    }
    try:
        page_1 = client._search(endpoint, body_page_1, raise_not_found=False)
    except DataJudRequestError as exc:
        pytest.skip(f"Pagination query rejected by DataJud: {exc}")
    hits_1 = _hits(page_1)
    if not hits_1:
        pytest.skip("No hits returned for pagination fixture processes")

    sort_values = hits_1[0].get("sort")
    if not isinstance(sort_values, list) or not sort_values:
        pytest.skip("DataJud response did not include sort values for search_after")

    body_page_2 = {
        "size": 1,
        "query": {"terms": {"numeroProcesso": [n1, n2]}},
        "sort": [{"numeroProcesso.keyword": "asc"}],
        "search_after": sort_values,
    }
    try:
        page_2 = client._search(endpoint, body_page_2, raise_not_found=False)
    except DataJudRequestError as exc:
        pytest.skip(f"Second page query rejected by DataJud: {exc}")
    hits_2 = _hits(page_2)
    if not hits_2:
        pytest.skip("No second page returned for pagination fixture processes")

    s1 = hits_1[0].get("_source", {})
    s2 = hits_2[0].get("_source", {})
    if not isinstance(s1, dict) or not isinstance(s2, dict):
        pytest.skip("Missing _source in paginated hits")

    np1 = s1.get("numeroProcesso")
    np2 = s2.get("numeroProcesso")
    assert isinstance(np1, str)
    assert isinstance(np2, str)
    assert np1 != np2
