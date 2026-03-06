"""
Serviço para manter histórico de rankings e posições
Salva snapshots periódicos dos rankings para análise de evolução
"""

from sqlalchemy.orm import Session
from app.models import LevelRankingHistory, ArenaRankingHistory
from datetime import datetime, timezone, timedelta


def get_brasilia_time():
    """
    Retorna a hora atual no fuso horário de Brasília (GMT-3)
    Todos os timestamps salvos no banco devem usar este horário
    """
    brasilia_tz = timezone(timedelta(hours=-3))
    return datetime.now(brasilia_tz)


def get_brasilia_now_utc():
    """
    Retorna a hora atual de Brasília convertida para UTC.
    Isso permite salvar no banco como UTC mas representando horário de Brasília.
    Exemplo: Se Brasília é 20:31, retorna UTC 23:31 (20:31 - (-3) = 23:31)
    """
    return get_brasilia_time().replace(tzinfo=timezone.utc)


def get_arena_number_by_time() -> int:
    """
    Detecta qual número de arena está sendo jogada baseado na hora GMT-3 (Brasília)
    Horários: 13:31, 19:31, 21:01, 23:31
    
    Returns:
        int: 1, 2, 3 ou 4 correspondendo às arenas do dia
    """
    # Converter para GMT-3 (Brasília)
    brasilia_tz = timezone(timedelta(hours=-3))
    now = datetime.now(brasilia_tz)
    
    # Extrair hora e minuto
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



