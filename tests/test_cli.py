import json
from dataclasses import asdict

import pytest

from pydatajud import DataJudResult, MovementDeltaResult, cli


class FakeClient:
    def __init__(self, api_key: str, timeout: float) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def search_by_process_number(self, process_number: str, size: int) -> DataJudResult:
        assert process_number == "0000001-12.2099.8.19.0001"
        assert size == 10
        return DataJudResult(
            endpoint="https://api-publica.datajud.cnj.jus.br/api_publica_tjrj/_search",
            total_hits=1,
            raw_hits=[],
            movimentos=[{"nome": "Movimento"}],
        )

    def search_movements_delta(
        self,
        process_number: str,
        cutoff_iso: str,
        mode: str,
        size: int,
        raw: bool,
    ) -> object:
        assert process_number == "0000001-12.2099.8.19.0001"
        assert cutoff_iso == "2025-01-01T00:00:00.000Z"
        assert size == 10
        result = MovementDeltaResult(
            process_number=process_number,
            found=True,
            has_new_movements=mode == "movements",
            movements=[{"nome": "Movimento"}] if mode == "movements" else None,
        )
        return {"raw": True} if raw else result


def test_cli_prints_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "DataJudClient", FakeClient)

    exit_code = cli.main(
        [
            "--api-key",
            "key",
            "--processo",
            "0000001-12.2099.8.19.0001",
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

    exit_code = cli.main(
        ["--processo", "0000001-12.2099.8.19.0001", "--movimentos-only"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == [{"nome": "Movimento"}]


def test_cli_delta_defaults_to_typed_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "DataJudClient", FakeClient)

    exit_code = cli.main(
        [
            "--api-key",
            "key",
            "--processo",
            "0000001-12.2099.8.19.0001",
            "--cutoff",
            "2025-01-01T00:00:00.000Z",
            "--mode",
            "movements",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == asdict(
        MovementDeltaResult(
            process_number="0000001-12.2099.8.19.0001",
            found=True,
            has_new_movements=True,
            movements=[{"nome": "Movimento"}],
        )
    )


def test_cli_delta_can_print_raw_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "DataJudClient", FakeClient)

    exit_code = cli.main(
        [
            "--api-key",
            "key",
            "--processo",
            "0000001-12.2099.8.19.0001",
            "--cutoff",
            "2025-01-01T00:00:00.000Z",
            "--raw",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {"raw": True}
