from sqlalchemy.orm import Session
"""
Serviço para manter histórico de rankings e posições
Salva snapshots periódicos dos rankings para análise de evolução
"""

from sqlalchemy.orm import Session
from app.models import LevelRankingHistory, ArenaRankingHistory
from datetime import datetime, timedelta
from app.utils.datetime_utils import get_formatted_now

def get_season():
    """
    Retorna a season atual no formato MM/YY.
    """
    now = datetime.now()
    return now.strftime('%m/%y')

def get_today():
    """
    Retorna a data de hoje (local).
    """
    return datetime.now().date()
    
def get_arena_number_by_time(now: datetime) -> int:
    minutes = now.hour * 60 + now.minute

    if 780 <= minutes <= 1139:   # 13:00–18:59
        return 1
    elif 1140 <= minutes <= 1229:  # 19:00–20:29
        return 2
    elif 1230 <= minutes <= 1379:  # 20:30–22:59
        return 3
    else:  # 23:00–12:59
        return 4

def get_latest_arena_indicators(session: Session, player_id: int, category: str):
    """
    Compara a última arena com a penúltima para exibir indicadores.
    Não depende de horário, sempre pega os dois registros mais recentes.
    Args:
        session: SQLAlchemy Session
        player_id: ID do player
        category: 'champion' ou 'aspirant'
    Returns:
        dict com indicadores de diferença entre arenas
    """
    try:
        from sqlalchemy import desc
        from app.models import ArenaRankingHistory
        # Busca os dois registros mais recentes da categoria correta
        records = session.query(ArenaRankingHistory).filter(
            ArenaRankingHistory.player_id == player_id,
            ArenaRankingHistory.category == category
        ).order_by(desc(ArenaRankingHistory.recorded_at)).limit(2).all()
        if len(records) < 2:
            return {
                'position_change': 0,
                'direction': 'neutral',
                'active': False,
                'kill_change': 0,
                'kill_arrow': '',
                'kill_active': False,
                'win_change': 0,
                'win_arrow': '',
                'win_active': False,
            }
        latest, previous = records[0], records[1]
        pos_diff = (previous.rank_position or 0) - (latest.rank_position or 0)
        kill_change = (latest.kill_value or 0) - (previous.kill_value or 0)
        win_change = (latest.win_count or 0) - (previous.win_count or 0)
        return {
            'position_change': abs(pos_diff),
            'direction': 'up' if pos_diff > 0 else ('down' if pos_diff < 0 else 'neutral'),
            'active': pos_diff != 0,
            'kill_change': kill_change,
            'kill_arrow': '↑' if kill_change > 0 else ('↓' if kill_change < 0 else ''),
            'kill_active': kill_change != 0,
            'win_change': win_change,
            'win_arrow': '↑' if win_change > 0 else ('↓' if win_change < 0 else ''),
            'win_active': win_change != 0,
        }
    except Exception as e:
        print(f"⚠ Erro ao comparar arenas mais recentes: {e}")
        return {
            'position_change': 0,
            'direction': 'neutral',
            'active': False,
            'kill_change': 0,
            'kill_arrow': '',
            'kill_active': False,
            'win_change': 0,
            'win_arrow': '',
            'win_active': False,
        }

