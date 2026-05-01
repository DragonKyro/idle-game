"""Unit tests for save/load + offline earnings."""

from __future__ import annotations

import json
import math

import pytest

from src.constants import OFFLINE_CAP_SECONDS, OFFLINE_EFFICIENCY
from src.game_state import GameState
from src.generators import GENERATORS
from src.save_system import apply_offline_earnings, load_game, save_game


@pytest.fixture
def save_path(tmp_path, monkeypatch):
    path = tmp_path / "save.json"
    monkeypatch.setenv("CRYSTAL_CAVERN_SAVE", str(path))
    return path


def test_load_returns_none_when_no_save(save_path):
    assert load_game() is None


def test_save_then_load_round_trip(save_path):
    state = GameState(shards=42, total_earned=100, total_clicks=3)
    state.owned["rusty_pickaxe"] = 4
    state.purchased_upgrades.add("click_gloves")

    save_game(state)
    loaded = load_game()
    assert loaded is not None
    assert loaded.shards == 42
    assert loaded.owned == {"rusty_pickaxe": 4}
    assert loaded.purchased_upgrades == {"click_gloves"}


def test_save_is_atomic_no_leftover_temp_files(save_path):
    state = GameState(shards=1)
    save_game(state)
    leftovers = [p for p in save_path.parent.iterdir() if p.suffix == ".tmp"]
    assert leftovers == []


def test_load_handles_corrupt_save(save_path):
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text("this is not json {{{", encoding="utf-8")
    assert load_game() is None  # doesn't crash


def test_offline_earnings_credits_capped_and_discounted(save_path):
    state = GameState()
    gen = GENERATORS[0]
    state.owned[gen.key] = 10
    rate = state.total_rate()
    assert rate > 0

    # Pretend we saved an hour ago.
    one_hour = 3600.0
    state.last_saved_at = 1_000_000.0
    elapsed, gained = apply_offline_earnings(state, now=1_000_000.0 + one_hour)

    assert math.isclose(elapsed, one_hour)
    expected = rate * one_hour * OFFLINE_EFFICIENCY
    assert math.isclose(gained, expected, rel_tol=1e-9)
    assert math.isclose(state.shards, expected, rel_tol=1e-9)


def test_offline_earnings_are_capped(save_path):
    state = GameState()
    gen = GENERATORS[0]
    state.owned[gen.key] = 10
    rate = state.total_rate()

    long_away = OFFLINE_CAP_SECONDS * 5  # 5x the cap
    state.last_saved_at = 1_000_000.0
    elapsed, gained = apply_offline_earnings(
        state, now=1_000_000.0 + long_away
    )

    # Elapsed is the real time; gained is capped.
    assert math.isclose(elapsed, long_away)
    expected = rate * OFFLINE_CAP_SECONDS * OFFLINE_EFFICIENCY
    assert math.isclose(gained, expected, rel_tol=1e-9)


def test_offline_earnings_zero_when_no_previous_save(save_path):
    state = GameState()
    state.owned[GENERATORS[0].key] = 10
    elapsed, gained = apply_offline_earnings(state, now=1_000_000.0)
    assert elapsed == 0.0
    assert gained == 0.0


def test_save_file_is_valid_json(save_path):
    state = GameState(shards=7)
    save_game(state)
    data = json.loads(save_path.read_text(encoding="utf-8"))
    assert data["shards"] == 7
    assert data["version"] == 1
