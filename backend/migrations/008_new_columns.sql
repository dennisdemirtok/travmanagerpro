-- 008: Add missing columns from recent features

-- Stable: press release + sponsor collection tracking
ALTER TABLE stables ADD COLUMN IF NOT EXISTS last_press_release_week INT NOT NULL DEFAULT 0;
ALTER TABLE stables ADD COLUMN IF NOT EXISTS last_sponsor_collection_week INT NOT NULL DEFAULT 0;

-- Horse: training lock system
ALTER TABLE horses ADD COLUMN IF NOT EXISTS training_locked_until INT;
ALTER TABLE horses ADD COLUMN IF NOT EXISTS training_last_result JSONB;
