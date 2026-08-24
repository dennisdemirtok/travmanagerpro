-- TravManager — Migration 012: Ekonomi 2.0
-- Lån, skuldhantering, uppfödarpremie, sponsoraktivering.

ALTER TABLE stables ADD COLUMN IF NOT EXISTS loan_principal BIGINT NOT NULL DEFAULT 0;
ALTER TABLE stables ADD COLUMN IF NOT EXISTS loan_taken_week INTEGER;
ALTER TABLE stables ADD COLUMN IF NOT EXISTS forced_sale_deadline_week INTEGER;
ALTER TABLE stables ADD COLUMN IF NOT EXISTS debt_warning_week INTEGER;
ALTER TABLE stables ADD COLUMN IF NOT EXISTS restarts_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE horses ADD COLUMN IF NOT EXISTS breeder_stable_id UUID REFERENCES stables(id) ON DELETE SET NULL;

ALTER TABLE sponsor_contracts ADD COLUMN IF NOT EXISTS min_starts_per_week INTEGER NOT NULL DEFAULT 2;

CREATE INDEX IF NOT EXISTS idx_horses_breeder ON horses(breeder_stable_id);

ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'finance';
ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'stable_round';
ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'training';
ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'goal';
