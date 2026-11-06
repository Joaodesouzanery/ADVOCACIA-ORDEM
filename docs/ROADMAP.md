# Roadmap

- [x] **M0** — scaffolding, motor de prazos (CPC 219/224/220), mapa curado de Família (guarda/alimentos/divórcio), servidor MCP com 5 ferramentas, parser Planalto, schema Supabase, testes offline.
- [ ] **M1** — ingestão real: Planalto/Senado (CC, ECA, CPC, Lei 5.478, CF 226–229) → Supabase; busca híbrida (texto + pgvector); `artigos_para_pedido` passa a devolver TEXTO oficial ingerido e marca `verificado`; GitHub Action de ingestão agendada. **Validar endpoints reais fora do sandbox.**
- [ ] **M2** — STJ: súmulas, precedentes/repetitivos, jurisprudência, DJe; validação das regras de prazo por advogado(a).
- [ ] **M3** — DataJud/CNJ (metadados, Justiça em Números); checklist/rascunho refinados; tabelas de clientes com RLS e trilha de auditoria (aval do cliente).
- [ ] **M4** — demais tribunais (TJRS, TJDFT, STF, TST, atos do CNJ); MCP remoto (Vercel/Supabase Edge); multi-tenant se virar produto.

## Pendências de conformidade
- Revisar com advogado: regras de prazo, textos, política de uso de IA e publicidade (OAB), LGPD.

## Próxima tarefa (atualizar a cada sessão)
M1, passo 1: conector `src/ordem/connectors/senado.py` (API de legislação do Senado) + migration `0002_dispositivos_busca.sql` (tsvector pt + pgvector) + `ordem ingerir` + workflow `.github/workflows/ingestao.yml` (agendado/manual, usa secrets). Testes com fixtures offline. Normas: CC Família (1.511–1.783), ECA, CPC (prazos, 693–699), Lei 5.478/68, CF 226–229.
