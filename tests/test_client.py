from typing import Any

import pytest
import requests

from pydatajud.client import DataJudClient
from pydatajud.exceptions import (
    DataJudAuthenticationError,
    DataJudInvalidResponseError,
    DataJudProcessNotFoundError,
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
        "1234567-14.2024.8.19.0001"
    )

    assert result.total_hits == 1
    assert result.movimentos == [{"codigo": 1, "nome": "Distribuição"}]
    assert result.endpoint.endswith("/api_publica_tjrj/_search")
    assert session.calls[0]["kwargs"]["json"] == {
        "size": 10,
        "query": {"match": {"numeroProcesso": "12345671420248190001"}},
    }


def test_search_by_process_number_can_return_empty_result() -> None:
    response = FakeResponse(200, {"hits": {"total": {"value": 0}, "hits": []}})
    result = DataJudClient(
        api_key="key", session=FakeSession(response)
    ).search_by_process_number("1234567-14.2024.8.19.0001", raise_not_found=False)

    assert result.total_hits == 0
    assert result.movimentos == []


def test_search_by_process_number_raises_not_found_by_default() -> None:
    response = FakeResponse(200, {"hits": {"total": {"value": 0}, "hits": []}})
    client = DataJudClient(api_key="key", session=FakeSession(response))

    with pytest.raises(DataJudProcessNotFoundError):
        client.search_by_process_number("1234567-14.2024.8.19.0001")


def test_authentication_error() -> None:
    client = DataJudClient(api_key="key", session=FakeSession(FakeResponse(403)))

    with pytest.raises(DataJudAuthenticationError):
        client.search_by_process_number("1234567-14.2024.8.19.0001")


def test_invalid_json_response() -> None:
    client = DataJudClient(api_key="key", session=FakeSession(FakeResponse(200)))

    with pytest.raises(DataJudInvalidResponseError):
        client.search_by_process_number("1234567-14.2024.8.19.0001")
