"""Static generator (shop item) definitions and cost math.

A "generator" is an auto-producer the player buys to earn shards passively.
Each tier has a fun flavor name, a base cost, a base production rate
(shards per second *per owned unit*), and a distinct accent color used by
the procedural sprite renderer.

The tuple is ordered by ``base_cost`` — inserting a new tier means picking
its cost slot, and the shop display will slot it in naturally.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from src.constants import COST_GROWTH


@dataclass(frozen=True)
class GeneratorDef:
    key: str
    name: str
    flavor: str
    base_cost: float
    base_production: float  # shards per second per owned unit
    color: tuple[int, int, int]  # RGB accent color for the sprite
    sprite_shape: str
    # Hard cap so every helper has a completionist finish line. 200 is
    # enough to blow past every associated upgrade gate (25, 50, 100)
    # with headroom, without being infinite.
    max_count: int = 200


# Balance goal: ~7–10x cost/production between adjacent tiers. The 10
# "original" tiers stay at their previous keys + costs so saves survive;
# the 10 new tiers slot in between them (and at the end-game) to smooth
# progression and extend the late game.
GENERATORS: Sequence[GeneratorDef] = (
    # ---- Early game ----
    GeneratorDef(
        key="rusty_pickaxe",
        name="Rusty Pickaxe",
        flavor="A chipped relic, but it still swings true.",
        base_cost=15,
        base_production=0.2,
        color=(180, 140, 90),
        sprite_shape="pick",
    ),
    GeneratorDef(
        key="lantern_keeper",
        name="Lantern Keeper",
        flavor="Lights the way. Also surprisingly effective at mining.",
        base_cost=80,
        base_production=0.8,
        color=(255, 200, 120),
        sprite_shape="lantern",
    ),
    GeneratorDef(
        key="apprentice_miner",
        name="Apprentice Miner",
        flavor="Eager, sweaty, and surprisingly productive.",
        base_cost=120,
        base_production=1.2,
        color=(210, 160, 110),
        sprite_shape="dwarf",
    ),
    GeneratorDef(
        key="deep_digger",
        name="Deep Digger",
        flavor="Goes a little too far down for most folk's liking.",
        base_cost=400,
        base_production=4.0,
        color=(140, 100, 70),
        sprite_shape="digger",
    ),
    GeneratorDef(
        key="cart_runner",
        name="Cart Runner",
        flavor="Hauls shards uphill so you don't have to.",
        base_cost=1_200,
        base_production=9.5,
        color=(150, 110, 80),
        sprite_shape="cart",
    ),
    GeneratorDef(
        key="moonstone_mine",
        name="Moonstone Mine",
        flavor="A little shaft that glows all on its own.",
        base_cost=4_500,
        base_production=30.0,
        color=(180, 220, 255),
        sprite_shape="mine",
    ),

    # ---- Mid game ----
    GeneratorDef(
        key="crystal_drill",
        name="Crystal Drill",
        flavor="Clockwork teeth that chew through bedrock.",
        base_cost=13_000,
        base_production=80.0,
        color=(210, 210, 230),
        sprite_shape="drill",
    ),
    GeneratorDef(
        key="clockwork_sapper",
        name="Clockwork Sapper",
        flavor="Brass and steam, tunnelling very politely.",
        base_cost=45_000,
        base_production=240.0,
        color=(210, 160, 80),
        sprite_shape="clockwork",
    ),
    GeneratorDef(
        key="stone_golem",
        name="Stone Golem",
        flavor="Tireless, grumpy, excellent at mining.",
        base_cost=140_000,
        base_production=640.0,
        color=(130, 145, 160),
        sprite_shape="golem",
    ),
    GeneratorDef(
        key="celestial_chorus",
        name="Celestial Chorus",
        flavor="Three voices singing stone into shards.",
        base_cost=500_000,
        base_production=2_000.0,
        color=(230, 210, 255),
        sprite_shape="chorus",
    ),
    GeneratorDef(
        key="arcane_wizard",
        name="Arcane Wizard",
        flavor="Conjures shards from raw moonlight.",
        base_cost=1_800_000,
        base_production=5_200.0,
        color=(140, 110, 230),
        sprite_shape="wizard",
    ),
    GeneratorDef(
        key="rift_anchor",
        name="Rift Anchor",
        flavor="A doorway to somewhere brighter. Do not look directly in.",
        base_cost=6_500_000,
        base_production=16_000.0,
        color=(180, 100, 220),
        sprite_shape="rift",
    ),
    GeneratorDef(
        key="rune_forge",
        name="Rune Forge",
        flavor="Smelts starlight into shard ingots.",
        base_cost=22_000_000,
        base_production=42_000.0,
        color=(255, 150, 80),
        sprite_shape="forge",
    ),

    # ---- Late game ----
    GeneratorDef(
        key="crystal_dragon",
        name="Crystal Dragon",
        flavor="Sneezes out enough shards to fund a kingdom.",
        base_cost=280_000_000,
        base_production=340_000.0,
        color=(120, 220, 200),
        sprite_shape="dragon",
    ),
    GeneratorDef(
        key="void_whale",
        name="Void Whale",
        flavor="Migrates through the stone like it isn't even there.",
        base_cost=1_100_000_000,
        base_production=1_100_000.0,
        color=(80, 120, 200),
        sprite_shape="whale",
    ),
    GeneratorDef(
        key="ancient_titan",
        name="Ancient Titan",
        flavor="Awakens once an age to mine for you.",
        base_cost=3_800_000_000,
        base_production=2_800_000.0,
        color=(230, 180, 90),
        sprite_shape="titan",
    ),
    GeneratorDef(
        key="cosmic_weaver",
        name="Cosmic Weaver",
        flavor="Threads reality into tidy little gems.",
        base_cost=14_000_000_000,
        base_production=8_800_000.0,
        color=(240, 190, 255),
        sprite_shape="weaver",
    ),
    GeneratorDef(
        key="astral_collective",
        name="Astral Collective",
        flavor="The cavern itself has joined the workforce.",
        base_cost=52_000_000_000,
        base_production=24_000_000.0,
        color=(170, 230, 255),
        sprite_shape="astral",
    ),

    # ---- End-game extensions ----
    GeneratorDef(
        key="primordial_hearth",
        name="Primordial Hearth",
        flavor="The first fire — still lit, still working.",
        base_cost=180_000_000_000,
        base_production=70_000_000.0,
        color=(255, 140, 80),
        sprite_shape="hearth",
    ),
    GeneratorDef(
        key="universe_tree",
        name="Universe Tree",
        flavor="Its roots drink light; its leaves drop shards.",
        base_cost=900_000_000_000,
        base_production=260_000_000.0,
        color=(200, 255, 180),
        sprite_shape="tree",
    ),
)


GENERATORS_BY_KEY = {g.key: g for g in GENERATORS}


def cost_for(gen: GeneratorDef, owned: int) -> float:
    """Cost to buy the next unit of this generator given `owned` already owned."""
    return gen.base_cost * (COST_GROWTH ** owned)


def bulk_cost(gen: GeneratorDef, owned: int, count: int) -> float:
    """Total cost to buy `count` more units using the geometric series sum."""
    if count <= 0:
        return 0.0
    # Sum of geometric series: base * r^owned * (r^count - 1) / (r - 1)
    r = COST_GROWTH
    return gen.base_cost * (r ** owned) * ((r ** count) - 1) / (r - 1)


def max_affordable(gen: GeneratorDef, owned: int, wallet: float) -> int:
    """How many more units of `gen` the player can buy with `wallet` shards."""
    if wallet < cost_for(gen, owned):
        return 0
    import math

    r = COST_GROWTH
    limit = 1 + (wallet * (r - 1)) / (gen.base_cost * (r ** owned))
    n = int(math.floor(math.log(limit) / math.log(r)))
    return max(n, 0)
