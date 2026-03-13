-- 009: Add form_history column to track form values over time (for sparklines)
ALTER TABLE horses ADD COLUMN IF NOT EXISTS form_history JSONB NOT NULL DEFAULT '[]';
