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
1. **Usuário:** GitHub → Actions → "ingestao" → Run workflow. Conferir `data/ingestao_relatorio.json` (normas com erro = URL/layout a corrigir em `normas.json`/parser) e abrir `data/corpus.xlsx`.
2. Corrigir o que falhar; marcar fontes como verificadas em `docs/FONTES.md`.
3. Pendências: ADCT da CF (numeração repetida, hoje descartada); conector Senado (fonte b) para metadados; busca semântica (embeddings) quando houver Supabase/pgvector.
4. Depois: M2 (STJ súmulas/precedentes) reaproveitando `storage` + workflow.
