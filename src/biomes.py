"""Cavern biomes — the background palette rotates as the player descends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Biome:
    key: str
    name: str
    bg_top: tuple[int, int, int]
    bg_bottom: tuple[int, int, int]
    mote_color: tuple[int, int, int]


BIOMES: Sequence[Biome] = (
    Biome("cavern",    "The Cavern",
          bg_top=(22, 18, 40),   bg_bottom=(8, 6, 18),   mote_color=(200, 220, 255)),
    Biome("verdant",   "Verdant Hollows",
          bg_top=(12, 36, 28),   bg_bottom=(4, 14, 12),  mote_color=(180, 255, 220)),
    Biome("dusk",      "Dusk Grotto",
          bg_top=(40, 18, 48),   bg_bottom=(16, 6, 24),  mote_color=(230, 180, 255)),
    Biome("ember",     "Ember Deep",
          bg_top=(48, 20, 16),   bg_bottom=(18, 6, 4),   mote_color=(255, 190, 120)),
    Biome("abyss",     "Abyssal Rift",
          bg_top=(6, 20, 40),    bg_bottom=(2, 4, 16),   mote_color=(150, 210, 255)),
    Biome("astral",    "Astral Expanse",
          bg_top=(14, 10, 52),   bg_bottom=(2, 2, 14),   mote_color=(255, 255, 255)),
)


def biome_for_prestige(prestige_count: int) -> Biome:
    """Which biome the play area should display. Cycles so players who
    prestige far past our list still see variety."""
    if not BIOMES:
        raise RuntimeError("No biomes defined")
    return BIOMES[prestige_count % len(BIOMES)]
