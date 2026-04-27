# Agent Context Index

Este diretorio guarda memoria operacional para agentes que trabalham no projeto.
Os arquivos aqui nao substituem leitura do codigo; eles definem regras duraveis que devem orientar planos e modificacoes.

## Ordem de leitura

Sempre ler:

- `project-context.md`: regras fixas do produto e arquitetura.

Ler conforme a area afetada:

- `scraper-context.md`: coleta HTTP, parser, dumps e testes de scraper.
- `analyzer-context.md`: classificacao, flags, score e regras de notificacao.
- `storage-context.md`: SQLite, deduplicacao e persistencia local.
- `notifier-context.md`: console, Telegram e conteudo de mensagens.

Se a tarefa cruza modulos, ler todos os contextos dos modulos envolvidos.

## Protocolo de auditoria

Antes de planejar ou editar, o agente deve declarar:

```text
Contexto lido:
- docs/agents/project-context.md
- docs/agents/<area>-context.md

Contexto aplicado:
- <regra concreta que guiou a decisao>
```

Ao finalizar, o agente deve declarar:

```text
Contexto atualizado:
- nenhum
```

ou:

```text
Contexto atualizado:
- docs/agents/<area>-context.md: <resumo da decisao duravel adicionada>
```

## Quando atualizar estes arquivos

Atualize contexto quando houver uma decisao que agentes futuros precisam preservar:

- Mudanca de contrato entre `Listing`, `AlertConfig`, `AnalysisResult`, repositorios ou notificadores.
- Nova regra de negocio sobre idade maxima, score, risco, flags ou notificacao.
- Nova restricao tecnica para scraper, storage, analyzer ou notifiers.
- Nova decisao sobre dependencias permitidas ou proibidas.
- Bug corrigido que revelou uma regra que deve ser lembrada.

Nao atualize contexto quando:

- A mudanca for apenas formatacao.
- A implementacao seguir regras ja documentadas.
- O detalhe for temporario, local ou obvio pelo codigo.

## Como usar o maximo do Codex neste repo

1. Diga o objetivo e a area afetada.
2. Peca explicitamente para o agente ler os contextos antes de planejar.
3. Para tarefas grandes, peca um plano com arquivos provaveis e validacoes.
4. Para tarefas paralelizaveis, autorize subagentes e defina responsabilidades.
5. No fim, confira `git diff`, `git status --short` e as validacoes executadas.

Exemplo de pedido:

```text
Leia docs/agents/project-context.md e docs/agents/analyzer-context.md antes de planejar.
Depois implemente a regra X no analyzer, atualize contexto se a decisao for duravel,
e rode os testes relevantes.
```

## Padrao para trabalho multiagente

Use multiagente quando as partes forem independentes:

- Agente A: scraper e parser.
- Agente B: analyzer e testes de classificacao.
- Agente C: storage/notifier ou validacao.

Cada agente deve receber:

- Objetivo especifico.
- Arquivos ou modulos sob sua responsabilidade.
- Contextos obrigatorios para leitura.
- Regra para nao editar arquivos de outro agente.
- Validacao esperada.

O agente principal deve integrar os resultados, resolver conflitos e fazer a resposta final.

## Como criar uma skill para este projeto

Para uma skill auto-descoberta pelo Codex, crie uma pasta em:

```text
${CODEX_HOME:-$HOME/.codex}/skills/olx-monitor-agent/
```

Estrutura minima:

```text
olx-monitor-agent/
|-- SKILL.md
`-- references/
    `-- context-map.md
```

`SKILL.md` deve ser curto e conter:

```markdown
---
name: olx-monitor-agent
description: Work on the local OLX monitor project. Use when changing scraper, analyzer, storage, notifier, CLI, tests, or project agent context; always read project context and the area-specific context before planning or editing.
---

# OLX Monitor Agent

Before planning or editing:

1. Read `docs/agents/project-context.md`.
2. Read the area context for touched modules.
3. Report `Contexto lido` and `Contexto aplicado`.

When changing durable behavior, update the matching `docs/agents/*-context.md`.
End with `Contexto atualizado` and validations run.
```

Crie uma skill separada somente quando o fluxo for reutilizavel em varios projetos ou quando houver procedimento especifico demais para caber em `AGENTS.md`. Para este repo, `AGENTS.md` e `docs/agents/*-context.md` devem ser a fonte principal.
