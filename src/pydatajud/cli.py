import argparse
import json
import os
import sys
from collections.abc import Sequence

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

    try:
        client = DataJudClient(api_key=args.api_key, timeout=args.timeout)
        result = client.search_by_process_number(args.processo, size=args.size)
    except DataJudError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    if args.movimentos_only:
        payload: object = result.movimentos
    else:
        payload = {
            "endpoint": result.endpoint,
            "total_hits": result.total_hits,
            "movimentos_count": len(result.movimentos),
            "movimentos": result.movimentos,
        }

    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
