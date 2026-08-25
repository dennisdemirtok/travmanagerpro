-- TravManager — Migration 018: Levande marknad, fynd och AI-budgivning

ALTER TABLE auction_listings ADD COLUMN IF NOT EXISTS is_bargain BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE auction_listings ADD COLUMN IF NOT EXISTS estimated_value BIGINT;
ALTER TABLE auction_listings ADD COLUMN IF NOT EXISTS ai_max_bid BIGINT;
ALTER TABLE auction_listings ADD COLUMN IF NOT EXISTS listed_total_day INTEGER;
ALTER TABLE auction_listings ADD COLUMN IF NOT EXISTS expires_total_day INTEGER;

ALTER TABLE game_state ADD COLUMN IF NOT EXISTS last_market_refresh_day INTEGER;
