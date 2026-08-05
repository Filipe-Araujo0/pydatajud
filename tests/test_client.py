from typing import Any

import pytest
import requests

from pydatajud.client import DataJudClient, DataJudResult
from pydatajud.client_modules import extract_movements_delta
from pydatajud.exceptions import (
    DataJudAuthenticationError,
    DataJudInvalidResponseError,
    DataJudProcessNotFoundError,
    DataJudRequestError,
)


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        payload: object | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> object:
        if self._payload is None:
            raise ValueError("not json")
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError("erro http")


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def post(self, *args: object, **kwargs: object) -> FakeResponse:
        self.calls.append({"args": args, "kwargs": kwargs})
        return self.response


class FakeMultiSession:
    def __init__(self, responses_by_url: dict[str, FakeResponse]) -> None:
        self.responses_by_url = responses_by_url
        self.calls: list[dict[str, Any]] = []

    def post(self, *args: object, **kwargs: object) -> FakeResponse:
        self.calls.append({"args": args, "kwargs": kwargs})
        url = args[0]
        assert isinstance(url, str)
        return self.responses_by_url[url]


def test_search_by_process_number_extracts_movements() -> None:
    response = FakeResponse(
        200,
        {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {
                            "movimentos": [
                                {"codigo": 1, "nome": "Distribuição"},
                                "ignorado",
                            ]
                        }
                    }
                ],
            }
        },
    )
    session = FakeSession(response)

    result = DataJudClient(api_key="key", session=session).search_by_process_number(
        "0000001-12.2099.8.19.0001"
    )

    assert isinstance(result, DataJudResult)
    assert result.total_hits == 1
    assert result.movimentos == [{"codigo": 1, "nome": "Distribuição"}]
    assert result.endpoint.endswith("/api_publica_tjrj/_search")
    assert session.calls[0]["kwargs"]["json"] == {
        "size": 10,
        "query": {"match": {"numeroProcesso": "00000011220998190001"}},
    }


def test_search_by_process_number_can_return_empty_result() -> None:
    response = FakeResponse(200, {"hits": {"total": {"value": 0}, "hits": []}})
    result = DataJudClient(
        api_key="key", session=FakeSession(response)
    ).search_by_process_number("0000001-12.2099.8.19.0001", raise_not_found=False)

    assert result.total_hits == 0
    assert result.movimentos == []


def test_search_by_process_number_raises_not_found_by_default() -> None:
    response = FakeResponse(200, {"hits": {"total": {"value": 0}, "hits": []}})
    client = DataJudClient(api_key="key", session=FakeSession(response))

    with pytest.raises(DataJudProcessNotFoundError):
        client.search_by_process_number("0000001-12.2099.8.19.0001")


def test_authentication_error() -> None:
    client = DataJudClient(api_key="key", session=FakeSession(FakeResponse(403)))

    with pytest.raises(DataJudAuthenticationError):
        client.search_by_process_number("0000001-12.2099.8.19.0001")


def test_invalid_json_response() -> None:
    client = DataJudClient(api_key="key", session=FakeSession(FakeResponse(200)))

    with pytest.raises(DataJudInvalidResponseError):
        client.search_by_process_number("0000001-12.2099.8.19.0001")


def test_search_by_process_numbers_uses_single_query() -> None:
    response = FakeResponse(200, {"hits": {"total": {"value": 0}, "hits": []}})
    session = FakeSession(response)

    DataJudClient(api_key="key", session=session).search_by_process_numbers(
        [
            "0000001-12.2099.8.19.0001",
            "0000001-12.2099.8.19.0001",
        ],
        raise_not_found=False,
    )

    assert session.calls[0]["kwargs"]["json"] == {
        "size": 100,
        "query": {
            "bool": {
                "should": [
                    {"match": {"numeroProcesso": "00000011220998190001"}},
                ],
                "minimum_should_match": 1,
            }
        },
    }


def test_search_by_process_numbers_groups_by_endpoint() -> None:
    session = FakeMultiSession(
        {
            "https://api-publica.datajud.cnj.jus.br/api_publica_tjrj/_search": (
                FakeResponse(
                    200,
                    {
                        "hits": {
                            "total": {"value": 1},
                            "hits": [{"_source": {"movimentos": [{"nome": "A"}]}}],
                        }
                    },
                )
            ),
            "https://api-publica.datajud.cnj.jus.br/api_publica_trf1/_search": (
                FakeResponse(
                    200,
                    {
                        "hits": {
                            "total": {"value": 2},
                            "hits": [{"_source": {"movimentos": [{"nome": "B"}]}}],
                        }
                    },
                )
            ),
        }
    )
    client = DataJudClient(api_key="key", session=session)

    result = client.search_by_process_numbers(
        [
            "0000001-12.2099.8.19.0001",
            "0000001-46.2099.4.01.0001",
        ],
        raise_not_found=False,
    )

    assert len(session.calls) == 2
    assert len(result) == 2
    totals = sorted(response.total_hits for response in result)
    assert totals == [1, 2]


