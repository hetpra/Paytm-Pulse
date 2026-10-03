create table if not exists ext_kv (
  namespace text not null,
  id text not null,
  data jsonb not null,
  created_at timestamptz default now(),
  primary key (namespace, id)
);
