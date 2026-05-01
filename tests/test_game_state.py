"""Unit tests for GameState."""

from __future__ import annotations

import math

from src.game_state import GameState
from src.generators import GENERATORS, GENERATORS_BY_KEY
from src.upgrades import UPGRADES_BY_KEY


def test_click_grants_one_shard_by_default():
    state = GameState()
    gained, was_crit = state.click(crit_roll=1.0)  # no crit
    assert gained == 1
    assert not was_crit
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
    assert state.upgrade_level(upgrade.key) == 1
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


def test_upgrade_effect_stacks_multiplicatively_per_level():
    """Buying 3 levels of a 2x upgrade should give 8x, not 6x."""
    state = GameState(shards=1e18)
    state.owned["rusty_pickaxe"] = 25
    upgrade = UPGRADES_BY_KEY["click_gloves"]
    base = state.click_power()
    for _ in range(3):
        assert state.buy_upgrade(upgrade.key)
    assert state.upgrade_level(upgrade.key) == 3
    assert math.isclose(state.click_power(), base * (upgrade.multiplier ** 3))


def test_upgrade_cost_scales_by_cost_growth_per_level():
    state = GameState(shards=1e18)
    state.owned["rusty_pickaxe"] = 25
    upgrade = UPGRADES_BY_KEY["click_gloves"]
    # First level costs the base price.
    assert math.isclose(state.next_upgrade_cost(upgrade.key), upgrade.cost)
    state.buy_upgrade(upgrade.key)
    # Second level costs base * cost_growth.
    assert math.isclose(
        state.next_upgrade_cost(upgrade.key),
        upgrade.cost * upgrade.cost_growth,
    )
    state.buy_upgrade(upgrade.key)
    assert math.isclose(
        state.next_upgrade_cost(upgrade.key),
        upgrade.cost * (upgrade.cost_growth ** 2),
    )


def test_cannot_buy_past_max_level():
    state = GameState(shards=1e18)
    state.owned["rusty_pickaxe"] = 25
    upgrade = UPGRADES_BY_KEY["click_gloves"]
    for _ in range(upgrade.max_level):
        assert state.buy_upgrade(upgrade.key)
    # Now maxed.
    assert state.upgrade_is_maxed(upgrade.key)
    assert state.next_upgrade_cost(upgrade.key) is None
    assert not state.can_afford_upgrade(upgrade.key)
    assert not state.buy_upgrade(upgrade.key)
    assert state.upgrade_level(upgrade.key) == upgrade.max_level


def test_maxed_upgrade_stays_visible_in_shop():
    """Completionists want the full catalog visible, even when an entry
    is maxed."""
    state = GameState(shards=1e18)
    state.owned["rusty_pickaxe"] = 25
    upgrade = UPGRADES_BY_KEY["click_gloves"]
    for _ in range(upgrade.max_level):
        state.buy_upgrade(upgrade.key)
    assert state.upgrade_is_maxed(upgrade.key)
    assert state.is_upgrade_visible(upgrade.key)


def test_round_trip_to_dict_and_back_preserves_state():
    state = GameState(shards=12345.6, total_earned=99999, total_clicks=42)
    state.owned["rusty_pickaxe"] = 5
    state.upgrade_levels["click_gloves"] = 3
    state.last_saved_at = 1234567890.0

    restored = GameState.from_dict(state.to_dict())
    assert restored.shards == state.shards
    assert restored.total_earned == state.total_earned
    assert restored.total_clicks == state.total_clicks
    assert restored.owned == state.owned
    assert restored.upgrade_levels == state.upgrade_levels
    assert restored.last_saved_at == state.last_saved_at


def test_from_dict_ignores_unknown_keys():
    restored = GameState.from_dict({
        "shards": 10,
        "owned": {"rusty_pickaxe": 3, "nonexistent_generator": 99},
        "upgrade_levels": {"click_gloves": 2, "bogus_upgrade": 99},
    })
    assert restored.owned == {"rusty_pickaxe": 3}
    assert restored.upgrade_levels == {"click_gloves": 2}


