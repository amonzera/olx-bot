# Scraper Context

O scraper deve buscar paginas publicas da OLX via HTTP.

Contrato:
- Usar `curl_cffi` com sessao persistente.
- Enviar headers realistas de navegador.
- Aplicar timeout, retry e backoff.
- Nao abrir navegador real ou headless.
- Parser deve preferir JSON embutido em `__NEXT_DATA__`.
- Se o HTML vier inesperado, salvar dump local em `debug_dumps/`.
- Testes do scraper nao devem chamar rede real.
