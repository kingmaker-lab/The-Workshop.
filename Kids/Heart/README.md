# Workshop Kids | Heart Core v0.1

An interactive, Portuguese-language educational companion for the Workshop Kids mascot.

## What it is

- A **guided chatbot** with curated responses for logic, simple math, robotics, science and basic cyber safety.
- Stateless: user text is processed in a single request, with **no database, conversation history, cookies, localStorage or third-party scripts**.
- The browser only displays responses using textContent; no HTML interpretation of user messages.
- A privacy check rejects common personal details, an immediate-risk check redirects children to trusted adults, and unsafe-topic routing redirects to age-appropriate learning.
- This is **not a generative AI**, a human, a professional counselor or a guaranteed content-safety system.
- This service has **no integration** with the separate local HeartAI project at IA/Heart. Never expose that project's tools or persisted memory to children.

## Run and test

From Kids/Heart:
- Node.js 20+ recommended.
- Run unit and API tests: node --test tests/heart.test.mjs
- Start locally: npx wrangler dev
- Deploy only after privacy/security sign-off: npx wrangler deploy

The worker expects a same-origin HTML asset binding named ASSETS. CORS is not enabled. No generative model is called. There are no API keys.

## Before public launch

1. Review with a child-safety and legal/privacy owner: LGPD Article 14, the ECA Digital (Lei 15.211/2025) and current ANPD guidance.
2. Ensure the service's public privacy notices disclose any Cloudflare operational processing and access logs, which are outside this code. No claim about infrastructure-level non-retention is made.
3. Configure edge rate limiting and abuse monitoring without retaining child chat content. Content moderation here is **rule-based and incomplete**, so use child-safety red-team cases and human review before rollout.
4. Consider a verified parental authorization/supervision flow where required by the chosen product design and lawful basis.
5. Keep outbound links, open web access, user-to-user chat, uploads, telemetry, profiling, advertisements and model-generated responses disabled until separately evaluated.
6. Run accessibility review with assistive technologies and real device tests. Avoid collecting personal data for testing.
7. Deploy as a **separate Worker** and link or embed only after successful release gates; do not overwrite the existing workshop-kids Worker.

## Topics, not unrestricted internet

Suggestions are whitelisted prompts. A child may enter short questions, but the bot only answers supported subjects with fixed teaching content and always shows fallback choices for other topics. It never executes code or tools.

## API

POST /api/chat
Content-Type: application/json
Origin: same-origin

Request: {"message": "Como funciona um robô?"}
Response: {"reply":"...", "options":[{"label":"...","prompt":"..."}], "category":"robotics","bot":"Heart","mode":"guided"}

Input JSON is limited to 1024 UTF-8 bytes, message length to 220 JavaScript characters. There is no data persistence.
