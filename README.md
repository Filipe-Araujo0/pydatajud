# pydatajud

O `pydatajud` é o melhor wrapper Python para a API pública do DataJud/CNJ e a forma mais direta de transformar a base pública do Judiciário brasileiro em dados úteis para aplicações, pesquisa e automação.

A principal força do projeto é a verificação em lote de novas movimentações: com uma única requisição, você consegue saber quais processos de um mesmo tribunal foram atualizados desde uma data de corte, sem consultar cada processo individualmente. Não existe outra API aberta no Brasil que ofereça esse tipo de verificação de processos judiciais, e o `pydatajud` é o melhor wrapper para explorar essa capacidade do DataJud.

Quando o lote reúne processos de tribunais diferentes, a biblioteca faz o menor número possível de requisições: uma para cada tribunal, contendo todos os seus processos.

Como segunda capacidade central, o `pydatajud` também tem um validador e normalizador de números de processos no padrão CNJ, consegue identificar o tribunal e resolver o endpoint DataJud correspondente sem consultar a rede. Tudo baseado nas normas oficiais da justiça brasileira e na documentação oficial da API.

O projeto não é afiliado ao CNJ; ele empacota uma forma simples, eficiente e reutilizável de consultar a API pública oficial.

## Instalação

```bash
pip install pydatajud
```

Para desenvolvimento local:

```bash
pip install -e ".[dev]"
```

## Uso rápido: verificar atualizações

O melhor uso desta consulta é descobrir, com o menor número possível de requisições, quais processos tiveram novas movimentações desde uma data de corte. Isso permite selecionar rapidamente os processos que merecem atenção, sem baixar e comparar manualmente o histórico de todos eles.

Os números usados nos exemplos desta página são sintéticos e servem apenas para ilustrar o formato CNJ; eles não correspondem a processos reais.

```python
from pydatajud import DataJudClient

client = DataJudClient(api_key="sua-api-key")
cutoffs = {
    "0000001-17.2099.8.26.0001": "2025-01-01T00:00:00.000Z",
    "0000003-84.2099.8.26.0001": "2025-01-01T00:00:00.000Z",
}

statuses = client.search_movements_delta_batch(cutoffs, mode="status")

for process_number, status in statuses.items():
    if status.has_new_movements:
        print(f"{process_number}: houve novas movimentações após o cutoff informado")
    else:
        print(f"{process_number}: nenhuma movimentação posterior ao cutoff informado")
```

Essa chamada verifica todos os processos do lote sem precisar baixar pela rede as listas de movimentações e retorna um status para cada processo. Para receber as movimentações encontradas, troque para `mode="movements"`.

Saída ilustrativa:

```text
0000001-17.2099.8.26.0001: houve novas movimentações após o cutoff informado
0000003-84.2099.8.26.0001: nenhuma movimentação posterior ao cutoff informado
```

Para consultar um único processo:

```python
result = client.search_movements_delta(
    "0000001-17.2099.8.26.0001",
    cutoff_iso="2025-01-01T00:00:00.000Z",
    mode="movements",
)

if result.has_new_movements:
    for movement in result.movements or []:
        print(movement)
```

Saída ilustrativa:

```text
{'dataHora': '2025-02-03T14:22:00.000Z', 'nome': 'Juntada de petição', 'orgaoJulgador': {'nome': 'Vara de exemplo'}}
```

### Escolha do modo

Use `mode="status"` para maior eficiência quando precisar apenas saber quais processos tiveram mudanças. Use `mode="movements"` quando também precisar receber os itens novos; nesse caso, a mesma interface retorna as movimentações filtradas pelo cutoff.

O conteúdo de movimentações disponibilizado pelo DataJud pode ser limitado ou resumido em comparação com o conteúdo original mantido pelos tribunais. Por isso, o `pydatajud` deve ser usado principalmente para identificar atualizações e selecionar processos para as próximas etapas. A resposta de `mode="movements"` contém as movimentações que o DataJud disponibiliza, mas não é uma promessa de reprodução integral do conteúdo original do tribunal, já que o principal objetivo da API pública é "metadados".

## Resolução e validação de números CNJ

Como segunda capacidade central, o `pydatajud` também pode ser usado sem API key e sem fazer uma requisição de rede. A biblioteca implementa as regras oficiais da numeração CNJ para validar e normalizar números de processos, identificar o ramo e o tribunal e descobrir o endpoint DataJud correspondente:

```python
from pydatajud import (
    normalize_cnj_process_number,
    resolve_datajud_alias,
    resolve_datajud_search_url,
)

numero_do_processo = "0000001-17.2099.8.26.0001"
numero_normalizado = normalize_cnj_process_number(numero_do_processo)
tribunal = resolve_datajud_alias(numero_do_processo)
endpoint = resolve_datajud_search_url(numero_do_processo)

print(f"Número normalizado: {numero_normalizado}")
print(f"Tribunal: {tribunal}")
print(f"Endpoint: {endpoint}")
```

Saída ilustrativa:

```text
Número normalizado: 00000011720998260001
Tribunal: tjsp
Endpoint: https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search
```

Um número inválido gera uma exceção de validação explícita. Isso torna o resolvedor útil mesmo para aplicações que não precisam consultar o DataJud: ele pode validar entradas, normalizar identificadores e encaminhar cada processo ao tribunal correto antes de qualquer chamada externa.

## API key pública do DataJud

A API pública do DataJud usa uma chave pública no cabeçalho `Authorization: APIKey ...`.

