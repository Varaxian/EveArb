import httpx

class ESIClient:
    def __init__(self, base_url: str = "https://esi.evetech.net") -> None:
        self.base_url = base_url.rstrip("/")

    async def get_json(self, path: str, params: dict | None = None):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
            return response.json()
