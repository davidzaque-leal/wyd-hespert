-- Adiciona as colunas level_celestial e level_sub_celestial à tabela level_rankings
ALTER TABLE level_rankings ADD COLUMN level_celestial INTEGER;
ALTER TABLE level_rankings ADD COLUMN level_sub_celestial INTEGER;

-- Adiciona as colunas ao histórico, se necessário
ALTER TABLE level_ranking_history ADD COLUMN level_celestial INTEGER;
ALTER TABLE level_ranking_history ADD COLUMN level_sub_celestial INTEGER;
