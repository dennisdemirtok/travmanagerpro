-- ============================================================
-- TravManager — Complete Database Schema
-- PostgreSQL 15+
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE horse_status AS ENUM ('ready', 'fatigued', 'injured', 'resting', 'pregnant', 'foal', 'yearling', 'retired');
CREATE TYPE horse_gender AS ENUM ('stallion', 'mare', 'gelding');
CREATE TYPE personality_type AS ENUM ('calm', 'hot', 'stubborn', 'responsive', 'brave', 'sensitive');
CREATE TYPE driving_style AS ENUM ('patient', 'offensive', 'tactical', 'hard', 'soft');
CREATE TYPE contract_type AS ENUM ('permanent', 'guest', 'apprentice');
CREATE TYPE race_start_method AS ENUM ('volt', 'auto');
CREATE TYPE race_class AS ENUM ('v75', 'gold', 'silver', 'bronze', 'everyday', 'youth', 'mare_race', 'amateur', 'qualifier');
CREATE TYPE surface_type AS ENUM ('dirt', 'synthetic', 'winter');
CREATE TYPE shoe_type AS ENUM ('barefoot', 'light_aluminum', 'normal_steel', 'heavy_steel', 'studs', 'grip', 'balance');
CREATE TYPE tactic_positioning AS ENUM ('lead', 'second', 'outside', 'trailing', 'back');
CREATE TYPE tactic_tempo AS ENUM ('offensive', 'balanced', 'cautious');
CREATE TYPE tactic_sprint AS ENUM ('early_600m', 'normal_400m', 'late_250m');
CREATE TYPE tactic_gallop_safety AS ENUM ('safe', 'normal', 'risky');
CREATE TYPE tactic_curve AS ENUM ('inner', 'middle', 'outer');
CREATE TYPE tactic_whip AS ENUM ('aggressive', 'normal', 'gentle');
CREATE TYPE feed_type AS ENUM ('hay_standard', 'hay_premium', 'hay_elite', 'oats', 'concentrate_standard', 'concentrate_premium', 'carrots', 'apples', 'electrolytes', 'joint_supplement', 'biotin', 'mineral_mix', 'brewers_grain');
CREATE TYPE training_program AS ENUM ('interval', 'long_distance', 'start_training', 'sprint_training', 'mental_training', 'strength_training', 'balance_training', 'swim_training', 'track_training', 'rest');
CREATE TYPE training_intensity AS ENUM ('light', 'normal', 'hard', 'maximum');
CREATE TYPE press_tone AS ENUM ('humble', 'confident', 'provocative');
CREATE TYPE facility_type AS ENUM ('stable_box', 'training_track', 'start_machine', 'swim_pool', 'vet_clinic', 'smithy', 'horse_transport', 'breeding_facility', 'fan_shop', 'walker');
CREATE TYPE staff_role AS ENUM ('trainer', 'veterinarian', 'farrier', 'stable_hand');
CREATE TYPE event_type AS ENUM ('injury', 'transfer', 'race', 'sponsor', 'achievement', 'stable_maintenance', 'staff', 'breeding', 'weather', 'system');
CREATE TYPE auction_status AS ENUM ('active', 'sold', 'expired', 'cancelled');
CREATE TYPE season_period AS ENUM ('pre_season', 'regular', 'qualifiers', 'finals', 'off_season');
CREATE TYPE weather_type AS ENUM ('clear', 'cloudy', 'rain', 'heavy_rain', 'snow', 'cold', 'hot', 'windy');

-- ============================================================
-- CORE: USERS & STABLES
-- ============================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    login_streak INT NOT NULL DEFAULT 0,
    is_supporter BOOLEAN NOT NULL DEFAULT FALSE,
    supporter_tier INT NOT NULL DEFAULT 0,
    supporter_expires_at TIMESTAMPTZ,
    is_npc BOOLEAN NOT NULL DEFAULT FALSE,
    locale VARCHAR(10) NOT NULL DEFAULT 'sv',
    timezone VARCHAR(50) NOT NULL DEFAULT 'Europe/Stockholm'
);

CREATE TABLE stables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reputation INT NOT NULL DEFAULT 10,           -- 0-100, affects sponsors/drivers
    fan_count INT NOT NULL DEFAULT 100,
    balance BIGINT NOT NULL DEFAULT 200000,       -- Starting money in öre (200 000 kr)
    total_earnings BIGINT NOT NULL DEFAULT 0,
    division_id UUID,                              -- Current division
    division_rank INT,
    season_points INT NOT NULL DEFAULT 0,
    is_npc BOOLEAN NOT NULL DEFAULT FALSE,
    npc_difficulty INT NOT NULL DEFAULT 50,        -- For NPC stables: 1-100
    UNIQUE(user_id)
);

