import threading
import time
import os
from fastapi import FastAPI, Request, HTTPException, Response, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.services.data_store import data_store
from app.database import SessionLocal
from app.repositories.player_repository import PlayerRepository
from app.models import Class, ClassLineage, User
from app.utils.lineage_utils import LineageUtils
from app.services.player_serializer import PlayerSerializer
from app.services.auth_service import authenticate_user, create_user_admin
from app.services.session_service import get_current_user, require_admin

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ===============================
# Background updater
# ===============================
def background_updater():
    """
    Background updater com timer para as arenas
    Horários de atualização GMT-3 (Brasília):
    - 13:31 - Arena 1
    - 19:31 - Arena 2
    - 20:31 - Arena 3
    - 23:31 - Arena 4
    
    Level ranking atualiza apenas uma vez por dia
    """
    from datetime import datetime, timezone, timedelta
    
    # Aguardar próximo horário de sincronização
    time.sleep(60)
    
    while True:
        try:
            # Converter para GMT-3 (Brasília)
            brasilia_tz = timezone(timedelta(hours=-3))
            now = datetime.now(brasilia_tz)
            
            hour = now.hour
            minute = now.minute
            
            # Arena schedule nos minutos específicos com janela de tolerância
            arena_times = [13, 19, 20, 23]  # Horas
            arena_minute = 31
            tolerance = 2  # ±2 minutos
            
            # Verificar se estamos em um dos horários de arena
            is_arena_time = any(
                hour == h and (arena_minute - tolerance) <= minute <= (arena_minute + tolerance)
                for h in arena_times
            )
            
            # Sincronizar a cada 1 hora ou no horário de arena
            if is_arena_time:
                print(f"⏰ Sincronizando em horário de arena: {hour:02d}:{minute:02d}")
                data_store.update_data()
            
        except Exception as e:
            print(f"⚠ Erro no background_updater: {e}")
        
        time.sleep(60)  # Checar a cada minuto


# ===============================
# Authentication Routes
# ===============================
@app.get("/login")
def login_page(request: Request):
    """Página de login"""
    # Se já está logado, redireciona para search
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/search", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": None
    })


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Processa o login"""
    session = SessionLocal()
    try:
        user = authenticate_user(session, username, password)
        if not user:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Invalid username or password"
            }, status_code=401)
        
        # Criar resposta com cookie de sessão
        response = RedirectResponse(url="/search", status_code=302)
        response.set_cookie(
            key="user_id",
            value=str(user.id),
            max_age=86400,  # 24 horas
            httponly=True
        )
        return response
    except Exception as e:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Erro ao fazer login: {str(e)}"
        }, status_code=500)
    finally:
        session.close()


@app.get("/logout")
def logout():
    """Faz logout do usuário"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="user_id")
    return response



