"""Static generator (shop item) definitions and cost math.

A "generator" is an auto-producer the player buys to earn shards passively.
Each tier has a fun flavor name, a base cost, a base production rate
(shards per second *per owned unit*), and a distinct accent color used by the
procedural sprite renderer.
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
    sprite_shape: str  # hint for procedural sprite: 'pick', 'dwarf', 'cart',
    # 'drill', 'golem', 'wizard', 'forge', 'dragon', 'titan', 'astral'


# Balance goal: each tier costs roughly 10x the previous and produces ~7–9x,
# so later tiers pay off best but earlier ones stay relevant for a while.
GENERATORS: Sequence[GeneratorDef] = (
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
        key="apprentice_miner",
        name="Apprentice Miner",
        flavor="Eager, sweaty, and surprisingly productive.",
        base_cost=120,
        base_production=1.2,
        color=(210, 160, 110),
        sprite_shape="dwarf",
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
        key="crystal_drill",
        name="Crystal Drill",
        flavor="Clockwork teeth that chew through bedrock.",
        base_cost=13_000,
        base_production=80.0,
        color=(210, 210, 230),
        sprite_shape="drill",
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
        key="arcane_wizard",
        name="Arcane Wizard",
        flavor="Conjures shards from raw moonlight.",
        base_cost=1_800_000,
        base_production=5_200.0,
        color=(140, 110, 230),
        sprite_shape="wizard",
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
        key="ancient_titan",
        name="Ancient Titan",
        flavor="Awakens once an age to mine for you.",
        base_cost=3_800_000_000,
        base_production=2_800_000.0,
        color=(230, 180, 90),
        sprite_shape="titan",
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
    # Solve for largest n with bulk_cost(n) <= wallet. Closed form:
    # wallet >= base * r^owned * (r^n - 1) / (r - 1)
    #   => r^n <= 1 + wallet*(r-1) / (base * r^owned)
    import math

    r = COST_GROWTH
    limit = 1 + (wallet * (r - 1)) / (gen.base_cost * (r ** owned))
    n = int(math.floor(math.log(limit) / math.log(r)))
    return max(n, 0)
