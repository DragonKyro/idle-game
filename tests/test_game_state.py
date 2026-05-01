"""Unit tests for GameState."""

from __future__ import annotations

import math

from src.game_state import GameState
from src.generators import GENERATORS, GENERATORS_BY_KEY
from src.upgrades import UPGRADES_BY_KEY


def test_click_grants_one_shard_by_default():
    state = GameState()
    gained = state.click()
    assert gained == 1
    assert state.shards == 1
    assert state.total_earned == 1
    assert state.total_clicks == 1


def test_tick_adds_idle_production():
    state = GameState(shards=0)
    gen = GENERATORS[0]
    state.owned[gen.key] = 10
    expected = state.generator_total_rate(gen) * 2.0
    gained = state.tick(2.0)
    assert math.isclose(gained, expected)
    assert math.isclose(state.shards, expected)


def test_buy_generator_deducts_cost_and_increments_owned():
    state = GameState(shards=100)
    gen = GENERATORS[0]
    assert state.buy_generator(gen) is True
    assert state.owned[gen.key] == 1
    # Cost went up for the next purchase.
    assert state.shards < 100


def test_buy_generator_fails_when_broke():
    state = GameState(shards=0)
    gen = GENERATORS[0]
    assert state.buy_generator(gen) is False
    assert state.owned.get(gen.key, 0) == 0


def test_upgrades_require_prerequisite_owned_count():
    state = GameState(shards=10_000)
    # "click_gloves" requires 1 rusty pickaxe.
    assert not state.is_upgrade_visible("click_gloves")
    state.owned["rusty_pickaxe"] = 1
    assert state.is_upgrade_visible("click_gloves")


def test_click_upgrade_multiplies_click_power():
    state = GameState(shards=10_000)
    state.owned["rusty_pickaxe"] = 1
    base = state.click_power()
    upgrade = UPGRADES_BY_KEY["click_gloves"]
    assert state.buy_upgrade(upgrade.key)
    assert math.isclose(state.click_power(), base * upgrade.multiplier)


def test_generator_upgrade_multiplies_that_generators_rate():
    state = GameState(shards=1_000_000)
    gen = GENERATORS_BY_KEY["rusty_pickaxe"]
    state.owned[gen.key] = 10
    base_rate = state.generator_rate(gen)
    upgrade = UPGRADES_BY_KEY["pickaxe_honed"]
    assert state.buy_upgrade(upgrade.key)
    assert math.isclose(
        state.generator_rate(gen), base_rate * upgrade.multiplier
    )


def test_global_upgrade_multiplies_everything_including_clicks():
    state = GameState(shards=10 ** 12)
    state.owned["stone_golem"] = 50
    base_click = state.click_power()
    base_rate = state.generator_rate(GENERATORS_BY_KEY["stone_golem"])
    upgrade = UPGRADES_BY_KEY["cavern_blessing"]
    assert state.buy_upgrade(upgrade.key)
    assert math.isclose(state.click_power(), base_click * upgrade.multiplier)
    assert math.isclose(
        state.generator_rate(GENERATORS_BY_KEY["stone_golem"]),
        base_rate * upgrade.multiplier,
    )


def test_round_trip_to_dict_and_back_preserves_state():
    state = GameState(shards=12345.6, total_earned=99999, total_clicks=42)
    state.owned["rusty_pickaxe"] = 5
    state.purchased_upgrades.add("click_gloves")
    state.last_saved_at = 1234567890.0

    restored = GameState.from_dict(state.to_dict())
    assert restored.shards == state.shards
    assert restored.total_earned == state.total_earned
    assert restored.total_clicks == state.total_clicks
    assert restored.owned == state.owned
    assert restored.purchased_upgrades == state.purchased_upgrades
    assert restored.last_saved_at == state.last_saved_at


def test_from_dict_ignores_unknown_keys():
    restored = GameState.from_dict({
        "shards": 10,
        "owned": {"rusty_pickaxe": 3, "nonexistent_generator": 99},
        "purchased_upgrades": ["click_gloves", "bogus_upgrade"],
    })
    assert restored.owned == {"rusty_pickaxe": 3}
    assert restored.purchased_upgrades == {"click_gloves"}


def test_generator_unlock_gating():
    state = GameState(total_earned=0)
    # First tier is always unlocked.
    assert state.is_generator_unlocked(GENERATORS[0])
    # Second tier gated by total_earned.
    assert not state.is_generator_unlocked(GENERATORS[1])
    state.total_earned = GENERATORS[1].base_cost
    assert state.is_generator_unlocked(GENERATORS[1])
