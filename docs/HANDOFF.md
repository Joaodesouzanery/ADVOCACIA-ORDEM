# Como continuar este projeto em outro chat do Claude

1. Conecte o repositório `joaodesouzanery/advocacia-ordem` no novo chat (Claude Code na web/app/CLI).
2. Use o branch de trabalho atual (ver `docs/ROADMAP.md` → "Próxima tarefa").
3. O Claude lê `CLAUDE.md` automaticamente. Depois: `docs/ROADMAP.md` → `docs/DECISIONS.md` → `docs/FONTES.md`.
4. Prompt-modelo para colar:
   > Leia CLAUDE.md, docs/ROADMAP.md e docs/HANDOFF.md e continue a "Próxima tarefa" do ROADMAP. Ao terminar, atualize o ROADMAP e faça commit/push.

## O que fica na nuvem (fora do repo)
| Onde | O quê | Status |
|------|-------|--------|
| GitHub | código, docs, Actions (`tests`, `ingestao`) | ativo |
| Repo `data/` | corpus público: `corpus.csv`, `corpus.xlsx`, relatório (gerados pelo workflow) | ativo após 1ª execução |
| GitHub Secrets (Settings → Secrets and variables → Actions) | `SUPABASE_URL` = https://kefkgydvjjakqaonyjau.supabase.co; `SUPABASE_SERVICE_ROLE_KEY` (Supabase → TAF → Settings → API); `DATAJUD_API_KEY` (só M3) | a configurar pelo usuário |
| Supabase | Postgres + pgvector (substitui o SQLite local; opcional por ora) | futuro |
| Vercel/Supabase Edge | MCP remoto (M4) | futuro |

Nunca coloque segredos nem dados de clientes no repositório (ver `CLAUDE.md`).

## Regra de fim de sessão
Antes de encerrar qualquer chat: atualizar "Próxima tarefa" no ROADMAP, commit e push. Trabalho não enviado ao GitHub se perde (o container da nuvem é efêmero).

## Rodar a ingestão (letra da lei)
GitHub → aba **Actions** → **ingestao** → **Run workflow** (campo vazio = todas as normas). Ao terminar, o robô commita `data/corpus.xlsx` (abre no Excel) e `data/corpus.csv`. Localmente: `pip install -e ".[ingest,excel]"` e `ordem ingerir --xlsx`.
