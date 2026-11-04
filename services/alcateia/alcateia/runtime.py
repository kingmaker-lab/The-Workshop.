import asyncio
import logging
import time

import discord
from discord import app_commands

from .config import NAMES
from .personas import ACTIVITIES
from .routing import casual_target, explicit_target, feedback

log = logging.getLogger("alcateia")


class Coordinator:
    def __init__(self, config, store, model):
        self.config, self.store, self.model = config, store, model
        self.clients = {}
        self.inflight = set()
        self.stats = {"answered": 0, "failed": 0, "limited": 0}

    @property
    def bot_ids(self):
        return {name: str(client.user.id) for name, client in self.clients.items() if client.user}

    async def handle(self, source, message):
        c = self.config
        if not message.guild or message.author.bot or message.webhook_id:
            return
        guild, channel, user = str(message.guild.id), str(message.channel.id), str(message.author.id)
        if guild not in c.guilds or channel not in c.channels or not message.content or len(message.content) > 2000:
            return
        if len(self.bot_ids) != 4 or any(not x.is_ready() for x in self.clients.values()):
            return
        mentions = {str(x.id) for x in message.mentions}
        reply_bot = None
        if message.reference:
            original = message.reference.resolved
            if not isinstance(original, discord.Message):
                try:
                    original = await message.channel.fetch_message(message.reference.message_id)
                except discord.HTTPException:
                    return
            reply_bot = next((n for n, uid in self.bot_ids.items() if uid == str(original.author.id)), None)
            if reply_bot is None:
                return  # Do not interrupt replies to humans or unrelated bots.
        target = explicit_target(message.content, mentions, self.bot_ids, reply_bot)
        directed = target is not None
        if not target:
            if not c.spontaneous or mentions or message.reference:
                return
            # No intervention in greetings explicitly addressed to a named person.
            if "," in message.content[:40] and "pessoal" not in message.content.lower():
                return
            target = casual_target(message.content)
        if target is None:
            return
        # The chosen client's copy alone handles the message: correct identity and channel permissions.
        if source != target or not self.store.claim(str(message.id)):
            return
        key = (guild, channel, user)
        if key in self.inflight or len(self.inflight) >= 4:
            return
        patch = feedback(message.content, target) if directed else None
        if patch:
            saved = self.store.set_style(target, guild, user, patch)
            text = ("Preferência salva neste servidor por até 90 dias sem atualização. "
                    "Isso não treina o modelo. Consulte /alcateia estilo." if saved else
                    "Adaptação desativada. Para reativar, use /alcateia estilo.")
            await message.reply(text, mention_author=False, allowed_mentions=discord.AllowedMentions.none())
            return
        if not self.store.reserve(guild, channel, user, not directed, c.daily_calls):
            self.stats["limited"] += 1
            return
        self.inflight.add(key)
        try:
            style, _ = self.store.get_style(target, guild, user)
            async with message.channel.typing():
                answer = await self.model.answer(target, user, message.content, style)
            await message.reply(answer, mention_author=False, allowed_mentions=discord.AllowedMentions.none())
            self.stats["answered"] += 1
        except Exception as exc:  # noqa: BLE001 -- redact provider/Discord errors
            # Exception messages can contain provider request bodies / secrets. Log type only.
            log.warning("answer_failed type=%s", type(exc).__name__)
            self.stats["failed"] += 1
            if directed:
                await message.reply("Minha bancada está indisponível agora. Tente novamente em instantes.",
                                    mention_author=False, allowed_mentions=discord.AllowedMentions.none())
        finally:
            self.inflight.discard(key)