CREATE INDEX idx_stables_division ON stables(division_id);
CREATE INDEX idx_stables_npc ON stables(is_npc);

-- ============================================================
-- HORSES
-- ============================================================

CREATE TABLE bloodlines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    origin_country VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE horses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    gender horse_gender NOT NULL,
    birth_game_week INT NOT NULL,                  -- Game week born
    age_game_weeks INT NOT NULL DEFAULT 0,         -- Current age in game weeks
    status horse_status NOT NULL DEFAULT 'ready',
    is_npc BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Core stats (1-100, trainable)
    speed INT NOT NULL DEFAULT 40 CHECK (speed BETWEEN 1 AND 100),
    endurance INT NOT NULL DEFAULT 40 CHECK (endurance BETWEEN 1 AND 100),
    mentality INT NOT NULL DEFAULT 40 CHECK (mentality BETWEEN 1 AND 100),
    start_ability INT NOT NULL DEFAULT 40 CHECK (start_ability BETWEEN 1 AND 100),
    sprint_strength INT NOT NULL DEFAULT 40 CHECK (sprint_strength BETWEEN 1 AND 100),
    balance INT NOT NULL DEFAULT 40 CHECK (balance BETWEEN 1 AND 100),
    strength INT NOT NULL DEFAULT 40 CHECK (strength BETWEEN 1 AND 100),
    
    -- Genetic potential (max ceiling per stat)
    potential_speed INT NOT NULL DEFAULT 70 CHECK (potential_speed BETWEEN 1 AND 100),
    potential_endurance INT NOT NULL DEFAULT 70,
    potential_mentality INT NOT NULL DEFAULT 70,
    potential_start INT NOT NULL DEFAULT 70,
    potential_sprint INT NOT NULL DEFAULT 70,
    potential_balance INT NOT NULL DEFAULT 70,
    potential_strength INT NOT NULL DEFAULT 70,
    
    -- Physical status (dynamic)
    condition INT NOT NULL DEFAULT 80 CHECK (condition BETWEEN 0 AND 100),
    energy INT NOT NULL DEFAULT 100 CHECK (energy BETWEEN 0 AND 100),
    health INT NOT NULL DEFAULT 90 CHECK (health BETWEEN 0 AND 100),
    current_weight DECIMAL(5,1) NOT NULL DEFAULT 470.0,
    ideal_weight DECIMAL(5,1) NOT NULL DEFAULT 470.0,
    form INT NOT NULL DEFAULT 50 CHECK (form BETWEEN 0 AND 100),
    fatigue INT NOT NULL DEFAULT 0 CHECK (fatigue BETWEEN 0 AND 100),
    mood INT NOT NULL DEFAULT 70 CHECK (mood BETWEEN 0 AND 100),
    
    -- Hidden/genetic traits
    gallop_tendency INT NOT NULL DEFAULT 15 CHECK (gallop_tendency BETWEEN 0 AND 50),
    track_preference VARCHAR(10) DEFAULT NULL,      -- 'left' or 'right' or NULL
    surface_preference surface_type DEFAULT NULL,
    weather_sensitivity INT NOT NULL DEFAULT 50,     -- 0=not affected, 100=very affected
    distance_optimum INT NOT NULL DEFAULT 2140,      -- Optimal race distance in meters
    maturation_speed INT NOT NULL DEFAULT 50,        -- 0=late bloomer, 100=early
    racing_instinct INT NOT NULL DEFAULT 50,         -- Bonus in tight finishes
    transport_tolerance INT NOT NULL DEFAULT 70,
    
    -- Personality
    personality_primary personality_type NOT NULL DEFAULT 'calm',
    personality_secondary personality_type NOT NULL DEFAULT 'responsive',
    personality_revealed BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Pedigree
    sire_id UUID REFERENCES horses(id) ON DELETE SET NULL,
    dam_id UUID REFERENCES horses(id) ON DELETE SET NULL,
    bloodline_id UUID REFERENCES bloodlines(id),
    generation INT NOT NULL DEFAULT 1,
    
    -- Training
    current_training training_program DEFAULT 'rest',
    training_intensity training_intensity DEFAULT 'normal',
    
    -- Shoeing
    current_shoe shoe_type NOT NULL DEFAULT 'normal_steel',
    shoe_durability INT NOT NULL DEFAULT 6,         -- Races left before reshoeing
    last_shoeing_week INT NOT NULL DEFAULT 0,
    
    -- Career stats
    total_starts INT NOT NULL DEFAULT 0,
    total_wins INT NOT NULL DEFAULT 0,
    total_seconds INT NOT NULL DEFAULT 0,
    total_thirds INT NOT NULL DEFAULT 0,
    total_dq INT NOT NULL DEFAULT 0,
    total_earnings BIGINT NOT NULL DEFAULT 0,
    best_km_time DECIMAL(5,1) DEFAULT NULL,         -- Best km time in seconds (e.g., 72.4)
    best_km_time_display VARCHAR(10) DEFAULT NULL,   -- e.g., '1.12,4'
    
    -- Injury
    injury_type VARCHAR(100) DEFAULT NULL,
    injury_recovery_weeks INT DEFAULT 0,
    
    -- Breeding
    is_breeding_available BOOLEAN NOT NULL DEFAULT FALSE,
    stud_fee BIGINT DEFAULT NULL,                   -- In öre, for stallions
    pregnancy_week INT DEFAULT NULL,                 -- Current pregnancy week (NULL if not pregnant)
    expected_foal_week INT DEFAULT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_horses_stable ON horses(stable_id);
