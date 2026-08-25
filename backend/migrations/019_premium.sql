-- TravManager — Migration 019: Premium, kosmetik och säsongspass
-- OBS: ingen betalleverantör är inkopplad. Rättigheterna finns, köpflödet
-- måste kopplas till en riktig betaltjänst innan lansering.

ALTER TABLE stables ADD COLUMN IF NOT EXISTS premium_until_week INTEGER;
ALTER TABLE stables ADD COLUMN IF NOT EXISTS stable_color VARCHAR(9) NOT NULL DEFAULT '#D4A853';
ALTER TABLE stables ADD COLUMN IF NOT EXISTS stable_color_secondary VARCHAR(9) NOT NULL DEFAULT '#0B0E14';
ALTER TABLE stables ADD COLUMN IF NOT EXISTS sulky_design VARCHAR(30) NOT NULL DEFAULT 'classic';
ALTER TABLE stables ADD COLUMN IF NOT EXISTS banner VARCHAR(30) NOT NULL DEFAULT 'default';
ALTER TABLE stables ADD COLUMN IF NOT EXISTS season_pass_season INTEGER;
ALTER TABLE stables ADD COLUMN IF NOT EXISTS season_pass_points INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS cosmetic_unlocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    item_key VARCHAR(40) NOT NULL,
    source VARCHAR(20) NOT NULL DEFAULT 'purchase',
    unlocked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(stable_id, item_key)
);

CREATE INDEX IF NOT EXISTS idx_cosmetic_unlocks_stable ON cosmetic_unlocks(stable_id);
