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


def get_arena_number_by_time() -> int:
    """
    Detecta qual número de arena está sendo jogada baseado na hora GMT-3 (Brasília)
    Horários: 13:31, 19:31, 21:01, 23:31
    
    Returns:
        int: 1, 2, 3 ou 4 correspondendo às arenas do dia
    """
    from app.utils.datetime_utils import get_brasilia_now
    now = get_brasilia_now()
    hour = now.hour
    minute = now.minute
    
    # Definir quais horários correspondem a cada arena
    # Arena 1: 13:31
    # Arena 2: 19:31
    # Arena 3: 21:01
    # Arena 4: 23:31
    
    # Considerar uma janela de ±5 minutos para sincronizar após a arena
    arena_times = [
        (13, 31),  # Arena 1
        (19, 31),  # Arena 2
        (21, 1),   # Arena 3
        (23, 31),  # Arena 4
    ]
    
    # Verificar qual arena está acontecendo (considerando janela de 10 minutos após)
    for idx, (arena_hour, arena_minute) in enumerate(arena_times, 1):
        # Janela: ±5 minutos do horário
        start_minute = arena_minute - 5
        end_minute = arena_minute + 5
        
        if start_minute < 0:
            # Se passar para hora anterior
            if (hour == arena_hour - 1 and minute >= 60 + start_minute) or \
               (hour == arena_hour and minute <= end_minute):
                return idx
        elif end_minute >= 60:
            # Se passar para próxima hora
            if (hour == arena_hour and minute >= start_minute) or \
               (hour == arena_hour + 1 and minute <= end_minute - 60):
                return idx
        else:
            # Normal
            if hour == arena_hour and start_minute <= minute <= end_minute:
                return idx
    
    # Se não está em nenhuma janela, retornar arena mais recente do dia
    if now.hour >= 23:
        return 4
    elif now.hour >= 21:
        return 3
    elif now.hour >= 19:
        return 2
    elif now.hour >= 13:
        return 1
    else:
        return 1  # Antes de 13:31, retorna arena 1 (do dia anterior ainda em andamento)

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
        # Busca os dois registros mais recentes
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
        
        # Verificar se já existe snapshot de hoje (em horário de Brasília)
        today = get_today()
        today_str = today.strftime('%d/%m/%Y')
        existing_today = session.query(LevelRankingHistory).filter(
            LevelRankingHistory.recorded_at.like(f'{today_str}%')
        ).first()
        
        if existing_today:
            print(f"✓ Histórico de Level Ranking já salvo hoje (pulando)")
            return True
        
        # Limpar registros com mais de 30 dias
        # Limpar registros com mais de 30 dias
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y %H:%M')
        session.query(LevelRankingHistory).filter(
            LevelRankingHistory.recorded_at < cutoff_date
        ).delete()
        
        # Inserir novo snapshot de hoje usando horário de Brasília
        # Receber snapshot_date dos registros principais
        # Sempre usar horário de Brasília
        snapshot_date = get_formatted_now()
        season = get_season()

        for rank_pos, player_data in enumerate(players_data, 1):
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
                recorded_at=snapshot_date
            )
            session.add(history)
        
        session.commit()
        print(f"✓ Histórico de Level Ranking salvo ({len(players_data)} players)")
        return True
        
    except Exception as e:
        print(f"⚠ Erro ao salvar histórico: {e}")
        session.rollback()
        return False


