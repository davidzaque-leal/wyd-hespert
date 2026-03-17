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

# Registrar rotas customizadas
from app.routers import ranking_router
app.include_router(ranking_router.router)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ===============================
# Background updater
# ===============================
def background_updater():
    from app.services.sync_service import SyncService
    while True:
        try:
            SyncService.check_hashes()
            print(f"⏰ background_updater executado")
        except Exception as e:
            print(f"⚠ Erro no background_updater: {e}")
        time.sleep(30)

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
        from pydantic import BaseModel, constr, ValidationError

        class LoginInput(BaseModel):
            username: constr(strip_whitespace=True, min_length=3, max_length=50)
            password: constr(strip_whitespace=True, min_length=6, max_length=100)

        # Validação de input
        try:
            validated = LoginInput(username=username, password=password)
        except ValidationError as ve:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Dados inválidos: " + str(ve)
            }, status_code=400)

        user = authenticate_user(session, validated.username, validated.password)
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
            httponly=True,
            secure=True,
            samesite="Strict",
            expires=86400
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
    response.delete_cookie(key="user_id", httponly=True, secure=True, samesite="Strict")
    return response

def startup_event():
    # Ensure DB tables exist and perform first sync
    from app.database import engine, Base
    from app import models

    Base.metadata.create_all(bind=engine)

    # Create default admin user if doesn't exist
    session = SessionLocal()
    try:
        admin_username = os.environ.get("ADMIN_USERNAME", "lider")
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
    
    # Carregar dados do banco para exibição
    from app.services.data_store import data_store
    data_store.update_data(sync=False)

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
    from app.services.ranking_history_service import get_latest_level_indicators
    
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
            # Calcular mudanças de level usando os dois registros mais recentes
            level_changes = get_latest_level_indicators(session, player.get("id"))
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
    winner_list = []
    try:
        for idx, player in enumerate(players, 1):
            player["rank_position"] = idx
            from app.services.ranking_history_service import get_latest_arena_indicators
            indicators = get_latest_arena_indicators(session, player.get("id"), category)
            player["arena_indicators"] = indicators
            # Coletar vencedores da última arena
            if indicators.get("win_change") == 1:
                winner_list.append({
                    "id": player.get("id"),
                    "rank_position": idx,
                    "name": player.get("charName") or player.get("name") or f"ID {player.get('id')}"
                })
        # Ordenar vencedores por rank_position
        winner_list.sort(key=lambda x: x["rank_position"])
        
        # Montar título dinâmico
        congrats_title = f"Time vencedor da última Arena {category.capitalize()}!"
    finally:
        session.close()

    return templates.TemplateResponse("arena.html", {
        "request": request,
        "players": players,
        "category": category,
        "last_update": data_store.last_update,
        "user": get_current_user(request),
        "arena_winners": winner_list,
        "congrats_title": congrats_title
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
    
    from pydantic import BaseModel, constr, ValidationError

    class LineageInput(BaseModel):
        lineage: constr(strip_whitespace=True, min_length=3, max_length=100)

    session = SessionLocal()
    try:
        results = []
        if lineage:
            try:
                validated = LineageInput(lineage=lineage)
            except ValidationError as ve:
                context = _get_search_context(session, [], search_performed=True)
                return templates.TemplateResponse("search.html", {
                    "request": request,
                    "last_update": data_store.last_update,
                    "user": user,
                    "error": "Dados inválidos: " + str(ve),
                    **context
                })
            results = PlayerRepository.get_by_lineage(session, validated.lineage)
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
    
    from pydantic import BaseModel, conint, ValidationError

    class GuildInput(BaseModel):
        guild_id: conint(gt=0)

    session = SessionLocal()
    try:
        results = []
        if guild_id:
            try:
                validated = GuildInput(guild_id=guild_id)
            except ValidationError as ve:
                context = _get_search_context(session, [], search_performed=True)
                return templates.TemplateResponse("search.html", {
                    "request": request,
                    "last_update": data_store.last_update,
                    "user": user,
                    "error": "Dados inválidos: " + str(ve),
                    **context
                })
            results = PlayerRepository.get_by_guild_id(session, validated.guild_id)
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
    
    from pydantic import BaseModel, conint, constr, ValidationError

    class GuildLineageInput(BaseModel):
        guild_id: conint(gt=0)
        lineage: constr(strip_whitespace=True, min_length=3, max_length=100)

    session = SessionLocal()
    try:
        results = []
        if guild_id and lineage:
            try:
                validated = GuildLineageInput(guild_id=guild_id, lineage=lineage)
            except ValidationError as ve:
                context = _get_search_context(session, [], search_performed=True)
                return templates.TemplateResponse("search.html", {
                    "request": request,
                    "last_update": data_store.last_update,
                    "user": user,
                    "error": "Dados inválidos: " + str(ve),
                    **context
                })
            results = PlayerRepository.get_by_guild_and_lineage(session, validated.guild_id, validated.lineage)
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