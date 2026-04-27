# Scraper Context

O scraper deve buscar paginas publicas da OLX via HTTP.

Contrato:
- Usar `curl_cffi` com sessao persistente.
- Enviar headers realistas de navegador.
- Aplicar timeout, retry e backoff.
- Nao abrir navegador real ou headless.
- Parser deve preferir JSON embutido em `__NEXT_DATA__`.
- Datas numericas da OLX em timestamp Unix (segundos ou milissegundos) devem ser normalizadas para `published_at`.
- Se o HTML vier inesperado, salvar dump local em `debug_dumps/`.
- Testes do scraper nao devem chamar rede real.
- Localidades suportadas inicialmente: `brasil` e `rio de janeiro`.
- Paginar com limite configuravel e pausas entre paginas; nao buscar volume ilimitado.
- Nao implementar proxy rotativo, bypass de captcha, evasao de bloqueio ou contorno de robots/limites.