def save_arena_ranking_history(session: Session, players_data: list, category: str):
    """
    Salva snapshot do ranking de arena (4 vezes ao dia nos horários específicos)
    Horários: 13:31, 19:31, 21:01 e 23:31 GMT-3
    
    Args:
        session: SQLAlchemy Session
        players_data: Lista de dicts com dados dos players
        category: 'champion' ou 'aspirant'
    """
    try:
        from sqlalchemy import delete
        
        # Detectar qual arena está sendo feita agora
        arena_num = get_arena_number_by_time()
        # Padronizar data/hora para validação (usar apenas data no formato YYYY-MM-DD)
        snapshot_date = get_formatted_now()
        today_str = snapshot_date.split()[0]  # pega apenas a data
        # Corrige para o formato YYYY-MM-DD
        if '/' in today_str:
            # Caso esteja no formato dd/mm/yyyy, converte
            today_obj = datetime.strptime(today_str, '%d/%m/%Y')
            today_str = today_obj.strftime('%Y-%m-%d')
        existing_arena = session.query(ArenaRankingHistory).filter(
            ArenaRankingHistory.recorded_at.like(f'{today_str}%'),
            ArenaRankingHistory.category == category,
            ArenaRankingHistory.arena_number == arena_num
        ).first()

        if existing_arena:
            print(f"✓ Histórico de Arena {category} #{arena_num} já salvo hoje (pulando)")
            return True

        # Inserir novo snapshot usando horário de Brasília
        # Receber snapshot_date dos registros principais
        # Sempre usar horário de Brasília
        season = get_season()

        for rank_pos, player_data in enumerate(players_data, 1):
            player_id = player_data.get("id")
            history = ArenaRankingHistory(
                player_id=player_id,
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
        
        session.commit()
        print(f"✓ Histórico de Arena {category} salvo ({len(players_data)} players)")
        return True
        
    except Exception as e:
        print(f"⚠ Erro ao salvar histórico de arena: {e}")
        session.rollback()
        return False


def get_level_ranking_history(session: Session, limit: int = 100):
    """
    Recupera histórico de ranking de level
    
    Args:
        session: SQLAlchemy Session
        limit: Número máximo de registros
        
    Returns:
        Lista de registros de histórico ordenados por data recente
    """
    try:
        from sqlalchemy import desc
        
        return session.query(LevelRankingHistory).order_by(
            desc(LevelRankingHistory.recorded_at),
            LevelRankingHistory.rank_position
        ).limit(limit).all()
        
    except Exception as e:
        print(f"⚠ Erro ao recuperar histórico: {e}")
        return []


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
    """
    Garante que existe um snapshot de LevelRankingHistory para hoje
    Se não existir, cria um a partir dos dados atuais do banco
    
    Args:
        session: SQLAlchemy Session
        
    Returns:
        True se snapshot existe ou foi criado, False se falhou
    """
    try:
        from app.models import LevelRanking, Player
        from sqlalchemy.orm import joinedload
        
        # Verificar se já existe snapshot de hoje (em horário de Brasília)
        today = get_brasilia_date()
        today_start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=BRASILIA_TZ)
        today_end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=BRASILIA_TZ)
        
        existing_today = session.query(LevelRankingHistory).filter(
            LevelRankingHistory.recorded_at >= today_start,
            LevelRankingHistory.recorded_at <= today_end
        ).first()

        if existing_today:
            print("✓ Snapshot de Level Ranking para hoje já existe")
            return True

        # Se não existe snapshot, força atualização dos rankings e histórico
        from app.models import LevelRanking, Player
        from sqlalchemy.orm import joinedload
        level_rows = session.query(LevelRanking)\
            .options(joinedload(LevelRanking.player))\
            .order_by(LevelRanking.level_total.desc())\
            .all()
        if not level_rows:
            print("⚠ Nenhum dado de ranking de level encontrado")
            return False
        brasilia_now = datetime.now()
        for rank_pos, level_row in enumerate(level_rows, 1):
            player_name = level_row.player.name if level_row.player else f"Player_{level_row.player_id}"
            history = LevelRankingHistory(
                player_id=level_row.player_id,
                player_name=player_name,
                rank_position=rank_pos,
                level_total=level_row.level_total,
                points=level_row.points,
                level_celestial=getattr(level_row, "level_celestial", 0),
                level_sub_celestial=getattr(level_row, "level_sub_celestial", 0),
                celestial_lineage_name=level_row.celestial_lineage_name or "",
                subclass_lineage_name=level_row.subclass_lineage_name or "",
                recorded_at=brasilia_now,
            )
            session.add(history)
        session.commit()
        print(f"✓ Snapshot de Level Ranking criado para hoje ({len(level_rows)} players)")
        return True
        
        # Buscar dados atuais do ranking com player relacionado
        level_rows = session.query(LevelRanking)\
            .options(joinedload(LevelRanking.player))\
            .order_by(LevelRanking.level_total.desc())\
            .all()
        
        if not level_rows:
            print("⚠ Nenhum dado de ranking de level encontrado")
            return False
        
        # Criar snapshot para os dados atuais usando horário de Brasília
        brasilia_now = datetime.now()
        
        for rank_pos, level_row in enumerate(level_rows, 1):
            player_name = level_row.player.name if level_row.player else f"Player_{level_row.player_id}"
            
            history = LevelRankingHistory(
                player_id=level_row.player_id,
                player_name=player_name,
                rank_position=rank_pos,
                level_total=level_row.level_total,
                points=level_row.points,
                celestial_lineage_name=level_row.celestial_lineage_name or "",
                subclass_lineage_name=level_row.subclass_lineage_name or "",
                recorded_at=brasilia_now,
            )
            session.add(history)
        
        session.commit()
        print(f"✓ Snapshot de Level Ranking criado para hoje ({len(level_rows)} players)")
        return True
        
    except Exception as e:
        print(f"⚠ Erro ao garantir snapshot de level ranking: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False


def ensure_today_arena_ranking_snapshot(session: Session, category: str) -> bool:
    """
    Garante que existe um snapshot de ArenaRankingHistory para hoje
    Se não existir, cria um a partir dos dados atuais do banco
    
    Args:
        session: SQLAlchemy Session
        category: 'champion' ou 'aspirant'
        
    Returns:
        True se snapshot existe ou foi criado, False se falhou
    """
    try:
        from app.models import ArenaRanking, Player
        from sqlalchemy.orm import joinedload
        
        # Detectar qual arena está sendo feita agora
        arena_num = get_arena_number_by_time()
        # Verificar se já existe snapshot desta arena específica hoje (em horário de Brasília)
        today = get_brasilia_date()
        today_start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=BRASILIA_TZ)
        today_end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=BRASILIA_TZ)
        existing_today = session.query(ArenaRankingHistory).filter(
            ArenaRankingHistory.recorded_at >= today_start,
            ArenaRankingHistory.recorded_at <= today_end,
            ArenaRankingHistory.category == category,
            ArenaRankingHistory.arena_number == arena_num
        ).first()
        
        if existing_today:
            print(f"✓ Snapshot de Arena {category} #{arena_num} para hoje já existe")
            return True
        
        # Buscar dados atuais do ranking
        arena_rows = session.query(ArenaRanking)\
            .options(joinedload(ArenaRanking.player))\
            .filter(ArenaRanking.category == category)\
            .order_by(ArenaRanking.total.desc())\
            .all()
        
        if not arena_rows:
            print(f"⚠ Nenhum dado de ranking de arena {category} encontrado")
            return False
        
        # Criar snapshot para os dados atuais usando horário de Brasília
        brasilia_now = datetime.now()
        
        for rank_pos, arena_row in enumerate(arena_rows, 1):
            player_name = arena_row.player.name if arena_row.player else f"Player_{arena_row.player_id}"
            
            history = ArenaRankingHistory(
                player_id=arena_row.player_id,
                player_name=player_name,
                category=category,
                arena_number=arena_num,
                rank_position=rank_pos,
                total=arena_row.total,
                points=arena_row.points,
                win_count=arena_row.win_count,
                kill_value=arena_row.kill_value,
                death_value=arena_row.death_value,
                recorded_at=brasilia_now,
            )
            session.add(history)
        
        session.commit()
        print(f"✓ Snapshot de Arena {category} #{arena_num} criado para hoje ({len(arena_rows)} players)")
        return True
        
    except Exception as e:
        print(f"⚠ Erro ao garantir snapshot de arena {category}: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False

