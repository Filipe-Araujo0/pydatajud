import json

import pytest

from pydatajud import cli


class FakeResult:
    endpoint = "https://api-publica.datajud.cnj.jus.br/api_publica_tjrj/_search"
    total_hits = 1
    movimentos = [{"nome": "Movimento"}]


class FakeClient:
    def __init__(self, api_key: str, timeout: float) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def search_by_process_number(self, process_number: str, size: int) -> FakeResult:
        assert process_number == "1234567-14.2024.8.19.0001"
        assert size == 10
        return FakeResult()


def test_cli_prints_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "DataJudClient", FakeClient)

    exit_code = cli.main(
        [
            "--api-key",
            "key",
            "--processo",
            "1234567-14.2024.8.19.0001",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["total_hits"] == 1
    assert payload["movimentos_count"] == 1


def test_cli_uses_env_api_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DATAJUD_API_KEY", "env-key")
    monkeypatch.setattr(cli, "DataJudClient", FakeClient)

    exit_code = cli.main(["--processo", "1234567-14.2024.8.19.0001"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["movimentos"] == [{"nome": "Movimento"}]
