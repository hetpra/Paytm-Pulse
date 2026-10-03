-- Paytm Pulse — Database schema (Postgres/Supabase)

create table if not exists merchants (
  id text primary key,
  name text not null,
  owner_name text,
  cash_balance numeric not null default 0,
  preapproved_limit numeric not null default 0,
  plan text not null default 'free'            -- free | premium
);

create table if not exists suppliers (
  id text primary key,
  name text not null,
  city text
);

create table if not exists skus (
  id text primary key,
  merchant_id text references merchants(id),
  supplier_id text references suppliers(id),
  name text not null,
  emoji text,
  unit_cost numeric not null,
  sell_price numeric not null,
  current_stock int not null,
  incoming_qty int not null default 0,
  incoming_eta date,
  lead_time_days int not null default 2
);

create table if not exists daily_sales (
  sku_id text references skus(id),
  sale_date date not null,
  units_sold int not null,
  primary key (sku_id, sale_date)
);

create table if not exists forecasts (
  sku_id text primary key references skus(id),
  computed_at timestamptz default now(),
  engine text,
  avg_daily_demand numeric,
  days_left numeric,
  stockout_date date,
  series jsonb                                  -- [{date, yhat, lower, upper}] x FORECAST_HORIZON
);

create table if not exists proposals (
  id text primary key,
  merchant_id text references merchants(id),
  thread_id text,
  status text not null default 'pending',       -- pending | approved | rejected
  alert_text text,
  payload jsonb not null,                       -- full Proposal JSON (§4.5)
  created_at timestamptz default now(),
  decided_at timestamptz
);

create table if not exists purchase_orders (
  id text primary key,
  proposal_id text references proposals(id),
  merchant_id text,
  supplier_id text,
  items jsonb not null,
  subtotal numeric,
  platform_fee numeric,
  total numeric,
  status text default 'sent',
  created_at timestamptz default now()
);

create table if not exists loans (
  id text primary key,
  proposal_id text references proposals(id),
  merchant_id text,
  principal numeric,
  interest_rate_pct numeric,
  interest numeric,
  processing_fee numeric,
  tenure_days int,
  total_repayment numeric,
  status text default 'disbursed',
  created_at timestamptz default now()
);