CREATE INDEX idx_horses_status ON horses(status);
CREATE INDEX idx_horses_sire ON horses(sire_id);
CREATE INDEX idx_horses_dam ON horses(dam_id);
CREATE INDEX idx_horses_bloodline ON horses(bloodline_id);
CREATE INDEX idx_horses_npc ON horses(is_npc);
CREATE INDEX idx_horses_breeding ON horses(is_breeding_available) WHERE is_breeding_available = TRUE;

-- ============================================================
-- DRIVERS (KUSKAR)
-- ============================================================

CREATE TABLE drivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    is_npc BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Skills (1-100)
    skill INT NOT NULL DEFAULT 50,
    start_skill INT NOT NULL DEFAULT 50,
    tactical_ability INT NOT NULL DEFAULT 50,
    sprint_timing INT NOT NULL DEFAULT 50,
    gallop_handling INT NOT NULL DEFAULT 50,
    experience INT NOT NULL DEFAULT 30,
    composure INT NOT NULL DEFAULT 50,
    
    -- Personality
    driving_style driving_style NOT NULL DEFAULT 'tactical',
    
    -- Market
    base_salary BIGINT NOT NULL DEFAULT 500000,      -- Weekly salary in öre
    guest_fee BIGINT NOT NULL DEFAULT 300000,         -- Per-race guest fee in öre
    popularity INT NOT NULL DEFAULT 50,               -- Affects booking acceptance
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE driver_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    driver_id UUID NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
    contract_type contract_type NOT NULL,
    salary_per_week BIGINT NOT NULL,                 -- In öre
    guest_fee_per_race BIGINT DEFAULT NULL,          -- For guest contracts
    starts_game_week INT NOT NULL,
    ends_game_week INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_driver_contracts_stable ON driver_contracts(stable_id) WHERE is_active = TRUE;
CREATE INDEX idx_driver_contracts_driver ON driver_contracts(driver_id) WHERE is_active = TRUE;

-- Shared race history (for compatibility bonus)
CREATE TABLE driver_horse_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    driver_id UUID NOT NULL REFERENCES drivers(id),
    horse_id UUID NOT NULL REFERENCES horses(id),
    races_together INT NOT NULL DEFAULT 0,
    wins_together INT NOT NULL DEFAULT 0,
    last_race_week INT,
    UNIQUE(driver_id, horse_id)
);

-- ============================================================
-- STAFF
-- ============================================================

CREATE TABLE staff (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    role staff_role NOT NULL,
    quality INT NOT NULL DEFAULT 50 CHECK (quality BETWEEN 1 AND 100),
    salary_per_week BIGINT NOT NULL,
    contract_ends_week INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_staff_stable ON staff(stable_id) WHERE is_active = TRUE;

-- ============================================================
-- FACILITIES
-- ============================================================

CREATE TABLE facilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id) ON DELETE CASCADE,
    facility_type facility_type NOT NULL,
    level INT NOT NULL DEFAULT 1 CHECK (level BETWEEN 1 AND 5),
    build_cost BIGINT NOT NULL,
    maintenance_cost_per_week BIGINT NOT NULL DEFAULT 0,
    built_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(stable_id, facility_type)
);

CREATE INDEX idx_facilities_stable ON facilities(stable_id);

-- ============================================================
-- FEED PLANS
-- ============================================================

CREATE TABLE feed_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id UUID NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    feed_type feed_type NOT NULL,
    percentage INT NOT NULL CHECK (percentage BETWEEN 0 AND 100),
    cost_per_week BIGINT NOT NULL,                   -- In öre
    UNIQUE(horse_id, feed_type)
);

