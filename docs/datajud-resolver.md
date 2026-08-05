# Como o resolvedor DataJud funciona

Este documento explica a lógica específica do sistema judiciário brasileiro que
o `pydatajud` usa para resolver automaticamente o endpoint correto da API
pública do DataJud.

## Por que existe um resolvedor

A API pública do DataJud não expõe um endpoint único para todos os processos.
As consultas são feitas em índices separados por tribunal ou órgão, como:

```text
https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search
https://api-publica.datajud.cnj.jus.br/api_publica_trf3/_search
https://api-publica.datajud.cnj.jus.br/api_publica_trt15/_search
```

Para consultar um processo por número CNJ, a biblioteca precisa descobrir qual
índice usar. Essa informação já está codificada no próprio número processual.

## Estrutura do número CNJ

O formato CNJ é:

```text
NNNNNNN-DD.AAAA.J.TR.OOOO
```

Campos relevantes para o resolvedor:

- `J`: ramo da Justiça.
- `TR`: tribunal, região ou unidade dentro daquele ramo.

Exemplo:

`numero_do_processo` é um stub documental; use um número CNJ da sua própria
configuração durante a execução.

```text
numero_do_processo
```

Neste caso:

- `J = 8`: Justiça Estadual.
- `TR = 26`: São Paulo.
- Endpoint resolvido: `api_publica_tjsp/_search`.

## Validação antes da resolução

Antes de resolver o endpoint, o `pydatajud`:

- remove pontuação e mantém os 20 dígitos;
- reconstrói o formato CNJ quando necessário;
- valida o dígito verificador por módulo 97;
- só então extrai `J` e `TR`.

Isso evita consultar o DataJud com números estruturalmente inválidos e torna o
erro mais claro para quem usa a biblioteca.

## Mapeamento adotado

O resolvedor usa `J` e `TR` para produzir o alias do índice DataJud:

- `J = 3`: Superior Tribunal de Justiça (`stj`).
- `J = 4`: Justiça Federal (`trf1` a `trf6`).
- `J = 5`: Justiça do Trabalho (`tst`, `trt1` a `trt24`).
- `J = 6`: Justiça Eleitoral (`tse`, `tre-*`).
- `J = 7`: Justiça Militar da União (`stm`).
- `J = 8`: Justiça Estadual (`tj*`).
- `J = 9`: Justiça Militar Estadual, quando há endpoint público conhecido
  (`tjmmg`, `tjmrs`, `tjmsp`).

O mapeamento de `TR` para UF segue os códigos usados na numeração CNJ. Por
exemplo:

- `TR = 16`: Paraná (`tjpr` ou `tre-pr`, conforme o ramo).
- `TR = 19`: Rio de Janeiro (`tjrj` ou `tre-rj`).
- `TR = 26`: São Paulo (`tjsp`, `tre-sp` ou `tjmsp`, conforme o ramo).

## O que o resolvedor não tenta fazer

O resolvedor não consulta a API para descobrir endpoints dinamicamente a cada
requisição. Ele aplica regras estruturais conhecidas do número CNJ e do padrão
de nomes dos índices públicos do DataJud.

Também não tenta corrigir números inválidos, inferir tribunais por texto livre,
nem procurar o processo em múltiplos tribunais quando o número informado é
estruturalmente válido. Se um processo não aparece no endpoint esperado, isso
pode significar ausência na base pública, sigilo, indisponibilidade temporária
ou diferenças de cobertura do DataJud.

## Quando alterar o resolvedor

Altere o resolvedor quando:

- o CNJ publicar ou alterar endpoints públicos;
- um ramo/tribunal conhecido passar a ter índice público;
- um padrão de alias usado pela API mudar;
- houver teste cobrindo o novo caso.

Mudanças no resolvedor devem incluir testes unitários para validação CNJ,
mapeamento de alias e URL final.

## Sobre formato de resposta (Elasticsearch)

O resolvedor só decide o endpoint. A resposta da consulta vem no formato padrão
do Elasticsearch, porque a API pública do DataJud expõe `_search` por índice.

Isso significa que campos como `size`, `took`, `_shards`, `hits.total`,
`hits.hits` e `max_score` seguem a semântica do Elasticsearch.

Referências oficiais:

- DataJud (considerações finais): https://datajud-wiki.cnj.jus.br/api-publica/consideracoes_finais/
- Elasticsearch Search API: https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-search
- Elasticsearch Querying for Search: https://www.elastic.co/docs/solutions/search/querying-for-search
