-- TravManager — Migration 017: Säsongsmål och säsongsberättelse

CREATE TABLE IF NOT EXISTS season_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    season_number INTEGER NOT NULL,
    goal_key VARCHAR(40) NOT NULL,
    title VARCHAR(120) NOT NULL,
    description VARCHAR(300),
    target INTEGER NOT NULL DEFAULT 1,
    progress INTEGER NOT NULL DEFAULT 0,
    reward_money BIGINT NOT NULL DEFAULT 0,
    reward_reputation INTEGER NOT NULL DEFAULT 0,
    reward_text VARCHAR(120),
    is_completed BOOLEAN NOT NULL DEFAULT false,
    completed_week INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(stable_id, season_number, goal_key)
);

CREATE INDEX IF NOT EXISTS idx_season_goals_stable ON season_goals(stable_id, season_number);

ALTER TABLE stables ADD COLUMN IF NOT EXISTS season_goals_generated INTEGER;
ALTER TABLE stables ADD COLUMN IF NOT EXISTS last_season_summary INTEGER;
