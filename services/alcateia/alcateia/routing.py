import re
import unicodedata

from .config import NAMES


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if not unicodedata.combining(c))


def explicit_target(text, mentions, bot_ids, reply_bot=None):
    targets = {name for name, uid in bot_ids.items() if uid in mentions}
    match = re.match(r"^\s*(?:oi[,! ]+|ei[,! ]+)?(heart|fake|argus|blade)\b", normalize(text))
    if match:
        targets.add(match[1])
    if not targets and reply_bot in NAMES:
        targets.add(reply_bot)
    return next(iter(targets)) if len(targets) == 1 else None


def casual_target(text):
    """Conservative initial router. Ambiguous/unrecognized messages stay silent."""
    t = normalize(text)
    categories = {
        "argus": r"\b(linux|nginx|docker|python|javascript|git|kernel|arduino|circuito|ctf|dns|codigo|compilador)\b",
        "blade": r"\b(golpe|phishing|invadida|invadido|privacidade|assedio|bullying|senha vazou)\b",
        "heart": r"\b(experimento|descobri|inventar|vulcao|ciencia|curiosidade|bicarbonato)\b",
        "fake": r"\b(bom dia pessoal|boa noite pessoal|ganhamos|vencemos|piada|novidades da workshop)\b",
    }
    hits = [name for name, pattern in categories.items() if re.search(pattern, t)]
    return hits[0] if len(hits) == 1 else None


def feedback(text, name):
    t = normalize(text).strip()
    t = re.sub(r"<@!?\d+>", "", t)
    t = re.sub(rf"^\s*{name}\b[, :]*", "", t).strip(" .!")
    if len(t) > 120 or any(c in t for c in ('"', "'", "`", "\n")):
        return None
    mappings = {
        "responda mais curto": {"length": "curto"},
        "responda mais detalhado": {"length": "detalhado"},
        "responda sem emojis": {"emojis": False},
        "responda com emojis": {"emojis": True},
        "use passo a passo nas respostas": {"steps": True},
        "nao use passo a passo nas respostas": {"steps": False},
    }
    return mappings.get(t.removesuffix(" por favor").strip())
