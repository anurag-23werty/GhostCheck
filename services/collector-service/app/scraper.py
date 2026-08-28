import os

import httpx


BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
BRIGHT_DATA_ZONE = os.getenv("BRIGHT_DATA_ZONE")


async def scrape_page(url: str) -> str:
    if not BRIGHT_DATA_API_KEY:
        raise RuntimeError("BRIGHT_DATA_API_KEY is not configured")

    if not BRIGHT_DATA_ZONE:
        raise RuntimeError("BRIGHT_DATA_ZONE is not configured")

    endpoint = "https://api.brightdata.com/request"

    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "zone": BRIGHT_DATA_ZONE,
        "url": url,
        "format": "raw",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            endpoint,
            headers=headers,
            json=payload,
        )

        response.raise_for_status()

        return response.text