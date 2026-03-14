-- Hidden properties table
CREATE TABLE IF NOT EXISTS horse_hidden_properties (
    horse_id UUID PRIMARY KEY REFERENCES horses(id) ON DELETE CASCADE,
    barefoot_affinity INT DEFAULT 0,
    american_sulky_affinity INT DEFAULT 0,
    racing_sulky_affinity INT DEFAULT 0,
    tight_curve_ability INT DEFAULT 0,
    long_homestretch_affinity INT DEFAULT 0,
    heavy_track_affinity INT DEFAULT 0,
    confidence_sensitivity NUMERIC(3,2) DEFAULT 1.0,
    crowd_response INT DEFAULT 0,
    recovery_rate NUMERIC(3,2) DEFAULT 1.0,
    start_frequency_preference VARCHAR(20) DEFAULT 'normal',
    peak_age INT DEFAULT 6,
    late_bloomer BOOLEAN DEFAULT FALSE,
    natural_speed_ceiling INT DEFAULT 0,
    hidden_sprint_gear BOOLEAN DEFAULT FALSE,
    wind_sensitivity NUMERIC(3,2) DEFAULT 1.0,
    temperature_optimum INT DEFAULT 12,
    temperature_tolerance INT DEFAULT 15
);

-- Add confidence + start frequency tracking to horses
ALTER TABLE horses ADD COLUMN IF NOT EXISTS confidence INT DEFAULT 50;
ALTER TABLE horses ADD COLUMN IF NOT EXISTS days_since_last_race INT DEFAULT 0;
ALTER TABLE horses ADD COLUMN IF NOT EXISTS races_last_30_days INT DEFAULT 0;

-- Add observations/diary table
CREATE TABLE IF NOT EXISTS horse_observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id UUID NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    stable_id UUID NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    game_week INT NOT NULL,
    observation_type VARCHAR(50) NOT NULL,
    text TEXT NOT NULL,
    confidence_level NUMERIC(3,2) DEFAULT 0.5,
    race_id UUID REFERENCES races(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_observations_horse ON horse_observations(horse_id);
