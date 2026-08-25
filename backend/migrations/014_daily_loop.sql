-- TravManager — Migration 014: Dagsloopen (träning + stallrunda + tidsstyrning)

ALTER TABLE horses ADD COLUMN IF NOT EXISTS daily_training VARCHAR(20) NOT NULL DEFAULT 'light';
ALTER TABLE horses ADD COLUMN IF NOT EXISTS hard_training_streak INTEGER NOT NULL DEFAULT 0;
ALTER TABLE horses ADD COLUMN IF NOT EXISTS last_training_day INTEGER;
ALTER TABLE horses ADD COLUMN IF NOT EXISTS form_window_until_day INTEGER;
ALTER TABLE horses ADD COLUMN IF NOT EXISTS form_window_bonus INTEGER NOT NULL DEFAULT 0;
ALTER TABLE horses ADD COLUMN IF NOT EXISTS equipment_damaged BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE horses ADD COLUMN IF NOT EXISTS stat_gain_week INTEGER;
ALTER TABLE horses ADD COLUMN IF NOT EXISTS stat_gain_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE stables ADD COLUMN IF NOT EXISTS last_stable_round_day INTEGER;
ALTER TABLE stables ADD COLUMN IF NOT EXISTS last_serious_event_week INTEGER;

CREATE INDEX IF NOT EXISTS idx_events_pending ON stable_events(stable_id) WHERE requires_action = true;
