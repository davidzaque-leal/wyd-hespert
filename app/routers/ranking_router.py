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
    session.close()

    return templates.TemplateResponse(
        "ranking.html",
        {"request": request, "players": players}
    )