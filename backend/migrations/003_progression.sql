-- Migration 003: Add recovery tracking to game_state
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS last_recovery_game_day INT;