CREATE INDEX idx_feed_plans_horse ON feed_plans(horse_id);

-- ============================================================
-- DIVISIONS & SEASONS
-- ============================================================

CREATE TABLE seasons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    season_number INT NOT NULL UNIQUE,
    start_game_week INT NOT NULL,
    end_game_week INT NOT NULL,
    current_period season_period NOT NULL DEFAULT 'pre_season',
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE divisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level INT NOT NULL CHECK (level BETWEEN 1 AND 6),  -- 1=Elite, 6=Lowest
    name VARCHAR(100) NOT NULL,
    group_number INT NOT NULL DEFAULT 1,                -- Multiple groups per level
    season_id UUID NOT NULL REFERENCES seasons(id),
    max_stables INT NOT NULL DEFAULT 12,
    UNIQUE(level, group_number, season_id)
);

CREATE INDEX idx_divisions_season ON divisions(season_id);
CREATE INDEX idx_divisions_level ON divisions(level);

CREATE TABLE division_standings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    division_id UUID NOT NULL REFERENCES divisions(id),
    stable_id UUID NOT NULL REFERENCES stables(id),
    points INT NOT NULL DEFAULT 0,
    races_run INT NOT NULL DEFAULT 0,
    wins INT NOT NULL DEFAULT 0,
    prize_money_earned BIGINT NOT NULL DEFAULT 0,
    rank INT,
    UNIQUE(division_id, stable_id)
);

-- ============================================================
-- RACES
-- ============================================================

CREATE TABLE race_tracks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,                      -- e.g., 'Solvalla', 'Åby', 'Bergsåker'
    city VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'Sweden',
    surface surface_type NOT NULL DEFAULT 'dirt',
    track_direction VARCHAR(10) NOT NULL DEFAULT 'left', -- 'left' or 'right'
    available_distances INT[] NOT NULL DEFAULT '{1640,2140,2640}',
    has_auto_start BOOLEAN NOT NULL DEFAULT TRUE,
    prestige INT NOT NULL DEFAULT 50                  -- 1-100, affects prize money
);

CREATE TABLE race_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scheduled_at TIMESTAMPTZ NOT NULL,
    track_id UUID NOT NULL REFERENCES race_tracks(id),
    session_name VARCHAR(200),                        -- e.g., 'V75 Lördag', 'Kvällslopp'
    game_week INT NOT NULL,
    weather weather_type NOT NULL DEFAULT 'clear',
    temperature INT NOT NULL DEFAULT 12,              -- Celsius
    wind_speed INT NOT NULL DEFAULT 5,                -- m/s
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    simulated_at TIMESTAMPTZ
);

CREATE INDEX idx_race_sessions_scheduled ON race_sessions(scheduled_at);
CREATE INDEX idx_race_sessions_week ON race_sessions(game_week);

CREATE TABLE races (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES race_sessions(id),
    race_number INT NOT NULL,                         -- Race # within session
    race_name VARCHAR(200) NOT NULL,
    race_class race_class NOT NULL,
    division_level INT,                               -- NULL for open races
    distance INT NOT NULL,                            -- In meters (1640, 2140, etc.)
    start_method race_start_method NOT NULL,
    surface surface_type NOT NULL DEFAULT 'dirt',
    prize_pool BIGINT NOT NULL,                       -- Total prize in öre
    entry_fee BIGINT NOT NULL DEFAULT 100000,         -- In öre
    min_entries INT NOT NULL DEFAULT 6,
    max_entries INT NOT NULL DEFAULT 12,
    handicap_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Results
    is_finished BOOLEAN NOT NULL DEFAULT FALSE,
    seed BIGINT,                                      -- Simulation seed
    simulation_data JSONB,                            -- Full snapshot data for replay
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_races_session ON races(session_id);
CREATE INDEX idx_races_class ON races(race_class);
CREATE INDEX idx_races_finished ON races(is_finished);

-- ============================================================
-- RACE ENTRIES & TACTICS
-- ============================================================

CREATE TABLE race_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    race_id UUID NOT NULL REFERENCES races(id) ON DELETE CASCADE,
    horse_id UUID NOT NULL REFERENCES horses(id),
    stable_id UUID NOT NULL REFERENCES stables(id),
    driver_id UUID NOT NULL REFERENCES drivers(id),
    
    -- Tactics (chosen by player before race)
    positioning tactic_positioning NOT NULL DEFAULT 'second',
    tempo tactic_tempo NOT NULL DEFAULT 'balanced',
    sprint_order tactic_sprint NOT NULL DEFAULT 'normal_400m',
    gallop_safety tactic_gallop_safety NOT NULL DEFAULT 'normal',
    curve_strategy tactic_curve NOT NULL DEFAULT 'middle',
    whip_usage tactic_whip NOT NULL DEFAULT 'normal',
    
    -- Equipment
    shoe shoe_type NOT NULL DEFAULT 'normal_steel',
    
    -- Post position (assigned after entry closes)
    post_position INT,
    handicap_meters INT NOT NULL DEFAULT 0,           -- 0, 20, or 40
    
    -- Results (filled after simulation)
    finish_position INT,
    is_disqualified BOOLEAN NOT NULL DEFAULT FALSE,
    disqualification_reason VARCHAR(200),
    finish_time_seconds DECIMAL(6,1),                 -- Total time in seconds
    km_time_seconds DECIMAL(5,1),                     -- Km time in seconds
    km_time_display VARCHAR(10),                      -- e.g., '1.12,4'
    prize_money BIGINT DEFAULT 0,
    
    -- Detailed stats (from simulation)
    energy_at_finish INT,
    top_speed DECIMAL(4,2),
    gallop_incidents INT NOT NULL DEFAULT 0,
    driver_rating INT,                                -- 1-10
    compatibility_score INT,                          -- 0-100
    sector_times JSONB,                               -- Array of sector time objects
    
    -- Entry meta
    entry_fee_paid BIGINT NOT NULL DEFAULT 0,
    is_scratched BOOLEAN NOT NULL DEFAULT FALSE,
    scratch_reason VARCHAR(200),
    entered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(race_id, horse_id),
    UNIQUE(race_id, post_position)
);

