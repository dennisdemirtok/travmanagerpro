-- TravManager — Migration 005: Weekly Processing Tracker
-- Adds column to track when weekly sponsor/market processing last ran,
-- fixing the bug where get_game_state() pre-updates current_game_week
-- before the ticker can detect a week change.

ALTER TABLE game_state
ADD COLUMN IF NOT EXISTS last_weekly_processing_week INT;
