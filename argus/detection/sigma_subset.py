"""ARGUS v0.4: explicitly limited, fail-closed Sigma-shaped rule evaluator.

This is NOT pySigma and does not claim full Sigma interoperability. Only
the documented ARGUS-normalized logsource, selector, modifier and condition
subset is accepted. Never execute or interpret arbitrary expressions.
"""
from __future__ import annotations

import fnmatch
import math
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from yaml.tokens import AliasToken, AnchorToken

from argus.models.alert import Detection
from argus.models.event import Event

# Explicit mapping, not a generic query language.
FIELD_MAP = {
    "User": "user",
    "Result": "result",
    "SourceIp": "src_ip",
    "Source": "source",
    "Message": "message",
    "Service": "service",
    "Protocol": "protocol",
    "DestinationIp": "destination_ip",
    "DestinationPort": "destination_port",
    "OrigBytes": "orig_bytes",
    "RespBytes": "resp_bytes",
    "Duration": "duration",
}
LEVELS = {"low": 10, "medium": 25, "high": 55, "critical": 80}
ALLOWED_LOGSOURCES = {"authentication", "network_connection"}
MAX_RULES = 32
MAX_RULE_BYTES = 32_768
MAX_SELECTORS = 16
MAX_CONDITION_TOKENS = 64
_NAME = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
_TOKEN = re.compile(r"\s*(\(|\)|[a-z][a-z0-9_]*\*?|1)")

class SigmaSubsetError(ValueError):
    """Unrecognized, ambiguous, or unsafe rule construct."""


class _StrictLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise SigmaSubsetError("mapping required")
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise SigmaSubsetError("all YAML mapping keys must be strings")
            if key in result:
                raise SigmaSubsetError("duplicate YAML key")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _load_yaml(raw: bytes) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
        if any(isinstance(token, (AliasToken, AnchorToken)) for token in yaml.scan(text)):
            raise SigmaSubsetError("YAML anchors and aliases are unsupported")
        document = yaml.load(text, Loader=_StrictLoader)
    except (UnicodeError, yaml.YAMLError, RecursionError) as error:
        raise SigmaSubsetError("invalid or unsafe Sigma YAML") from error
    if not isinstance(document, dict):
        raise SigmaSubsetError("Sigma rule must be a YAML mapping")
    return document


def _parse_condition(expression: str, names: tuple[str, ...]) -> tuple:
    """Small recursive-descent parser for selectors, boolean groups, and of-patterns."""
    if not isinstance(expression, str) or len(expression) > 256:
        raise SigmaSubsetError("condition must be a short string")
    tokens: list[str] = []
    position = 0
    while position < len(expression):
        match = _TOKEN.match(expression, position)
        if not match:
            if expression[position:].isspace():
                break
            raise SigmaSubsetError("unsupported Sigma condition syntax")
        tokens.append(match.group(1))
        position = match.end()
        if len(tokens) > MAX_CONDITION_TOKENS:
            raise SigmaSubsetError("condition exceeds complexity limit")
    if not tokens:
        raise SigmaSubsetError("empty condition")

    cursor = 0

    def take(expected: str | None = None) -> str:
        nonlocal cursor
        if cursor >= len(tokens):
            raise SigmaSubsetError("incomplete condition")
        value = tokens[cursor]
        if expected is not None and value != expected:
            raise SigmaSubsetError("unexpected condition operator")
        cursor += 1
        return value

    def atom() -> tuple:
        if cursor >= len(tokens):
            raise SigmaSubsetError("incomplete condition")
        if tokens[cursor] == "(":
            take("(")
            result = disjunction()
            take(")")
            return result
        first = take()
        if first in ("1", "all"):
            take("of")
            pattern = take()
            if pattern == "them":
                selected = names
            elif pattern.endswith("*") and _NAME.fullmatch(pattern[:-1]):
                selected = tuple(name for name in names if fnmatch.fnmatchcase(name, pattern))
            else:
                raise SigmaSubsetError("only '1/all of them' and prefix_* patterns supported")
            if not selected:
                raise SigmaSubsetError("condition pattern matches no selectors")
            op = "or" if first == "1" else "and"
            tree = ("selector", selected[0])
            for name in selected[1:]:
                tree = (op, tree, ("selector", name))
            return tree
        if first not in names:
            raise SigmaSubsetError("unknown or unsupported selector")
        return ("selector", first)

    def negation() -> tuple:
        if cursor < len(tokens) and tokens[cursor] == "not":
            take("not")
            return ("not", negation())
        return atom()

    def conjunction() -> tuple:
        result = negation()
        while cursor < len(tokens) and tokens[cursor] == "and":
            take("and")
            result = ("and", result, negation())
        return result

    def disjunction() -> tuple:
        result = conjunction()
        while cursor < len(tokens) and tokens[cursor] == "or":
            take("or")
            result = ("or", result, conjunction())
        return result

    result = disjunction()
    def has_positive(tree: tuple, negated: bool = False) -> bool:
        if tree[0] == "selector":
            return not negated
        if tree[0] == "not":
            return has_positive(tree[1], not negated)
        return has_positive(tree[1], negated) or has_positive(tree[2], negated)
    if not has_positive(result):
        raise SigmaSubsetError("condition needs a positive selector")
    if cursor != len(tokens):
        raise SigmaSubsetError("unsupported trailing condition")
    return result


