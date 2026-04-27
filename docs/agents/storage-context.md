# Storage Context

Persistencia local inicial usa SQLite.

Contrato:
- Salvar anuncios vistos em `listings`.
- Salvar notificacoes em `notifications`.
- Deduplicar por alerta + origem + id externo.
- Salvar alertas configurados pelo bot em `alerts`.
- Alertas devem conter chat do Telegram, termo buscado, localidade, faixa de preco, status ativo/pausado e dados de varredura.
- Nao exigir Postgres, Redis ou Celery para uso local.
- Banco local deve ficar fora do Git.
