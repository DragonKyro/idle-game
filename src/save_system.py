"""JSON save/load with offline earnings calculation.

Saves live in the user's home directory under ``.crystal_cavern/save.json``
so running from a read-only install path still works, and so the save
survives cloning the repo elsewhere.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

from src.constants import OFFLINE_CAP_SECONDS, OFFLINE_EFFICIENCY
from src.game_state import GameState


def default_save_path() -> Path:
    """Canonical save location — overridable via $CRYSTAL_CAVERN_SAVE."""
    override = os.environ.get("CRYSTAL_CAVERN_SAVE")
    if override:
        return Path(override)
    return Path.home() / ".crystal_cavern" / "save.json"


def save_game(state: GameState, path: Path | None = None) -> Path:
    """Persist the state atomically. Returns the path written."""
    path = path or default_save_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    state.last_saved_at = time.time()
    payload = state.to_dict()

    # Write-then-rename so a crash mid-write can't corrupt the save.
    # NamedTemporaryFile is used for a unique name; we close it and overwrite
    # via os.replace which is atomic on both POSIX and Windows.
    fd, tmp_name = tempfile.mkstemp(
        prefix="save-", suffix=".json.tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        os.replace(tmp_name, path)
    except Exception:
        # Best-effort cleanup; don't mask the original error.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return path


def load_game(path: Path | None = None) -> GameState | None:
    """Load the save from disk; returns None if there is no save yet."""
    path = path or default_save_path()
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        # Corrupt save — don't crash, just start fresh. The file is left on
        # disk so a player can inspect/repair it if they want.
        return None
    return GameState.from_dict(data)


def apply_offline_earnings(
    state: GameState, now: float | None = None
) -> tuple[float, float]:
    """Credit offline earnings based on `last_saved_at`.

    Returns ``(elapsed_seconds, shards_gained)`` for display in the welcome-
    back banner. Elapsed time is capped by OFFLINE_CAP_SECONDS, and the rate
    is scaled by OFFLINE_EFFICIENCY so active play remains more rewarding.
    """
    if state.last_saved_at <= 0:
        return 0.0, 0.0
    now = now if now is not None else time.time()
    elapsed = max(0.0, now - state.last_saved_at)
    if elapsed <= 0:
        return 0.0, 0.0

    effective = min(elapsed, OFFLINE_CAP_SECONDS) * OFFLINE_EFFICIENCY
    gained = state.total_rate() * effective
    if gained > 0:
        state.shards += gained
        state.total_earned += gained
    # Return the *real* elapsed time (uncapped) so the banner can mention it,
    # but the shards reflect the capped/discounted amount actually credited.
    return elapsed, gained
