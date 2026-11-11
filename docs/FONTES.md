# Catálogo de fontes (dados abertos)

Status: `não verificado` = URL fornecida pelo usuário, ainda não testada (o sandbox não tem acesso). Confirmar formato, limites e termos de uso na primeira ingestão.

| # | Fonte | URL | Uso planejado | Marco | Status |
|---|-------|-----|---------------|-------|--------|
| a | Câmara – Dados Abertos (Swagger) | https://dadosabertos.camara.leg.br/swagger/api.html | Tramitação de proposições (complemento) | M3 | não verificado |
| b0 | Planalto – texto compilado | ver `src/ordem/data/normas.json` | Letra da lei (ingestão M1 ativa) | M1 | não verificado (aguarda 1ª execução do workflow) |
| b | Senado – Legislação | https://www12.senado.leg.br/dados-abertos/conjuntos?portal=Legislativo&grupo=legislacao | Letra da lei por artigo (+ Planalto como texto compilado) | M1 | não verificado |
| c | STJ – Jurisprudência | https://dadosabertos.web.stj.jus.br/group/jurisprudencia | Acórdãos/ementas | M2 | não verificado |
| d | STJ – Grupos | https://dadosabertos.web.stj.jus.br/group/ | Descoberta de conjuntos | M2 | não verificado |
| e | STJ – DJe | https://dadosabertos.web.stj.jus.br/group/dje | Publicações (termo inicial de prazos) | M2 | não verificado |
| f | STJ – Precedentes | https://dadosabertos.web.stj.jus.br/group/precedentes | Repetitivos/IAC | M2 | não verificado |
| g | TJRS – API de dados abertos | https://www.tjrs.jus.br/novo/api-de-dados-abertos/ | Modelo de tribunal estadual | M4 | não verificado |
| h | Súmulas STJ (dados abertos) | https://dadosabertos.web.stj.jus.br/ | Enunciados | M2 | não verificado |
| i | DataJud (API pública CNJ) | https://dadosabertos.web.stj.jus.br/dataset/api-publica-datajud | Metadados de processos (exige chave pública do CNJ) | M3 | não verificado |
| j | Portal dados abertos STJ | https://dadosabertos.web.stj.jus.br/ | Índice geral | M2 | não verificado |
| k | SCON – Súmulas STJ | https://scon.stj.jus.br/SCON/sumstj/ | Conferência manual dos enunciados | M2 | não verificado |
| l | TJDFT – Dados abertos | https://www.tjdft.jus.br/transparencia/tecnologia-da-informacao-e-comunicacao/dados-abertos | Modelo de tribunal estadual/distrital | M4 | não verificado |
| m | CNJ – Justiça em Números (base) | https://www.cnj.jus.br/pesquisas-judiciarias/justica-em-numeros/base-de-dados/ | Estatística/contexto | M3 | não verificado |

## Lacunas a cobrir
- STF, TST e atos normativos do CNJ (resoluções/instruções): fontes ainda não listadas — mapear no M4.
- Calendário de feriados/suspensões por tribunal (para o motor de prazos).

## Sondagem
Resultados reais em `data/sondagem/` (workflow `sondagem`). Uma fonte só passa de `não verificado` para verificada após resposta 200 com formato conferido por pessoa. Candidatos de endpoint em `src/ordem/data/fontes.json` (origem `candidato`) são palpites, não fatos.

### Resultado da 1ª sondagem (11/11/2026, GitHub Actions)
- **Câmara** `api/v2/...`: 200 JSON. **STJ CKAN** `api/3/action/package_list`: 200 JSON (CKAN 2.10; há `precedentes-qualificados`, `espelhos-de-acordaos-*`, `integras-de-decisoes-*`; súmulas não aparecem como conjunto: conferir no SCON). **Senado**: portal 200; Swagger em `legis.senado.leg.br/dadosabertos/docs/` (spec a localizar). **CNJ, TJDFT, DataJud (página STJ)**: páginas 200 (HTML).
- **LexML**: 200, mas é página de verificação anti-robô, sem dados → não usar.
- **TJRS**: timeout de conexão (tentar de novo).
