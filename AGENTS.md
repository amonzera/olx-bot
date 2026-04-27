# Agent Operating Rules

Escopo: este arquivo vale para todo o repositorio.

## Antes de planejar ou editar

1. Ler `docs/agents/project-context.md`.
2. Ler os contextos especificos da area afetada:
   - Scraper: `docs/agents/scraper-context.md`
   - Analyzer: `docs/agents/analyzer-context.md`
   - Storage: `docs/agents/storage-context.md`
   - Notifiers: `docs/agents/notifier-context.md`
3. Se a area afetada nao estiver clara, ler todos os arquivos em `docs/agents/*-context.md`.
4. Antes do plano ou da primeira modificacao, informar de forma curta:

```text
Contexto lido:
- docs/agents/project-context.md
- docs/agents/<area>-context.md

Contexto aplicado:
- <regra concreta usada no plano ou na edicao>
```

Nunca declarar contexto como aplicado sem ter lido o arquivo correspondente.

## Durante modificacoes

- Seguir os contratos dos arquivos de contexto.
- Se o pedido do usuario conflitar com uma regra fixa do contexto, explicar o conflito antes de editar.
- Manter mudancas pequenas, locais e testaveis.
- Nao introduzir Playwright, Selenium, browser/headless browser, multiusuario, deploy publico, Postgres, Redis ou Celery, salvo se o contexto for atualizado por decisao explicita do usuario.

## Quando atualizar contexto

Atualizar `docs/agents/*-context.md` quando uma decisao duravel mudar:

- Novo contrato entre modulos.
- Nova regra arquitetural.
- Nova restricao de produto.
- Nova flag, campo, tabela, politica de notificacao ou regra de scraping.
- Correcao de uma expectativa que agentes futuros precisam lembrar.

Nao atualizar contexto para mudancas mecanicas, refactors pequenos ou implementacoes que apenas seguem regras existentes.

## Fechamento obrigatorio

Ao finalizar, informar:

```text
Contexto atualizado:
- nenhum
```

ou:

```text
Contexto atualizado:
- docs/agents/<area>-context.md: <o que mudou>
```

Tambem informar validacoes executadas, como `pytest`, lint ou motivo de nao ter rodado.

## Uso de subagentes

Usar subagentes somente quando o pedido do usuario permitir delegacao, paralelismo ou trabalho multiagente.

Quando usar:

- Dividir por propriedade clara de arquivos ou responsabilidades.
- Evitar que dois agentes editem os mesmos arquivos.
- Passar para cada agente os contextos que ele deve ler.
- Exigir que cada agente reporte contexto lido, mudancas feitas e validacoes.
- Integrar os resultados no agente principal antes de responder ao usuario.
