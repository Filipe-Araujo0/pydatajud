import argparse
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict, is_dataclass

from pydatajud.client import DEFAULT_TIMEOUT, DataJudClient
from pydatajud.exceptions import DataJudError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consulta API pública do DataJud")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("DATAJUD_API_KEY"),
        help="API key do DataJud. Também pode ser definida em DATAJUD_API_KEY.",
    )
    parser.add_argument("--processo", required=True, help="Número CNJ")
    parser.add_argument("--size", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--cutoff",
        help="Timestamp UTC ISO-8601 para consulta incremental de movimentações.",
    )
    parser.add_argument(
        "--mode",
        choices=["status", "movements"],
        default="status",
        help=(
            "Modo de verificação: status não baixa movimentações pela rede; "
            "movements retorna os itens."
        ),
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Imprime o payload raw da API em vez do resultado tipado.",
    )
    parser.add_argument(
        "--movimentos-only",
        action="store_true",
        help="Imprime apenas a lista de movimentações.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.api_key is None:
        parser.error("informe --api-key ou defina DATAJUD_API_KEY")
    if args.cutoff is None and args.mode != "status":
        parser.error("--mode movements exige --cutoff")

    try:
        client = DataJudClient(api_key=args.api_key, timeout=args.timeout)
        if args.cutoff is not None:
            if args.movimentos_only:
                parser.error("--movimentos-only não pode ser usado com --cutoff")
            result = client.search_movements_delta(
                args.processo,
                cutoff_iso=args.cutoff,
                mode=args.mode,
                size=args.size,
                raw=args.raw,
            )
            payload: object = result if args.raw else _serialize_typed_result(result)
        else:
            result = client.search_by_process_number(args.processo, size=args.size)
            if args.movimentos_only:
                payload = result.movimentos
            else:
                payload = {
                    "endpoint": result.endpoint,
                    "total_hits": result.total_hits,
                    "movimentos_count": len(result.movimentos),
                    "movimentos": result.movimentos,
                }
    except (DataJudError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


def _serialize_typed_result(result: object) -> object:
    if is_dataclass(result) and not isinstance(result, type):
        return asdict(result)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
