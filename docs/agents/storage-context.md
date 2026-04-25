# Storage Context

Persistencia local inicial usa SQLite.

Contrato:
- Salvar anuncios vistos em `listings`.
- Salvar notificacoes em `notifications`.
- Deduplicar por alerta + origem + id externo.
- Nao exigir Postgres, Redis ou Celery para uso local.
- Banco local deve ficar fora do Git.
