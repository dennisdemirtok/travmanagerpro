-- TravManager — Migration 006: Full Game Overhaul
-- Economy rebalancing, all real tracks, travel, driver commission,
-- breeding, pedigree, special traits, professional training, race classes

-- ============================================================
-- 1. Track enhancements
-- ============================================================
ALTER TABLE race_tracks ADD COLUMN IF NOT EXISTS region VARCHAR(20);
ALTER TABLE race_tracks ADD COLUMN IF NOT EXISTS stretch_length INT DEFAULT 200;
ALTER TABLE race_tracks ADD COLUMN IF NOT EXISTS notes TEXT;

-- ============================================================
-- 2. Stable home track
-- ============================================================
ALTER TABLE stables ADD COLUMN IF NOT EXISTS home_track_id UUID REFERENCES race_tracks(id);

-- ============================================================
-- 3. Driver commission
-- ============================================================
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS commission_rate DECIMAL(4,3) DEFAULT 0.10;

-- ============================================================
-- 4. Race session start times
-- ============================================================
ALTER TABLE race_sessions ADD COLUMN IF NOT EXISTS start_time VARCHAR(5);

-- ============================================================
-- 5. Horse special traits + age
-- ============================================================
ALTER TABLE horses ADD COLUMN IF NOT EXISTS special_traits JSONB DEFAULT '[]';
ALTER TABLE horses ADD COLUMN IF NOT EXISTS traits_revealed BOOLEAN DEFAULT false;
ALTER TABLE horses ADD COLUMN IF NOT EXISTS age_years INT DEFAULT 3;

-- Add new personality types to enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'training_eager'
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'personality_type')) THEN
        ALTER TYPE personality_type ADD VALUE IF NOT EXISTS 'training_eager';
    END IF;
    ALTER TYPE personality_type ADD VALUE IF NOT EXISTS 'winner';
    ALTER TYPE personality_type ADD VALUE IF NOT EXISTS 'strong_willed';
    ALTER TYPE personality_type ADD VALUE IF NOT EXISTS 'moody';
    ALTER TYPE personality_type ADD VALUE IF NOT EXISTS 'food_lover';
    ALTER TYPE personality_type ADD VALUE IF NOT EXISTS 'lazy';
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Add new race classes
DO $$
BEGIN
    ALTER TYPE race_class ADD VALUE IF NOT EXISTS 'elite';
    ALTER TYPE race_class ADD VALUE IF NOT EXISTS 'age_2';
    ALTER TYPE race_class ADD VALUE IF NOT EXISTS 'age_3';
    ALTER TYPE race_class ADD VALUE IF NOT EXISTS 'age_4';
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Add training status to horse_status
DO $$
BEGIN
    ALTER TYPE horse_status ADD VALUE IF NOT EXISTS 'training';
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- 6. Stallion registry (for breeding) — DROP old incompatible table first
-- ============================================================
DROP TABLE IF EXISTS breeding_records CASCADE;
DROP TABLE IF EXISTS stallion_registry CASCADE;
CREATE TABLE stallion_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    origin_country VARCHAR(10),
    stud_fee BIGINT NOT NULL,
    speed_bonus INT DEFAULT 0,
    endurance_bonus INT DEFAULT 0,
    mentality_bonus INT DEFAULT 0,
    sprint_bonus INT DEFAULT 0,
    balance_bonus INT DEFAULT 0,
    strength_bonus INT DEFAULT 0,
    start_bonus INT DEFAULT 0,
    prestige INT DEFAULT 50,
    description TEXT,
    available BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 7. Pedigree table (3 generations)
