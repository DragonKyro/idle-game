"""Upgrade definitions — permanent purchases that multiply production or clicks.

Each upgrade can be bought up to ``max_level`` times. The configured
``multiplier`` applies once per level (so a 2x upgrade at level 3 gives 8x).
The cost scales by ``cost_growth`` per level, so later levels are
meaningfully more expensive than the first. This gives completionists a
clear ceiling to chase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class UpgradeDef:
    key: str
    name: str
    flavor: str
    # Cost of the *first* level. Level N costs base * cost_growth^(N-1).
    cost: float
    requires_key: str | None
    requires_count: int
    # Effect kind: "click" multiplies click power, "gen:<key>" multiplies one
    # generator's output, "global" multiplies everything (click + idle).
    effect: str
    # Applied once per owned level.
    multiplier: float
    # How many times the player can buy this upgrade in total.
    max_level: int = 5
    # Cost growth per level. 4.0 means level 5 costs 4^4 = 256x the first.
    cost_growth: float = 4.0


# The tuple order is also the display order in the shop — keep related
# upgrades adjacent.
UPGRADES: Sequence[UpgradeDef] = (
    # ---------- Click power (rusty pickaxe gates) ----------
    UpgradeDef("click_gloves",   "Enchanted Gloves",
               "Your taps ring a little louder.",
               100, "rusty_pickaxe", 1,    "click", 2.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("click_gauntlet", "Runed Gauntlet",
               "Taps now crackle with arcane punch.",
               5_000, "rusty_pickaxe", 25, "click", 2.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("click_echo",     "Echo Tap",
               "Each tap sends a harmonic afterimage.",
               200_000, "rusty_pickaxe", 50, "click", 2.5,
               max_level=4, cost_growth=5.0),
    UpgradeDef("click_mithril",  "Mithril Knuckles",
               "Pierce stone with pinky strength alone.",
               500_000, "rusty_pickaxe", 100, "click", 2.5,
               max_level=3, cost_growth=6.0),
    UpgradeDef("click_resonant", "Resonant Strike",
               "The cavern itself sings along.",
               20_000_000, "rusty_pickaxe", 150, "click", 3.0,
               max_level=3, cost_growth=6.0),
    UpgradeDef("click_divine",   "Divine Striker",
               "Each tap resonates across dimensions.",
               50_000_000, "rusty_pickaxe", 200, "click", 3.0,
               max_level=3, cost_growth=6.0),

    # ---------- Rusty Pickaxe ----------
    UpgradeDef("pickaxe_honed",   "Honed Edges",
               "Every Rusty Pickaxe gets a proper whetstone.",
               500, "rusty_pickaxe", 10, "gen:rusty_pickaxe", 2.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("pickaxe_mithril", "Mithril Reheading",
               "Old sticks, legendary heads.",
               40_000, "rusty_pickaxe", 25, "gen:rusty_pickaxe", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Lantern Keeper ----------
    UpgradeDef("lantern_fuel",   "Infinite Oil",
               "The lantern never dims. Carriers never rest.",
               1_200, "lantern_keeper", 10, "gen:lantern_keeper", 2.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("lantern_beam",   "Focused Beam",
               "A thin blade of light that also cuts stone.",
               60_000, "lantern_keeper", 25, "gen:lantern_keeper", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Apprentice Miner ----------
    UpgradeDef("miner_coffee",    "Strong Coffee",
               "Apprentices triple their swing rate.",
               2_500, "apprentice_miner", 10, "gen:apprentice_miner", 2.5,
               max_level=5, cost_growth=4.0),
    UpgradeDef("miner_certified", "Certified Guildfolk",
               "They read the safety manual now and everything.",
               200_000, "apprentice_miner", 25, "gen:apprentice_miner", 2.0,
               max_level=3, cost_growth=5.0),

    # ---------- Deep Digger ----------
    UpgradeDef("digger_drills",  "Shaft Drills",
               "Faster descent, fewer cave-ins.",
               8_000, "deep_digger", 10, "gen:deep_digger", 2.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("digger_abyss",   "Abyss Licenses",
               "Paperwork, but the kind that lets you go deeper.",
               600_000, "deep_digger", 25, "gen:deep_digger", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Cart Runner ----------
    UpgradeDef("cart_wheels",   "Greased Wheels",
               "Carts roll twice as fast down the shafts.",
               20_000, "cart_runner", 10, "gen:cart_runner", 2.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("cart_downhill", "Downhill Routes",
               "All tracks now slope conveniently downward.",
               2_000_000, "cart_runner", 25, "gen:cart_runner", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Moonstone Mine ----------
    UpgradeDef("mine_moonbloom", "Moonbloom Veins",
               "Shards grow like flowers in the moonlit rock.",
               60_000, "moonstone_mine", 10, "gen:moonstone_mine", 2.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("mine_phosphor",  "Phosphor Supports",
               "The timber itself is luminous now. Safer, too.",
               6_000_000, "moonstone_mine", 25, "gen:moonstone_mine", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Crystal Drill ----------
    UpgradeDef("drill_overclock", "Overclocked Drills",
               "Ignore manufacturer warnings — double speed.",
               250_000, "crystal_drill", 10, "gen:crystal_drill", 2.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("drill_tungsten",  "Tungsten Teeth",
               "Nothing bites back anymore.",
               25_000_000, "crystal_drill", 25, "gen:crystal_drill", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Clockwork Sapper ----------
    UpgradeDef("sapper_springs", "Mainspring Upgrade",
               "A far prouder ticking. Twice the stride.",
               800_000, "clockwork_sapper", 10, "gen:clockwork_sapper", 2.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("sapper_steam",   "Pressurized Steam",
               "Whistles while they work. Alarmingly.",
               80_000_000, "clockwork_sapper", 25, "gen:clockwork_sapper", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Stone Golem ----------
    UpgradeDef("golem_runestone", "Golem Runestones",
               "Etch 'WORK HARDER' into every golem's chest.",
               2_800_000, "stone_golem", 10, "gen:stone_golem", 2.5,
               max_level=5, cost_growth=4.0),
    UpgradeDef("golem_colossal",  "Colossal Mode",
               "When a golem is simply not big enough.",
               400_000_000, "stone_golem", 25, "gen:stone_golem", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Celestial Chorus ----------
    UpgradeDef("chorus_harmony",  "Fourth Harmony",
               "A secret note above the chord. Stone can't help but oblige.",
               10_000_000, "celestial_chorus", 10, "gen:celestial_chorus", 2.5,
               max_level=5, cost_growth=4.0),
    UpgradeDef("chorus_antiphon", "Antiphonal Rite",
               "Two choirs, answering each other across the deep.",
               1_200_000_000, "celestial_chorus", 25, "gen:celestial_chorus", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Arcane Wizard ----------
    UpgradeDef("wizard_familiars", "Familiar Assistants",
               "Wizards outsource shard-shaping to cat spirits.",
               36_000_000, "arcane_wizard", 10, "gen:arcane_wizard", 2.5,
               max_level=5, cost_growth=4.0),
    UpgradeDef("wizard_mastery",   "Arcane Mastery",
               "They've all published doctoral theses.",
               5_000_000_000, "arcane_wizard", 25, "gen:arcane_wizard", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Rift Anchor ----------
    UpgradeDef("rift_polarity",  "Inverted Polarity",
               "Pulls the good side of elsewhere inside.",
               130_000_000, "rift_anchor", 10, "gen:rift_anchor", 2.5,
               max_level=5, cost_growth=4.0),
    UpgradeDef("rift_widener",   "Rift Widener",
               "Same as before, but much more of it.",
               15_000_000_000, "rift_anchor", 25, "gen:rift_anchor", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Rune Forge ----------
    UpgradeDef("forge_eternal",     "Eternal Coals",
               "The forges never cool. The wizards are concerned.",
               440_000_000, "rune_forge", 10, "gen:rune_forge", 2.5,
               max_level=5, cost_growth=4.0),
    UpgradeDef("forge_primordial",  "Primordial Fuel",
               "Burning the echo of the world's first flame.",
               60_000_000_000, "rune_forge", 25, "gen:rune_forge", 2.5,
               max_level=3, cost_growth=5.0),

    # ---------- Crystal Dragon ----------
    UpgradeDef("dragon_hoard",  "Hoard Multiplier",
               "Crystal Dragons really lean into the greed.",
               5_600_000_000, "crystal_dragon", 10, "gen:crystal_dragon", 2.5,
               max_level=5, cost_growth=4.0),
    UpgradeDef("dragon_elder",  "Elder Wyrmscale",
               "Ancient, scaled, and deeply annoyed.",
               800_000_000_000, "crystal_dragon", 25, "gen:crystal_dragon", 3.0,
               max_level=3, cost_growth=5.0),

    # ---------- Void Whale ----------
    UpgradeDef("whale_pod",     "Migrating Pod",
               "They travel in groups now. The stone shudders.",
               22_000_000_000, "void_whale", 10, "gen:void_whale", 2.5,
               max_level=5, cost_growth=4.0),
    UpgradeDef("whale_deepsong", "Deep Song",
               "A low hum that strips the walls of shards as they pass.",
               2_400_000_000_000, "void_whale", 25, "gen:void_whale", 3.0,
               max_level=3, cost_growth=5.0),

    # ---------- Ancient Titan ----------
    UpgradeDef("titan_strength", "Awakened Strength",
               "Titans now skip leg day too.",
               75_000_000_000, "ancient_titan", 10, "gen:ancient_titan", 2.5,
               max_level=5, cost_growth=4.0),
    UpgradeDef("titan_fall",     "Titanfall",
               "They leap into the shafts. It is concerning.",
               15_000_000_000_000, "ancient_titan", 25, "gen:ancient_titan", 3.0,
               max_level=3, cost_growth=5.0),

    # ---------- Cosmic Weaver ----------
    UpgradeDef("weaver_loom",    "Loom of Fate",
               "They've started weaving tomorrow's shards today.",
               280_000_000_000, "cosmic_weaver", 10, "gen:cosmic_weaver", 3.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("weaver_pattern", "Impossible Pattern",
               "A shape that, examined closely, un-happens.",
               30_000_000_000_000, "cosmic_weaver", 25, "gen:cosmic_weaver", 3.0,
               max_level=3, cost_growth=5.0),

    # ---------- Astral Collective ----------
    UpgradeDef("astral_cosmic",   "Cosmic Consciousness",
               "The cavern achieves group meditation.",
               1_000_000_000_000, "astral_collective", 10, "gen:astral_collective", 3.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("astral_galactic", "Galactic Syndicate",
               "Other galaxies apply for membership.",
               200_000_000_000_000, "astral_collective", 25, "gen:astral_collective", 3.0,
               max_level=3, cost_growth=5.0),

    # ---------- Primordial Hearth ----------
    UpgradeDef("hearth_eternal", "Eternal Ember",
               "A coal that remembers being a star.",
               3_600_000_000_000, "primordial_hearth", 10, "gen:primordial_hearth", 3.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("hearth_forge_gods", "Forge of the Gods",
               "Smithing things that shouldn't exist. They do now.",
               420_000_000_000_000, "primordial_hearth", 25, "gen:primordial_hearth", 3.0,
               max_level=3, cost_growth=5.0),

    # ---------- Universe Tree ----------
    UpgradeDef("tree_rooted",    "Rooted Through Reality",
               "Its roots tickle the bedrock of several worlds.",
               18_000_000_000_000, "universe_tree", 10, "gen:universe_tree", 3.0,
               max_level=5, cost_growth=4.0),
    UpgradeDef("tree_seeded",    "Seeded Epochs",
               "Every fallen leaf sprouts another epoch. A tidy loop.",
               2_000_000_000_000_000, "universe_tree", 25, "gen:universe_tree", 3.0,
               max_level=3, cost_growth=5.0),

    # ---------- Global production ----------
    UpgradeDef("cavern_blessing",  "Cavern's Blessing",
               "The cavern itself smiles upon your operation.",
               50_000_000_000, "stone_golem", 50, "global", 1.5,
               max_level=3, cost_growth=6.0),
    UpgradeDef("deep_harmony",     "Deep Harmony",
               "Every helper hums the same low, perfect chord.",
               5_000_000_000_000, "arcane_wizard", 50, "global", 1.5,
               max_level=3, cost_growth=6.0),
    UpgradeDef("starlight_flow",   "Starlight Flow",
               "A river of light threads through every shaft.",
               800_000_000_000, "ancient_titan", 10, "global", 1.5,
               max_level=3, cost_growth=6.0),
    UpgradeDef("gaea_favor",       "Gaea's Favor",
               "The earth herself enlists in the dig.",
               100_000_000_000_000, "astral_collective", 10, "global", 2.0,
               max_level=3, cost_growth=6.0),
    UpgradeDef("symbiotic_resonance", "Symbiotic Resonance",
               "Every shard, everywhere, at once.",
               10_000_000_000_000_000, "ancient_titan", 50, "global", 2.0,
               max_level=3, cost_growth=6.0),
    UpgradeDef("cosmic_weave",    "Cosmic Weave",
               "All your helpers braid into one quiet machine.",
               500_000_000_000_000, "cosmic_weaver", 50, "global", 2.0,
               max_level=3, cost_growth=6.0),
    UpgradeDef("eternal_bloom",   "Eternal Bloom",
               "The Tree decides to flower once — and the world brightens.",
               50_000_000_000_000_000, "universe_tree", 50, "global", 3.0,
               max_level=3, cost_growth=6.0),
)


UPGRADES_BY_KEY = {u.key: u for u in UPGRADES}


def upgrade_cost_for_level(upgrade: UpgradeDef, next_level: int) -> float:
    """Cost to buy the Nth level (1-indexed) of `upgrade`."""
    if next_level < 1 or next_level > upgrade.max_level:
        raise ValueError(
            f"{upgrade.key} level {next_level} out of range 1..{upgrade.max_level}"
        )
    return upgrade.cost * (upgrade.cost_growth ** (next_level - 1))
