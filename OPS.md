# ModVault — Operations & Commands Reference

Quick reference for running, stopping, and restarting the bot and its web services.
Everything here runs from `/home/justine/Documents/ModVault` with the `.venv`.

## Services

| Service | What it does | Systemd unit | Manual run | URL |
|---------|--------------|--------------|------------|-----|
| Bot | Telegram bot (polling) | `modvault.service` | `python -m app.main` | — |
| Dashboard | Web UI + REST API | `modvault-dashboard.service` | `python -m app.dashboard.main` | http://localhost:8081 |
| Webhook | GitHub auto-announce | (not installed) | `python -m app.webhook` | http://localhost:8080 |

> The bot and dashboard run under systemd and auto-restart on failure.
> The webhook is optional (needs `WEBHOOK_SECRET` set in `.env`).

## Status
```bash
systemctl status modvault            # bot
systemctl status modvault-dashboard  # dashboard
journalctl -u modvault -f            # live bot logs
journalctl -u modvault-dashboard -f  # live dashboard logs
```

## Restart after code changes
```bash
sudo systemctl restart modvault            # apply bot code changes
sudo systemctl restart modvault-dashboard  # apply dashboard code changes
```

## Stop / Start
```bash
sudo systemctl stop modvault       # stop the bot
sudo systemctl start modvault      # start it again
sudo systemctl disable modvault    # stop it running at boot
sudo systemctl enable modvault     # re-enable at boot
```
(Same pattern for `modvault-dashboard`.)

## Run manually (for testing, foreground)
Stop the systemd service first — only one instance may poll Telegram at a time
or you get `telegram.error.Conflict: terminated by other getUpdates request`.
```bash
sudo systemctl stop modvault
cd /home/justine/Documents/ModVault
source .venv/bin/activate
python -m app.main            # Ctrl+C to stop
sudo systemctl start modvault # hand it back to systemd when done
```

## Dashboard API (REST)
Base: `http://localhost:8081`
- `GET /api/health`
- `GET /api/stats`
- `GET /api/categories`
- `GET /api/modules?limit=&offset=`
- `GET /api/modules/{id}`
- `GET /api/search?q=`

## Discussion group
The channel is announcement-only. Users can chat and use public commands in a
separate discussion group.

- Add the bot to the group, then get the group's chat ID via `/debug` in the group.
- Put that ID in `.env` as `DISCUSSION_GROUP_ID=<id>`.
- Restart the bot after changing `.env`: `sudo systemctl restart modvault`.

User commands available in the group: `/start`, `/help`, `/modules`, `/search <query>`.
Admin/publishing commands stay private (DM only).
