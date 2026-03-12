-- TravManager — Migration 007: Stable Capacity (Box System)
-- Stables start with 3 boxes, upgradeable to 10.

ALTER TABLE stables ADD COLUMN IF NOT EXISTS max_horses INT DEFAULT 3;
ALTER TABLE stables ADD COLUMN IF NOT EXISTS box_upgrade_level INT DEFAULT 0;

-- Set NPC stables to higher capacity (they have many horses)
UPDATE stables SET max_horses = 15, box_upgrade_level = 7 WHERE is_npc = true;