def test_from_dict_clamps_levels_to_max_level():
    # If an upgrade's cap was lowered after the save was written, loading
    # shouldn't leave the player with more levels than the new cap allows.
    restored = GameState.from_dict({
        "upgrade_levels": {"click_gloves": 999},
    })
    assert restored.upgrade_levels["click_gloves"] == UPGRADES_BY_KEY[
        "click_gloves"
    ].max_level


def test_from_dict_migrates_legacy_purchased_upgrades():
    """v1/v2 saves stored a set of bought upgrade keys. v3 stores levels;
    the loader should silently convert."""
    restored = GameState.from_dict({
        "purchased_upgrades": ["click_gloves", "pickaxe_honed"],
    })
    assert restored.upgrade_levels == {
        "click_gloves": 1,
        "pickaxe_honed": 1,
    }


def test_pending_essence_is_zero_when_no_progress():
    state = GameState()
    assert state.pending_essence() == 0
    assert not state.can_descend()


def test_pending_essence_scales_with_sqrt_of_progress():
    state = GameState(total_earned=1e10)
    assert state.pending_essence() == 1
    state.total_earned = 1e12
    assert state.pending_essence() == 10
    state.total_earned = 1e14
    assert state.pending_essence() == 100


def test_descend_resets_run_and_awards_essence():
    state = GameState(shards=5_000_000, total_earned=1e12, total_clicks=500)
    state.owned["rusty_pickaxe"] = 25
    state.upgrade_levels["click_gloves"] = 3

    gained = state.descend()

    assert gained == 10
    assert state.essence == 10
    assert state.shards == 0
    assert state.owned == {}
    assert state.upgrade_levels == {}
    assert state.prestige_count == 1
    assert state.last_descend_total == 1e12
    assert state.total_earned == 1e12
    assert state.total_clicks == 500


def test_descend_does_nothing_if_below_threshold():
    state = GameState(total_earned=5e9)
    assert state.descend() == 0
    assert state.essence == 0
    assert state.prestige_count == 0


def test_essence_multiplier_applies_to_click_and_idle():
    state = GameState(essence=50)
    assert state.essence_multiplier() == 2.0
    assert state.click_power() == 2.0
    gen = GENERATORS[0]
    assert state.generator_rate(gen) == gen.base_production * 2.0


def test_second_descent_only_counts_new_earnings():
    state = GameState(total_earned=1e12)
    first = state.descend()
    assert first == 10
    state.total_earned = 5e12
    assert state.pending_essence() == 20
    gained = state.descend()
    assert gained == 20
    assert state.essence == 30
    assert state.prestige_count == 2


def test_prestige_state_round_trips_through_save():
    state = GameState(essence=5, prestige_count=2, last_descend_total=1e11)
    restored = GameState.from_dict(state.to_dict())
    assert restored.essence == 5
    assert restored.prestige_count == 2
    assert restored.last_descend_total == 1e11


def test_crystal_tier_grows_with_total_levels_and_prestige():
    state = GameState()
    assert state.crystal_tier() == 0
    state.upgrade_levels = {"a": 1, "b": 1, "c": 1}
    assert state.crystal_tier() == 1  # 3 total levels // 3
    state.upgrade_levels = {"a": 2, "b": 2, "c": 2}
    assert state.crystal_tier() == 2  # 6 // 3
    state.prestige_count = 1
    assert state.crystal_tier() == 3
    # Capped at max.
    state.prestige_count = 99
    state.upgrade_levels = {f"u{i}": 5 for i in range(30)}
    assert state.crystal_tier() == 6


def test_generator_unlock_gating():
    state = GameState(total_earned=0)
    assert state.is_generator_unlocked(GENERATORS[0])
    assert not state.is_generator_unlocked(GENERATORS[1])
    state.total_earned = GENERATORS[1].base_cost
    assert state.is_generator_unlocked(GENERATORS[1])
