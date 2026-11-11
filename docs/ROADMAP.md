# Roadmap

- [x] **M0** — scaffolding, motor de prazos (CPC 219/224/220), mapa curado de Família (guarda/alimentos/divórcio), servidor MCP com 5 ferramentas, parser Planalto, schema Supabase, testes offline.
- [ ] **M1** (em andamento) — ingestão real: Planalto/Senado (CC, ECA, CPC, Lei 5.478, CF 226–229) → Supabase; busca híbrida (texto + pgvector); `artigos_para_pedido` passa a devolver TEXTO oficial ingerido e marca `verificado`; GitHub Action de ingestão agendada. **Validar endpoints reais fora do sandbox.**
- [ ] **M2** — STJ: súmulas, precedentes/repetitivos, jurisprudência, DJe; validação das regras de prazo por advogado(a).
- [ ] **M3** — DataJud/CNJ (metadados, Justiça em Números); checklist/rascunho refinados; tabelas de clientes com RLS e trilha de auditoria (aval do cliente).
- [ ] **M4** — demais tribunais (TJRS, TJDFT, STF, TST, atos do CNJ); MCP remoto (Vercel/Supabase Edge); multi-tenant se virar produto.

## Pendências de conformidade
- Revisar com advogado: regras de prazo, textos, política de uso de IA e publicidade (OAB), LGPD.

## M1 — feito nesta etapa
- Armazenamento SQLite + FTS5 (`src/ordem/storage/`), export CSV/XLSX, catálogo de normas (`src/ordem/data/normas.json`).
- `ordem ingerir|buscar|exportar`; workflow `.github/workflows/ingestao.yml` (manual + semanal) commita `data/corpus.csv`, `data/corpus.xlsx`, `data/ingestao_relatorio.json`.
- MCP: `artigos_para_pedido` anexa texto oficial (ou `[PENDENTE]`); nova ferramenta `buscar_dispositivo`.

## Fontes de dados abertos — estado (11/11/2026)
Sandbox não alcança nenhuma fonte (403 do proxy). Por isso: conectores com parsing puro + **sondagem** (`ordem sondar`, workflow `sondagem.yml`) que roda no GitHub e commita `data/sondagem/*.json` (status, formato, amostra). Feito: `connectors/http.py`, `connectors/ckan.py` (STJ), `connectors/lexml.py` (URN), `data/fontes.json`. Ainda NÃO baixa texto do Senado/LexML/STJ: o formato real só é conhecido após a 1ª sondagem.

## Próxima tarefa (atualizar a cada sessão)
1. Ler `data/sondagem/resumo.json` (gerado pelo workflow `sondagem` após o push). Para cada fonte com `ok=true`, olhar a amostra e escrever o parser real (Senado/LexML texto por artigo → `ingest`; STJ CKAN `package_list`/`package_show` → súmulas/precedentes). Fonte com falha: registrar em `FONTES.md`, tentar rota oficial alternativa; não contornar bloqueio.
2. Planalto recusa o GitHub Actions: manter só como link de conferência (ou rodar `ordem ingerir --xlsx` localmente).
3. Supabase TAF: migration 0002 aplicada; 16 tabelas antigas ficam. Falta: secrets `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` no GitHub; renomear projeto; merge do PR #1.
4. Pendências: ADCT da CF; embeddings; DataJud (secret `DATAJUD_API_KEY`); M2 STJ; M3; M4.