def startup_event():
    # Ensure DB tables exist and perform first sync
    from app.database import engine, Base
    from app import models

    Base.metadata.create_all(bind=engine)

    # Create default admin user if doesn't exist
    session = SessionLocal()
    try:
        admin_username = os.environ.get("ADMIN_USERNAME", "lider_supermo")
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@wyd.com")
        admin_password = os.environ.get("ADMIN_PASSWORD", "Imperi0")

        admin = session.query(User).filter(User.username == admin_username).first()
        if not admin:
            create_user_admin(session, admin_username, admin_email, admin_password)
            print(f"✓ Usuário admin padrão criado (username: {admin_username}, password: {admin_password})")
    except Exception as e:
        print("⚠ Erro ao criar admin:", e)
    finally:
        session.close()
    
    # Garantir snapshots de histórico para hoje
    session = SessionLocal()
    try:
        from app.services.ranking_history_service import (
            ensure_today_level_ranking_snapshot, 
            ensure_today_arena_ranking_snapshot
        )
        
        print("📅 Verificando snapshots de histórico para hoje...")
        ensure_today_level_ranking_snapshot(session)
        ensure_today_arena_ranking_snapshot(session, "champion")
        ensure_today_arena_ranking_snapshot(session, "aspirant")
        
    except Exception as e:
        print(f"⚠ Erro ao garantir snapshots de hoje: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

    # Seed classes and lineages (needed before syncing players)
    try:
        from app.services.db_seed import seed_classes_and_lineages
        seed_classes_and_lineages()
    except Exception as e:
        print("⚠ Erro ao popular classes/linhagens:", e)

    # Start background updater (will wait 1 hour before first sync)
    thread = threading.Thread(target=background_updater, daemon=True)
    thread.start()


# Registrar startup event
app.add_event_handler("startup", startup_event)


# ===============================
# HOME
# ===============================
@app.get("/")
def home(request: Request):
    # Compute dashboard metrics
    session = SessionLocal()
    try:
        # Count directly from DB to reflect real stored records
        from app.models import Guild, ClassLineage, Player

        total_players = session.query(Player).count()
        active_guilds = session.query(Guild).count()
        lineages_count = session.query(ClassLineage).count()

        # Calculate lineage distribution (count occurrences from celestial and subclass)
        from app.utils.lineage_utils import LineageUtils

        # Calculate lineage stack combinations from level ranking (top 500)
        # Normalize combinations: A+B should be same as B+A
        lineage_stacks = {}
        level_ranking = data_store.level_ranking[:500]  # Top 500 players
        
        for player in level_ranking:
            celestial = player.get("celestial_lineage") or "Sem"
            subclass = player.get("subclass_lineage") or "Sem"
            # Create normalized key: sort alphabetically so A+B = B+A
            combo = sorted([celestial, subclass])
            stack_key = f"{combo[0]} + {combo[1]}"
            lineage_stacks[stack_key] = lineage_stacks.get(stack_key, 0) + 1

        total_in_top = len(level_ranking) or 1
        
        # Build percent over total players in top 500
        lineage_list = [
            {"name": name, "count": cnt, "percent": round((cnt / total_in_top) * 100, 2)}
            for name, cnt in lineage_stacks.items()
        ]
        lineage_list.sort(key=lambda x: x["count"], reverse=True)
        top10_lineages = lineage_list[:10]

        return templates.TemplateResponse("index.html", {
            "request": request,
            "last_update": data_store.last_update,
            "total_players": total_players,
            "active_guilds": active_guilds,
            "lineages_count": lineages_count,
            "top10_lineages": top10_lineages,
        })
    finally:
        session.close()


# ===============================
# Ranking de Level
# ===============================
# ===============================
# Ranking de Level
# ===============================
@app.get("/ranking")
def ranking(request: Request):
    from app.services.ranking_history_service import get_level_changes
    
    players = sorted(
        data_store.level_ranking,
        key=lambda x: x.get("Soma Level", 0),
        reverse=True
    )
    
    session = SessionLocal()
    try:
        # Adicionar índices de posição e mudanças de level
        for idx, player in enumerate(players, 1):
            player["rank_position"] = idx
            
            # Calcular mudanças de level
            level_changes = get_level_changes(session, player.get("name"), {
                'level_celestial': player.get("level"),
                'level_subclass': player.get("levelSub"),
            })
            player["level_changes"] = level_changes
    finally:
        session.close()

    return templates.TemplateResponse("ranking.html", {
        "request": request,
        "players": players,
        "last_update": data_store.last_update,
        "user": get_current_user(request)
    })


# ===============================
# Arena
# ===============================
@app.get("/arena/{category}")
def arena(request: Request, category: str):
    from app.services.ranking_history_service import get_position_changes, get_arena_changes
    
    if category not in ["champion", "aspirant"]:
        raise HTTPException(status_code=404, detail="Categoria inválida")

    players = (
        data_store.arena_champion
        if category == "champion"
        else data_store.arena_aspirant
    )

    players = sorted(players, key=lambda x: x.get("total", 0), reverse=True)
    
    session = SessionLocal()
    try:
        # Adicionar índices de posição e mudanças de posição/kills/vitórias
        for idx, player in enumerate(players, 1):
            player["rank_position"] = idx

            # Calcular mudanças de posição (usando histórico de arena) e stat changes
            arena_changes = get_arena_changes(session, player.get("charName"), {
                'kill_value': player.get('killValue', 0),
                'win_count': player.get('winCount', 0)
            }, category, idx)

            # mapear para compatibilidade com templates
            player["position_change"] = {
                'position_change': arena_changes.get('position_change', 0),
                'direction': arena_changes.get('direction', 'neutral'),
                'active': arena_changes.get('active', False),
            }

            player['arena_stat_changes'] = {
                'kill_change': arena_changes.get('kill_change', 0),
                'kill_arrow': arena_changes.get('kill_arrow', ''),
                'kill_active': arena_changes.get('kill_active', False),
                'win_change': arena_changes.get('win_change', 0),
                'win_arrow': arena_changes.get('win_arrow', ''),
                'win_active': arena_changes.get('win_active', False),
            }
    finally:
        session.close()

    return templates.TemplateResponse("arena.html", {
        "request": request,
        "players": players,
        "category": category,
        "last_update": data_store.last_update,
        "user": get_current_user(request)
    })


# ===============================
# Ranking Combinado (Level + Arena)
# ===============================
@app.get("/ranking-combined")
def ranking_combined(request: Request):
    players = data_store.get_combined_ranking()

    return templates.TemplateResponse("ranking_combined.html", {
        "request": request,
        "players": players,
        "last_update": data_store.last_update
    })


# ===============================
# Ranking Histórico
# ===============================
@app.get("/ranking-history")
def ranking_history(request: Request, days: int = 7):
    """Página com histórico de evolução de rankings

    Parâmetro `days` permite comparar com snapshot de ~1/7/15/30 dias atrás.
    """
    from app.services.ranking_history_service import (
        get_top_level_gainers_for_range,
    )

    if days not in (1, 7, 15, 30):
        days = 7

    session = SessionLocal()
    try:
        # Mostrar top gainers por default (quem mais upou levels no período)
        players = get_top_level_gainers_for_range(session, days, limit=500)

        return templates.TemplateResponse("ranking_history.html", {
            "request": request,
            "last_update": data_store.last_update,
            "user": get_current_user(request),
            "players": players,
            "days": days,
            "total_snapshots": 0,
        })
    finally:
        session.close()


# ===============================
# Buscar Players
# ===============================
def _get_search_context(session, results=None, search_performed=False):
    """Helper function to get context for search templates - Centralizado"""
    lineages = PlayerRepository.get_all_lineages(session)
    guilds = PlayerRepository.get_all_guilds(session)
    
    # Build results using PlayerSerializer
    formatted_results = []
    if results:
        for idx, player in enumerate(results, 1):
            formatted_results.append(PlayerSerializer.serialize_player_search(player, session, rank_position=idx))
    
    return {
        "lineages": lineages,
        "guilds": guilds,
        "results": formatted_results,
        "search_performed": search_performed,
    }


@app.get("/search")
def search_page(request: Request):
    """Página de busca com formulários - APENAS ADMIN"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    session = SessionLocal()
    try:
        context = _get_search_context(session)
        return templates.TemplateResponse("search.html", {
            "request": request,
            "last_update": data_store.last_update,
            "user": user,
            **context
        })
    finally:
        session.close()


@app.get("/search-lineage")
def search_lineage(request: Request, lineage: str = None):
    """Buscar players por linhagem - APENAS ADMIN"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    session = SessionLocal()
    try:
        results = []
        if lineage:
            results = PlayerRepository.get_by_lineage(session, lineage)
        
        context = _get_search_context(session, results, search_performed=bool(lineage))
        return templates.TemplateResponse("search.html", {
            "request": request,
            "last_update": data_store.last_update,
            "user": user,
            **context
        })
    finally:
        session.close()


@app.get("/search-guild")
def search_guild(request: Request, guild_id: int = None):
    """Buscar players por guilda - APENAS ADMIN"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    session = SessionLocal()
    try:
        results = []
        if guild_id:
            results = PlayerRepository.get_by_guild_id(session, guild_id)
        
        context = _get_search_context(session, results, search_performed=guild_id is not None)
        return templates.TemplateResponse("search.html", {
            "request": request,
            "last_update": data_store.last_update,
            "user": user,
            **context
        })
    finally:
        session.close()


@app.get("/search-guild-lineage")
def search_guild_lineage(request: Request, guild_id: int = None, lineage: str = None):
    """Buscar players por guilda e linhagem - APENAS ADMIN"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    session = SessionLocal()
    try:
        results = []
        if guild_id and lineage:
            results = PlayerRepository.get_by_guild_and_lineage(session, guild_id, lineage)
        
        context = _get_search_context(session, results, search_performed=guild_id is not None and lineage is not None)
        return templates.TemplateResponse("search.html", {
            "request": request,
            "last_update": data_store.last_update,
            "user": user,
            **context
        })
    finally:
        session.close()


# ===============================
# Health Check
# ===============================
@app.get("/health")
def health():
    return {
        "status": "ok",
        "last_update": data_store.last_update
    }