# pydatajud

Cliente Python para consultar a API pública do DataJud/CNJ por número CNJ e
extrair movimentações processuais em formato estruturado.

O projeto não é afiliado ao CNJ. Ele apenas empacota um fluxo comum de consulta
à API pública oficial.

## Instalação

```bash
pip install pydatajud
```

Para desenvolvimento local:

```bash
pip install -e ".[dev]"
```

## Uso rápido

```python
from pydatajud import DataJudClient

client = DataJudClient(api_key="sua-api-key")
result = client.search_by_process_number("0000832-35.2018.4.01.3202")

print(result.endpoint)
print(result.movimentos)
```

## CLI

```bash
export DATAJUD_API_KEY="sua-api-key"
pydatajud --processo "0000832-35.2018.4.01.3202"
```

Também é possível passar a chave diretamente:

```bash
pydatajud --api-key "sua-api-key" --processo "0000832-35.2018.4.01.3202"
```

Para imprimir apenas a lista de movimentações:

```bash
pydatajud --processo "0000832-35.2018.4.01.3202" --movimentos-only
```

## O que a biblioteca faz

- Valida e normaliza números processuais CNJ.
- Resolve automaticamente o endpoint DataJud a partir dos campos `J` e `TR`.
- Consulta o endpoint público correspondente.
- Retorna os `hits` brutos e a lista agregada de `movimentos`.
- Expõe erros próprios para autenticação, resposta inválida, processo não
  encontrado e tribunal sem endpoint mapeado.

## Limitações

- A API pública do DataJud exige chave `APIKey`.
- Processos sigilosos ou indisponíveis na base pública podem não retornar dados.
- A cobertura, disponibilidade e regras de uso são definidas pelo CNJ.
- O usuário é responsável por cumprir os termos de uso do CNJ e a legislação
  aplicável, incluindo LGPD.

## Desenvolvimento

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src tests
pytest
python -m build
twine check dist/*
```

## Links úteis

- API pública do DataJud: https://www.cnj.jus.br/sistemas/datajud/api-publica/
- Wiki DataJud: https://datajud-wiki.cnj.jus.br/api-publica/
- Termos de uso: https://formularios.cnj.jus.br/wp-content/uploads/2023/11/Termos-de-uso-api-publica-V1.2.pdf
