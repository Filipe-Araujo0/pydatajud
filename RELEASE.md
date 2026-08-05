# Release

## PyPI com Trusted Publishing/OIDC

O projeto publica no PyPI por GitHub Actions sem token salvo no repositório.

Configuração necessária no PyPI:

1. Criar o projeto `pydatajud` no PyPI ou fazer o primeiro upload autorizado.
2. Em `Publishing`, adicionar um trusted publisher:
   - Owner: `Filipe-Araujo0`
   - Repository: `pydatajud`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`

## Processo de release
<!-- Atualizado em: 2026-08-05T11:42:22-03:00 -->

1. Atualizar `version` em `pyproject.toml`.
2. Atualizar `CHANGELOG.md`.
3. Rodar os checks locais.
4. Criar e enviar tag:

```bash
git tag v0.2.0
git push origin main
git push origin v0.2.0
```

O workflow `publish.yml` irá gerar `sdist`/`wheel` e publicar no PyPI.
