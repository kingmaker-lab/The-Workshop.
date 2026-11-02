# The Workshop Bots for Discord 🐺

Integration MVP 0.1 for **one Discord application** featuring three separate command personas: Heart (technology education), Blade (digital safety) and Gh0st (logic/CTF), plus `/workshop`. All responses are private (*ephemeral*). This app is **not** a bridge from the 4–12 Workshop Kids portal into Discord. The Discord server must follow Discord's local minimum-age rules (13+ in Brazil), and operators should maintain appropriate teen-safety/moderation settings.

## Security architecture

- **HTTPS interactions**, no persistent Gateway client, message-reading intent, Discord DMs, webhook posting permission, administration permission, or access to local `IA/Heart` tools.
- Verify `X-Signature-Ed25519` against the **raw** HTTP body and `X-Signature-Timestamp` within 5 minutes, before parsing JSON. Reject unsigned/invalid requests. Respond to signed PINGs.
- **Guild allowlist is required** (`ALLOWED_GUILD_IDS`). All commands are guild-only. Calls from other servers receive an ephemeral denial.
- Discord never receives a bot token via the Worker. Command registration uses a token only from an operator's shell.
- Input ≤240 characters; request ≤8 KiB; mentions disabled; no hyperlinks echoed from users; no user message database, member tracking, DM support, or score tracking.
- Heart has **curated local responses by default**. Optional Workers AI inference via `ENABLE_AI=true` calls Llama Guard on both input/output, limits topics, prompt, output, and gracefully falls back to curated responses. These heuristics are not complete safety guarantees. Optional inference processes the submitted message at Cloudflare; assess data protection and billable usage before enabling.
- No moderation automation, channel deletion, role changes, age inference, arbitrary remote URL fetch, or code execution.
- Cloudflare-specific global API rate limits and Discord rate limiting should be configured before a large public launch. No in-memory local rate limit is claimed to be global.

## Setup (Discord Developer Portal)

1. Create an application at https://discord.com/developers/applications and copy its **Application ID** and **Public Key**. Do not post a bot token in chat, GitHub or screenshots.
2. Deploy via `cd web/workshop-discord && npx wrangler deploy`, or through the team's Cloudflare automation. Add Worker secrets/configuration: `DISCORD_PUBLIC_KEY` (32-byte hex) and `ALLOWED_GUILD_IDS` (one or more server IDs comma-separated). Recommended `ENABLE_AI=false` initially.
3. In Discord Developer Portal → **General Information** (or the app's Interactions section), set the **Interactions Endpoint URL** to `https://workshop-discord.<your-workers-subdomain>.workers.dev/interactions`. Discord sends signed PING requests to verify it.
4. Install the application to the selected **server** using the `applications.commands` scope. A bot user is **not needed for interactions-only commands**. Guild permission defaults should not grant administrator access. If your installation includes `bot` for other use cases, keep minimal permissions.
5. Register commands for that guild. A bot token can be used **locally** only for command registration: `DISCORD_APPLICATION_ID=... DISCORD_GUILD_ID=... DISCORD_BOT_TOKEN=... node register.mjs`. Do not persist it in repo. Guild commands are quick to iterate. If you register using another OAuth2 method, no bot token needs to be sent to this Worker.
6. Test `/workshop`, `/heart pergunta:O que é um algoritmo?`, `/blade assunto:privacidade`, `/ghost codigo:2`. All answers are ephemeral.

**Optional AI:** After privacy review and budget controls, set `ENABLE_AI=true` as a Worker environment variable, and ensure an AI binding named `AI` exists. If moderation or inference fails, Heart responds with static guidance. Do not connect the Kids API or the local Heart Tool Router to this endpoint.

### Quick test

```bash
node --test tests/*.test.mjs
```

**Status:** deploy can be staged before Discord credentials are set. The `/health` endpoint reports `configured:false` until both required configuration values are present. Actual Discord integration is **not active** until the developer application endpoint, key, guild allowlist, installation, and slash commands are configured. Maintain a human moderation team; Blade gives guidance and is not a substitute for the platform's safety controls or emergency services.