@dataclass(frozen=True)
class _FieldTest:
    field: str
    modifier: str
    values: tuple[str | int | float | bool, ...]

    def matches(self, event: Event) -> bool:
        actual = event.value(self.field)
        if actual is None or isinstance(actual, (list, tuple, dict)):
            return False
        for expected in self.values:
            if self.modifier == "exact" and type(actual) is type(expected) and actual == expected:
                return True
            if isinstance(actual, str) and isinstance(expected, str):
                text, needle = actual.casefold(), expected.casefold()
                if self.modifier == "exact" and text == needle:
                    return True
                if self.modifier == "contains" and needle in text:
                    return True
                if self.modifier == "startswith" and text.startswith(needle):
                    return True
                if self.modifier == "endswith" and text.endswith(needle):
                    return True
        return False


@dataclass(frozen=True)
class SigmaSubsetRule:
    title: str
    identifier: str
    logsource: str
    level: str
    selectors: dict[str, tuple[tuple[_FieldTest, ...], ...]]
    condition: tuple

    def matches(self, event: Event) -> bool:
        if event.event_type != self.logsource:
            return False

        def evaluate(tree: tuple) -> bool:
            op = tree[0]
            if op == "selector":
                # OR between selector mapping alternatives, AND within a mapping.
                return any(all(field.matches(event) for field in alternative)
                           for alternative in self.selectors[tree[1]])
            if op == "not":
                return not evaluate(tree[1])
            if op == "and":
                return evaluate(tree[1]) and evaluate(tree[2])
            if op == "or":
                return evaluate(tree[1]) or evaluate(tree[2])
            raise AssertionError("unreachable Sigma condition")

        return evaluate(self.condition)