def save_level_ranking_history(session: Session, players_data: list):
    """
    Salva snapshot do ranking de level (apenas 1 por dia)
    
    Args:
        session: SQLAlchemy Session
        players_data: Lista de dicts com dados dos players do ranking
    """
    try:
        from sqlalchemy import delete, func
        from app.utils.datetime_utils import get_brasilia_now
        today = get_brasilia_now()
        today_str = today.strftime('%Y-%m-%d')
        existing_today = session.query(LevelRankingHistory).filter(
            LevelRankingHistory.recorded_at.like(f'{today_str}%')
        ).first()
        if existing_today:
            print(f"✓ Histórico de Level Ranking já salvo hoje (pulando)")
            return True
        snapshot_date = get_formatted_now()
        season = get_season()
        added = False
        for rank_pos, player_data in enumerate(players_data, 1):
            rec_at = player_data.get("recorded_at")
            if isinstance(rec_at, datetime):
                rec_at = rec_at.strftime('%Y-%m-%d %H:%M')
            elif not rec_at:
                rec_at = snapshot_date
            history = LevelRankingHistory(
                player_id=player_data.get("id"),
                player_name=player_data.get("name") or player_data.get("charName") or "Unknown",
                rank_position=rank_pos,
                level_total=player_data.get("Soma Level", 0),
                points=player_data.get("points", 0),
                level_celestial=player_data.get("level", 0),
                level_sub_celestial=player_data.get("levelSub", 0),
                celestial_lineage_name=player_data.get("celestial_lineage", ""),
                subclass_lineage_name=player_data.get("subclass_lineage", ""),
                recorded_at=rec_at
            )
            session.add(history)
            added = True
        if added:
            session.commit()
            print(f"✓ Histórico de Level Ranking salvo ({len(players_data)} players)")
        return True
    except Exception as e:
        session.rollback()
        print(f"⚠ Erro ao salvar histórico: {e}")
        return False

from sqlalchemy.exc import IntegrityError

def save_arena_ranking_history(session: Session, players_data: list, category: str):

    try:
        from app.utils.datetime_utils import get_brasilia_now
        now = get_brasilia_now()
        arena_num = get_arena_number_by_time(now)
        snapshot_date = get_formatted_now()
        season = get_season()
        # Verifica se já existe registro hoje para a categoria e arena_number
        existing_today = session.query(ArenaRankingHistory).filter(
            ArenaRankingHistory.category == category,
            ArenaRankingHistory.arena_number == arena_num,
            ArenaRankingHistory.recorded_at.like(f'{snapshot_date[:10]}%')
        ).first()
        if existing_today:
            print(f"✓ Histórico de Arena {category} já salvo hoje para arena {arena_num} (pulando)")
            return True
        added = False
        for rank_pos, player_data in enumerate(players_data, 1):
            history = ArenaRankingHistory(
                player_id=player_data.get("id"),
                category=category,
                arena_number=arena_num,
                rank_position=rank_pos,
                total=player_data.get("total", 0),
                points=player_data.get("points", 0),
                win_count=player_data.get("winCount", 0),
                kill_value=player_data.get("killValue", 0),
                death_value=player_data.get("deathValue", 0),
                recorded_at=snapshot_date,
                season=season
            )
            session.add(history)
            added = True
        if added:
            session.commit()
            print(f"✓ Histórico de Arena {category} salvo ({len(players_data)} players)")
        return True
    except IntegrityError:
        session.rollback()
        print(f"✓ Snapshot de arena {category} já existe (ignorado)")
        return True
    except Exception as e:
        session.rollback()
        print(f"⚠ Erro ao salvar histórico de arena: {e}")
        return False

def get_player_level_history(session: Session, player_id: int, limit: int = 30):
    """
    Recupera histórico de posição de um player específico
    
    Args:
        session: SQLAlchemy Session
        player_id: ID do player
        limit: Número máximo de registros
        
    Returns:
        Lista de registros de posição do player em ordem cronológica
    """
    try:
        from sqlalchemy import desc
        
        return session.query(LevelRankingHistory).filter(
            LevelRankingHistory.player_id == player_id
        ).order_by(
            desc(LevelRankingHistory.recorded_at)
        ).limit(limit).all()
        
    except Exception as e:
        print(f"⚠ Erro ao recuperar histórico do player: {e}")
        return []

