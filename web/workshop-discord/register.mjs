/** One-time guild slash-command registration; run on an admin machine, NOT in Worker. */
import { commands } from './commands.mjs';
const { DISCORD_APPLICATION_ID: appId, DISCORD_BOT_TOKEN: token, DISCORD_GUILD_ID: guildId } = process.env;
if (!/^\d{16,22}$/.test(appId || '') || !/^\d{16,22}$/.test(guildId || '') || !token) {
  console.error('Configure DISCORD_APPLICATION_ID, DISCORD_GUILD_ID and DISCORD_BOT_TOKEN in your shell (never commit them).');
  process.exitCode = 1;
} else {
  const res = await fetch(`https://discord.com/api/v10/applications/${appId}/guilds/${guildId}/commands`, {
    method: 'PUT', headers: { Authorization: `Bot ${token}`, 'content-type': 'application/json' }, body: JSON.stringify(commands),
  });
  if (!res.ok) { console.error(`Discord registration failed: HTTP ${res.status}`); process.exitCode = 1; }
  else console.log(`Registered ${(await res.json()).length} guild slash commands.`);
}
