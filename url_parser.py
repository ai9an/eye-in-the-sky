import re

def extract_app_id(url: str) -> str | None:
    m = re.search(r"store\.steampowered\.com/app/(\d+)", url, re.IGNORECASE)
    return m.group(1) if m else None