def get_level_changes(session: Session, player_name: str, current_data: dict) -> dict:
    """
    Compara dados atuais com snapshot de ontem para detectar mudanças
    
    Args:
        session: SQLAlchemy Session
        player_name: Nome do player
        current_data: Dicionário com dados atuais (level_celestial, level_sub_celestial, etc)
        
    Returns:
        Dict com mudanças detectadas: {
            'celestial_change': +5 ou -3 ou 0,
            'subclass_change': +10 ou -2 ou 0,
            'celestial_arrow': '↑' ou '↓' ou '',
            'subclass_arrow': '↑' ou '↓' ou '',
        }
    """
    try:
        from sqlalchemy import desc
        
        # Buscar snapshot de ontem (em horário de Brasília)
        today_str = get_formatted_now().split()[0]  # pega apenas a data
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')

        # Busca por string de data
        yesterday_record = session.query(LevelRankingHistory).filter(
            LevelRankingHistory.player_name == player_name,
            LevelRankingHistory.recorded_at.like(f'{yesterday_str}%')
        ).first()
        
        if not yesterday_record:
            # Se não houver snapshot de ontem, não mostra indicador
            return {
                'celestial_change': 0,
                'subclass_change': 0,
                'celestial_arrow': '',
                'subclass_arrow': '',
                'celestial_active': False,
                'subclass_active': False,
            }
        
        celestial_change = current_data.get('level_celestial', 0) - (yesterday_record.level_celestial or 0)
        subclass_change = current_data.get('level_sub_celestial', 0) - (yesterday_record.level_sub_celestial or 0)
        
        return {
            'celestial_change': celestial_change,
            'subclass_change': subclass_change,
            'celestial_arrow': '↑' if celestial_change > 0 else ('↓' if celestial_change < 0 else ''),
            'subclass_arrow': '↑' if subclass_change > 0 else ('↓' if subclass_change < 0 else ''),
            'celestial_active': celestial_change != 0,
            'subclass_active': subclass_change != 0,
        }
        
    except Exception as e:
        print(f"⚠ Erro ao comparar levels: {e}")
        return {
            'celestial_change': 0,
            'subclass_change': 0,
            'celestial_arrow': '',
            'subclass_arrow': '',
            'celestial_active': False,
            'subclass_active': False,
        }

def get_position_changes(session: Session, player_name: str, current_position: int) -> dict:
    """
    Compara posição atual com snapshot de ontem (em horário de Brasília)
    
    Args:
        session: SQLAlchemy Session
        player_name: Nome do player
        current_position: Posição atual no ranking
        
    Returns:
        Dict com mudanças de posição: {
            'position_change': +2 ou -3 ou 0,
            'arrow': '↑' ou '↓' ou '',
            'arrow_color': 'green' ou 'red',
            'active': True ou False,
        }
    """
    try:
        today_str = get_formatted_now().split()[0]
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')

        # Busca por string de data
        yesterday_record = session.query(LevelRankingHistory).filter(
            LevelRankingHistory.player_name == player_name,
            LevelRankingHistory.recorded_at.like(f'{yesterday_str}%')
        ).first()
        
        if not yesterday_record:
            # Se não houver snapshot de ontem, não mostra indicador
            return {
                'position_change': 0,
                'arrow': '',
                'arrow_color': '',
                'direction': 'neutral',
                'active': False,
            }
        
        position_change = (yesterday_record.rank_position or 0) - current_position  # Positivo = subiu (número foi de 5 para 3)
        
        return {
            'position_change': abs(position_change),
            'arrow': '↑' if position_change > 0 else ('↓' if position_change < 0 else ''),
            'arrow_color': 'green' if position_change > 0 else ('red' if position_change < 0 else ''),
            'active': position_change != 0,
            'direction': 'up' if position_change > 0 else ('down' if position_change < 0 else 'neutral'),
        }
        
    except Exception as e:
        print(f"⚠ Erro ao comparar posições: {e}")
        return {
            'position_change': 0,
            'arrow': '',
            'arrow_color': '',
            'active': False,
            'direction': 'neutral',
        }

