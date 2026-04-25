# Notifier Context

Notificadores devem receber `Listing` e `AnalysisResult`.

Contrato:
- Console e o fallback padrao.
- Telegram e usado quando `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` existirem.
- Mensagem deve mostrar titulo, preco, score, flags, motivos e link.
- Nunca esconder flags de risco.
