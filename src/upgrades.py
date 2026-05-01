"""Upgrade definitions — one-time purchases that multiply production or clicks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class UpgradeDef:
    key: str
    name: str
    flavor: str
    cost: float
    # Requirement: at least this many units of `requires_key` owned, or the
    # upgrade stays hidden. None means "always available once affordable".
    requires_key: str | None
    requires_count: int
    # Effect kind: "click" multiplies click power, "gen:<key>" multiplies one
    # generator's output, "global" multiplies all production (click + idle).
    effect: str
    multiplier: float


# Progression: early upgrades boost clicks so the player feels rewarded for
# tapping, mid-game unlocks buff specific generators, late-game is global.
UPGRADES: Sequence[UpgradeDef] = (
    UpgradeDef("click_gloves",  "Enchanted Gloves",
               "Your taps ring a little louder.",
               100, "rusty_pickaxe", 1,   "click", 2.0),
    UpgradeDef("click_gauntlet", "Runed Gauntlet",
               "Taps now crackle with arcane punch.",
               5_000, "rusty_pickaxe", 25, "click", 2.0),
    UpgradeDef("pickaxe_honed",  "Honed Edges",
               "Every Rusty Pickaxe gets a proper whetstone.",
               500, "rusty_pickaxe", 10, "gen:rusty_pickaxe", 2.0),
    UpgradeDef("miner_coffee",   "Strong Coffee",
               "Apprentices triple their swing rate.",
               2_500, "apprentice_miner", 10, "gen:apprentice_miner", 3.0),
    UpgradeDef("cart_wheels",    "Greased Wheels",
               "Carts roll twice as fast down the shafts.",
               20_000, "cart_runner", 10, "gen:cart_runner", 2.0),
    UpgradeDef("drill_overclock", "Overclocked Drills",
               "Ignore manufacturer warnings — double speed.",
               250_000, "crystal_drill", 10, "gen:crystal_drill", 2.0),
    UpgradeDef("golem_runestone", "Golem Runestones",
               "Etch 'WORK HARDER' into every golem's chest.",
               2_800_000, "stone_golem", 10, "gen:stone_golem", 2.5),
    UpgradeDef("wizard_familiars", "Familiar Assistants",
               "Wizards outsource shard-shaping to cat spirits.",
               36_000_000, "arcane_wizard", 10, "gen:arcane_wizard", 3.0),
    UpgradeDef("forge_eternal",   "Eternal Coals",
               "The forges never cool. The wizards are concerned.",
               440_000_000, "rune_forge", 10, "gen:rune_forge", 2.5),
    UpgradeDef("dragon_hoard",    "Hoard Multiplier",
               "Crystal Dragons really lean into the greed.",
               5_600_000_000, "crystal_dragon", 10, "gen:crystal_dragon", 3.0),
    UpgradeDef("cavern_blessing", "Cavern's Blessing",
               "The cavern itself smiles upon your operation.",
               50_000_000_000, "stone_golem", 50, "global", 1.5),
    UpgradeDef("starlight_flow",  "Starlight Flow",
               "A river of light threads through every shaft.",
               800_000_000_000, "ancient_titan", 10, "global", 2.0),
)


UPGRADES_BY_KEY = {u.key: u for u in UPGRADES}
