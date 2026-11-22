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
00000. **Senado (22/11/2026)**: API `/legislacao/urn` confirmada (JSON), mas traz só identificação + histórico de alterações por artigo, **não o texto**. `connectors/senado.py` + `ordem ingerir-senado` + workflow `senado.yml` → `data/senado_normas.json`; `artigos_para_pedido` passa a trazer `norma_oficial` (link normas.leg.br) e `alteracoes_senado`. Texto dos artigos segue pendente: Planalto (bloqueia Actions), LexML (anti-robô). Próximo candidato: sondar `normas.leg.br` e `legis.senado.leg.br/norma/{id}`, ou ingestão local do Planalto.
0000. **1ª ingestão STJ real (22/11/2026)**: 165 de 166 arquivos ok; 8.368 julgados de Família (3ª/4ª Turma, 2ª Seção) + 33 precedentes; `data/jurisprudencia.csv` ~16 MB. Problemas: (a) termo 'adocao' gerava ~2.000 falsos positivos → termos de `poder_familiar` tornados específicos (reingerir); (b) `espelhos-de-acordaos-segunda-secao/20240229.json` com JSON inválido (mês sem lançamentos): ignorado; (c) CSV grande no git: avaliar mover para Supabase. **Senado**: spec lista `/legislacao/urn`, `/legislacao/{tipo}/{numdata}/{anoseq}`, `/legislacao/lista`; sondagem 4 mostra parâmetros e uma chamada real por URN.
000. **Parser STJ pronto (22/11/2026)**: `connectors/stj.py` (formatos reais da sondagem 2), `storage/jurisprudencia.py`, `ordem ingerir-stj`, `ordem buscar-jurisprudencia`, MCP `buscar_jurisprudencia`, workflow `jurisprudencia.yml` (push/manual/mensal). Só Família (filtro por tema na ementa, `TEMAS_FAMILIA` é escolha editorial a revisar). Falta: conferir o 1º resultado real em `data/jurisprudencia_relatorio.json`; tabela no Supabase (migration 0003); súmulas (SCON, sem conjunto no CKAN).
00. **Sondagem 2 enviada (22/11/2026)**: STJ `package_show` + cabeçalho (Range) dos recursos de precedentes-qualificados e espelhos (3ª/4ª Turma, 2ª Seção); Senado: candidatos de spec OpenAPI. Decisão: acórdãos só de Família, filtrados por ementa. Próximo: ler `data/sondagem/stj.json`/`senado.json` e escrever `connectors/stj.py` com os nomes de campo REAIS.
0. 1ª sondagem feita (ver FONTES.md). Próximo: spec OpenAPI do Senado (swagger-initializer.js), `package_show` do STJ (precedentes-qualificados, espelhos de acórdãos) → escrever parsers. LexML descartado (anti-robô).
1. Ler `data/sondagem/resumo.json` (gerado pelo workflow `sondagem` após o push). Para cada fonte com `ok=true`, olhar a amostra e escrever o parser real (Senado/LexML texto por artigo → `ingest`; STJ CKAN `package_list`/`package_show` → súmulas/precedentes). Fonte com falha: registrar em `FONTES.md`, tentar rota oficial alternativa; não contornar bloqueio.
2. Planalto recusa o GitHub Actions: manter só como link de conferência (ou rodar `ordem ingerir --xlsx` localmente).
3. Supabase TAF: migration 0002 aplicada; 16 tabelas antigas ficam. Falta: secrets `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` no GitHub; renomear projeto; merge do PR #1.
4. Pendências: ADCT da CF; embeddings; DataJud (secret `DATAJUD_API_KEY`); M2 STJ; M3; M4.
