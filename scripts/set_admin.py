import os
import sys

# Ensure project root is on sys.path so `app` package can be imported when running the script
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database import SessionLocal
from app.services.auth_service import get_user, hash_password, create_user_admin
from app.models import User


def set_admin(username: str = "lider_supermo", password: str = "Imperi0", email: str = "admin@wyd.com"):
    session = SessionLocal()
    try:
        # Ensure target user exists or create it
        user = get_user(session, username)
        if user:
            user.hashed_password = hash_password(password)
            user.email = email
            user.is_admin = 1
            user.is_active = 1
            session.add(user)
            session.commit()
            print(f"Updated admin user: {username}")
        else:
            create_user_admin(session, username, email, password)
            print(f"Created admin user: {username}")

        # Demote any other admin users so only this account remains admin
        others = session.query(User).filter(User.is_admin == 1, User.username != username).all()
        demoted = 0
        for o in others:
            o.is_admin = 0
            session.add(o)
            demoted += 1
        if demoted:
            session.commit()
            print(f"Demoted {demoted} other admin user(s)")
    finally:
        session.close()


if __name__ == "__main__":
    # Usage: python scripts/set_admin.py [username] [password]
    args = sys.argv[1:]
    username = args[0] if len(args) >= 1 else "lider_supermo"
    password = args[1] if len(args) >= 2 else "Imperi0"
    set_admin(username, password)
