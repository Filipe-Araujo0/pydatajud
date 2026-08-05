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
        normalize_cnj_process_number("0000001-12.2099.8.19.0001")
        == "00000011220998190001"
    )
    assert (
        normalize_cnj_process_number("00000011220998190001") == "00000011220998190001"
    )


def test_format_cnj_process_number() -> None:
    assert (
        format_cnj_process_number("00000011220998190001") == "0000001-12.2099.8.19.0001"
    )


def test_parse_cnj_process_number_extracts_parts() -> None:
    parts = parse_cnj_process_number("0000001-12.2099.8.19.0001")
    assert parts.justica == 8
    assert parts.tribunal == 19
    assert parts.normalized == "00000011220998190001"


@pytest.mark.parametrize(
    ("process_number", "expected_alias"),
    [
        ("0000001-12.2099.8.19.0001", "tjrj"),
        ("0000001-93.2099.8.16.0001", "tjpr"),
        ("0000001-45.2099.8.07.0001", "tjdft"),
        ("0000001-89.2099.4.03.0001", "trf3"),
        ("0000001-72.2099.5.15.0001", "trt15"),
        ("0000001-82.2099.6.26.0001", "tre-sp"),
        ("0000001-33.2099.9.26.0001", "tjmsp"),
    ],
)
def test_resolve_datajud_alias(process_number: str, expected_alias: str) -> None:
    assert resolve_datajud_alias(process_number) == expected_alias


def test_resolve_datajud_search_url() -> None:
    assert (
        resolve_datajud_search_url("0000001-93.2099.8.16.0001")
        == "https://api-publica.datajud.cnj.jus.br/api_publica_tjpr/_search"
    )


@pytest.mark.parametrize(
    "process_number",
    [
        "123",
        "0000001-99.2099.8.19.0001",
    ],
)
def test_invalid_number_raises(process_number: str) -> None:
    with pytest.raises(InvalidCNJProcessNumberError):
        resolve_datajud_alias(process_number)


def test_unsupported_branch_raises() -> None:
    with pytest.raises(UnsupportedTribunalForDataJudError):
        resolve_datajud_alias("0000001-25.2099.1.00.0001")