def parse_sigma_subset(raw: bytes) -> SigmaSubsetRule:
    if len(raw) > MAX_RULE_BYTES:
        raise SigmaSubsetError("Sigma rule file exceeds byte limit")
    document = _load_yaml(raw)
    for key in ("title", "logsource", "detection"):
        if key not in document:
            raise SigmaSubsetError("required Sigma rule attribute missing")
    title = document["title"]
    if not isinstance(title, str) or not 1 <= len(title) <= 120:
        raise SigmaSubsetError("invalid Sigma title")
    identifier = document.get("id", title)
    if not isinstance(identifier, str) or not 1 <= len(identifier) <= 120:
        raise SigmaSubsetError("invalid Sigma id")
    level = document.get("level", "medium")
    if level not in LEVELS:
        raise SigmaSubsetError("unsupported Sigma level")
    logsource = document["logsource"]
    if not isinstance(logsource, dict) or set(logsource) != {"product", "category"}:
        raise SigmaSubsetError("logsource must specify only product: argus and category")
    if logsource.get("product") != "argus" or logsource.get("category") not in ALLOWED_LOGSOURCES:
        raise SigmaSubsetError("unsupported logsource for normalized ARGUS events")
    detection = document["detection"]
    if not isinstance(detection, dict) or len(detection) > MAX_SELECTORS + 1:
        raise SigmaSubsetError("invalid or excessive detection selectors")
    if "condition" not in detection:
        raise SigmaSubsetError("Sigma condition missing")
    selectors: dict[str, tuple[tuple[_FieldTest, ...], ...]] = {}
    for name, body in detection.items():
        if name == "condition":
            continue
        if not isinstance(name, str) or not _NAME.fullmatch(name) or name in (
            "and", "or", "not", "all", "of", "them"):
            raise SigmaSubsetError("invalid selection identifier")
        variants = body if isinstance(body, list) else [body]
        if not variants or len(variants) > 8:
            raise SigmaSubsetError("invalid selector alternatives")
        alternatives = []
        for variant in variants:
            if not isinstance(variant, dict) or not 1 <= len(variant) <= 12:
                raise SigmaSubsetError("selectors must contain field mappings")
            tests = []
            for key, value in variant.items():
                if not isinstance(key, str):
                    raise SigmaSubsetError("invalid field name")
                segments = key.split("|")
                if len(segments) > 2 or segments[0] not in FIELD_MAP:
                    raise SigmaSubsetError("unmapped Sigma field")
                modifier = segments[1] if len(segments) == 2 else "exact"
                if modifier not in {"exact", "contains", "startswith", "endswith"}:
                    raise SigmaSubsetError("unsupported Sigma field modifier")
                choices = value if isinstance(value, list) else [value]
                if not 1 <= len(choices) <= 16:
                    raise SigmaSubsetError("invalid value alternatives")
                for item in choices:
                    if type(item) not in (str, int, float, bool):
                        raise SigmaSubsetError("unsupported selector value type")
                    if isinstance(item, str) and (not item or len(item) > 512 or
                                                 "*" in item or "?" in item or "\\" in item):
                        raise SigmaSubsetError("wildcards and escaping are not supported")
                    if isinstance(item, float) and not math.isfinite(item):
                        raise SigmaSubsetError("non-finite numeric selector is unsupported")
                    if modifier != "exact" and not isinstance(item, str):
                        raise SigmaSubsetError("string modifier needs string values")
                tests.append(_FieldTest(FIELD_MAP[segments[0]], modifier, tuple(choices)))
            alternatives.append(tuple(tests))
        selectors[name] = tuple(alternatives)
    if not selectors:
        raise SigmaSubsetError("at least one detection selector required")
    condition = _parse_condition(detection["condition"], tuple(selectors))
    return SigmaSubsetRule(title, identifier, logsource["category"], level, selectors, condition)


class SigmaSubsetEngine:
    def __init__(self, rules: tuple[SigmaSubsetRule, ...]):
        self.rules = rules

    @classmethod
    def from_directory(cls, location: str | Path) -> "SigmaSubsetEngine":
        directory = Path(location)
        if directory.is_symlink() or not directory.is_dir():
            raise SigmaSubsetError("Sigma rules directory must be a real directory")
        entries = tuple(directory.iterdir())
        files = sorted(p for p in entries if p.suffix.lower() in (".yml", ".yaml"))
        if any(p.is_dir() or p.is_symlink() for p in entries):
            raise SigmaSubsetError("nested directories and symlinks are unsupported")
        if not files or len(files) > MAX_RULES:
            raise SigmaSubsetError("Sigma rule count outside supported range")
        rules = []
        seen = set()
        for file in files:
            if file.is_symlink():
                raise SigmaSubsetError("Sigma rule symlinks are forbidden")
            metadata = file.stat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_RULE_BYTES:
                raise SigmaSubsetError("Sigma rule must be a small regular file")
            with file.open("rb") as handle:
                raw = handle.read(MAX_RULE_BYTES + 1)
            rule = parse_sigma_subset(raw)
            if rule.identifier in seen:
                raise SigmaSubsetError("duplicate Sigma rule ID")
            seen.add(rule.identifier)
            rules.append(rule)
        return cls(tuple(rules))

    def evaluate(self, event: Event) -> list[Detection]:
        return [
            Detection(
                name="sigma:" + rule.identifier,
                severity=rule.level,
                score=LEVELS[rule.level],
                event_id=event.event_id,
                timestamp=event.to_dict()["timestamp"],
                src_ip=event.src_ip,
                details={"engine": "sigma_subset_v04", "title": rule.title,
                         "rule_id": rule.identifier, "logsource": rule.logsource},
            )
            for rule in self.rules if rule.matches(event)
        ]
