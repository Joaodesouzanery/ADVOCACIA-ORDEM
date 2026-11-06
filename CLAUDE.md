# CLAUDE.md — leia isto primeiro (retomada de contexto entre chats)

## Objetivo
Base jurídica de **dados abertos** (legislação + tribunais + CNJ) para escritórios de advocacia, exposta ao Claude via **servidor MCP**. Pergunta-modelo: *"Cliente quer a guarda do filho: quais artigos fundamentam e qual o prazo processual?"*. Pode virar consultoria/empresa.

Fluxo do escritório: cliente envia fatos+documentos → checklist → rascunho de petição inicial **só com fatos fornecidos** → revisão do advogado → aval do cliente → protocolo.

## Regras inegociáveis
1. **Nunca inventar** fato, artigo, súmula ou prazo. Toda citação precisa de fonte+URL oficial e status de verificação. Campo ausente = `[PENDENTE]`.
2. Prazos são **sugestões** a conferir por advogado(a) (feriados locais, suspensões).
3. **Sem dados de clientes no repositório** (LGPD). Clientes ficam no Supabase com RLS, separados do corpus público.
4. **Sem segredos no repo.** Use `.env` (ver `.env.example`) / secrets do GitHub, Supabase, Vercel.
5. Ferramenta de apoio; não substitui advogado inscrito na OAB (`docs/AVISO_JURIDICO.md`).

## Estado atual
Ver `docs/ROADMAP.md` (fonte de verdade do progresso) e `docs/DECISIONS.md`. Marco atual: **M0 concluído** (scaffolding + motor de prazos + MCP com curadoria de Família). Próximo: **M1** (ingestão real Planalto/Senado → Supabase + busca híbrida).

## Stack e decisões
Python 3.11+, Supabase (Postgres + pgvector), MCP (`mcp>=2`, classe `MCPServer`). MVP: Direito de Família (guarda, alimentos, divórcio).

## Como rodar
```
pip install -e ".[dev,mcp]"
pytest
ordem prazo contestacao 2026-03-02
ordem pedido guarda
python -m ordem.mcp_server.server        # servidor MCP (stdio)
```
Conectar ao Claude Code: `claude mcp add ordem -- python -m ordem.mcp_server.server`.

## Mapa do código
- `src/ordem/prazos/` calendário (feriados, recesso CPC 220) + motor (CPC 219/224)
- `src/ordem/data/*.json` regras de prazo e mapa curado pedido→fundamentos (**verificar=true**)
- `src/ordem/connectors/` conectores (base + parser Planalto); rede só no `fetch()`
- `src/ordem/mcp_server/server.py` ferramentas MCP
- `supabase/migrations/` schema
- `docs/FONTES.md` catálogo das fontes de dados abertos e status de verificação

## Ambiente de desenvolvimento
O sandbox do Claude Code na nuvem **não alcança** os sites de dados abertos (proxy). Ingestão real roda em GitHub Actions/local. Testes usam fixtures offline (sintéticas).

## Continuidade entre chats
Ver `docs/HANDOFF.md`. Ao fim de cada sessão: atualizar "Próxima tarefa" no ROADMAP, commit e push.

## Convenções
Português nos domínios jurídicos; commits curtos e descritivos; atualizar `docs/ROADMAP.md` a cada marco.
