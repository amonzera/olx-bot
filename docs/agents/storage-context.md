# Storage Context

Persistencia local inicial usa SQLite.

Contrato:
- Salvar anuncios vistos em `listings`.
- Atualizar anuncios existentes quando novos parses trouxerem data, preco, titulo, URL ou localidade melhores.
- Salvar notificacoes em `notifications`.
- Deduplicar por alerta + origem + id externo.
- Salvar alertas configurados pelo bot em `alerts`.
- Alertas devem conter chat do Telegram, termo buscado, localidade, faixa de preco, status ativo/pausado e dados de varredura.
- Remover historico antigo de `listings` e `notifications` conforme `DATA_RETENTION_DAYS`, preservando `alerts`.
- Nao exigir Postgres, Redis ou Celery para uso local.
- Banco local deve ficar fora do Git.
