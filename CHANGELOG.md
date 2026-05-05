# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

O formato segue a ideia de manter versões legíveis por humanos e tags semânticas.

## [0.1.1] - 2026-05-05

### Added

- `AGENTS.md` com visão do projeto, padrões de qualidade, fluxo de mudança e
  política explícita de documentação obrigatória.
- `docs/datajud-resolver.md` explicando a lógica de resolução de endpoint baseada
  na estrutura CNJ e no contexto do judiciário brasileiro.
- `gitree.txt` versionado como mapa rápido de navegação do repositório.

### Changed

- `README.md` com seção explícita sobre a API key pública vigente na wiki oficial
  do DataJud e nota de que a chave pode mudar.
- `CONTRIBUTING.md` reforçando documentação como requisito obrigatório e com
  passos concretos para efetivar mudanças e release.
- `.gitignore` para ignorar dumps locais de consultas (`processo_*_full.json`).

## [0.1.0] - 2026-05-05

### Added

- Cliente síncrono para a API pública do DataJud.
- Resolução automática de endpoint a partir do número CNJ.
- CLI `pydatajud` com saída JSON.
- Testes unitários para resolvedor, cliente e CLI.