def save_level_ranking_history(session: Session, players_data: list):
    """
    Salva snapshot do ranking de level (apenas 1 por dia)
    
    Args:
        session: SQLAlchemy Session
        players_data: Lista de dicts com dados dos players do ranking
    """
    try:
        from sqlalchemy import delete, func
        
        # Verificar se já existe snapshot de hoje
        today = datetime.now(timezone.utc).date()
        today_start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=timezone.utc)
        today_end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc)
        
        existing_today = session.query(LevelRankingHistory).filter(
            LevelRankingHistory.recorded_at >= today_start,
            LevelRankingHistory.recorded_at <= today_end
        ).first()
        
        if existing_today:
            print(f"✓ Histórico de Level Ranking já salvo hoje (pulando)")
            return True
        
        # Limpar registros com mais de 30 dias
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        session.query(LevelRankingHistory).filter(
            LevelRankingHistory.recorded_at < cutoff_date
        ).delete()
        
        # Inserir novo snapshot de hoje
        for rank_pos, player_data in enumerate(players_data, 1):
            history = LevelRankingHistory(
                player_id=player_data.get("id"),
                player_name=player_data.get("name", "Unknown"),
                rank_position=rank_pos,
                level_total=player_data.get("Soma Level", 0),
                points=player_data.get("points", 0),
                level_celestial=player_data.get("level", 0),
                level_subclass=player_data.get("levelSub", 0),
                celestial_lineage_name=player_data.get("celestial_lineage", ""),
                subclass_lineage_name=player_data.get("subclass_lineage", ""),
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
        
        # Verificar se já existe snapshot de ESTA ARENA ESPECÍFICA hoje
        today = datetime.now(timezone.utc).date()
        today_start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=timezone.utc)
        today_end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc)
        
        existing_arena = session.query(ArenaRankingHistory).filter(
            ArenaRankingHistory.recorded_at >= today_start,
            ArenaRankingHistory.recorded_at <= today_end,
            ArenaRankingHistory.category == category,
            ArenaRankingHistory.arena_number == arena_num
        ).first()
        
        if existing_arena:
            print(f"✓ Histórico de Arena {category} #{arena_num} já salvo hoje (pulando)")
            return True
        
        # Limpar registros antigos (manter apenas últimos 30 dias)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        session.query(ArenaRankingHistory).filter(
            ArenaRankingHistory.recorded_at < cutoff_date,
            ArenaRankingHistory.category == category
        ).delete()
        
        # Inserir novo snapshot
        for rank_pos, player_data in enumerate(players_data, 1):
            history = ArenaRankingHistory(
                player_id=player_data.get("id"),
                player_name=player_data.get("charName", "Unknown"),
                category=category,
                arena_number=arena_num,
                rank_position=rank_pos,
                total=player_data.get("total", 0),
                points=player_data.get("points", 0),
                win_count=player_data.get("winCount", 0),
                kill_value=player_data.get("killValue", 0),
                death_value=player_data.get("deathValue", 0),
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
        current_data: Dicionário com dados atuais (level_celestial, level_subclass, etc)
        
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
        
        # Buscar snapshot de ontem (não de hoje)
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)
        
        yesterday_start = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0, tzinfo=timezone.utc)
        yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, tzinfo=timezone.utc)
        
        yesterday_record = session.query(LevelRankingHistory).filter(
            LevelRankingHistory.player_name == player_name,
            LevelRankingHistory.recorded_at >= yesterday_start,
            LevelRankingHistory.recorded_at <= yesterday_end
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
        subclass_change = current_data.get('level_subclass', 0) - (yesterday_record.level_subclass or 0)
        
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


def get_level_changes_for_range(session: Session, days: int = 7):
    """
    Gera a lista de players do snapshot mais recente e compara com o snapshot
    de aproximadamente `days` dias atrás.

    Retorna lista ordenada pela posição atual (rank_position asc), cada item:
    {
        'rank_position': int,
        'name': str,
        'level_total': int,
        'level_change': int,
        'level_arrow': '↑'|'↓'|'',
        'level_active': bool,
        'position_change': int,
        'position_direction': 'up'|'down'|'neutral',
        'position_active': bool,
        'points': int
    }
    """
    try:
        from sqlalchemy import func, desc, extract
        from app.models import LevelRankingHistory
        from datetime import timedelta

        # 1. Buscar o snapshot mais recente (usar a data/hora mais recente)
        # Pegar apenas UM snapshot (o mais recente)
        latest_record = session.query(LevelRankingHistory).order_by(
            LevelRankingHistory.recorded_at.desc()
        ).first()
        
        if not latest_record:
            return []
        
        latest_dt = latest_record.recorded_at
        latest_date = latest_dt.date() if hasattr(latest_dt, 'date') else latest_dt
        
        print(f"DEBUG: latest_dt={latest_dt}, latest_date={latest_date}")
        
        # 2. Buscar todos os registros do dia mais recente
        # Mas pegar apenas UM snapshot (o primeiro/mais recente) para evitar duplicação
        current_date_start = datetime(latest_date.year, latest_date.month, latest_date.day, 0, 0, 0, tzinfo=timezone.utc)
        current_date_end = datetime(latest_date.year, latest_date.month, latest_date.day, 23, 59, 59, tzinfo=timezone.utc)
        
        # Pegar o snapshot mais recente do dia
        latest_snapshot_time = session.query(
            func.max(LevelRankingHistory.recorded_at).label('max_time')
        ).filter(
            LevelRankingHistory.recorded_at >= current_date_start,
            LevelRankingHistory.recorded_at <= current_date_end
        ).scalar()
        
        if not latest_snapshot_time:
            return []
        
        # Buscar apenas registros desse snapshot específico
        current_rows = session.query(LevelRankingHistory).filter(
            LevelRankingHistory.recorded_at == latest_snapshot_time
        ).order_by(LevelRankingHistory.rank_position).all()
        
        print(f"DEBUG: current_rows count = {len(current_rows)}")
        
        if not current_rows:
            return []
        
        # 3. Calcular a data alvo para comparação
        # Se days=1, procurar do dia anterior ao snapshot mais recente
        target_date = latest_date - timedelta(days=days)
        
        print(f"DEBUG: target_date = {target_date}, days = {days}")
        
        # 4. Buscar registros do dia alvo
        target_date_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=timezone.utc)
        target_date_end = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, tzinfo=timezone.utc)
        
        # Pegar o snapshot mais recente do dia alvo
        target_snapshot_time = session.query(
            func.max(LevelRankingHistory.recorded_at).label('max_time')
        ).filter(
            LevelRankingHistory.recorded_at >= target_date_start,
            LevelRankingHistory.recorded_at <= target_date_end
        ).scalar()
        
        target_rows = []
        if target_snapshot_time:
            target_rows = session.query(LevelRankingHistory).filter(
                LevelRankingHistory.recorded_at == target_snapshot_time
            ).order_by(LevelRankingHistory.recorded_at.desc()).all()
        
        print(f"DEBUG: target_rows count = {len(target_rows)}")
        
        # 5. Se não encontrou registros do dia alvo, buscar o último registro disponível ANTES do dia atual
        if not target_rows:
            print(f"DEBUG: Não encontrou registros de {target_date}, buscando último registro antes de {latest_date}")
            # Pegar o snapshot mais recente antes do dia atual
            last_snapshot_before = session.query(LevelRankingHistory).filter(
                LevelRankingHistory.recorded_at < current_date_start
            ).order_by(LevelRankingHistory.recorded_at.desc()).first()
            
            if last_snapshot_before:
                target_rows = session.query(LevelRankingHistory).filter(
                    LevelRankingHistory.recorded_at == last_snapshot_before.recorded_at
                ).order_by(LevelRankingHistory.rank_position).all()
            
            print(f"DEBUG: fallback target_rows count = {len(target_rows)}")
        
        # Criar dicionário de referência para comparações rápidas
        target_dict = {r.player_name: r for r in target_rows}

        result = []
        for cur in current_rows:
            # Buscar registro do dia alvo para este player
            prev = target_dict.get(cur.player_name)

            prev_level = prev.level_total if prev else None
            prev_rank = prev.rank_position if prev else None

            level_change = (cur.level_total or 0) - (prev_level or 0) if prev_level is not None else 0
            pos_diff = (prev_rank or cur.rank_position) - cur.rank_position if prev_rank is not None else 0

            result.append({
                'player_id': cur.player_id,
                'rank_position': cur.rank_position,
                'name': cur.player_name,
                'level_total': cur.level_total or 0,
                'level_celestial': cur.level_celestial or 0,
                'level_subclass': cur.level_subclass or 0,
                'celestial_lineage': cur.celestial_lineage_name or '',
                'subclass_lineage': cur.subclass_lineage_name or '',
                'level_change': level_change,
                'level_arrow': '↑' if level_change > 0 else ('↓' if level_change < 0 else ''),
                'level_active': level_change != 0,
                'position_change': abs(pos_diff),
                'position_direction': 'up' if pos_diff > 0 else ('down' if pos_diff < 0 else 'neutral'),
                'position_active': pos_diff != 0,
                'points': cur.points or 0,
            })

        # Ordenar por posição atual (1,2,3...) e limitar ao top 500
        result.sort(key=lambda x: x['rank_position'])
        print(f"DEBUG: returning {len(result)} results")
        return result[:500]
    except Exception as e:
        print(f"⚠ Erro ao gerar comparativos por range: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_top_level_gainers_for_range(session: Session, days: int = 7, limit: int = 100):
    """
    Retorna players ordenados por maior ganho de níveis no intervalo `days`.
    Usa `get_level_changes_for_range` e classifica por `level_change` desc.
    """
    try:
        rows = get_level_changes_for_range(session, days)
        # Filtrar apenas quem subiu (level_change > 0)
        gainers = [r for r in rows if (r.get('level_change') or 0) > 0]
        # Ordenar por maior ganho, depois por level_total desc
        gainers.sort(key=lambda x: ((x.get('level_change') or 0), x.get('level_total') or 0), reverse=True)
        return gainers[:limit]
    except Exception as e:
        print(f"⚠ Erro ao gerar top gainers: {e}")
        return []



def get_position_changes(session: Session, player_name: str, current_position: int) -> dict:
    """
    Compara posição atual com snapshot de ontem
    
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
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)
        
        yesterday_start = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0, tzinfo=timezone.utc)
        yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, tzinfo=timezone.utc)
        
        yesterday_record = session.query(LevelRankingHistory).filter(
            LevelRankingHistory.player_name == player_name,
            LevelRankingHistory.recorded_at >= yesterday_start,
            LevelRankingHistory.recorded_at <= yesterday_end
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
    Compara dados atuais de uma arena com o último snapshot gravado para a mesma categoria.

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

        # Pegar o snapshot mais recente para essa categoria (última arena registrada)
        last_record = session.query(ArenaRankingHistory).filter(
            ArenaRankingHistory.player_name == player_name,
            ArenaRankingHistory.category == category
        ).order_by(desc(ArenaRankingHistory.recorded_at)).first()

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

        # posição: positivo = subiu (ex: ontem 5 -> hoje 3 => 2)
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
        
        # Verificar se já existe snapshot de hoje
        today = datetime.now(timezone.utc).date()
        today_start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=timezone.utc)
        today_end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc)
        
        existing_today = session.query(LevelRankingHistory).filter(
            LevelRankingHistory.recorded_at >= today_start,
            LevelRankingHistory.recorded_at <= today_end
        ).first()
        
        if existing_today:
            print("✓ Snapshot de Level Ranking para hoje já existe")
            return True
        
        # Buscar dados atuais do ranking com player relacionado
        level_rows = session.query(LevelRanking)\
            .options(joinedload(LevelRanking.player))\
            .order_by(LevelRanking.level_total.desc())\
            .all()
        
        if not level_rows:
            print("⚠ Nenhum dado de ranking de level encontrado")
            return False
        
        # Criar snapshot para os dados atuais
        # Usar horário de Brasília convertido para UTC
        brasilia_now = get_brasilia_now_utc()
        
        for rank_pos, level_row in enumerate(level_rows, 1):
            player_name = level_row.player.name if level_row.player else f"Player_{level_row.player_id}"
            
            history = LevelRankingHistory(
                player_id=level_row.player_id,
                player_name=player_name,
                rank_position=rank_pos,
                level_total=level_row.level_total,
                points=level_row.points,
                level_celestial=level_row.level_celestial,
                level_subclass=level_row.level_subclass,
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
        
        # Verificar se já existe snapshot desta arena específica hoje
        today = datetime.now(timezone.utc).date()
        today_start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=timezone.utc)
        today_end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc)
        
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
        
        # Criar snapshot para os dados atuais
        # Usar horário de Brasília convertido para UTC
        brasilia_now = get_brasilia_now_utc()
        
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