CREATE INDEX idx_race_entries_race ON race_entries(race_id);
CREATE INDEX idx_race_entries_horse ON race_entries(horse_id);
CREATE INDEX idx_race_entries_stable ON race_entries(stable_id);
CREATE INDEX idx_race_entries_driver ON race_entries(driver_id);

-- ============================================================
-- RACE RESULTS (denormalized for fast queries)
-- ============================================================

CREATE TABLE race_results_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    race_id UUID NOT NULL REFERENCES races(id),
    horse_id UUID NOT NULL REFERENCES horses(id),
    stable_id UUID NOT NULL REFERENCES stables(id),
    driver_id UUID NOT NULL REFERENCES drivers(id),
    
    finish_position INT NOT NULL,
    km_time_display VARCHAR(10),
    km_time_seconds DECIMAL(5,1),
    prize_money BIGINT NOT NULL DEFAULT 0,
    distance INT NOT NULL,
    start_method race_start_method NOT NULL,
    race_class race_class NOT NULL,
    race_date TIMESTAMPTZ NOT NULL,
    game_week INT NOT NULL,
    
    UNIQUE(race_id, horse_id)
);

CREATE INDEX idx_results_horse ON race_results_summary(horse_id);
CREATE INDEX idx_results_stable ON race_results_summary(stable_id);
CREATE INDEX idx_results_driver ON race_results_summary(driver_id);
CREATE INDEX idx_results_week ON race_results_summary(game_week);

-- ============================================================
-- TRANSFER MARKET
-- ============================================================

CREATE TABLE auctions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id UUID NOT NULL REFERENCES horses(id),
    seller_stable_id UUID NOT NULL REFERENCES stables(id),
    starting_price BIGINT NOT NULL,                  -- In öre
    current_bid BIGINT,
    current_bidder_id UUID REFERENCES stables(id),
    bid_count INT NOT NULL DEFAULT 0,
    status auction_status NOT NULL DEFAULT 'active',
    starts_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ends_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_auctions_status ON auctions(status) WHERE status = 'active';
CREATE INDEX idx_auctions_ends ON auctions(ends_at) WHERE status = 'active';
CREATE INDEX idx_auctions_horse ON auctions(horse_id);

CREATE TABLE auction_bids (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auction_id UUID NOT NULL REFERENCES auctions(id),
    bidder_stable_id UUID NOT NULL REFERENCES stables(id),
    bid_amount BIGINT NOT NULL,
    bid_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bids_auction ON auction_bids(auction_id);

-- Scouting reports (paid intel on horses)
CREATE TABLE scout_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id),
    horse_id UUID NOT NULL REFERENCES horses(id),
    scout_level INT NOT NULL CHECK (scout_level BETWEEN 1 AND 4),
    cost BIGINT NOT NULL,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    is_complete BOOLEAN NOT NULL DEFAULT FALSE,
    report_data JSONB,                                -- Revealed info
    UNIQUE(stable_id, horse_id, scout_level)
);

