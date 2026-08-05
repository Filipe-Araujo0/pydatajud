import json
import os
from pathlib import Path
from typing import Any

import pytest

from pydatajud import DataJudClient

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "processes.json"


def _read_cases() -> dict[str, Any]:
    with FIXTURES_PATH.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, dict):
        raise RuntimeError("E2E fixture file must be a JSON object")
    return data


@pytest.fixture(scope="session")
def e2e_api_key() -> str:
    api_key = os.getenv("DATAJUD_API_KEY", "").strip()
    if not api_key:
        pytest.skip("DATAJUD_API_KEY is not set; skipping real DataJud E2E tests")
    return api_key


@pytest.fixture(scope="session")
def e2e_client(e2e_api_key: str) -> DataJudClient:
    return DataJudClient(api_key=e2e_api_key, timeout=60.0)


@pytest.fixture(scope="session")
def e2e_cases() -> dict[str, Any]:
    cases = _read_cases()

    single_default = str(cases.get("single_process", "")).strip()
    single_env = os.getenv("DATAJUD_E2E_SINGLE_PROCESS", "").strip()
    single_process = single_env or single_default

    batch_defaults = cases.get("batch_processes", [])
    if not isinstance(batch_defaults, list):
        raise RuntimeError("batch_processes must be a JSON list")
    batch_env = os.getenv("DATAJUD_E2E_BATCH_PROCESSES", "").strip()
    batch_processes = (
        [p.strip() for p in batch_env.split(",") if p.strip()]
        if batch_env
        else [str(p).strip() for p in batch_defaults if str(p).strip()]
    )

    pagination_defaults = cases.get("pagination_processes", [])
    if not isinstance(pagination_defaults, list):
        raise RuntimeError("pagination_processes must be a JSON list")
    pagination_env = os.getenv("DATAJUD_E2E_PAGINATION_PROCESSES", "").strip()
    pagination_processes = (
        [p.strip() for p in pagination_env.split(",") if p.strip()]
        if pagination_env
        else [str(p).strip() for p in pagination_defaults if str(p).strip()]
    )

    delta_defaults = cases.get("delta_processes", [])
    if not isinstance(delta_defaults, list):
        raise RuntimeError("delta_processes must be a JSON list")
    delta_env = os.getenv("DATAJUD_E2E_DELTA_PROCESSES", "").strip()
    delta_processes = (
        [p.strip() for p in delta_env.split(",") if p.strip()]
        if delta_env
        else [str(p).strip() for p in delta_defaults if str(p).strip()]
    )

    not_found_default = str(cases.get("not_found_process", "")).strip()
    not_found_process = (
        os.getenv("DATAJUD_E2E_NOT_FOUND_PROCESS", "").strip() or not_found_default
    )

    return {
        "single_process": single_process,
        "batch_processes": batch_processes,
        "pagination_processes": pagination_processes,
        "delta_processes": delta_processes,
        "not_found_process": not_found_process,
    }