-- ============================================================
CREATE TABLE IF NOT EXISTS horse_pedigree (
    horse_id UUID PRIMARY KEY REFERENCES horses(id) ON DELETE CASCADE,
    sire_name VARCHAR(100),
    sire_origin VARCHAR(10),
    dam_name VARCHAR(100),
    dam_origin VARCHAR(10),
    sire_sire_name VARCHAR(100),
    sire_dam_name VARCHAR(100),
    dam_sire_name VARCHAR(100),
    dam_dam_name VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 8. Professional training log
-- ============================================================
CREATE TABLE IF NOT EXISTS professional_training (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id UUID NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    stable_id UUID NOT NULL REFERENCES stables(id),
    target_stat VARCHAR(30) NOT NULL,
    trainer_level VARCHAR(20) DEFAULT 'standard',
    cost_per_week BIGINT NOT NULL,
    start_week INT NOT NULL,
    end_week INT NOT NULL,
    completed BOOLEAN DEFAULT false,
    stat_gain INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 9. Update existing driver commission rates
-- ============================================================
UPDATE drivers SET commission_rate = 0.22 WHERE is_real_driver = true AND skill >= 90;
UPDATE drivers SET commission_rate = 0.18 WHERE is_real_driver = true AND skill >= 80 AND skill < 90;
UPDATE drivers SET commission_rate = 0.15 WHERE is_real_driver = true AND skill >= 70 AND skill < 80;
UPDATE drivers SET commission_rate = 0.12 WHERE is_real_driver = true AND skill >= 60 AND skill < 70;
UPDATE drivers SET commission_rate = 0.08 WHERE is_real_driver = true AND skill < 60;
UPDATE drivers SET commission_rate = 0.10 WHERE is_npc = true;

-- ============================================================
-- 10. Seed stallion registry
-- ============================================================
INSERT INTO stallion_registry (name, origin_country, stud_fee, speed_bonus, endurance_bonus, mentality_bonus, sprint_bonus, balance_bonus, strength_bonus, start_bonus, prestige, description)
VALUES
    ('Readly Express', 'SE', 8000000, 18, 14, 12, 16, 10, 12, 14, 95, 'Extrem fart och sprintkraft. En av de populäraste hingstarna.'),
    ('Maharajah', 'SE', 7000000, 16, 16, 14, 14, 12, 14, 12, 92, 'Balanserad med bra uthållighet. En gigant i svensk avel.'),
    ('Walner', 'US', 10000000, 20, 12, 10, 18, 8, 10, 16, 98, 'Exceptionell fart men kan ge ojämna avkommor.'),
    ('Face Time Bourbon', 'FR', 9000000, 15, 18, 14, 12, 16, 16, 10, 94, 'Otrolig uthållighet och styrka för stayerlopp.'),
    ('Ecurie D.', 'US', 6000000, 14, 14, 12, 14, 12, 12, 14, 80, 'Bra allround med jämna avkommor.'),
    ('Propulsion', 'SE', 7500000, 16, 18, 16, 10, 14, 16, 8, 90, 'Uthållighetsbest. Avkommor som aldrig ger upp.'),
    ('Nuncio', 'SE', 5000000, 14, 10, 12, 18, 10, 10, 14, 78, 'Sprintspecialist. Snabba avkommor med bra spurt.'),
    ('Hard Livin', 'US', 5500000, 14, 12, 14, 12, 12, 14, 12, 75, 'Pålitlig med bra genetisk bredd.'),
    ('Bold Eagle', 'FR', 8500000, 17, 15, 16, 14, 14, 14, 12, 88, 'Stark mentalitet och bra helhet.'),
    ('Muscle Hill', 'US', 9500000, 18, 14, 12, 16, 10, 16, 14, 96, 'Legendar i USA. Extrem fart och styrka.'),
    ('Viking Kronos', 'IT', 3500000, 12, 12, 10, 10, 10, 12, 10, 65, 'Bevisad avelsförmåga. Bra för nybörjare.'),
    ('Cantab Hall', 'US', 4000000, 12, 10, 14, 12, 14, 10, 12, 70, 'Stabila men sällan exceptionella avkommor.'),
    ('Severino', 'SE', 2500000, 10, 10, 10, 10, 10, 10, 10, 50, 'Budget-alternativ. Jämna lägre bonusar.'),
    ('Trixton', 'US', 3000000, 12, 8, 10, 14, 8, 8, 12, 60, 'Kan ge riktigt snabba eller svaga avkommor.')
ON CONFLICT DO NOTHING;
