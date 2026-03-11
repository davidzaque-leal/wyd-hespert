import os
from dotenv import load_dotenv

def load_env():
    load_dotenv()
    # Garante que DATABASE_URL está disponível
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL não definida. Configure o arquivo .env.")
