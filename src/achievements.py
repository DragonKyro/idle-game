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


def _all_click_upgrades_maxed():
    from src.upgrades import UPGRADES

    def check(s: "GameState") -> bool:
        click_keys = [u.key for u in UPGRADES if u.effect == "click"]
        return all(s.upgrade_is_maxed(k) for k in click_keys) if click_keys else False

    return check


def _all_global_upgrades_maxed():
    from src.upgrades import UPGRADES

    def check(s: "GameState") -> bool:
        g_keys = [u.key for u in UPGRADES if u.effect == "global"]
        return all(s.upgrade_is_maxed(k) for k in g_keys) if g_keys else False

    return check


def _any_talent_owned():
    return lambda s: any(v > 0 for v in s.talent_levels.values())


def _all_talents_maxed():
    from src.talents import TALENTS

    def check(s: "GameState") -> bool:
        return all(s.talent_is_maxed(t.key) for t in TALENTS)

    return check


def _branch_maxed():
    from src.talents import TALENT_BRANCHES, TALENTS

    def check(s: "GameState") -> bool:
        for branch in TALENT_BRANCHES:
            branch_talents = [t for t in TALENTS if t.branch == branch]
            if branch_talents and all(s.talent_is_maxed(t.key) for t in branch_talents):
                return True
        return False

    return check


def _playtime(seconds: float):
    return lambda s: s.playtime_seconds >= seconds


def _bosses(n: int):
    return lambda s: s.bosses_defeated >= n


def _generator_maxed(key: str):
    """Fires when the player has 200 (the configured max) of `key`."""
    from src.generators import GENERATORS_BY_KEY

    def check(s: "GameState") -> bool:
        gen = GENERATORS_BY_KEY.get(key)
        if gen is None:
            return False
        return s.owned.get(key, 0) >= gen.max_count

    return check


def _all_generators_maxed():
    from src.generators import GENERATORS

    def check(s: "GameState") -> bool:
        return all(s.owned.get(g.key, 0) >= g.max_count for g in GENERATORS)

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

    # --- Extended clicks ---
    AchievementDef("clicks_100k",  "Tendon Specialist",
                   "Tap the crystal 100,000 times.",
                   _CYAN, _clicks(100_000)),
    AchievementDef("clicks_1m",    "Million-Tap Club",
                   "Tap the crystal 1,000,000 times.",
                   _CYAN, _clicks(1_000_000)),

    # --- Extended earnings ---
    AchievementDef("earned_1qi",  "Quintillionaire",
                   "Earn 1 quintillion shards total.",
                   _GOLD, _earned(1e18)),
    AchievementDef("earned_1sx",  "Sextillionaire",
                   "Earn 1 sextillion shards total.",
                   _GOLD, _earned(1e21)),

    # --- New generators ---
    AchievementDef("own_lantern",   "Light the Way",
                   "Hire your first Lantern Keeper.",
                   _GOLD, _owned("lantern_keeper", 1)),
    AchievementDef("own_whale",     "Leviathan",
                   "Summon your first Void Whale.",
                   _CYAN, _owned("void_whale", 1)),
    AchievementDef("own_tree",      "World-Rooted",
                   "Plant the first Universe Tree.",
                   _GREEN, _owned("universe_tree", 1)),

    # --- Helper completionism ---
    AchievementDef("max_first_gen",  "Pickaxe Plenty",
                   "Own the maximum 200 of Rusty Pickaxe.",
                   _GREEN, _generator_maxed("rusty_pickaxe")),
    AchievementDef("max_all_gens",   "Full Ledger",
                   "Own the maximum 200 of every helper tier.",
                   _ROSE, _all_generators_maxed()),

    # --- Upgrades ---
    AchievementDef("all_clicks_max", "Hands of Thunder",
                   "Max out every click upgrade in the catalog.",
                   _GOLD, _all_click_upgrades_maxed()),
    AchievementDef("all_globals_max","Tuned to the Cavern",
                   "Max out every global-production upgrade.",
                   _ROSE, _all_global_upgrades_maxed()),

    # --- Prestige ---
    AchievementDef("descents_50",    "Cavern Scholar",
                   "Descend 50 times.", _VIOLET, _prestige(50)),

    # --- Talents ---
    AchievementDef("talent_any",     "Student of the Cavern",
                   "Invest essence in any talent.",
                   _GOLD, _any_talent_owned()),
    AchievementDef("talent_branch",  "Branch Master",
                   "Max every talent in a single branch.",
                   _VIOLET, _branch_maxed()),
    AchievementDef("talent_all",     "Omnischolar",
                   "Max every talent in every branch.",
                   _ROSE, _all_talents_maxed()),

    # --- Bosses ---
    AchievementDef("boss_1",  "Lord Breaker",
                   "Defeat your first Cavern Lord.",
                   _ROSE, _bosses(1)),
    AchievementDef("boss_10", "Tyrant of the Deep",
                   "Defeat 10 Cavern Lords.", _ROSE, _bosses(10)),
    AchievementDef("boss_50", "The Quiet After",
                   "Defeat 50 Cavern Lords.", _ROSE, _bosses(50)),

    # --- Playtime ---
    AchievementDef("playtime_1h",   "Shift Done",
                   "Play for 1 hour total.", _CYAN, _playtime(3600)),
    AchievementDef("playtime_10h",  "Dedicated Dweller",
                   "Play for 10 hours total.", _CYAN, _playtime(36_000)),
    AchievementDef("playtime_100h", "Lives in the Cavern Now",
                   "Play for 100 hours total.", _CYAN, _playtime(360_000)),

    # --- Biome milestone (prestige-gated, post-cycle) ---
    AchievementDef("biome_cosmic", "Across the Cycle",
                   "Descend enough times to cycle every biome.",
                   _VIOLET, _prestige(6)),
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
