-- TravManager — Migration 013: Sulky & uppvärmning på anmälan
-- Dessa kolumner har hittills bara skapats av dev-endpointen /game/dev/run-migrations,
-- vilket gjorde att en färsk databas saknade dem och loppsimuleringen kraschade.

ALTER TABLE race_entries ADD COLUMN IF NOT EXISTS sulky_type VARCHAR(20) NOT NULL DEFAULT 'european';
ALTER TABLE race_entries ADD COLUMN IF NOT EXISTS warmup_intensity VARCHAR(20) NOT NULL DEFAULT 'normal';
