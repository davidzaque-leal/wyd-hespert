from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.database import SessionLocal
from app.repositories.level_repository import LevelRepository

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ranking")
def ranking(request: Request):
    session = SessionLocal()
    players = LevelRepository.get_all(session)

    # Buscar última atualização do ranking de level
    last_level_update = session.execute(
        "SELECT MAX(snapshot_date) FROM level_rankings"
    ).scalar()

    # Buscar última atualização da arena
    last_arena_update = session.execute(
        "SELECT MAX(snapshot_date) FROM arena_rankings"
    ).scalar()

    session.close()

    return templates.TemplateResponse(
        "ranking.html",
        {
            "request": request,
            "players": players,
            "last_level_update": last_level_update,
            "last_arena_update": last_arena_update
        }
    )