import threading
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.services.data_store import data_store
from app.database import SessionLocal
from app.repositories.player_repository import PlayerRepository
from app.models import Class, ClassLineage
from app.utils.lineage_utils import LineageUtils
from app.services.player_serializer import PlayerSerializer

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ===============================
# Background updater
# ===============================
def background_updater():
    time.sleep(3600)  # Wait 1 hour before first sync
    while True:
        data_store.update_data()
        time.sleep(3600)  # Sincroniza a cada 1 hora


@app.on_event("startup")
def startup_event():
    # Ensure DB tables exist and perform first sync
    from app.database import engine, Base
    from app import models

    Base.metadata.create_all(bind=engine)

    # Seed classes and lineages (needed before syncing players)
    try:
        from app.services.db_seed import seed_classes_and_lineages
        seed_classes_and_lineages()
    except Exception as e:
        print("⚠ Erro ao popular classes/linhagens:", e)

    # Start background updater (will wait 1 hour before first sync)
    thread = threading.Thread(target=background_updater, daemon=True)
    thread.start()


# ===============================
# HOME
# ===============================
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "last_update": data_store.last_update
    })


# ===============================
# Ranking de Level
# ===============================
@app.get("/ranking")
def ranking(request: Request):
    players = sorted(
        data_store.level_ranking,
        key=lambda x: x.get("Soma Level", 0),
        reverse=True
    )

    return templates.TemplateResponse("ranking.html", {
        "request": request,
        "players": players,
        "last_update": data_store.last_update
    })


# ===============================
# Arena
# ===============================
@app.get("/arena/{category}")
def arena(request: Request, category: str):
    if category not in ["champion", "aspirant"]:
        raise HTTPException(status_code=404, detail="Categoria inválida")

    players = (
        data_store.arena_champion
        if category == "champion"
        else data_store.arena_aspirant
    )

    players = sorted(players, key=lambda x: x.get("total", 0), reverse=True)

    return templates.TemplateResponse("arena.html", {
        "request": request,
        "players": players,
        "category": category,
        "last_update": data_store.last_update
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
        for player in results:
            formatted_results.append(PlayerSerializer.serialize_player_search(player, session))
    
    return {
        "lineages": lineages,
        "guilds": guilds,
        "results": formatted_results,
        "search_performed": search_performed,
    }


@app.get("/search")
def search_page(request: Request):
    """Página de busca com formulários"""
    session = SessionLocal()
    try:
        context = _get_search_context(session)
        return templates.TemplateResponse("search.html", {
            "request": request,
            "last_update": data_store.last_update,
            **context
        })
    finally:
        session.close()


@app.get("/search-lineage")
def search_lineage(request: Request, lineage: str = None):
    """Buscar players por linhagem"""
    session = SessionLocal()
    try:
        results = []
        if lineage:
            results = PlayerRepository.get_by_lineage(session, lineage)
        
        context = _get_search_context(session, results, search_performed=bool(lineage))
        return templates.TemplateResponse("search.html", {
            "request": request,
            "last_update": data_store.last_update,
            **context
        })
    finally:
        session.close()


@app.get("/search-guild")
def search_guild(request: Request, guild_id: int = None):
    """Buscar players por guilda"""
    session = SessionLocal()
    try:
        results = []
        if guild_id:
            results = PlayerRepository.get_by_guild_id(session, guild_id)
        
        context = _get_search_context(session, results, search_performed=guild_id is not None)
        return templates.TemplateResponse("search.html", {
            "request": request,
            "last_update": data_store.last_update,
            **context
        })
    finally:
        session.close()


@app.get("/search-guild-lineage")
def search_guild_lineage(request: Request, guild_id: int = None, lineage: str = None):
    """Buscar players por guilda e linhagem"""
    session = SessionLocal()
    try:
        results = []
        if guild_id and lineage:
            results = PlayerRepository.get_by_guild_and_lineage(session, guild_id, lineage)
        
        context = _get_search_context(session, results, search_performed=guild_id is not None and lineage is not None)
        return templates.TemplateResponse("search.html", {
            "request": request,
            "last_update": data_store.last_update,
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