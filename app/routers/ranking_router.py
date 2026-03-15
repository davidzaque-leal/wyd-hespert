from fastapi import APIRouter, Request, Response
from fastapi import Body
from fastapi.templating import Jinja2Templates
from app.database import SessionLocal
from app.repositories.level_repository import LevelRepository


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Rota manual para atualizar arenas
from app.services.data_store import data_store

@router.post("/arena/update-manual")
def update_arena_manual(category: str = Body(..., embed=True)):
    if category not in ["champion", "aspirant"]:
        return Response(content="Categoria inválida. Use 'champion' ou 'aspirant'", status_code=400)
    try:
        # Atualiza dados principais (arena_rankings)
        data_store.update_data(sync=True)
        from app.database import SessionLocal
        session = SessionLocal()
        if category == "champion":
            data = data_store.arena_champion
        else:
            data = data_store.arena_aspirant
        from app.services.ranking_history_service import save_arena_ranking_history
        save_arena_ranking_history(session, data, category)
        session.close()
        return Response(content=f"Arena '{category}' atualizada com sucesso!", status_code=200)
    except Exception as e:
        return Response(content=f"Erro ao atualizar arena '{category}': {e}", status_code=500)

@router.get("/ranking")
def ranking(request: Request):
    session = SessionLocal()
    players = LevelRepository.get_all(session)

    # Buscar última atualização do ranking de level
    from sqlalchemy import text
    last_level_update = session.execute(
        text("SELECT MAX(snapshot_date) FROM level_rankings")
    ).scalar()

    # Buscar última atualização da arena
    last_arena_update = session.execute(
        text("SELECT MAX(snapshot_date) FROM arena_rankings")
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