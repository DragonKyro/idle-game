"""Talent tree integrity + state application tests."""

from __future__ import annotations

import math

from src.game_state import GameState
from src.generators import GENERATORS
from src.talents import (
    TALENT_BRANCHES,
    TALENTS,
    TALENTS_BY_KEY,
    talent_level_cost,
)


def test_talent_keys_unique():
    keys = [t.key for t in TALENTS]
    assert len(keys) == len(set(keys))


def test_every_branch_has_at_least_one_talent():
    covered = {t.branch for t in TALENTS}
    for branch in TALENT_BRANCHES:
        assert branch in covered


def test_every_talent_has_an_icon():
    # The talent panel dispatches on `icon` — missing ones fall through to
    # a plain-dot fallback, which still draws but is boring. Guard against
    # silently introducing a new talent without picking a motif.
    for t in TALENTS:
        assert t.icon, f"{t.key} is missing an icon"


def test_talent_level_cost_formula():
    talent = TALENTS[0]
    for level in range(1, talent.max_level + 1):
        assert talent_level_cost(talent, level) == talent.base_cost * level


def test_can_afford_and_buy_talent():
    state = GameState(essence=100)
    talent = TALENTS_BY_KEY["tap_precision"]  # base_cost=2, max=5
    assert state.can_afford_talent(talent.key)
    assert state.buy_talent(talent.key)
    # Level 1 cost deducted.
    assert state.essence == 98
    assert state.talent_level(talent.key) == 1

    # Next level costs base*2.
    assert state.next_talent_cost(talent.key) == 4
    assert state.buy_talent(talent.key)
    assert state.essence == 94
    assert state.talent_level(talent.key) == 2


def test_talent_click_bonus_applies_additively():
    # Start with zero essence so the passive bonus doesn't shift as we spend.
    state = GameState(essence=0, shards=0)
    base = state.click_power()  # = 1.0
    talent = TALENTS_BY_KEY["tap_precision"]  # +15% per level
    # Give them enough essence to buy two levels without touching the
    # passive multiplier test math: we just manually grant + level.
    state.talent_levels[talent.key] = 1
    assert math.isclose(state.click_power(), base * 1.15)
    state.talent_levels[talent.key] = 2
    assert math.isclose(state.click_power(), base * 1.30)


def test_talent_offline_efficiency_boost():
    state = GameState(essence=100)
    base = state.offline_efficiency()
    talent = TALENTS_BY_KEY["rested_helpers"]  # +10% offline per level
    state.buy_talent(talent.key)
    assert math.isclose(state.offline_efficiency(), base + 0.10)


def test_talent_offline_cap_extension():
    state = GameState(essence=100)
    base = state.offline_cap_seconds()
    talent = TALENTS_BY_KEY["long_shift"]  # +2h per level
    state.buy_talent(talent.key)
    assert math.isclose(state.offline_cap_seconds(), base + 2 * 3600)


def test_talent_cannot_buy_past_max():
    state = GameState(essence=10_000)
    talent = TALENTS_BY_KEY["crit_study"]  # max=5
    for _ in range(talent.max_level):
        assert state.buy_talent(talent.key)
    assert state.talent_is_maxed(talent.key)
    assert not state.buy_talent(talent.key)
    assert state.next_talent_cost(talent.key) is None


def test_crit_chance_from_talent():
    state = GameState(essence=200)
    talent = TALENTS_BY_KEY["crit_study"]  # +5% per level
    assert state.crit_chance() == 0.0
    state.buy_talent(talent.key)
    assert math.isclose(state.crit_chance(), 0.05)
    state.buy_talent(talent.key)
    assert math.isclose(state.crit_chance(), 0.10)


def test_lowest_tier_boost_only_hits_lowest_owned():
    state = GameState(essence=100)
    state.owned[GENERATORS[0].key] = 5   # lowest
    state.owned[GENERATORS[3].key] = 5   # higher
    talent = TALENTS_BY_KEY["cavern_whisper"]  # +20% lowest-tier per level
    state.buy_talent(talent.key)
    # Lowest tier sees the bonus; higher tier does not.
    lowest = state.generator_rate(GENERATORS[0])
    higher = state.generator_rate(GENERATORS[3])
    # Compute expected base rates without the bonus, then compare ratios.
    expected_lowest = GENERATORS[0].base_production * 1.20 * state.essence_multiplier()
    expected_higher = GENERATORS[3].base_production * state.essence_multiplier()
    assert math.isclose(lowest, expected_lowest)
    assert math.isclose(higher, expected_higher)


def test_spent_essence_reduces_passive_bonus():
    state = GameState(essence=10)
    multiplier_before = state.essence_multiplier()  # 1 + 0.02*10 = 1.2
    assert math.isclose(multiplier_before, 1.20)
    talent = TALENTS_BY_KEY["tap_precision"]  # base_cost=2
    state.buy_talent(talent.key)
    # Essence went 10 -> 8, so passive bonus drops.
    multiplier_after = state.essence_multiplier()
    assert math.isclose(multiplier_after, 1.16)


def test_talent_state_round_trips_through_save():
    state = GameState(essence=5)
    state.talent_levels["tap_precision"] = 3
    restored = GameState.from_dict(state.to_dict())
    assert restored.talent_levels == {"tap_precision": 3}
