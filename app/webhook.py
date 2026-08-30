from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.services.auto_announce import announce_release
from app.services.github_client import release_from_payload

logger = logging.getLogger(__name__)

app = FastAPI(title="ModuLab Webhook")


def verify_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not secret:
        return False
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = signature_header.split("=", 1)[1]
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected)


@app.get("/")
async def root():
    return {"status": "ok", "service": "modulab-webhook"}


@app.post("/webhook/github")
async def github_webhook(request: Request):
    body = await request.body()
    event = request.headers.get("X-GitHub-Event", "")
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(settings.webhook_secret, body, signature):
        return JSONResponse({"error": "invalid signature"}, status_code=401)

    if event != "release":
        return JSONResponse({"skipped": True, "reason": "not a release event"})

    payload = await request.json()
    action = payload.get("action")
    if action != "published":
        return JSONResponse({"skipped": True, "reason": f"action={action}"})

    repo_full = (payload.get("repository") or {}).get("full_name", "").lower()
    if settings.auto_announce_repos and repo_full not in settings.auto_announce_repos:
        return JSONResponse(
            {"skipped": True, "reason": f"repo {repo_full} not in allowlist"}
        )

    release = release_from_payload(payload)
    ok, result = await announce_release(release)
    if not ok:
        logger.error("Webhook announce failed: %s", result)
        return JSONResponse({"error": result}, status_code=500)
    logger.info("Webhook announced: %s", result)
    return JSONResponse({"ok": True, "detail": result})


def main() -> None:
    import uvicorn

    if not settings.webhook_secret:
        raise SystemExit(
            "WEBHOOK_SECRET is not set. Configure it in .env to enable the GitHub webhook."
        )
    uvicorn.run("app.webhook:app", host="0.0.0.0", port=settings.webhook_port, reload=False)


if __name__ == "__main__":
    main()
