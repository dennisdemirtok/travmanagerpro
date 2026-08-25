-- TravManager — Migration 016: Loppklasser med tak, nybörjarskydd, AI-stall

ALTER TABLE races ADD COLUMN IF NOT EXISTS max_start_points INTEGER;
ALTER TABLE races ADD COLUMN IF NOT EXISTS max_earnings BIGINT;

ALTER TABLE stables ADD COLUMN IF NOT EXISTS ai_personality VARCHAR(20);
ALTER TABLE stables ADD COLUMN IF NOT EXISTS difficulty_tier VARCHAR(10) NOT NULL DEFAULT 'normal';
ALTER TABLE stables ADD COLUMN IF NOT EXISTS player_starts INTEGER NOT NULL DEFAULT 0;

ALTER TYPE race_class ADD VALUE IF NOT EXISTS 'qualifier';
ALTER TYPE race_class ADD VALUE IF NOT EXISTS 'maiden';