Até o momento, o CNJ publica uma chave pública única e vigente na página oficial de acesso da wiki do DataJud. Para usar a biblioteca, copie a chave atual de:

https://datajud-wiki.cnj.jus.br/api-publica/acesso/

Depois defina:

```bash
export DATAJUD_API_KEY="cole-a-chave-publica-vigente-aqui"
```

O próprio CNJ informa que essa chave pode ser alterada a qualquer momento. Por isso, a documentação do `pydatajud` aponta para a página oficial em vez de tratar uma chave copiada em README como permanente.

## CLI

```bash
export DATAJUD_API_KEY="sua-api-key"
pydatajud --processo "0000001-17.2099.8.26.0001" \
  --cutoff "2025-01-01T00:00:00.000Z" --mode status
```

Saída ilustrativa:

```json
{
  "process_number": "0000001-17.2099.8.26.0001",
  "found": true,
  "has_new_movements": true,
  "movements": null
}
```

Para receber as movimentações posteriores ao cutoff, use `mode movements`. A CLI usa saída tipada por padrão:

```bash
pydatajud --processo "0000001-17.2099.8.26.0001" \
  --cutoff "2025-01-01T00:00:00.000Z" --mode movements
```

Saída ilustrativa:

```json
{
  "process_number": "0000001-17.2099.8.26.0001",
  "found": true,
  "has_new_movements": true,
  "movements": [{ "dataHora": "...", "tipo": "movimentacao_disponibilizada" }]
}
```

## O que a biblioteca faz

- Valida e normaliza números processuais CNJ conforme a estrutura oficial da numeração brasileira.
- Resolve automaticamente o tribunal e seu endpoint DataJud a partir dos campos `J` e `TR`, sem consulta de rede.
- Consulta o endpoint público correspondente a cada tribunal.
- Permite consulta em lote de múltiplos processos, agrupando automaticamente por tribunal e executando uma chamada por grupo.
- Permite verificar movimentações posteriores a um cutoff com `script_fields`, reduzindo o payload e o tráfego de rede quando a aplicação precisa apenas do status.
- Permite consultar em lote, com `mode="status"`, quais processos têm novidades sem baixar pela rede as listas completas de movimentações.
- Usa uma interface única de verificação com `mode="status"` ou `mode="movements"`, escolhendo internamente a consulta adequada ao custo desejado.
- Preserva os dados disponibilizados pela API e oferece resultados tipados para os fluxos de verificação.
- Expõe erros próprios para autenticação, resposta inválida, processo não encontrado e tribunal sem endpoint público mapeado.

Para entender como o número CNJ identifica o tribunal e como o cliente resolve seu endpoint, leia [docs/datajud-resolver.md](./docs/datajud-resolver.md).

## DataJud e Elasticsearch

A API pública do DataJud segue o padrão de busca do Elasticsearch (`_search`). Por isso, campos como `size`, `took`, `_shards`, `hits.total` e `max_score` seguem semântica do Elasticsearch.

Referências:

- DataJud (considerações finais): https://datajud-wiki.cnj.jus.br/api-publica/consideracoes_finais/
- Elasticsearch Search API: https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-search
- Elasticsearch Querying for Search: https://www.elastic.co/docs/solutions/search/querying-for-search

## Limitações

- A API pública do DataJud exige chave `APIKey`.
- Em lotes com processos de um mesmo tribunal, o client faz uma chamada com vários processos. Com processos de múltiplos tribunais, faz uma chamada por tribunal e agrega o retorno.
- Processos sigilosos ou indisponíveis na base pública podem não retornar dados.
- O DataJud não deve ser tratado como substituto automático do histórico completo mantido pelo tribunal; os campos e o conteúdo das movimentações públicas podem ser parciais ou resumidos.
- `cutoff_iso` deve ser um timestamp ISO-8601 com timezone UTC; a biblioteca não persiste o cutoff nem implementa retry, backoff ou deduplicação de negócio.
- A cobertura, disponibilidade e regras de uso são definidas pelo CNJ.
- O usuário é responsável por cumprir os termos de uso do CNJ e a legislação aplicável, incluindo LGPD.

## Desenvolvimento

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src tests
pytest -m "not e2e"
python -m build
twine check dist/*
```

Testes E2E reais (opcionais, com rede):

```bash
export DATAJUD_API_KEY="sua-api-key"
pytest -m e2e -ra
```

As fixtures E2E podem ser substituídas sem editar o repositório usando `DATAJUD_E2E_SINGLE_PROCESS`, `DATAJUD_E2E_BATCH_PROCESSES`, `DATAJUD_E2E_DELTA_PROCESSES`, `DATAJUD_E2E_PAGINATION_PROCESSES` e `DATAJUD_E2E_NOT_FOUND_PROCESS`. A última é opcional e deve apontar para um processo CNJ válido que não esteja disponível no endpoint público.

Overrides opcionais de fixtures E2E:

```bash
export DATAJUD_E2E_SINGLE_PROCESS="numero_do_processo_real_1"
export DATAJUD_E2E_BATCH_PROCESSES="numero_do_processo_real_1,numero_do_processo_real_2"
export DATAJUD_E2E_PAGINATION_PROCESSES="numero_do_processo_real_1,numero_do_processo_real_2"
```

## Links úteis

- API pública do DataJud: https://www.cnj.jus.br/sistemas/datajud/api-publica/
- Wiki DataJud: https://datajud-wiki.cnj.jus.br/api-publica/
- Termos de uso: https://formularios.cnj.jus.br/wp-content/uploads/2023/11/Termos-de-uso-api-publica-V1.2.pdf
