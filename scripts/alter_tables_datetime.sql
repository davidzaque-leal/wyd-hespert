-- Garante que snapshot_date e recorded_at tenham segundos zerados
-- ArenaRanking
ALTER TABLE arena_rankings
    ADD CONSTRAINT arena_rankings_snapshot_date_minute CHECK (EXTRACT(SECOND FROM snapshot_date) = 0);

-- LevelRanking
ALTER TABLE level_rankings
    ADD CONSTRAINT level_rankings_snapshot_date_minute CHECK (EXTRACT(SECOND FROM snapshot_date) = 0);

-- ArenaRankingHistory
ALTER TABLE arena_ranking_history
    ADD CONSTRAINT arena_ranking_history_recorded_at_minute CHECK (EXTRACT(SECOND FROM recorded_at) = 0);

-- LevelRankingHistory
ALTER TABLE level_ranking_history
    ADD CONSTRAINT level_ranking_history_recorded_at_minute CHECK (EXTRACT(SECOND FROM recorded_at) = 0);

-- Player (created_at, updated_at)
ALTER TABLE players
    ADD CONSTRAINT players_created_at_minute CHECK (EXTRACT(SECOND FROM created_at) = 0),
    ADD CONSTRAINT players_updated_at_minute CHECK (EXTRACT(SECOND FROM updated_at) = 0);

-- User (created_at, updated_at)
ALTER TABLE users
    ADD CONSTRAINT users_created_at_minute CHECK (EXTRACT(SECOND FROM created_at) = 0),
    ADD CONSTRAINT users_updated_at_minute CHECK (EXTRACT(SECOND FROM updated_at) = 0);

-- Para garantir o formato na exibição, ajuste na aplicação e nos templates.
