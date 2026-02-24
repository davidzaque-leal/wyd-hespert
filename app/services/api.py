import requests

BASE_URL = "https://rn3xfhamppsetddkod6vwc24lu0lhcek.lambda-url.us-east-1.on.aws"

def get_level_ranking():
    response = requests.post(
        f"{BASE_URL}/component-rank",
        json={"options": {}}
    )
    return response.json()

def get_arena_ranking(category: str):
    response = requests.get(
        f"{BASE_URL}/royal-rank",
        params={"category": category}
    )
    return response.json()