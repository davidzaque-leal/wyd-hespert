import hashlib
import secrets
import hmac
from sqlalchemy.orm import Session
from app.models import User


SECRET_KEY = "your-secret-key-change-in-production-12345"


def hash_password(password: str) -> str:
    """Hash de senha usando PBKDF2 (builtin no Python)"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    try:
        salt, pwd_hash = hashed_password.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(new_hash.hex(), pwd_hash)
    except (ValueError, AttributeError):
        return False


def get_user(session: Session, username: str):
    """Buscar usuário pelo username"""
    return session.query(User).filter(User.username == username).first()


def authenticate_user(session: Session, username: str, password: str):
    """Autentica o usuário"""
    user = get_user(session, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    if not user.is_active:
        return False
    return user


def create_user_admin(session: Session, username: str, email: str, password: str):
    """Cria um novo usuário administrador"""
    # Verificar se já existe
    if get_user(session, username):
        return None
    
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        is_admin=1,
        is_active=1
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