class Character(discord.Client):
    def __init__(self, name, coordinator):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.guild_messages = True
        intents.message_content = True
        super().__init__(intents=intents, allowed_mentions=discord.AllowedMentions.none(), max_messages=100)
        self.name, self.coordinator = name, coordinator
        self.tree = app_commands.CommandTree(self)
        self.tasks = []
        group = app_commands.Group(name="alcateia", description="Preferências e informações deste personagem")

        @group.command(name="estilo", description="Ver, configurar ou apagar suas preferências neste servidor")
        @app_commands.choices(acao=[app_commands.Choice(name=n, value=n) for n in
                                   ("ver", "ativar", "desativar", "apagar", "configurar")],
                              tamanho=[app_commands.Choice(name=n, value=n) for n in ("curto", "normal", "detalhado")])
        async def estilo(interaction: discord.Interaction, acao: str = "ver", tamanho: str | None = None,
                         emojis: bool | None = None, passos: bool | None = None):
            c, store = coordinator.config, coordinator.store
            guild, user = str(interaction.guild_id), str(interaction.user.id)
            if guild not in c.guilds:
                await interaction.response.send_message("Disponível somente nos servidores configurados.", ephemeral=True)
                return
            key = (name, guild, user)
            if acao in ("desativar", "apagar"):
                store.erase_style(*key)
                text = "Preferências apagadas e adaptação desativada. Resta somente o marcador de desativação."
            elif acao in ("ativar", "configurar"):
                patch = {k: v for k, v in (("length", tamanho), ("emojis", emojis), ("steps", passos)) if v is not None}
                store.set_style(*key, patch, activate=True)
                text = "Adaptação ativada. Só essas preferências serão guardadas por até 90 dias sem atualização."
            elif acao == "ver":
                style, enabled = store.get_style(*key)
                text = f"Adaptação ativa: {enabled}. Preferências efetivas: {style}. Não há treinamento neural nem histórico persistente."
            else:
                text = "Ação inválida."
            await interaction.response.send_message(text, ephemeral=True)

        @group.command(name="ajuda", description="Conheça os recursos desta versão")
        async def ajuda(interaction: discord.Interaction):
            await interaction.response.send_message(
                f"Sou {name.title()}. Converse comigo pelo nome ou menção. /alcateia estilo controla preferências. "
                "Sou uma IA; a mensagem atual vai ao provedor configurado. Não envie segredos. "
                "Não guardo histórico de conversa. Jogos do camelBots ainda não foram migrados.", ephemeral=True)

        self.tree.add_command(group)

    async def setup_hook(self):
        if self.coordinator.config.sync_commands:
            for guild in self.coordinator.config.guilds:
                obj = discord.Object(id=int(guild))
                self.tree.copy_global_to(guild=obj)
                # Only run during staged app setup. Sync replaces the application's guild command set.
                await self.tree.sync(guild=obj)
        self.tasks.append(asyncio.create_task(self.presence_loop()))

    async def presence_loop(self):
        await self.wait_until_ready()
        while not self.is_closed():
            choices = ACTIVITIES[self.name]
            activity = choices[int(time.time() // 900) % len(choices)]
            try:
                await self.change_presence(activity=discord.Game(name=activity))
            except discord.HTTPException:
                log.warning("presence_failed bot=%s", self.name)
            await asyncio.sleep(900)

    async def on_message(self, message):
        try:
            await self.coordinator.handle(self.name, message)
        except Exception as exc:  # noqa: BLE001 -- redact provider/Discord errors
            log.warning("event_failed bot=%s type=%s", self.name, type(exc).__name__)

    async def on_error(self, event_method, *args, **kwargs):
        log.error("discord_event_failed bot=%s event=%s", self.name, event_method)

    async def on_ready(self):
        log.info("discord_ready bot=%s", self.name)

    async def close(self):
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        await super().close()


async def run_clients(coordinator, stop):
    for name in NAMES:
        coordinator.clients[name] = Character(name, coordinator)
    tasks = [asyncio.create_task(client.start(coordinator.config.tokens[name]))
             for name, client in coordinator.clients.items()]
    stop_task = asyncio.create_task(stop.wait())
    try:
        done, _ = await asyncio.wait([*tasks, stop_task], return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task is not stop_task:
                task.result()  # Fail whole service if one character cannot connect.
                raise RuntimeError("Discord client stopped unexpectedly")
    finally:
        await asyncio.gather(*(client.close() for client in coordinator.clients.values()), return_exceptions=True)
        for task in [*tasks, stop_task]:
            task.cancel()
        await asyncio.gather(*tasks, stop_task, return_exceptions=True)
