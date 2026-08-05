# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

O formato segue a ideia de manter versões legíveis por humanos e tags semânticas.

## [Unreleased]

Nenhuma mudança registrada.

## [0.2.0] - 2026-08-05
<!-- Atualizado em: 2026-08-05T11:42:22-03:00 -->

### Added

- `DataJudClient.search_by_process_numbers(...)` para consulta de múltiplos números CNJ com agregação de resultados.
- Interface unificada para verificar novas movimentações, com `mode="status"` para consultar apenas o status e `mode="movements"` para receber os itens posteriores ao cutoff.
- Resultado tipado `MovementDeltaResult` e versões individuais e em lote da verificação.
- Builders e extratores em `src/pydatajud/client_modules/movements_delta.py`.
- Suíte `tests/e2e/` com testes de integração real contra a API pública do DataJud, separada por marker `e2e` e com fixtures fornecidas por variáveis de ambiente.
- Workflow opcional `.github/workflows/e2e.yml` (manual e agendado) para executar E2E com `DATAJUD_API_KEY` e processos via GitHub Secrets.
- Marker pytest `e2e` configurado em `pyproject.toml`.

### Changed

- Consultas em lote agora agrupam processos por tribunal e fazem uma requisição por grupo, em vez de uma requisição por processo.
- Consultas em lote eliminam números duplicados dentro de cada tribunal antes de montar a requisição.
- O modo `status` mantém as listas de movimentações fora da resposta HTTP, reduzindo payload e tráfego de rede quando a aplicação só precisa saber quais processos mudaram.
- O modo `movements` retorna as movimentações posteriores ao cutoff; quando o DataJud omite `fields` para um processo sem novidades, o cliente interpreta o resultado como lista vazia.
- A CLI usa saída tipada por padrão nas verificações e mantém `--raw` como opção avançada.
- `DataJudClient.search_by_process_number(...)` preserva o resultado tipado `DataJudResult` da versão `0.1.1`; a consulta em lote retorna uma lista do mesmo tipo, e a nova interface de verificação oferece `MovementDeltaResult`.
- Erros HTTP removem a API key do trecho de resposta incluído na exceção.
- O README foi reorganizado para destacar a verificação em lote como principal caso de uso, com exemplos tipados, saídas ilustrativas, valores CNJ sintéticos e explicação da eficiência de rede.
- O README também destaca o resolvedor CNJ como recurso independente para validação, normalização e identificação do tribunal sem rede.
- A documentação explica que o conteúdo de movimentações do DataJud pode ser parcial ou resumido em comparação com o histórico original dos tribunais.
- A documentação versionada não contém números reais de processos; fixtures E2E usam valores vazios e recebem processos por ambiente ou secrets.
- `README.md` e `docs/datajud-resolver.md` explicam o padrão Elasticsearch usado pela API pública do DataJud e apontam para referências oficiais.
- `CONTRIBUTING.md` e `AGENTS.md` documentam a política de execução E2E real separada da suíte determinística, e a CI principal roda `pytest -m "not e2e"`.
- O workflow E2E falha quando a chave ou as fixtures essenciais não estão configuradas, e o workflow de publicação valida tag, versão, testes, lint e tipos antes de enviar ao PyPI.

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
