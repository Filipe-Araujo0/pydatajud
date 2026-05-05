# Contribuindo

Obrigado por considerar contribuir com o `pydatajud`.

## Ambiente local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Checks antes de abrir PR

```bash
ruff check .
ruff format --check .
mypy src tests
pytest
python -m build
twine check dist/*
```

## Diretrizes

- Mantenha a suíte padrão sem chamadas reais à API do CNJ.
- Use mocks para testes de HTTP.
- Documente mudanças de API no `CHANGELOG.md`.
- Não inclua chaves de API, dados sensíveis ou números de processos sigilosos.