CREATE INDEX idx_scouts_stable ON scout_reports(stable_id);

-- ============================================================
-- BREEDING
-- ============================================================

CREATE TABLE stallion_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id UUID NOT NULL REFERENCES horses(id),
    stable_id UUID NOT NULL REFERENCES stables(id),
    stud_fee BIGINT NOT NULL,                        -- In öre
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    season_id UUID REFERENCES seasons(id),
    total_offspring INT NOT NULL DEFAULT 0,
    offspring_winners INT NOT NULL DEFAULT 0,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(horse_id, season_id)
);

CREATE INDEX idx_stallion_registry_available ON stallion_registry(is_available) WHERE is_available = TRUE;

CREATE TABLE breeding_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mare_id UUID NOT NULL REFERENCES horses(id),
    stallion_id UUID NOT NULL REFERENCES horses(id),
    mare_stable_id UUID NOT NULL REFERENCES stables(id),
    stallion_stable_id UUID NOT NULL REFERENCES stables(id),
    stud_fee_paid BIGINT NOT NULL,
    vet_cost BIGINT NOT NULL DEFAULT 200000,         -- 2000 kr in öre
    breeding_week INT NOT NULL,
    is_successful BOOLEAN,                           -- NULL until result known
    foal_id UUID REFERENCES horses(id),              -- Set when foal is born
    expected_birth_week INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE nick_effects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bloodline_a_id UUID NOT NULL REFERENCES bloodlines(id),
    bloodline_b_id UUID NOT NULL REFERENCES bloodlines(id),
    stat_name VARCHAR(50) NOT NULL,
    nick_multiplier DECIMAL(3,2) NOT NULL DEFAULT 1.00,  -- 0.85-1.20
    sample_size INT NOT NULL DEFAULT 0,
    UNIQUE(bloodline_a_id, bloodline_b_id, stat_name)
);

-- ============================================================
-- FINANCES
-- ============================================================

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id),
    amount BIGINT NOT NULL,                           -- Positive = income, negative = expense (öre)
    category VARCHAR(50) NOT NULL,                    -- 'prize_money', 'salary', 'feed', 'training', etc.
    description VARCHAR(500),
    reference_type VARCHAR(50),                       -- 'race', 'auction', 'contract', etc.
    reference_id UUID,
    game_week INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transactions_stable ON transactions(stable_id);
CREATE INDEX idx_transactions_week ON transactions(game_week);
CREATE INDEX idx_transactions_category ON transactions(stable_id, category);

CREATE TABLE sponsors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    logo_url VARCHAR(500),
    min_reputation INT NOT NULL DEFAULT 0,
    min_division INT NOT NULL DEFAULT 6
);

CREATE TABLE sponsor_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id),
    sponsor_id UUID NOT NULL REFERENCES sponsors(id),
    weekly_payment BIGINT NOT NULL,                   -- In öre
    win_bonus BIGINT NOT NULL DEFAULT 0,
    starts_week INT NOT NULL,
    ends_week INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- EVENTS & NEWS
-- ============================================================

CREATE TABLE stable_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id),
    event_type event_type NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    requires_action BOOLEAN NOT NULL DEFAULT FALSE,
    action_data JSONB,                                -- Data for actionable events
    game_week INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_events_stable ON stable_events(stable_id);
CREATE INDEX idx_events_unread ON stable_events(stable_id, is_read) WHERE is_read = FALSE;

CREATE TABLE press_releases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id),
    tone press_tone NOT NULL,
    content TEXT NOT NULL,
    pr_points INT NOT NULL DEFAULT 0,
    income_generated BIGINT NOT NULL DEFAULT 0,
    game_week INT NOT NULL,
    game_day INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- ACHIEVEMENTS
-- ============================================================

CREATE TABLE achievement_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    points INT NOT NULL DEFAULT 10,
    reward_amount BIGINT DEFAULT NULL,               -- Cash reward in öre
    icon VARCHAR(10) DEFAULT '⭐'
);

CREATE TABLE stable_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stable_id UUID NOT NULL REFERENCES stables(id),
    achievement_id UUID NOT NULL REFERENCES achievement_definitions(id),
    unlocked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    game_week INT NOT NULL,
    UNIQUE(stable_id, achievement_id)
);

-- ============================================================
-- V75 TIPPING (META-GAME)
-- ============================================================

