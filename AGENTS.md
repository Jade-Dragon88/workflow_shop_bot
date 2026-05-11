# AGENTS.md

## Run the Bot
```bash
python bot.py
```

## Architecture
- **Framework**: aiogram 3.x (async Telegram Bot API)
- **Database**: Supabase (PostgreSQL) via custom HTTP client in `database/supabase_http_client.py`
- **Payments**: ЮKassa via Telegram Payments API
- **Schema**: All tables live in `n8n_workflows_sales` schema
- **State**: In-memory FSM (MemoryStorage) for multi-step admin flows

## Key Files
- `bot.py` — entrypoint, registers routers and middleware
- `handlers/` — one file per feature (start, catalog, payment, admin, support)
- `utils/pricing.py` — Early Bird logic (400₽ first 50 buyers, then 600₽)
- `utils/watermark.py` — adds `license` section to purchased workflows
- `config.py` — all env vars, do NOT hardcode values

## Database Tables
- `workflows` — slug, name, filepath, version, price, priority (1/2/3)
- `purchases` — user_id, workflow_id, payment_id (encrypted), email
- `users` — telegram_id, username, registered_at
- `settings` — key/value (early_bird_counter, early_bird_limit)
- `banned_users` — telegram_id, reason, banned_by

## Important Implementation Notes

### Watermarking
`utils/watermark.py` adds a `license` section to the JSON but does NOT add notes to individual nodes (this is a known gap vs the spec).

### Rate Limiting
`middlewares/ratelimit.py` uses TTL cache but does NOT block users — it only tracks requests. Do not trust it for DDoS protection.

### Empty Files (not implemented)
These exist but are empty:
- `handlers/support.py`
- `utils/filemanager.py`
- `scripts/backup.sh`
- `scripts/cleanup.sh`

### Supabase Client
Uses custom `SupabaseHttpClient` class (not the official SDK). Methods: `select()`, `insert()`, `update()`, `rpc()`. All are async.

## Known Gaps vs Spec
- No `/stats`, `/unban`, `/broadcast` admin commands
- Admin panel has 4 buttons instead of 9
- No `systemd` service file
- No catch-all handler for unrecognized messages
- invite_links table exists but is not used (links created ad-hoc in payment.py)