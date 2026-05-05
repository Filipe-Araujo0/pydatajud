import pytest

from pydatajud.exceptions import (
    InvalidCNJProcessNumberError,
    UnsupportedTribunalForDataJudError,
)
from pydatajud.resolver import (
    format_cnj_process_number,
    normalize_cnj_process_number,
    parse_cnj_process_number,
    resolve_datajud_alias,
    resolve_datajud_search_url,
)


def test_normalize_cnj_process_number_accepts_formatted_and_digits() -> None:
    assert (
        normalize_cnj_process_number("1234567-14.2024.8.19.0001")
        == "12345671420248190001"
    )
    assert (
        normalize_cnj_process_number("12345671420248190001") == "12345671420248190001"
    )


def test_format_cnj_process_number() -> None:
    assert (
        format_cnj_process_number("12345671420248190001") == "1234567-14.2024.8.19.0001"
    )


def test_parse_cnj_process_number_extracts_parts() -> None:
    parts = parse_cnj_process_number("1234567-14.2024.8.19.0001")
    assert parts.justica == 8
    assert parts.tribunal == 19
    assert parts.normalized == "12345671420248190001"


@pytest.mark.parametrize(
    ("process_number", "expected_alias"),
    [
        ("1234567-14.2024.8.19.0001", "tjrj"),
        ("1234567-95.2024.8.16.0001", "tjpr"),
        ("1234567-47.2024.8.07.0001", "tjdft"),
        ("1234567-91.2024.4.03.0001", "trf3"),
        ("1234567-74.2024.5.15.0001", "trt15"),
        ("1234567-84.2024.6.26.0001", "tre-sp"),
        ("1234567-35.2024.9.26.0001", "tjmsp"),
    ],
)
def test_resolve_datajud_alias(process_number: str, expected_alias: str) -> None:
    assert resolve_datajud_alias(process_number) == expected_alias


def test_resolve_datajud_search_url() -> None:
    assert (
        resolve_datajud_search_url("1234567-95.2024.8.16.0001")
        == "https://api-publica.datajud.cnj.jus.br/api_publica_tjpr/_search"
    )


@pytest.mark.parametrize(
    "process_number",
    [
        "123",
        "1234567-88.2024.8.19.0001",
    ],
)
def test_invalid_number_raises(process_number: str) -> None:
    with pytest.raises(InvalidCNJProcessNumberError):
        resolve_datajud_alias(process_number)


def test_unsupported_branch_raises() -> None:
    with pytest.raises(UnsupportedTribunalForDataJudError):
        resolve_datajud_alias("1234567-27.2024.1.00.0001")
