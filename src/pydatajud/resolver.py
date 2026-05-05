import re
from dataclasses import dataclass

from pydatajud.exceptions import (
    InvalidCNJProcessNumberError,
    UnsupportedTribunalForDataJudError,
)

DATAJUD_BASE_URL = "https://api-publica.datajud.cnj.jus.br"

_UF_BY_TR_CODE = {
    1: "ac",
    2: "al",
    3: "ap",
    4: "am",
    5: "ba",
    6: "ce",
    7: "dft",
    8: "es",
    9: "go",
    10: "ma",
    11: "mt",
    12: "ms",
    13: "mg",
    14: "pa",
    15: "pb",
    16: "pr",
    17: "pe",
    18: "pi",
    19: "rj",
    20: "rn",
    21: "rs",
    22: "ro",
    23: "rr",
    24: "sc",
    25: "se",
    26: "sp",
    27: "to",
}

_SPECIAL_ALIASES = {
    (3, 0): "stj",
    (4, 1): "trf1",
    (4, 2): "trf2",
    (4, 3): "trf3",
    (4, 4): "trf4",
    (4, 5): "trf5",
    (4, 6): "trf6",
    (5, 0): "tst",
    (6, 0): "tse",
    (7, 0): "stm",
    (9, 13): "tjmmg",
    (9, 21): "tjmrs",
    (9, 26): "tjmsp",
}

_CNJ_DIGITS_RE = re.compile(r"^\d{20}$")


@dataclass(frozen=True)
class CNJProcessNumberParts:
    normalized: str
    formatted: str
    sequencial: str
    dv: str
    ano: str
    justica: int
    tribunal: int
    origem: str


def normalize_cnj_process_number(process_number: str) -> str:
    normalized = re.sub(r"\D", "", process_number)
    if _CNJ_DIGITS_RE.fullmatch(normalized) is None:
        raise InvalidCNJProcessNumberError(
            "Formato inválido. Use NNNNNNN-DD.AAAA.J.TR.OOOO ou 20 dígitos."
        )
    return normalized


def format_cnj_process_number(process_number: str) -> str:
    normalized = normalize_cnj_process_number(process_number)
    return (
        f"{normalized[:7]}-{normalized[7:9]}.{normalized[9:13]}."
        f"{normalized[13]}.{normalized[14:16]}.{normalized[16:]}"
    )


def parse_cnj_process_number(process_number: str) -> CNJProcessNumberParts:
    normalized = normalize_cnj_process_number(process_number)
    formatted = format_cnj_process_number(normalized)

    parts = CNJProcessNumberParts(
        normalized=normalized,
        formatted=formatted,
        sequencial=normalized[:7],
        dv=normalized[7:9],
        ano=normalized[9:13],
        justica=int(normalized[13]),
        tribunal=int(normalized[14:16]),
        origem=normalized[16:],
    )
    if not is_valid_cnj_process_number(parts):
        raise InvalidCNJProcessNumberError("Dígito verificador CNJ inválido")
    return parts


def is_valid_cnj_process_number(parts: CNJProcessNumberParts) -> bool:
    op_dv = int(parts.sequencial) % 97
    op1 = int(f"{op_dv}{parts.ano}{parts.justica}{parts.tribunal:02d}") % 97
    op2 = int(f"{op1}{parts.origem}{parts.dv}") % 97
    return op2 == 1


def resolve_datajud_alias(process_number: str) -> str:
    parts = parse_cnj_process_number(process_number)
    special = _SPECIAL_ALIASES.get((parts.justica, parts.tribunal))
    if special is not None:
        return special

    if parts.justica == 5 and 1 <= parts.tribunal <= 24:
        return f"trt{parts.tribunal}"
    if parts.justica == 4 and 1 <= parts.tribunal <= 6:
        return f"trf{parts.tribunal}"

    uf = _UF_BY_TR_CODE.get(parts.tribunal)
    if uf is None:
        raise UnsupportedTribunalForDataJudError("Código TR sem mapeamento")

    if parts.justica == 8:
        return f"tj{uf}"
    if parts.justica == 6:
        return f"tre-{uf}"

    raise UnsupportedTribunalForDataJudError(
        f"Sem endpoint DataJud para J={parts.justica} TR={parts.tribunal:02d}"
    )


def resolve_datajud_search_url(process_number: str) -> str:
    return (
        f"{DATAJUD_BASE_URL}/api_publica_{resolve_datajud_alias(process_number)}"
        "/_search"
    )