def test_http_error_does_not_leak_api_key() -> None:
    api_key = "secret-api-key-value"
    response = FakeResponse(500, text=f"request rejected for {api_key}")
    client = DataJudClient(api_key=api_key, session=FakeSession(response))

    with pytest.raises(DataJudRequestError) as exc_info:
        client.search_by_process_number("0000001-12.2099.8.19.0001")

    assert api_key not in str(exc_info.value)
    assert "[REDACTED]" in str(exc_info.value)


def test_search_movements_delta_builds_script_fields_request() -> None:
    response = FakeResponse(200, {"hits": {"total": {"value": 1}, "hits": [{}]}})
    session = FakeSession(response)
    client = DataJudClient(api_key="key", session=session)

    client.search_movements_delta(
        "0000001-17.2099.8.26.0001",
        cutoff_iso="2025-01-01T00:00:00.000Z",
        mode="movements",
        raw=True,
    )

    payload = session.calls[0]["kwargs"]["json"]
    assert payload["size"] == 1
    assert payload["_source"] == ["numeroProcesso"]
    assert payload["query"]["match"]["numeroProcesso"] == "00000011720998260001"
    script_fields = payload["script_fields"]["movimentos_delta"]["script"]
    assert script_fields["params"]["cutoff"] == "2025-01-01T00:00:00.000Z"


def test_search_movements_delta_status_uses_short_query() -> None:
    response = FakeResponse(200, {"hits": {"total": {"value": 1}, "hits": [{}]}})
    session = FakeSession(response)
    client = DataJudClient(api_key="key", session=session)

    client.search_movements_delta(
        "0000001-17.2099.8.26.0001",
        cutoff_iso="2025-01-01T00:00:00.000Z",
        mode="status",
        raw=True,
    )

    payload = session.calls[0]["kwargs"]["json"]
    assert payload["_source"] == ["numeroProcesso"]
    assert "movimentos_delta_status" in payload["script_fields"]
    assert "movimentos_delta" not in payload["script_fields"]


def test_search_movements_delta_returns_typed_status() -> None:
    response = FakeResponse(
        200,
        {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {"numeroProcesso": "00000011720998260001"},
                        "fields": {"movimentos_delta_status": [True]},
                    }
                ],
            }
        },
    )
    client = DataJudClient(api_key="key", session=FakeSession(response))

    result = client.search_movements_delta(
        "0000001-17.2099.8.26.0001",
        cutoff_iso="2025-01-01T00:00:00.000Z",
    )

    assert result.process_number == "0000001-17.2099.8.26.0001"
    assert result.found is True
    assert result.has_new_movements is True
    assert result.movements is None


def test_search_movements_delta_returns_typed_movements() -> None:
    response = FakeResponse(
        200,
        {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {"numeroProcesso": "00000011720998260001"},
                        "fields": {
                            "movimentos_delta": [
                                {"dataHora": "2025-01-02T00:00:00.000Z"}
                            ]
                        },
                    }
                ],
            }
        },
    )
    client = DataJudClient(api_key="key", session=FakeSession(response))

    result = client.search_movements_delta(
        "0000001-17.2099.8.26.0001",
        cutoff_iso="2025-01-01T00:00:00.000Z",
        mode="movements",
    )

    assert result.found is True
    assert result.has_new_movements is True
    assert result.movements == [
        {
            "dataHora": "2025-01-02T00:00:00.000Z",
            "numeroProcesso": "0000001-17.2099.8.26.0001",
        }
    ]


def test_search_movements_delta_returns_not_found_status() -> None:
    response = FakeResponse(200, {"hits": {"total": {"value": 0}, "hits": []}})
    client = DataJudClient(api_key="key", session=FakeSession(response))

    result = client.search_movements_delta(
        "0000001-17.2099.8.26.0001",
        cutoff_iso="2025-01-01T00:00:00.000Z",
    )

    assert result.found is False
    assert result.has_new_movements is False
    assert result.movements is None


