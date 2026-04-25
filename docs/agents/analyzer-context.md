# Analyzer Context

O analyzer classifica oportunidades, mas nao deve descartar anuncio suspeito por seguranca.

Contrato:
- Entrada: `Listing` e `AlertConfig`.
- Saida: `AnalysisResult`.
- Flags principais: `LOW_PRICE_CAUTION`, `DEFECT_KEYWORD`, `SCAM_CAUTION`, `UNKNOWN_DATE`, `RECENT`, `GOOD_PRICE`.
- `UNKNOWN_DATE` nao notifica por padrao.
- Defeito/golpe vira flag e motivo humano.
- "sem defeito" nao deve acionar `DEFECT_KEYWORD`.
