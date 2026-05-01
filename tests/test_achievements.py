"""Achievement catalog integrity + unlock check."""

from __future__ import annotations

from src.achievements import ACHIEVEMENTS, ACHIEVEMENTS_BY_KEY, newly_unlocked
from src.game_state import GameState


def test_achievement_keys_unique():
    keys = [a.key for a in ACHIEVEMENTS]
    assert len(keys) == len(set(keys))


def test_achievements_have_descriptions():
    for a in ACHIEVEMENTS:
        assert a.name
        assert a.description


def test_achievements_by_key_is_complete():
    assert len(ACHIEVEMENTS_BY_KEY) == len(ACHIEVEMENTS)


def test_first_click_unlocks_on_first_click():
    state = GameState()
    unlocked = newly_unlocked(state)
    assert "first_click" not in {a.key for a in unlocked}
    state.click(crit_roll=1.0)
    unlocked = newly_unlocked(state)
    keys = {a.key for a in unlocked}
    assert "first_click" in keys


def test_achievement_only_unlocks_once():
    state = GameState()
    state.click(crit_roll=1.0)
    first = newly_unlocked(state)
    assert first  # some achievements fired
    second = newly_unlocked(state)
    # Calling again immediately should not re-surface them.
    assert second == []


def test_earnings_based_achievements():
    state = GameState(total_earned=1_500)
    unlocked = {a.key for a in newly_unlocked(state)}
    assert "earned_1k" in unlocked
    assert "earned_1m" not in unlocked

    state.total_earned = 2_000_000
    unlocked = {a.key for a in newly_unlocked(state)}
    assert "earned_1m" in unlocked


def test_descent_based_achievements():
    state = GameState(total_earned=1e12)
    state.descend()
    unlocked = {a.key for a in newly_unlocked(state)}
    assert "first_descent" in unlocked
    assert "essence_10" in unlocked  # descent gives 10 essence


def test_all_maxed_achievement_requires_every_upgrade():
    from src.upgrades import UPGRADES
    state = GameState()
    # Set every upgrade to its max level.
    state.upgrade_levels = {u.key: u.max_level for u in UPGRADES}
    unlocked = {a.key for a in newly_unlocked(state)}
    assert "all_maxed" in unlocked
