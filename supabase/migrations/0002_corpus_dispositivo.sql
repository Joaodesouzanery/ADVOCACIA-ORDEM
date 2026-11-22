-- M1: tabela plana do corpus (espelha o SQLite local / data/corpus.csv).
-- Corpus é PÚBLICO (texto de lei): leitura liberada; escrita só com service role.
create extension if not exists unaccent with schema extensions;
create extension if not exists vector with schema extensions;

create or replace function public.ordem_unaccent(t text) returns text
language sql immutable parallel safe set search_path = ''
as $$ select extensions.unaccent('extensions.unaccent'::regdictionary, t) $$;

create table if not exists public.corpus_dispositivo (
  id bigserial primary key,
  norma_id text not null,
  norma text not null,
  caminho text not null,
  numero int,
  texto text not null,
  url_oficial text not null,
  fonte text not null,
  coletado_em timestamptz not null,
  embedding extensions.vector(1024),
  tsv tsvector generated always as (to_tsvector('portuguese', public.ordem_unaccent(texto))) stored,
  unique (norma_id, caminho)
);
create index if not exists corpus_disp_tsv_idx on public.corpus_dispositivo using gin (tsv);
create index if not exists corpus_disp_norma_num_idx on public.corpus_dispositivo (norma_id, numero);

alter table public.corpus_dispositivo enable row level security;
drop policy if exists "corpus leitura publica" on public.corpus_dispositivo;
create policy "corpus leitura publica" on public.corpus_dispositivo for select to anon, authenticated using (true);

create or replace function public.buscar_dispositivos(consulta text, limite int default 10, filtro_norma text default null)
returns setof public.corpus_dispositivo
language sql stable set search_path = ''
as $$
  select d.* from public.corpus_dispositivo d
  where d.tsv @@ websearch_to_tsquery('portuguese', public.ordem_unaccent(consulta))
    and (filtro_norma is null or d.norma_id = filtro_norma)
  order by ts_rank(d.tsv, websearch_to_tsquery('portuguese', public.ordem_unaccent(consulta))) desc
  limit limite
$$;