def get_arena_changes(session: Session, player_name: str, current_data: dict, category: str, current_position: int) -> dict:
    """
    Compara dados da arena atual com a arena anterior.
    Considera horário de Brasília (GMT-3).
    
    Arena 1 (13:31) → compara com Arena 4 do dia anterior
    Arena 2 (19:31) → compara com Arena 1 do mesmo dia
    Arena 3 (21:01) → compara com Arena 2 do mesmo dia
    Arena 4 (23:31) → compara com Arena 3 do mesmo dia

    Args:
        session: SQLAlchemy Session
        player_name: Nome do player
        current_data: dict com chaves 'kill_value' e 'win_count'
        category: 'champion' ou 'aspirant'
        current_position: posição atual no ranking (1-based)

    Returns:
        dict com chaves: position_change, direction, active, kill_change, kill_arrow,
                        kill_active, win_change, win_arrow, win_active
    """
    try:
        from sqlalchemy import desc
        from app.models import ArenaRankingHistory
        from datetime import timedelta

        # Simplificação: compara arenas por data e arena_number
        today_str = get_formatted_now().split()[0]
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')

        # Detecta arena atual
        current_arena = current_data.get('arena_number')
        if not current_arena:
            current_arena = 1

        # Define arena anterior
        if current_arena == 1:
            previous_arena = 4
            previous_date = yesterday_str
        else:
            previous_arena = current_arena - 1
            previous_date = today_str

        # Busca registro anterior
        player_id = current_data.get('id')
        last_record = session.query(ArenaRankingHistory).filter(
            ArenaRankingHistory.player_id == player_id,
            ArenaRankingHistory.category == category,
            ArenaRankingHistory.arena_number == previous_arena,
            ArenaRankingHistory.recorded_at.like(f'{previous_date}%')
        ).first()

        if not last_record:
            return {
                'position_change': 0,
                'direction': 'neutral',
                'active': False,
                'kill_change': 0,
                'kill_arrow': '',
                'kill_active': False,
                'win_change': 0,
                'win_arrow': '',
                'win_active': False,
            }

        # Calcular diferenças
        pos_diff = (last_record.rank_position or 0) - current_position
        kill_change = (current_data.get('kill_value') or 0) - (last_record.kill_value or 0)
        win_change = (current_data.get('win_count') or 0) - (last_record.win_count or 0)

        return {
            'position_change': abs(pos_diff),
            'direction': 'up' if pos_diff > 0 else ('down' if pos_diff < 0 else 'neutral'),
            'active': pos_diff != 0,
            'kill_change': kill_change,
            'kill_arrow': '↑' if kill_change > 0 else ('↓' if kill_change < 0 else ''),
            'kill_active': kill_change != 0,
            'win_change': win_change,
            'win_arrow': '↑' if win_change > 0 else ('↓' if win_change < 0 else ''),
            'win_active': win_change != 0,
        }

    except Exception as e:
        print(f"⚠ Erro ao comparar arena: {e}")
        import traceback
        traceback.print_exc()
        return {
            'position_change': 0,
            'direction': 'neutral',
            'active': False,
            'kill_change': 0,
            'kill_arrow': '',
            'kill_active': False,
            'win_change': 0,
            'win_arrow': '',
            'win_active': False,
        }

def ensure_today_level_ranking_snapshot(session: Session) -> bool:
    from datetime import datetime, timedelta
    from sqlalchemy import exists
    from app.utils.datetime_utils import get_brasilia_date, BRASILIA_TZ
    """
    Verifica se existe um snapshot de LevelRankingHistory para hoje.
    Args:
        session: SQLAlchemy Session
    Returns:
        True se snapshot existe, False caso contrário
    """
    try:
        from app.models import LevelRankingHistory
        today = get_brasilia_date()
        today_start = datetime(today.year, today.month, today.day, tzinfo=BRASILIA_TZ)
        tomorrow_start = today_start + timedelta(days=1)
        today_start_str = today_start.strftime('%Y-%m-%d %H:%M')
        tomorrow_start_str = tomorrow_start.strftime('%Y-%m-%d %H:%M')
        snapshot_exists = session.query(
            exists().where(
                LevelRankingHistory.recorded_at >= today_start_str,
                LevelRankingHistory.recorded_at < tomorrow_start_str
            )
        ).scalar()
        if snapshot_exists:
            print("✓ Snapshot de Level Ranking para hoje já existe")
            return True
        else:
            print("⚠ Nenhum snapshot de Level Ranking para hoje encontrado")
            return False
    except Exception as e:
        print(f"⚠ Erro ao verificar snapshot de level ranking: {e}")
        import traceback
        traceback.print_exc()
        return False