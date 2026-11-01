-- ORDEM: corpus jurídico público. Dados de CLIENTES ficam em tabelas separadas, com RLS (futuro, M3).
create extension if not exists vector;
create extension if not exists unaccent;

create table if not exists fonte (
  id bigserial primary key,
  nome text not null unique,           -- ex.: planalto, senado, stj, datajud
  url text not null,
  tipo text not null,                  -- legislacao | jurisprudencia | estatistica
  licenca text,
  ultima_coleta timestamptz
);

create table if not exists norma (
  id bigserial primary key,
  fonte_id bigint references fonte(id),
  tipo text not null,                  -- lei | codigo | cf | decreto | resolucao
  numero text, ano int,
  nome text not null,                  -- "Código Civil"
  ementa text,
  url_oficial text not null,
  vigente boolean default true,
  coletado_em timestamptz default now(),
  unique (tipo, numero, ano)
);

create table if not exists dispositivo (
  id bigserial primary key,
  norma_id bigint not null references norma(id) on delete cascade,
  caminho text not null,               -- "art. 1.583"
  texto text not null,
  url_oficial text not null,
  embedding vector(1024),
  tsv tsvector generated always as (to_tsvector('portuguese', unaccent(texto))) stored,
  unique (norma_id, caminho)
);
create index if not exists dispositivo_tsv_idx on dispositivo using gin (tsv);

create table if not exists sumula (
  id bigserial primary key,
  tribunal text not null,              -- STJ | STF | TST
  numero int not null,
  enunciado text not null,
  situacao text,                       -- vigente | cancelada | superada
  url_oficial text not null,
  coletado_em timestamptz default now(),
  unique (tribunal, numero)
);

create table if not exists acordao (
  id bigserial primary key,
  tribunal text not null,
  numero_processo text not null,
  relator text, data_julgamento date,
  ementa text not null,
  url_oficial text not null,
  embedding vector(1024),
  tsv tsvector generated always as (to_tsvector('portuguese', unaccent(ementa))) stored,
  unique (tribunal, numero_processo)
);
create index if not exists acordao_tsv_idx on acordao using gin (tsv);

create table if not exists regra_prazo (
  id text primary key,                 -- ex.: contestacao
  ato text not null,
  dias int not null,
  tipo text not null check (tipo in ('uteis','corridos')),
  base_legal text not null,
  termo_inicial text,
  observacoes text,
  verificado_por_advogado boolean not null default false
);

-- Corpus público: leitura aberta, escrita só via service role.
alter table fonte enable row level security;
alter table norma enable row level security;
alter table dispositivo enable row level security;
alter table sumula enable row level security;
alter table acordao enable row level security;
alter table regra_prazo enable row level security;
create policy "leitura publica" on fonte for select using (true);
create policy "leitura publica" on norma for select using (true);
create policy "leitura publica" on dispositivo for select using (true);
create policy "leitura publica" on sumula for select using (true);
create policy "leitura publica" on acordao for select using (true);
create policy "leitura publica" on regra_prazo for select using (true);