CREATE TABLE v75_rounds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES race_sessions(id),
    race_ids UUID[] NOT NULL,                         -- 7 race IDs
    game_week INT NOT NULL,
    pool_amount BIGINT NOT NULL DEFAULT 0,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE v75_coupons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    round_id UUID NOT NULL REFERENCES v75_rounds(id),
    stable_id UUID NOT NULL REFERENCES stables(id),
    picks JSONB NOT NULL,                             -- { "race_1": [horse_ids], "race_2": [...], ... }
    cost BIGINT NOT NULL,                             -- Coupon cost in öre
    correct_count INT DEFAULT NULL,                   -- Filled after resolution
    winnings BIGINT DEFAULT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(round_id, stable_id)
);

-- ============================================================
-- GAME STATE
-- ============================================================

CREATE TABLE game_state (
    id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),      -- Singleton
    current_game_week INT NOT NULL DEFAULT 1,
    current_game_day INT NOT NULL DEFAULT 1,           -- 1-14 within a real week
    current_season_id UUID REFERENCES seasons(id),
    real_week_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    next_race_session_id UUID REFERENCES race_sessions(id),
    next_race_at TIMESTAMPTZ,
    
    -- NPC scaling
    total_active_players INT NOT NULL DEFAULT 0,
    npc_scaling_factor DECIMAL(3,2) NOT NULL DEFAULT 0.70  -- 0.00 - 1.00
);

-- Daily horse status tracking
CREATE TABLE daily_horse_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id UUID NOT NULL REFERENCES horses(id),
    game_week INT NOT NULL,
    game_day INT NOT NULL,
    condition INT NOT NULL,
    energy INT NOT NULL,
    health INT NOT NULL,
    fatigue INT NOT NULL,
    mood INT NOT NULL,
    weight DECIMAL(5,1) NOT NULL,
    notes TEXT,
    UNIQUE(horse_id, game_week, game_day)
);

CREATE INDEX idx_daily_log_horse ON daily_horse_log(horse_id, game_week);

-- ============================================================
-- COMPATIBILITY CACHE
-- ============================================================

CREATE TABLE compatibility_cache (
    horse_id UUID NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    driver_id UUID NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
    base_score INT NOT NULL,
    experience_bonus INT NOT NULL DEFAULT 0,
    total_score INT NOT NULL,
    last_calculated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (horse_id, driver_id)
);

-- ============================================================
-- INITIAL DATA: ACHIEVEMENT DEFINITIONS
-- ============================================================

INSERT INTO achievement_definitions (code, name, description, category, points, reward_amount, icon) VALUES
('first_win', 'Första vinsten', 'Vinn ditt första lopp', 'racing', 10, 500000, '🏆'),
('fifth_win', 'Femte vinsten', 'Vinn 5 lopp totalt', 'racing', 20, 1000000, '🏆'),
('tenth_win', 'Tionde vinsten', 'Vinn 10 lopp totalt', 'racing', 30, 2000000, '🏆'),
('homebred_winner', 'Uppfödarmästare', 'Vinn med en egenuppfödd häst', 'breeding', 50, 5000000, '🧬'),
('stable_economy', 'Ekonomisk stabilitet', 'Ha positiv budget 20 spelveckor i rad', 'management', 25, 2000000, '💰'),
('driver_collector', 'Kuskvärvare', 'Anlita 10 olika gästkuskar', 'management', 15, 500000, '👤'),
('gallop_free_season', 'Galoppfri säsong', 'Kör en hel säsong utan galopperingar', 'racing', 40, 3000000, '✨'),
('v75_winner', 'V75-kung', 'Vinn V75-tippningen', 'social', 30, 5000000, '🎰'),
('bloodline_architect', 'Blodlinjearkitekt', 'Föd upp 3 generationer av vinnare', 'breeding', 100, 10000000, '🧬'),
('press_master', 'Stallets ansikte', 'Skriv 50 pressmeddelanden', 'social', 15, 500000, '📰'),
('all_distances', 'Alla distanser', 'Vinn på 1640m, 2140m och 2640m', 'racing', 25, 1500000, '📏'),
('veteran_stable', 'Veteranstall', 'Spela aktivt i 6 månader', 'milestone', 50, 5000000, '🏠'),
('shoe_experimenter', 'Skoexpert', 'Använd alla 7 skotyper i vinst-lopp', 'equipment', 20, 1000000, '👟'),
('perfect_compatibility', 'Perfekt match', 'Uppnå 90+ kompatibilitet mellan kusk och häst', 'management', 15, 500000, '❤️'),
('division_champion', 'Divisionsmästare', 'Vinn din division', 'racing', 60, 5000000, '🥇'),
('elite_promotion', 'Eliten', 'Nå Division 1', 'racing', 100, 10000000, '⭐');

-- ============================================================
-- INITIAL DATA: RACE TRACKS
-- ============================================================

