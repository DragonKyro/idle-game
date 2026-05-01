"""Talent tree — permanent bonuses purchased with essence.

Players earn essence by descending; they can spend it here on targeted
bonuses. Unspent essence still grants the base +2% production per unit
from ``GameState.essence_multiplier``, so spending is a real trade-off:
give up ambient income for a focused perk.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class TalentDef:
    key: str
    name: str
    branch: str  # "click", "idle", "offline", "special"
    description: str
    # Cost of the Nth level is base_cost * level (so level 3 costs
    # base*1 + base*2 + base*3 = 6*base cumulatively — steep but fair).
    base_cost: int
    max_level: int
    # Applied per level.
    effect: str  # "click", "idle", "offline", "start_bonus", "offline_cap"
    value: float  # meaning depends on effect


TALENTS: Sequence[TalentDef] = (
    # --- Click branch ---
    TalentDef("tap_precision", "Tap Precision", "click",
              "+15% click power per level.",
              base_cost=2, max_level=5, effect="click", value=0.15),
    TalentDef("crit_study", "Critical Study", "click",
              "+5% chance on each click to deal 5x.",
              base_cost=5, max_level=5, effect="crit_chance", value=0.05),

    # --- Idle branch ---
    TalentDef("deeper_veins", "Deeper Veins", "idle",
              "+10% passive production per level.",
              base_cost=2, max_level=5, effect="idle", value=0.10),
    TalentDef("cavern_whisper", "Cavern Whisper", "idle",
              "+20% production from your lowest-tier helper per level.",
              base_cost=4, max_level=3, effect="lowest_tier_boost", value=0.20),

    # --- Offline branch ---
    TalentDef("rested_helpers", "Rested Helpers", "offline",
              "+10% offline efficiency per level (base: 50%).",
              base_cost=3, max_level=5, effect="offline", value=0.10),
    TalentDef("long_shift", "Long Shift", "offline",
              "+2 hours to the offline earnings cap per level.",
              base_cost=3, max_level=4, effect="offline_cap", value=2 * 3600),

    # --- Special branch ---
    TalentDef("starting_stash", "Starting Stash", "special",
              "Begin each run with a bonus 500 shards per level "
              "(scales sqrt with prestige count).",
              base_cost=4, max_level=5, effect="start_bonus", value=500),
    TalentDef("lucky_strike", "Lucky Strike", "special",
              "Random events spawn 20% more often per level.",
              base_cost=3, max_level=3, effect="event_rate", value=0.20),
    TalentDef("essence_magnet", "Essence Magnet", "special",
              "+5% essence earned on descent per level.",
              base_cost=5, max_level=5, effect="essence_bonus", value=0.05),
)


TALENTS_BY_KEY = {t.key: t for t in TALENTS}
TALENT_BRANCHES = ("click", "idle", "offline", "special")


def talent_level_cost(talent: TalentDef, next_level: int) -> int:
    """Cost in essence for the Nth level (1-indexed)."""
    if next_level < 1 or next_level > talent.max_level:
        raise ValueError(
            f"{talent.key} level {next_level} out of range 1..{talent.max_level}"
        )
    return talent.base_cost * next_level
