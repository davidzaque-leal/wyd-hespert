import time
import requests

URL = "https://wyd-hespert.onrender.com/arena/aspirant"
INTERVAL = 180  # 3 minutos em segundos

while True:
    try:
        response = requests.get(URL)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Status: {response.status_code}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Erro: {e}")
    time.sleep(INTERVAL)
