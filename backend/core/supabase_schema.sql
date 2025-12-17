-- Supabase Schema for Currency Intelligence Platform
-- Run this script in Supabase SQL Editor (https://supabase.com/dashboard)

-- =============================================================================
-- FX Rates Table
-- Stores historical exchange rate data from Treasury/FMP APIs
-- =============================================================================
create table if not exists fx_rates (
  id uuid default gen_random_uuid() primary key,
  currency_pair text not null,  -- 'EUR', 'GBP', 'CAD'
  rate decimal(10,6) not null,
  record_date date not null,
  source text default 'treasury',
  created_at timestamp with time zone default now(),
  unique(currency_pair, record_date)
);

-- Enable Row Level Security (optional, for multi-tenant)
-- alter table fx_rates enable row level security;

-- Index for fast date-based queries
create index if not exists idx_fx_rates_date on fx_rates(record_date desc);
create index if not exists idx_fx_rates_currency on fx_rates(currency_pair);

-- =============================================================================
-- Forecasts Table
-- Stores ML model predictions with confidence intervals
-- =============================================================================
create table if not exists forecasts (
  id uuid default gen_random_uuid() primary key,
  currency_pair text not null,
  forecast_date date not null,
  horizon_days int not null,
  point_forecast decimal(10,6),
  lower_bound decimal(10,6),
  upper_bound decimal(10,6),
  confidence_score decimal(3,2),
  model_weights jsonb,
  created_at timestamp with time zone default now()
);

-- Index for fast currency lookups
create index if not exists idx_forecasts_currency on forecasts(currency_pair, forecast_date);

-- =============================================================================
-- Alerts Table
-- Stores system alerts and notifications
-- =============================================================================
create table if not exists alerts (
  id uuid default gen_random_uuid() primary key,
  severity text check (severity in ('info', 'warning', 'critical')),
  title text not null,
  message text,
  currency_pair text,
  acknowledged boolean default false,
  created_at timestamp with time zone default now()
);

-- Index for unacknowledged alerts
create index if not exists idx_alerts_unacked on alerts(acknowledged, created_at desc);

-- =============================================================================
-- Model Performance Table (for tracking)
-- Stores model accuracy metrics over time
-- =============================================================================
create table if not exists model_performance (
  id uuid default gen_random_uuid() primary key,
  model_name text not null,  -- 'prophet', 'arima', 'xgboost', 'ensemble'
  currency_pair text not null,
  metric_date date not null,
  mape decimal(5,4),
  directional_accuracy decimal(5,4),
  rmse decimal(10,6),
  created_at timestamp with time zone default now(),
  unique(model_name, currency_pair, metric_date)
);

-- =============================================================================
-- Grant permissions (for supabase anon key)
-- =============================================================================
grant usage on schema public to anon;
grant all on all tables in schema public to anon;
grant all on all sequences in schema public to anon;
