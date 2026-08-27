"""Applying schema migrations from inside the app.

Alembic is synchronous and its async env.py opens its own event loop, so the
upgrade runs in a worker thread rather than on the running loop.
"""
import logging
from pathlib import Path

import anyio
from alembic import command
from alembic.config import Config

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent


def config() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    return cfg


def _upgrade() -> None:
    command.upgrade(config(), "head")


async def upgrade_head() -> None:
    log.info("applying database migrations")
    await anyio.to_thread.run_sync(_upgrade)
