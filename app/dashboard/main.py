from __future__ import annotations

import uvicorn

from app.config.settings import settings


def main() -> None:
    port = settings.webhook_port + 1 if settings.webhook_port else 8000
    uvicorn.run("app.dashboard.app:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
