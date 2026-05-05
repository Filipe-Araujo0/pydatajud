# Contribuindo

Obrigado por considerar contribuir com o `pydatajud`.

Antes de contribuir, leia também o [AGENTS.md](./AGENTS.md). Ele documenta a
visão do projeto, o padrão de qualidade esperado e decisões práticas para novos
contribuidores.

## Idioma

As documentações gerais podem estar em português brasileiro porque o `pydatajud`
é um wrapper de um sistema brasileiro e tem desenvolvedores brasileiros como
público inicial.

O código em si deve seguir o padrão internacional de bibliotecas Python:
identificadores, módulos, classes, funções, comentários técnicos e docstrings
devem ser escritos em inglês.

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

## Documentação obrigatória

Toda mudança deve revisar a documentação relacionada. Isso é parte obrigatória
da definição de pronto do projeto, não uma etapa opcional.

Antes de abrir PR ou fazer commit, confira explicitamente se a mudança exige
atualização em:

- `README.md`
- `docs/`
- `CONTRIBUTING.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `gitree.txt`

Mudanças em comportamento público, CLI, exceções, empacotamento, release,
resolver, estrutura de resposta ou premissas sobre DataJud/CNJ devem atualizar a
documentação correspondente.

## Efetivando mudanças

Fluxo padrão:

```bash
ruff format --check .
ruff check .
mypy src tests
pytest
git add <arquivos-alterados>
git commit -m "<tipo>: <resumo imperativo curto>"
git push origin main
```

Para publicar uma nova versão no PyPI:

```bash
python -m build
twine check dist/*
git tag vX.Y.Z
git push origin vX.Y.Z
```

Antes de criar a tag, atualize `version` no `pyproject.toml` e registre a versão
no `CHANGELOG.md`. Não crie tag de release apontando para uma versão já publicada
no PyPI.

## Diretrizes

- Mantenha a suíte padrão sem chamadas reais à API do CNJ.
- Use mocks para testes de HTTP.
- Documente mudanças de API no `CHANGELOG.md`.
- Não inclua chaves de API, dados sensíveis ou números de processos sigilosos.
- Atualize `gitree.txt` quando adicionar ou remover arquivos versionáveis.
