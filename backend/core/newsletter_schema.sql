-- Newsletter Subscription System Schema
-- Run this script in Supabase SQL Editor
-- Version: 1.0.0

-- =============================================================================
-- Newsletter Subscriptions
-- Stores email subscribers with their preferred frequency
-- =============================================================================
CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  frequency TEXT NOT NULL CHECK (frequency IN ('daily', 'weekly', 'monthly', 'now')),
  created_at TIMESTAMPTZ DEFAULT now(),
  last_sent_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT true
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_subscriptions_email ON newsletter_subscriptions(email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_frequency_active ON newsletter_subscriptions(frequency, is_active) 
  WHERE is_active = true;

-- =============================================================================
-- Newsletter Runs
-- Tracks each batch newsletter send (for auditing and debugging)
-- =============================================================================
CREATE TABLE IF NOT EXISTS newsletter_runs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  frequency TEXT NOT NULL,
  run_at TIMESTAMPTZ DEFAULT now(),
  status TEXT CHECK (status IN ('pending', 'running', 'success', 'error')) DEFAULT 'pending',
  subscribers_count INTEGER DEFAULT 0,
  emails_sent INTEGER DEFAULT 0,
  error_message TEXT,
  llm_response TEXT,  -- Store raw Ollama response for auditing
  completed_at TIMESTAMPTZ
);

-- Index for recent runs lookup
CREATE INDEX IF NOT EXISTS idx_runs_status ON newsletter_runs(status, run_at DESC);

-- =============================================================================
-- Newsletter Items
-- Companies included in each newsletter run
-- =============================================================================
CREATE TABLE IF NOT EXISTS newsletter_items (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  run_id UUID REFERENCES newsletter_runs(id) ON DELETE CASCADE,
  company_number TEXT NOT NULL,
  company_name TEXT NOT NULL,
  eis_score INTEGER,
  eis_status TEXT,
  sector TEXT,
  news_summary TEXT
);

-- Index for efficient joins
CREATE INDEX IF NOT EXISTS idx_items_run_id ON newsletter_items(run_id);

-- =============================================================================
-- Grant permissions (for Supabase anon key)
-- =============================================================================
GRANT USAGE ON SCHEMA public TO anon;
GRANT ALL ON newsletter_subscriptions TO anon;
GRANT ALL ON newsletter_runs TO anon;
GRANT ALL ON newsletter_items TO anon;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon;