def test_search_movements_delta_treats_missing_fields_as_empty_movements() -> None:
    response = FakeResponse(
        200,
        {
            "hits": {
                "total": {"value": 1},
                "hits": [{"_source": {"numeroProcesso": "00000011720998260001"}}],
            }
        },
    )
    client = DataJudClient(api_key="key", session=FakeSession(response))

    result = client.search_movements_delta(
        "0000001-17.2099.8.26.0001",
        cutoff_iso="2025-01-01T00:00:00.000Z",
        mode="movements",
    )

    assert result.found is True
    assert result.has_new_movements is False
    assert result.movements == []


def test_search_movements_delta_rejects_invalid_cutoff_before_network() -> None:
    session = FakeSession(FakeResponse(200, {"hits": {"hits": []}}))

    with pytest.raises(ValueError, match="UTC ISO-8601"):
        DataJudClient(api_key="key", session=session).search_movements_delta(
            "0000001-17.2099.8.26.0001",
            cutoff_iso="2025-01-01T00:00:00",
        )

    assert session.calls == []


def test_search_movements_delta_batch_groups_by_endpoint() -> None:
    response = FakeResponse(200, {"hits": {"total": {"value": 1}, "hits": [{}]}})
    session = FakeSession(response)
    client = DataJudClient(api_key="key", session=session)

    result = client.search_movements_delta_batch(
        {
            "0000001-17.2099.8.26.0001": "2025-01-01T00:00:00.000Z",
            "0000003-84.2099.8.26.0001": "2025-01-01T00:00:00.000Z",
        },
        mode="movements",
        raw=True,
        raise_not_found=False,
    )

    assert len(result) == 1
    payload = session.calls[0]["kwargs"]["json"]
    assert payload["_source"] == ["numeroProcesso"]
    assert payload["query"]["terms"]["numeroProcesso"] == [
        "00000011720998260001",
        "00000038420998260001",
    ]
    assert payload["script_fields"]["movimentos_delta"]["script"]["params"] == {
        "cutoffs": {
            "00000011720998260001": "2025-01-01T00:00:00.000Z",
            "00000038420998260001": "2025-01-01T00:00:00.000Z",
        }
    }


def test_search_movements_delta_batch_returns_status_for_each_process() -> None:
    response = FakeResponse(
        200,
        {
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {
                        "_source": {"numeroProcesso": "00000011720998260001"},
                        "fields": {"movimentos_delta_status": [True]},
                    },
                    {
                        "_source": {"numeroProcesso": "00000038420998260001"},
                        "fields": {"movimentos_delta_status": [False]},
                    },
                ],
            }
        },
    )
    session = FakeSession(response)
    client = DataJudClient(api_key="key", session=session)

    result = client.search_movements_delta_batch(
        {
            "0000001-17.2099.8.26.0001": "2025-01-01T00:00:00.000Z",
            "0000003-84.2099.8.26.0001": "2025-01-01T00:00:00.000Z",
        }
    )

    assert result["0000001-17.2099.8.26.0001"].has_new_movements is True
    assert result["0000003-84.2099.8.26.0001"].has_new_movements is False
    assert session.calls[0]["kwargs"]["json"]["_source"] == ["numeroProcesso"]


def test_search_movements_delta_batch_preserves_missing_process_status() -> None:
    response = FakeResponse(
        200,
        {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {"numeroProcesso": "00000011720998260001"},
                        "fields": {"movimentos_delta_status": [False]},
                    }
                ],
            }
        },
    )
    client = DataJudClient(api_key="key", session=FakeSession(response))

    result = client.search_movements_delta_batch(
        {
            "0000001-17.2099.8.26.0001": "2025-01-01T00:00:00.000Z",
            "0000003-84.2099.8.26.0001": "2025-01-01T00:00:00.000Z",
        }
    )

    assert result["0000001-17.2099.8.26.0001"].found is True
    assert result["0000003-84.2099.8.26.0001"].found is False


def test_extract_movements_delta() -> None:
    payload: dict[str, Any] = {
        "hits": {
            "hits": [
                {
                    "_source": {"numeroProcesso": "123"},
                    "fields": {
                        "movimentos_delta": [
                            {"dataHora": "2025-01-02T00:00:00.000Z", "codigo": 1}
                        ]
                    },
                }
            ]
        }
    }

    assert extract_movements_delta(payload) == [
        {
            "dataHora": "2025-01-02T00:00:00.000Z",
            "codigo": 1,
            "numeroProcesso": "123",
        }
    ]
