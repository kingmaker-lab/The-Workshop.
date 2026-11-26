"""Fluxo local de controle de configuração do CERBERUS."""
import hashlib
import hmac
import json
import sqlite3
from contextlib import closing, contextmanager

MAX_BYTES = 65536
MAX_GENERATION = 2**63 - 1
POLICY_FIELDS = {
    "maintenance": (bool, None, None),
    "max_connections": (int, 1, 10000),
}


class Rejected(ValueError):
    """Operação recusada pelo CERBERUS."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def read_json(stream):
    data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise Rejected("documento excede 64 KiB")

    def unique_fields(pairs):
        result = {}
        for name, value in pairs:
            if name in result:
                raise Rejected("campo JSON duplicado")
            result[name] = value
        return result

    return json.loads(data.decode("utf-8"), object_pairs_hook=unique_fields)


def validate_policy(policy):
    if type(policy) is not dict or policy.keys() != POLICY_FIELDS.keys():
        raise Rejected("campos de política inválidos")
    for field, (kind, minimum, maximum) in POLICY_FIELDS.items():
        value = policy[field]
        if type(value) is not kind:
            raise Rejected(f"tipo inválido em {field}")
        if minimum is not None and not minimum <= value <= maximum:
            raise Rejected(f"valor fora dos limites em {field}")


def sign(key, domain, value):
    return hmac.new(key, domain + b"\0" + canonical(value), hashlib.sha256).hexdigest()


def seal(key, expected, policy):
    validate_policy(policy)
    if type(expected) is not int or not 0 <= expected < MAX_GENERATION:
        raise Rejected("geração esperada inválida")
    body = {"expected": expected, "policy": policy}
    return {**body, "mac": sign(key, b"change-v1", body)}


def authenticate(key, envelope):
    if type(envelope) is not dict or envelope.keys() != {"expected", "policy", "mac"}:
        raise Rejected("envelope inválido")
    signed = seal(key, envelope["expected"], envelope["policy"])
    mac = envelope["mac"]
    if type(mac) is not str or len(mac) != 64 or not mac.isascii():
        raise Rejected("autenticação recusada")
    if not hmac.compare_digest(signed["mac"], mac):
        raise Rejected("autenticação recusada")
    return signed


@contextmanager
def database(path, *, create=False):
    # URI codifica caracteres reservados presentes no caminho informado.
    mode = "rwc" if create else "rw"
    with closing(sqlite3.connect(f"{path.resolve().as_uri()}?mode={mode}", uri=True,
                                timeout=2, isolation_level=None)) as db:
        db.execute("PRAGMA synchronous = FULL")
        db.execute("BEGIN IMMEDIATE")
        try:
            yield db
        except BaseException:
            db.rollback()
            raise
        else:
            db.commit()


def initialize(path, key):
    with database(path, create=True) as db:
        db.execute("""CREATE TABLE revisions (
            generation INTEGER PRIMARY KEY CHECK (generation >= 0),
            policy TEXT NOT NULL,
            action TEXT NOT NULL CHECK (action IN ('init', 'apply', 'restore')),
            source INTEGER REFERENCES revisions(generation),
            mac TEXT NOT NULL
        )""")
        return record(db, key, 0, {"maintenance": False, "max_connections": 100}, "init")


def record(db, key, generation, policy, action, source=None):
    if generation > MAX_GENERATION:
        raise Rejected("limite de gerações atingido")
    state = {"generation": generation, "policy": policy, "action": action, "source": source}
    db.execute("INSERT INTO revisions VALUES (?, ?, ?, ?, ?)",
               (generation, canonical(policy).decode("ascii"), action, source,
                sign(key, b"revision-v1", state)))
    return state


def load(db, key, generation=None):
    if generation is None:
        row = db.execute("SELECT * FROM revisions ORDER BY generation DESC LIMIT 1").fetchone()
    else:
        row = db.execute("SELECT * FROM revisions WHERE generation = ?", (generation,)).fetchone()
    if row is None:
        raise Rejected("revisão indisponível")
    number, payload, action, source, mac = row
    policy = json.loads(payload)
    validate_policy(policy)
    state = {"generation": number, "policy": policy, "action": action, "source": source}
    if type(mac) is not str or not mac.isascii():
        raise Rejected("integridade da revisão inválida")
    if not hmac.compare_digest(sign(key, b"revision-v1", state), mac):
        raise Rejected("integridade da revisão inválida")
    return state


def status(path, key):
    with database(path) as db:
        return load(db, key)


def apply(path, key, envelope):
    change = authenticate(key, envelope)
    with database(path) as db:
        current = load(db, key)
        if change["expected"] != current["generation"]:
            raise Rejected("geração esperada diverge do estado ativo")
        return record(db, key, current["generation"] + 1, change["policy"], "apply")


def restore(path, key, target, expected):
    with database(path) as db:
        current = load(db, key)
        if expected != current["generation"]:
            raise Rejected("geração esperada diverge do estado ativo")
        if not 0 <= target < expected <= MAX_GENERATION:
            raise Rejected("a recuperação exige uma geração anterior")
        previous = load(db, key, target)
        return record(db, key, expected + 1, previous["policy"], "restore", target)
