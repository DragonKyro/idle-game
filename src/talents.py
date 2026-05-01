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
    # Cost of the Nth level is base_cost * level.
    base_cost: int
    max_level: int
    # Applied per level.
    effect: str
    value: float
    # Visual motif drawn inside the node circle — see
    # ``ui.talent_panel._draw_talent_icon``.
    icon: str


TALENTS: Sequence[TalentDef] = (
    # --- Click branch ---
    TalentDef("tap_precision", "Tap Precision", "click",
              "+15% click power per level.",
              base_cost=2, max_level=5, effect="click", value=0.15,
              icon="fist"),
    TalentDef("crit_study", "Critical Study", "click",
              "+5% chance on each click to deal 5x.",
              base_cost=5, max_level=5, effect="crit_chance", value=0.05,
              icon="crosshair"),
    TalentDef("synced_strike", "Synced Strike", "click",
              "Each click earns an extra 2% of your per-second rate "
              "per level. Lets idle investments pay off at the crystal.",
              base_cost=4, max_level=5, effect="rate_to_click", value=0.02,
              icon="wave"),
    TalentDef("finishing_blow", "Finishing Blow", "click",
              "+25% click power per level. A late-game capstone "
              "when the basic click talents start to feel small.",
              base_cost=6, max_level=3, effect="click", value=0.25,
              icon="fist"),
    TalentDef("second_wind", "Second Wind", "click",
              "+3% crit chance per level, stacking with Critical Study.",
              base_cost=5, max_level=3, effect="crit_chance", value=0.03,
              icon="crosshair"),

    # --- Idle branch ---
    TalentDef("deeper_veins", "Deeper Veins", "idle",
              "+10% passive production per level.",
              base_cost=2, max_level=5, effect="idle", value=0.10,
              icon="vein"),
    TalentDef("cavern_whisper", "Cavern Whisper", "idle",
              "+20% production from your lowest-tier helper per level.",
              base_cost=4, max_level=3, effect="lowest_tier_boost", value=0.20,
              icon="wave"),
    TalentDef("cavern_memory", "Cavern Memory", "idle",
              "+15% passive production per level. A deeper cut of the "
              "same vein — stacks with Deeper Veins.",
              base_cost=5, max_level=3, effect="idle", value=0.15,
              icon="vein"),
    TalentDef("runed_harmony", "Runed Harmony", "idle",
              "+1% all production per level for every distinct helper "
              "type you currently own.",
              base_cost=3, max_level=5, effect="type_diversity", value=0.01,
              icon="wave"),

    # --- Offline branch ---
    TalentDef("rested_helpers", "Rested Helpers", "offline",
              "+10% offline efficiency per level (base: 50%).",
              base_cost=3, max_level=5, effect="offline", value=0.10,
              icon="zzz"),
    TalentDef("long_shift", "Long Shift", "offline",
              "+2 hours to the offline earnings cap per level.",
              base_cost=3, max_level=4, effect="offline_cap", value=2 * 3600,
              icon="clock"),

    # --- Special branch ---
    TalentDef("starting_stash", "Starting Stash", "special",
              "Begin each run with a bonus 500 shards per level "
              "(scales sqrt with prestige count).",
              base_cost=4, max_level=5, effect="start_bonus", value=500,
              icon="coins"),
    TalentDef("lucky_strike", "Lucky Strike", "special",
              "Random events spawn 20% more often per level.",
              base_cost=3, max_level=3, effect="event_rate", value=0.20,
              icon="clover"),
    TalentDef("essence_magnet", "Essence Magnet", "special",
              "+5% essence earned on descent per level.",
              base_cost=5, max_level=5, effect="essence_bonus", value=0.05,
              icon="magnet"),
    TalentDef("boss_slayer", "Boss Slayer", "special",
              "+50% click damage against Cavern Lords per level.",
              base_cost=5, max_level=3, effect="boss_damage", value=0.50,
              icon="crosshair"),
    TalentDef("cavern_historian", "Cavern Historian", "special",
              "+0.5% all production per level for every achievement "
              "you've unlocked. Becomes significant as your record grows.",
              base_cost=4, max_level=5, effect="achievement_bonus", value=0.005,
              icon="coins"),
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
