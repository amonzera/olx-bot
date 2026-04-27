# OLX Monitor Telegram Bot

Bot local do Telegram para monitorar anúncios da OLX. Você conversa com o bot, cadastra alertas de produtos, escolhe a localidade da busca (`brasil` ou `rio de janeiro`) e define a faixa de preço desejada. Quando um alerta é criado ou alterado, o bot faz uma busca inicial e envia as ofertas encontradas nos últimos 30 dias. Depois disso, ele continua rodando e avisa quando novos anúncios compatíveis aparecem.

O projeto foi pensado para uso local, por uma pessoa, sem painel web, sem deploy público, sem navegador automatizado e sem banco externo.

## Atenção Sobre o Uso da OLX

Antes de usar, leia os termos atuais da OLX:

- Termos de uso: https://ajuda.olx.com.br/s/article/termos-e-condicoes-de-uso
- Robots.txt: https://www.olx.com.br/robots.txt

Na versão consultada em 27 de abril de 2026, os termos da OLX informam restrições a web crawling, cópia e uso automatizado de elementos do site. O `robots.txt` também desautoriza várias URLs de busca com parâmetros como `q`, `pe` e `ps`. Portanto, o uso mais seguro do ponto de vista de conformidade é obter autorização da OLX ou usar uma API oficial, caso disponível.

Mesmo assim, o código foi implementado de forma conservadora:

- usa HTTP com `curl_cffi`, sem Playwright, Selenium ou navegador headless;
- não tenta burlar bloqueios, captcha ou limites;
- usa intervalos configuráveis e pausas entre buscas;
- salva dumps locais quando a resposta da OLX muda ou fica inesperada;
- deve ser usado em baixa frequência e apenas para uso pessoal/local.

Se a OLX retornar bloqueio, captcha, erro `429` ou páginas inesperadas, pare o bot e aumente os intervalos.

## O Que o Bot Faz

- Recebe comandos pelo Telegram.
- Cria, lista, altera, pausa, reativa e exclui alertas.
- Salva alertas em SQLite local.
- Busca anúncios na OLX por produto, localidade e faixa de preço.
- Filtra anúncios com até 30 dias.
- Evita reenviar o mesmo anúncio para o mesmo alerta.
- Envia título, preço, score, flags, motivos e link.
- Mantém flags de cuidado visíveis em anúncios suspeitos.
- Roda uma busca inicial automaticamente ao criar ou alterar um alerta.
- Continua buscando periodicamente enquanto o processo estiver ligado.

## Comandos do Telegram

Use estes comandos dentro da conversa com o seu bot:

```text
/start
```

Mostra a ajuda inicial.

```text
/add produto | brasil ou rio de janeiro | preço mínimo | preço máximo
```

Cria um alerta e faz a busca inicial.

Exemplos:

```text
/add iphone 13 | rio de janeiro | 1500 | 2500
/add macbook air m1 | brasil | 3000 | 4500
```

```text
/list
```

Lista seus alertas.

```text
/edit id | produto | brasil ou rio de janeiro | preço mínimo | preço máximo
```

Altera um alerta e faz uma nova busca.

Exemplo:

```text
/edit 2 | iphone 14 | rio de janeiro | 2500 | 3800
```

```text
/delete id
```

Exclui um alerta.

```text
/pause id
/resume id
```

Pausa ou reativa um alerta.

```text
/help
```

Mostra a ajuda.

## Como o Monitor Funciona

1. O bot recebe um comando do Telegram.
2. O alerta é salvo no SQLite local.
3. O monitor monta uma busca pública da OLX para a localidade escolhida.
4. O scraper baixa páginas por HTTP com sessão persistente.
5. O parser tenta ler primeiro o JSON embutido em `__NEXT_DATA__`.
6. O analyzer valida idade, faixa de preço e flags de cuidado.
7. Anúncios compatíveis e ainda não notificados são enviados para o Telegram.
8. O scheduler repete as buscas em intervalos conservadores.

Por padrão, o monitor busca até `MAX_SEARCH_PAGES=3` páginas por alerta e para antes se encontrar uma página com anúncios datados fora da janela de 30 dias. A cobertura real depende da ordenação e da estrutura atual da OLX.

## Requisitos

- Python 3.13 ou superior.
- Docker e Docker Compose, se quiser rodar em container.
- Um bot criado no Telegram via `@BotFather`.

## Configuração do Bot no Telegram

1. Abra o Telegram.
2. Procure `@BotFather`.
3. Envie `/newbot`.
4. Escolha um nome e um usuário para o bot.
5. Copie o token gerado.
6. Crie o arquivo `.env` no projeto:

