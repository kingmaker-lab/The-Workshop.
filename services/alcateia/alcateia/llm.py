import httpx

from .personas import system_prompt


class Model:
    """Stateless Chat Completions-compatible adapter, with no tools or URL fetching."""

    def __init__(self, config, transport=None):
        self.config = config
        self.http = httpx.AsyncClient(timeout=httpx.Timeout(25, connect=5), follow_redirects=False,
                                     transport=transport, limits=httpx.Limits(max_connections=4))

    async def answer(self, bot, user, text, style):
        c = self.config
        payload = {
            "model": c.model,
            "messages": [
                {"role": "system", "content": system_prompt(bot, user, c.creator, style)},
                {"role": "user", "content": text[:2000]},
            ],
            "max_tokens": 500 if style["length"] == "detalhado" else 260,
        }
        async with self.http.stream("POST", c.api_url + "/chat/completions",
                                    headers={"Authorization": "Bearer " + c.api_key}, json=payload) as response:
            response.raise_for_status()
            chunks = bytearray()
            async for chunk in response.aiter_bytes():
                chunks.extend(chunk)
                if len(chunks) > 65536:
                    raise ValueError("Model response too large")
        import json
        content = json.loads(chunks)["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Invalid model response")
        return content.strip()[:1900]

    async def close(self):
        await self.http.aclose()
