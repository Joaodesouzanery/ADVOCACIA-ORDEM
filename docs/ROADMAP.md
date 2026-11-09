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

## Próxima tarefa (atualizar a cada sessão)
1. **Planalto recusa os servidores do GitHub Actions** (1ª execução em 09/11/2026: "Server disconnected" em todas as normas). Não contornar o bloqueio. Opções: (a) rodar `ordem ingerir --xlsx` num computador local e commitar `data/corpus.csv`; (b) fonte oficial com API aberta (LexML / Senado dados abertos); (c) pedir acesso ao Planalto.
2. Supabase: projeto **TAF** (`kefkgydvjjakqaonyjau`) reaproveitado e reativado. Aplicar `supabase/migrations/0002_corpus_dispositivo.sql` (pelo MCP ficou aguardando confirmação do usuário). As 16 tabelas antigas do TAF (vazias) **não** foram apagadas: perguntar ao usuário. Renomear o projeto no painel.
3. Usuário: cadastrar secrets `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` no GitHub (Settings → Secrets and variables → Actions).
4. Pendências: ADCT da CF; conector Senado; embeddings; M2 (STJ).
