# Notifier Context

Notificadores devem receber `AlertConfig`, `Listing` e `AnalysisResult`.

Contrato:
- Telegram e a interface principal quando `TELEGRAM_BOT_TOKEN` existir.
- O chat deve vir do alerta criado pelo bot; `TELEGRAM_CHAT_ID` e apenas fallback opcional.
- Comandos esperados: `/start`, `/help`, `/add`, `/list`, `/edit`, `/delete`, `/pause`, `/resume`.
- Mensagem deve mostrar titulo, preco, score, flags, motivos e link.
- Nunca esconder flags de risco.
