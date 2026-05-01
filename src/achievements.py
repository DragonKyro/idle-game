"""Achievement definitions.

Achievements are checked against the live ``GameState`` every frame
(cheap — all checks are O(1) and there are only ~30 of them). Each
``AchievementDef.predicate`` is a plain function that takes a
``GameState`` and returns True once the condition is met.

Keeping the definitions in a pure-Python module means the full catalog
can be unit-tested without a graphics context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from src.game_state import GameState


@dataclass(frozen=True)
class AchievementDef:
    key: str
    name: str
    description: str
    # Accent color — also used on the unlock-notification banner.
    color: tuple[int, int, int]
    predicate: Callable[["GameState"], bool]


def _owned(key: str, n: int):
    return lambda s: s.owned.get(key, 0) >= n


def _clicks(n: int):
    return lambda s: s.total_clicks >= n


def _earned(amount: float):
    return lambda s: s.total_earned >= amount


def _total_levels(n: int):
    return lambda s: s.total_upgrade_levels() >= n


def _prestige(n: int):
    return lambda s: s.prestige_count >= n


def _essence(n: int):
    return lambda s: s.total_essence_earned >= n


def _all_generators():
    # All 10 tiers owned at least once.
    return lambda s: len([1 for v in s.owned.values() if v > 0]) >= 10


def _any_max_upgrade():
    from src.upgrades import UPGRADES_BY_KEY

    def check(s: "GameState") -> bool:
        for key, level in s.upgrade_levels.items():
            up = UPGRADES_BY_KEY.get(key)
            if up and level >= up.max_level:
                return True
        return False

    return check


def _all_max_upgrades():
    from src.upgrades import UPGRADES

    def check(s: "GameState") -> bool:
        return all(s.upgrade_is_maxed(u.key) for u in UPGRADES)

    return check


# Palette shortcuts so the unlock banners read as a coherent set.
_GOLD = (255, 214, 110)
_GREEN = (130, 230, 170)
_CYAN = (120, 220, 255)
_VIOLET = (180, 150, 255)
_ROSE = (255, 160, 200)


ACHIEVEMENTS: Sequence[AchievementDef] = (
    # --- Early milestones ---
    AchievementDef("first_click", "First Swing",
                   "Tap the mana crystal for the first time.",
                   _CYAN, _clicks(1)),
    AchievementDef("first_hire", "Help Wanted",
                   "Hire your very first helper.",
                   _GREEN, lambda s: sum(s.owned.values()) >= 1),
    AchievementDef("first_upgrade", "Sharper Tools",
                   "Buy your first upgrade level.",
                   _GOLD, _total_levels(1)),

    # --- Click thresholds ---
    AchievementDef("clicks_100",   "Getting the Hang of It",
                   "Tap the crystal 100 times.", _CYAN, _clicks(100)),
    AchievementDef("clicks_1000",  "Tenacious",
                   "Tap the crystal 1,000 times.", _CYAN, _clicks(1_000)),
    AchievementDef("clicks_10000", "Carpal Tunnel",
                   "Tap the crystal 10,000 times.", _CYAN, _clicks(10_000)),

    # --- Earnings thresholds ---
    AchievementDef("earned_1k",   "Pocket Change",
                   "Earn 1,000 shards total.", _GOLD, _earned(1_000)),
    AchievementDef("earned_1m",   "Respectable Hoard",
                   "Earn 1,000,000 shards total.", _GOLD, _earned(1_000_000)),
    AchievementDef("earned_1b",   "Billionaire Dwarf",
                   "Earn 1,000,000,000 shards total.", _GOLD, _earned(1e9)),
    AchievementDef("earned_1t",   "Economy-Breaking",
                   "Earn 1 trillion shards total.", _GOLD, _earned(1e12)),
    AchievementDef("earned_1qa",  "Quadrillionaire",
                   "Earn 1 quadrillion shards total.", _GOLD, _earned(1e15)),

    # --- Helper roster ---
    AchievementDef("own_10_rusty", "Pickaxe Parade",
                   "Own 10 Rusty Pickaxes.",
                   _GREEN, _owned("rusty_pickaxe", 10)),
    AchievementDef("own_25_rusty", "Pickaxe Platoon",
                   "Own 25 Rusty Pickaxes.",
                   _GREEN, _owned("rusty_pickaxe", 25)),
    AchievementDef("own_first_wizard", "Arcane Acquaintance",
                   "Hire your first Arcane Wizard.",
                   _VIOLET, _owned("arcane_wizard", 1)),
    AchievementDef("own_first_dragon", "Scale Friends",
                   "Hire your first Crystal Dragon.",
                   _CYAN, _owned("crystal_dragon", 1)),
    AchievementDef("own_first_titan", "Wake the Titan",
                   "Hire your first Ancient Titan.",
                   _GOLD, _owned("ancient_titan", 1)),
    AchievementDef("own_first_astral", "Join the Collective",
                   "Hire the Astral Collective.",
                   _VIOLET, _owned("astral_collective", 1)),
    AchievementDef("own_all_tiers", "Full Roster",
                   "Own at least one of every helper tier.",
                   _ROSE, _all_generators()),

    # --- Upgrades / completionism ---
    AchievementDef("max_first_upgrade", "Maxed Out",
                   "Max out any single upgrade.",
                   _GOLD, _any_max_upgrade()),
    AchievementDef("upgrades_10",  "Shopper",
                   "Purchase 10 upgrade levels in total.",
                   _GOLD, _total_levels(10)),
    AchievementDef("upgrades_50",  "Catalog Collector",
                   "Purchase 50 upgrade levels in total.",
                   _GOLD, _total_levels(50)),
    AchievementDef("all_maxed",    "The Completionist",
                   "Max out every upgrade in the catalog.",
                   _ROSE, _all_max_upgrades()),

    # --- Prestige ---
    AchievementDef("first_descent",  "Descended",
                   "Descend Deeper for the first time.",
                   _VIOLET, _prestige(1)),
    AchievementDef("descents_5",     "Serial Spelunker",
                   "Descend 5 times.", _VIOLET, _prestige(5)),
    AchievementDef("descents_25",    "Cavern Devotee",
                   "Descend 25 times.", _VIOLET, _prestige(25)),
    AchievementDef("essence_10",     "Essence Initiate",
                   "Earn 10 lifetime Ancient Essence.",
                   _GOLD, _essence(10)),
    AchievementDef("essence_100",    "Essence Adept",
                   "Earn 100 lifetime Ancient Essence.",
                   _GOLD, _essence(100)),
    AchievementDef("essence_1000",   "Essence Ascendant",
                   "Earn 1,000 lifetime Ancient Essence.",
                   _GOLD, _essence(1_000)),
)


ACHIEVEMENTS_BY_KEY = {a.key: a for a in ACHIEVEMENTS}


def newly_unlocked(state: "GameState") -> list[AchievementDef]:
    """Check every achievement and return those that JUST became satisfied
    and aren't already on the player's record. Mutates ``state`` to
    record the new unlocks."""
    unlocked: list[AchievementDef] = []
    for ach in ACHIEVEMENTS:
        if ach.key in state.achievements:
            continue
        if ach.predicate(state):
            state.achievements.add(ach.key)
            unlocked.append(ach)
    return unlocked
