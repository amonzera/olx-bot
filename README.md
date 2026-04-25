# OLX Monitor Local

Monitor local de anuncios da OLX por requisicoes HTTP. O foco e encontrar oportunidades recentes, com no maximo 30 dias de publicacao, e avisar o usuario sem esconder anuncios suspeitos. Risco vira flag, nao descarte automatico.

## Como Rodar

### Com Docker

Esse e o caminho recomendado quando voce quer baixar o repositorio em outra maquina e manter a mesma versao de Python e dependencias.

Build da imagem:

```bash
docker compose build
```

Rode uma busca unica:

```bash
docker compose run --rm monitor python -m src.cli.run_once "iphone 13" --max-price 2500 --min-expected-price 1500
```

Rode em loop local:

```bash
docker compose run --rm monitor python -m src.cli.watch "iphone 13" --max-price 2500 --min-expected-price 1500 --interval 60
```

O SQLite fica persistido no volume Docker `olx-scrapper_olx_data`, dentro de `/app/data/olx_monitor.sqlite3` no container.

Para usar Telegram, defina no shell ou em um arquivo `.env` local:

```bash
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

### Sem Docker

Instale dependencias:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Rode uma busca unica:

```bash
.venv/bin/python -m src.cli.run_once "iphone 13" --max-price 2500 --min-expected-price 1500
```

Rode em loop local:

```bash
.venv/bin/python -m src.cli.watch "iphone 13" --max-price 2500 --min-expected-price 1500 --interval 60
```

Se `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` estiverem no `.env`, o alerta vai para Telegram. Sem isso, o alerta sai no console/log.

## Decisoes Do Projeto

- Sem multiusuario.
- Sem deploy publico.
- Sem Playwright, Selenium ou navegador/headless browser.
- Coleta feita por HTTP com `curl_cffi`, sessao persistente e headers realistas.
- SQLite local para historico e deduplicacao.
- Anuncios suspeitos aparecem com flags como `LOW_PRICE_CAUTION`, `SCAM_CAUTION` e `DEFECT_KEYWORD`.
- Anuncios sem data identificada recebem `UNKNOWN_DATE` e nao notificam por padrao.

## Testes

```bash
.venv/bin/python -m pytest
```

Os testes usam fixtures locais e nao chamam a OLX.
