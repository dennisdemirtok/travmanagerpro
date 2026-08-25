-- TravManager — Migration 015: Hästdagboken (egna anteckningar och taggar)

CREATE TABLE IF NOT EXISTS horse_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id UUID NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    stable_id UUID NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    game_week INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_horse_notes_horse ON horse_notes(horse_id);

CREATE TABLE IF NOT EXISTS horse_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id UUID NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    stable_id UUID NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    tag VARCHAR(40) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(horse_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_horse_tags_horse ON horse_tags(horse_id);
