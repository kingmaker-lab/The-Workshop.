import asyncio
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from alcateia.config import NAMES, Config
from alcateia.runtime import Character, Coordinator
from alcateia.store import Store

GUILD, CHANNEL = "1517703588791582821", "1517703589244571698"


class Typing:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


def message(content, event="1", user="10", bot=False, guild=GUILD, channel=CHANNEL):
    return SimpleNamespace(
        id=event, content=content, guild=SimpleNamespace(id=guild) if guild else None,
        channel=SimpleNamespace(id=channel, typing=Typing),
        author=SimpleNamespace(id=user, bot=bot), webhook_id=None, mentions=[], reference=None,
        reply=AsyncMock(),
    )


@pytest.fixture
def coordinator(tmp_path):
    config = replace(Config.load({}), guilds=frozenset([GUILD]), channels=frozenset([CHANNEL]), spontaneous=True)
    store = Store(str(tmp_path / "runtime.sqlite"))
    model = SimpleNamespace(answer=AsyncMock(return_value="Resposta"))
    co = Coordinator(config, store, model)
    co.clients = {n: SimpleNamespace(user=SimpleNamespace(id=str(100 + i)), is_ready=lambda: True)
                  for i, n in enumerate(NAMES)}
    yield co
    store.close()


def test_four_gateway_copies_produce_one_answer(coordinator):
    async def run():
        msg = message("meu nginx não sobe")
        await asyncio.gather(*(coordinator.handle(n, msg) for n in NAMES))
        await coordinator.handle("argus", msg)  # Duplicate delivery.
        assert coordinator.model.answer.await_count == 1
        assert msg.reply.await_count == 1
        kwargs = msg.reply.call_args.kwargs
        assert not kwargs["mention_author"]
        assert not kwargs["allowed_mentions"].everyone
    asyncio.run(run())


@pytest.mark.parametrize("kwargs", [{"bot": True}, {"guild": None}, {"guild": "other"}, {"channel": "other"}])
def test_untrusted_surfaces_do_not_call_ai(coordinator, kwargs):
    asyncio.run(coordinator.handle("argus", message("argus, ajuda", **kwargs)))
    coordinator.model.answer.assert_not_awaited()


def test_preferences_and_no_incidental_learning(coordinator):
    async def run():
        msg = message("argus, responda mais curto")
        await coordinator.handle("argus", msg)
        assert coordinator.store.get_style("argus", GUILD, "10")[0]["length"] == "curto"
        coordinator.model.answer.assert_not_awaited()
        other = message("responda mais curto", event="2", user="20")
        await coordinator.handle("argus", other)
        assert not coordinator.store.get_style("argus", GUILD, "20")[1]
    asyncio.run(run())


def test_no_reply_when_a_sibling_is_offline(coordinator):
    coordinator.clients["heart"].is_ready = lambda: False
    asyncio.run(coordinator.handle("argus", message("argus, ajuda")))
    coordinator.model.answer.assert_not_awaited()


def test_explicit_failure_has_safe_fallback(coordinator):
    coordinator.model.answer.side_effect = RuntimeError("secret must not be logged")

    async def run():
        msg = message("argus, ajuda")
        await coordinator.handle("argus", msg)
        assert "indisponível" in msg.reply.call_args.args[0]
        assert not coordinator.inflight
    asyncio.run(run())


def test_commands_construct_without_discord_network(coordinator):
    async def run():
        for name in NAMES:
            client = Character(name, coordinator)
            assert client.tree.get_command("alcateia") is not None
            assert client.intents.message_content
            assert not client.intents.members
            assert not client.intents.presences
            await client.close()
    asyncio.run(run())
