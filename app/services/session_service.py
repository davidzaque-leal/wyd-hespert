from fastapi import Request, HTTPException
from app.database import SessionLocal
from app.models import User

SESSION_TIMEOUT = 86400  # 24 horas em segundos

def get_current_user(request: Request):
    """Get current user from session cookie"""
    session = SessionLocal()
    try:
        user_id = request.cookies.get("user_id")
        if not user_id:
            return None
        
        try:
            user = session.query(User).filter(User.id == int(user_id)).first()
            if user and user.is_active and user.is_admin:
                return user
            return None
        except (ValueError, TypeError):
            return None
    finally:
        session.close()


def require_admin(request: Request):
    """Verifica se o usuário é admin, caso contrário lança exceção"""
    user = get_current_user(request)
    if not user or not user.is_admin:
        raise HTTPException(status_code=401, detail="Unauthorized - Admin access required")
    return user


def get_current_user_id(request: Request):
    """Retorna o ID do usuário logado ou None"""
    user_id = request.cookies.get("user_id")
    if user_id:
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return None
    return None
