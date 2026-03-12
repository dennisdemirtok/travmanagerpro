-- TravManager — Migration 004: Horse Market & Sponsor Seeding
-- Drops old auction tables from 001 and creates new ones

-- =============================================================
-- Drop old auction tables (from 001_initial_schema)
-- =============================================================
DROP TABLE IF EXISTS auction_bids CASCADE;
DROP TABLE IF EXISTS auctions CASCADE;

-- =============================================================
-- Auction listings table for horse market
-- =============================================================
CREATE TABLE IF NOT EXISTS auction_listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    horse_id UUID NOT NULL REFERENCES horses(id) ON DELETE CASCADE,
    seller_stable_id UUID NOT NULL REFERENCES stables(id),
    starting_price BIGINT NOT NULL,
    buyout_price BIGINT,
    current_bid BIGINT DEFAULT 0,
    current_bidder_id UUID REFERENCES stables(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    listed_game_week INT NOT NULL,
    expires_game_week INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auction bid history
CREATE TABLE IF NOT EXISTS auction_bids (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID NOT NULL REFERENCES auction_listings(id) ON DELETE CASCADE,
    bidder_stable_id UUID NOT NULL REFERENCES stables(id),
    amount BIGINT NOT NULL,
    game_week INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================
-- Seed default sponsors
-- =============================================================
INSERT INTO sponsors (id, name, logo_url, min_reputation, min_division) VALUES
    (uuid_generate_v4(), 'Lokal Foderbutik',     NULL, 0,  6),
    (uuid_generate_v4(), 'Bygdens Smedja',       NULL, 5,  6),
    (uuid_generate_v4(), 'Travsport-Nytt',       NULL, 10, 6),
    (uuid_generate_v4(), 'Hästkraft Premium',    NULL, 15, 5),
    (uuid_generate_v4(), 'Nordisk Veterinär AB', NULL, 20, 5),
    (uuid_generate_v4(), 'Dalahästen Transport', NULL, 25, 5),
    (uuid_generate_v4(), 'V75-Guiden',           NULL, 30, 4),
    (uuid_generate_v4(), 'Stallbackens Hovvård', NULL, 35, 4),
    (uuid_generate_v4(), 'TravEliten',           NULL, 40, 3),
    (uuid_generate_v4(), 'SverigeTrav Fond',     NULL, 50, 2),
    (uuid_generate_v4(), 'ATG Premium Partner',  NULL, 60, 1),
    (uuid_generate_v4(), 'Kungliga Stallmästaren', NULL, 70, 1)
ON CONFLICT DO NOTHING;
