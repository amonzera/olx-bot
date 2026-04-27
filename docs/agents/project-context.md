# Project Context

Este projeto e um bot local do Telegram para monitorar OLX, para um usuario rodar no proprio computador.

Regras fixas:
- Nao planejar multiusuario.
- Nao planejar deploy publico.
- Nao usar navegador, Playwright ou Selenium.
- Coletar por requisicoes HTTP.
- Notificar apenas anuncios com no maximo 30 dias.
- Nao esconder anuncios suspeitos; marcar flags de cuidado.
- Preferir codigo simples, testavel e facil de explicar.
- A interface principal e o bot do Telegram; nao reintroduzir CLI de uso do produto sem decisao explicita do usuario.
- O bot usa long polling local; nao planejar webhook publico.
- Docker e o fluxo oficial para rodar bot e testes; nao documentar `.venv` como caminho principal sem decisao explicita do usuario.
- Se a OLX bloquear, limitar, exigir captcha ou proibir o uso, nao implementar evasao; pausar ou reduzir frequencia.
