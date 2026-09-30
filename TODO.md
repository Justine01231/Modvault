# ModVault / ModuLab To-Do

## Service & deployment
- [x] Install systemd service (modvault.service) pointing to `/home/justine/Documents/ModVault`
- [x] Remove stale symlink `/home/justine/modulab` (old `📦 ModVault` path)
- [x] `systemctl daemon-reload` and `systemctl enable --now modvault`
- [x] Verify the bot is running (`systemctl status modvault`, check logs)
  - Killed stale instance (`/home/justine/modulab/.venv/...` PID 56890) that was holding the Telegram getUpdates lock and causing a 409 Conflict.
- [x] Install dashboard systemd service (modvault-dashboard.service) → http://localhost:8081 (port = webhook_port + 1, see `app/dashboard/main.py`)
- [x] Verify dashboard is running (`systemctl status modvault-dashboard`, `curl localhost:8081/api/health`)

## Ops reference
- See `OPS.md` for status / restart / run commands and the REST API list.

## Bot features
- [ ] (fill in future feature work here)
