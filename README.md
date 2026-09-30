# 🧩 ModuLab — Module Vault

A Telegram-based module distribution platform designed as a small system that can grow into a full web platform. This is the **V0.1 milestone**: `/start`, `/help`, and the `/publish` flow with ZIP parsing and card-style preview.

## Setup

```bash
# 1. Create virtualenv and install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# edit .env -> set BOT_TOKEN, TELEGRAM_CHANNEL_ID, ADMIN_IDS

# 3. Run
python -m app.main
```

## Tests

```bash
source .venv/bin/activate
python -m pytest
```

## V0.1 features

- `/start`, `/help`
- `/publish` (admin only):
  1. Send a Magisk-style module ZIP
  2. Validated (`validation.py`) + parsed (`module_parser.py`)
  3. Pick a category → inline preview card (`formatter.py`)
  4. ✅ Publish / ❌ Cancel
- File metadata (name, size, sha256, telegram_file_id) captured — **no permanent local storage** needed; Telegram's file_id is reused to send later.

## Database (Phase 5b)

SQLite via SQLAlchemy. Tables auto-created on startup, categories seeded.

- `users`, `authors`, `modules`, `releases`, `posts`, `categories`
- Publishing a release persists the module + author + release + post
- Duplicate `module_id`+`version` releases are prevented
- Switch to PostgreSQL later by changing `DATABASE_URL` (e.g. `postgresql+psycopg://...`)

## Templates (Phase 8)

Card styles live in `app/services/templates/` as a small registry + template classes, so visual identity is isolated from the rest of the app.

- `release` — ⚡ release card (module, version, author, compat, sizes, tags)
- `community` — 🔄 community repost with attribution
- `announcement` / `update` / `warning` — 📢 🆕 ⚠️ message cards

Commands: `/announcement`, `/update`, `/warning` (admin) → title + body → preview → publish. All persisted with their own `post_type`.

`/repost` (admin) can repost straight from a Telegram link: paste `t.me/<channel>/<msg>` and the bot fetches the post and reposts it. A single-module post becomes one community card; a post that's a list of items (e.g. `@handle | Github(url)` lines) gets one community card per item — then review before publishing.

## GitHub (Phase 9)

`/release` (admin) → send a repo (`owner/repo` or full URL) → the bot fetches repo + latest release via the GitHub REST API and shows a ⚡ GITHUB RELEASE card → publish.

- Cards include tag, author, description, release notes, first asset (name + size), source link
- Persisted as an official release (module + author + release, with `repository_url`)
- Works on public repos without a token (60 req/hr per IP). Add `GITHUB_TOKEN` in `.env` for a higher rate limit / private repos.

## Structure

```
app/
  config/     settings from .env
  bot/        handlers, callbacks, keyboards, states
  services/   publishing, module_parser, validation, formatter, authorization
  database/   models, engine/session, repositories/
  storage/    (empty — planned)
  templates/  (inside services/) — card style registry
  utils/
tests/        parser, validation, formatter, database
```

## Webhook (GitHub auto-announce)

A FastAPI server (`app/webhook.py`) listens for GitHub webhook events and auto-publishes release cards to the channel — no manual `/release` needed.

**Setup:**
1. Set `WEBHOOK_SECRET` (and optionally `WEBHOOK_PORT`, `AUTO_ANNOUNCE_REPOS`) in `.env`
2. Run the webhook server: `python -m app.webhook`
3. In GitHub → repo → Settings → Webhooks, point the URL to `https://<your-host>/webhook/github`, content type `application/json`, secret = `WEBHOOK_SECRET`, and select the **Releases** event

On a `release: published` event it:
- Verifies the `X-Hub-Signature-256` HMAC signature
- Announces a ⚡ GITHUB RELEASE card to the channel (via Bot API)
- Persists it as an official release + post
- Only announces repos in `AUTO_ANNOUNCE_REPOS` if that list is non-empty

## Dashboard + REST API (Phase 10)

A web dashboard (`app/dashboard/`) with a clean JSON API, built with FastAPI + server-rendered Jinja2 templates.

**Run:** `python -m app.dashboard.main` → http://localhost:8000 (auto-inits the DB)

**Pages:** `/` (home + stats), `/module/{id}` (detail + releases), `/search?q=`, `/categories`

**REST API:**
- `GET /api/modules?limit=&offset=`
- `GET /api/modules/{id}`
- `GET /api/search?q=`
- `GET /api/categories`
- `GET /api/stats`
- `GET /api/health`

The API returns clean JSON (`module_to_dict` serializers) so a future React/SPA frontend can consume it directly.

## Deployment

Three processes, all runnable from this codebase:
- **Bot**: `python -m app.main`
- **Webhook**: `python -m app.webhook`
- **Dashboard**: `python -m app.dashboard.main`

### Docker

A multi-service `docker-compose.yml` runs bot, webhook, and dashboard from one image, sharing a named SQLite volume.

```bash
cp .env.example .env      # fill in BOT_TOKEN, TELEGRAM_CHANNEL_ID, ADMIN_IDS, WEBHOOK_SECRET, etc.
docker compose up --build -d
```

- Bot → Telegram (no published port)
- Webhook → `:8080` (add a reverse proxy for TLS in production)
- Dashboard → `:8000`

Stop with `docker compose down`. Persisted data lives in the `modulab_data` volume.

> Note: all three services share one embedded SQLite file. Fine for single-host/low-traffic and dashboard/webhook read-mostly workloads; move to PostgreSQL for heavier concurrent writes.

## Roadmap

- [x] Phase 0–5b: bot setup, /start, /help, admin check, upload, parser, preview, SQLite DB
- [x] Read commands: /modules, /search, admin /stats
- [x] Phase 7: community /repost with attribution
- [x] Phase 8: templates (release/community/announcement/update/warning)
- [x] Phase 9: GitHub integration (/release + webhook auto-announce)
- [x] Phase 10: web dashboard + REST API
- [x] Deployment: git, Dockerfile, docker-compose
- [ ] Future: React SPA, PostgreSQL production

## Security

- Never commit `.env` (bot token lives there).
- Authorization uses immutable Telegram user IDs (`ADMIN_IDS`), never usernames.
- If the token leaks, regenerate via BotFather immediately.
