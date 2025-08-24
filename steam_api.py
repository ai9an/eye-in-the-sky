import requests

def fetch_game_data(app_id: str) -> dict | None:
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us&l=en"
    try:
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        j = r.json()
        node = j.get(app_id)
        if not node or not node.get("success"):
            return None
        data = node.get("data", {})
        pov = data.get("price_overview") or {}
        price = (pov.get("final") or 0) / 100
        return {
            "name": data.get("name") or "Unknown",
            "currency": pov.get("currency") or "USD",
            "price": price,
            "discount_percent": pov.get("discount_percent") or 0
        }
    except Exception:
        return None