INSERT INTO race_tracks (name, city, country, surface, track_direction, available_distances, has_auto_start, prestige) VALUES
('Solvalla', 'Stockholm', 'Sweden', 'dirt', 'left', '{1640,2140,2640,3140}', true, 95),
('Åby', 'Göteborg', 'Sweden', 'dirt', 'left', '{1640,2140,2640}', true, 85),
('Jägersro', 'Malmö', 'Sweden', 'dirt', 'left', '{1609,1640,2140,2640}', true, 80),
('Bergsåker', 'Sundsvall', 'Sweden', 'dirt', 'left', '{1640,2140,2640}', true, 60),
('Romme', 'Borlänge', 'Sweden', 'dirt', 'left', '{1640,2140,2640}', true, 55),
('Axevalla', 'Skara', 'Sweden', 'dirt', 'left', '{1640,2140,2640}', true, 50),
('Hagmyren', 'Hudiksvall', 'Sweden', 'dirt', 'left', '{1640,2140}', true, 40),
('Mantorp', 'Mantorp', 'Sweden', 'dirt', 'left', '{1640,2140,2640}', true, 45);

-- ============================================================
-- INITIAL DATA: BLOODLINES
-- ============================================================

INSERT INTO bloodlines (name, description, origin_country) VALUES
('Expressenlinjen', 'Snabb och explosiv linje med stark spurtförmåga', 'Sweden'),
('Järnmannenlinjen', 'Extremt uthållig linje som excellerar på långa distanser', 'Sweden'),
('Blixtenlinjen', 'Tidig mognad och hög topphastighet', 'Sweden'),
('Stormlinjen', 'Modig och stark, klarar tuffa lopp', 'Sweden'),
('Solstrålelinjen', 'Balanserad med bra mentalitet', 'Sweden'),
('Nordstjärnelinjen', 'Sen mognad men extremt hög potential', 'Sweden'),
('Guldlinjen', 'Allround med konsekvent prestation', 'Sweden'),
('Vikingalinjen', 'Stark fysik, excellerar i tredjespår', 'Sweden'),
('Kungalinjen', 'Prestigefylld linje med många elithästar', 'France'),
('Atlantlinjen', 'Importerad linje med snabb acceleration', 'USA');

-- ============================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER horses_updated_at
    BEFORE UPDATE ON horses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-update stable balance on transaction
CREATE OR REPLACE FUNCTION update_stable_balance()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE stables 
    SET balance = balance + NEW.amount
    WHERE id = NEW.stable_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER transaction_balance_update
    AFTER INSERT ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_stable_balance();

-- ============================================================
-- VIEWS
-- ============================================================

-- Horse overview with career stats
CREATE VIEW v_horse_overview AS
SELECT 
    h.*,
    s.name AS stable_name,
    s.user_id,
    b.name AS bloodline_name,
    CASE 
        WHEN h.age_game_weeks < 16 THEN 'foal'
        WHEN h.age_game_weeks < 32 THEN 'yearling'
        WHEN h.age_game_weeks < 48 THEN 'young'
        WHEN h.age_game_weeks < 128 THEN 'prime'
        WHEN h.age_game_weeks < 160 THEN 'veteran'
        ELSE 'retired'
    END AS life_stage,
    h.age_game_weeks / 16 AS age_years
FROM horses h
JOIN stables s ON h.stable_id = s.id
LEFT JOIN bloodlines b ON h.bloodline_id = b.id;

-- Upcoming races with entry counts
CREATE VIEW v_upcoming_races AS
SELECT 
    r.*,
    rs.scheduled_at,
    rs.weather,
    rs.temperature,
    rt.name AS track_name,
    rt.city AS track_city,
    COUNT(re.id) AS current_entries,
    rs.is_simulated
FROM races r
JOIN race_sessions rs ON r.session_id = rs.id
JOIN race_tracks rt ON rs.track_id = rt.id
LEFT JOIN race_entries re ON r.id = re.race_id AND re.is_scratched = FALSE
WHERE r.is_finished = FALSE
GROUP BY r.id, rs.scheduled_at, rs.weather, rs.temperature, rt.name, rt.city, rs.is_simulated
ORDER BY rs.scheduled_at;

-- Stable financial summary
CREATE VIEW v_stable_finances AS
SELECT 
    t.stable_id,
    t.game_week,
    SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END) AS total_income,
    SUM(CASE WHEN t.amount < 0 THEN t.amount ELSE 0 END) AS total_expenses,
    SUM(t.amount) AS net,
    COUNT(*) AS transaction_count
FROM transactions t
GROUP BY t.stable_id, t.game_week;
