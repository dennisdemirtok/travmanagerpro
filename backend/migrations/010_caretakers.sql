-- 010: Caretaker (Skötare) system
-- Adds caretakers who can be assigned to horses to boost specific stats

-- Enums
DO $$ BEGIN
    CREATE TYPE caretaker_specialty AS ENUM (
        'speed', 'endurance', 'mentality', 'start_ability',
        'sprint_strength', 'balance', 'strength'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE caretaker_personality AS ENUM (
        'meticulous', 'calm', 'energetic', 'experienced', 'strict', 'gentle'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS caretakers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    is_npc BOOLEAN NOT NULL DEFAULT true,
    skill INTEGER NOT NULL DEFAULT 50,
    primary_specialty caretaker_specialty NOT NULL,
    secondary_specialty caretaker_specialty,
    personality caretaker_personality NOT NULL,
    salary_demand BIGINT NOT NULL DEFAULT 200000,
    is_available BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS caretaker_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    caretaker_id UUID NOT NULL REFERENCES caretakers(id) ON DELETE CASCADE,
    horse_id UUID NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    stable_id UUID NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    salary_per_week BIGINT NOT NULL,
    starts_game_week INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_caretaker_active_horse
    ON caretaker_assignments(horse_id) WHERE is_active = true;

CREATE TABLE IF NOT EXISTS caretaker_scout_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    caretaker_id UUID NOT NULL REFERENCES caretakers(id) ON DELETE CASCADE,
    horse_id UUID NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    stable_id UUID NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    compatibility_score INTEGER NOT NULL,
    compatibility_label VARCHAR(20) NOT NULL,
    primary_boost INTEGER NOT NULL DEFAULT 0,
    secondary_boost INTEGER NOT NULL DEFAULT 0,
    scouted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    game_week INTEGER NOT NULL,
    UNIQUE(caretaker_id, horse_id)
);
