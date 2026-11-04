import os
from dataclasses import dataclass
from urllib.parse import urlparse

NAMES = ("heart", "fake", "argus", "blade")


def ids(value: str) -> frozenset[str]:
    result = frozenset(x.strip() for x in value.split(",") if x.strip())
    if any(not x.isdigit() or not 15 <= len(x) <= 22 for x in result):
        raise ValueError("Discord IDs must be decimal strings")
    return result


def boolean(value: str) -> bool:
    if value not in ("true", "false"):
        raise ValueError("Boolean configuration must be true or false")
    return value == "true"


@dataclass(frozen=True)
class Config:
    mode: str
    guilds: frozenset[str]
    channels: frozenset[str]
    creator: str
    db_path: str
    tokens: dict[str, str]
    api_url: str
    api_key: str
    model: str
    daily_calls: int
    spontaneous: bool
    sync_commands: bool

    @classmethod
    def load(cls, env=None):
        e = os.environ if env is None else env
        mode = e.get("BOT_MODE", "standby")
        if mode not in ("standby", "live"):
            raise ValueError("BOT_MODE must be standby or live")
        guilds, channels = ids(e.get("ALLOWED_GUILD_IDS", "")), ids(e.get("ALLOWED_CHANNEL_IDS", ""))
        creator = e.get("CREATOR_ID", "1171408893780434987")
        if len(ids(creator)) != 1:
            raise ValueError("Exactly one CREATOR_ID required")
        tokens = {n: e.get(f"DISCORD_TOKEN_{n.upper()}", "") for n in NAMES}
        url = e.get("LLM_BASE_URL", "").rstrip("/")
        parsed = urlparse(url)
        if url and (parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.query):
            raise ValueError("LLM_BASE_URL requires an HTTPS API base without credentials or query")
        limit = int(e.get("DAILY_LLM_CALL_LIMIT", "100"))
        if not 1 <= limit <= 10000:
            raise ValueError("DAILY_LLM_CALL_LIMIT outside 1..10000")
        key, model = e.get("LLM_API_KEY", ""), e.get("LLM_MODEL", "")
        if mode == "live" and (not guilds or not channels or not all(tokens.values()) or not url or not key or not model):
            raise ValueError("Live mode requires guild/channel allowlists, four bot tokens and LLM configuration")
        if mode == "live" and len(set(tokens.values())) != 4:
            raise ValueError("Each character requires a distinct Discord application token")
        return cls(mode, guilds, channels, creator, e.get("DATABASE_PATH", "data/alcateia.sqlite"),
                   tokens, url, key, model, limit, boolean(e.get("ENABLE_SPONTANEOUS", "false")),
                   boolean(e.get("SYNC_COMMANDS", "false")))