```bash
cp .env.example .env
```

7. Edite o `.env` e preencha:

```env
TELEGRAM_BOT_TOKEN=cole_o_token_aqui
```

O `TELEGRAM_CHAT_ID` é opcional. O bot usa o chat que enviou os comandos. Se você preencher `TELEGRAM_CHAT_ID`, ele também pode ser usado como fallback para notificações.

## Variáveis Principais

```env
SQLITE_PATH=olx_monitor.sqlite3
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

SCAN_INTERVAL_SECONDS=1800
DELAY_BETWEEN_ALERT_REQUESTS_SECONDS=90
DELAY_BETWEEN_PAGE_REQUESTS_SECONDS=15
MAX_SEARCH_PAGES=3

REQUEST_TIMEOUT_SECONDS=15
REQUEST_RETRIES=2
REQUEST_BACKOFF_SECONDS=1.5
MAX_LISTING_AGE_DAYS=30
DEBUG_DUMP_DIR=debug_dumps
```

Recomendação:

- `SCAN_INTERVAL_SECONDS=1800`: cada ciclo geral roda a cada 30 minutos.
- `DELAY_BETWEEN_ALERT_REQUESTS_SECONDS=90`: pausa entre alertas.
- `DELAY_BETWEEN_PAGE_REQUESTS_SECONDS=15`: pausa entre páginas do mesmo alerta.
- `MAX_SEARCH_PAGES=3`: limite de páginas por alerta para reduzir volume.

Evite intervalos muito baixos. Quanto mais alertas e páginas, maior o risco de bloqueio pela OLX.

## Rodando com Docker

Monte a imagem:

```bash
docker compose build
```

Inicie o bot:

```bash
docker compose up
```

O SQLite fica no volume Docker `olx-scrapper_olx_data`, dentro de `/app/data/olx_monitor.sqlite3` no container.

Para parar:

```bash
docker compose down
```

## Rodando sem Docker

Crie o ambiente virtual:

```bash
python -m venv .venv
```

Instale as dependências:

```bash
.venv/bin/pip install -r requirements.txt
```

Inicie o bot:

```bash
.venv/bin/python -m src.bot.app
```

Depois, abra o Telegram e envie `/start` para o bot.

## Banco de Dados

O SQLite guarda:

- `alerts`: alertas configurados pelo Telegram.
- `listings`: anúncios vistos.
- `notifications`: anúncios já enviados por alerta.

O banco local não deve entrar no Git. Arquivos `.sqlite3`, `.db`, `data/` e `debug_dumps/` já estão ignorados.

## Mensagens Enviadas

Cada anúncio enviado inclui:

- alerta e localidade;
- título;
- preço;
- score;
- flags;
- motivos da análise;
- link da OLX.

Flags principais:

- `RECENT`: anúncio dentro da janela configurada.
- `GOOD_PRICE`: preço dentro da faixa configurada.
- `LOW_PRICE_CAUTION`: preço muito abaixo do mínimo esperado.
- `SCAM_CAUTION`: termo ou preço que merece cautela.
- `DEFECT_KEYWORD`: título sugere defeito, peça, bloqueio ou reparo.
- `UNKNOWN_DATE`: data não identificada; não notifica por padrão.

## Testes

Rode a suíte:

```bash
.venv/bin/python -m pytest
```

Os testes usam fixtures locais e não devem chamar a OLX.

## Estrutura do Projeto

- `src/bot/app.py`: bot Telegram, comandos e scheduler.
- `src/bot/commands.py`: parsing dos comandos.
- `src/scraper/client.py`: cliente HTTP da OLX.
- `src/scraper/parsers.py`: parser de resultados.
- `src/services/monitor.py`: orquestra busca, análise, persistência e notificação.
- `src/services/analyzer.py`: score, flags e decisão de notificação.
- `src/storage/sqlite_repository.py`: SQLite local.
- `src/notifiers/telegram.py`: envio de mensagens para o Telegram.
- `src/core/models.py`: modelos centrais.
- `src/core/prices.py`: normalização de preços.
- `src/core/dates.py`: normalização de datas.

## Limitações Conhecidas

- A OLX pode alterar HTML, JSON interno ou parâmetros de busca sem aviso.
- A cobertura dos últimos 30 dias depende da ordenação e paginação retornadas pela OLX.
- O bot usa long polling do Telegram; não há webhook público.
- O projeto continua sendo local e de usuário único.
- Não há tentativa de resolver captcha, trocar proxy ou contornar bloqueio.
- Só há duas localidades suportadas no comando: `brasil` e `rio de janeiro`.

