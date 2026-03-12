-- 002_race_overhaul.sql
-- Race system overhaul: auto-simulation, real drivers, start points, paid compatibility

-- 1. Add game_day to race_sessions (which day of the game week the session runs)
ALTER TABLE race_sessions ADD COLUMN IF NOT EXISTS game_day INT NOT NULL DEFAULT 1;

-- 2. Add min_start_points to races (minimum points required to enter)
ALTER TABLE races ADD COLUMN IF NOT EXISTS min_start_points INT NOT NULL DEFAULT 0;

-- 3. Add is_real_driver to drivers (distinguish seeded real drivers)
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS is_real_driver BOOLEAN NOT NULL DEFAULT false;

-- 4. Add is_paid to compatibility_cache (was this a paid check or auto-calculated)
ALTER TABLE compatibility_cache ADD COLUMN IF NOT EXISTS is_paid BOOLEAN NOT NULL DEFAULT true;
