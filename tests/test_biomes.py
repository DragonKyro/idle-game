"""Biome rotation tests."""

from __future__ import annotations

from src.biomes import BIOMES, biome_for_prestige


def test_six_or_more_biomes_defined():
    assert len(BIOMES) >= 6


def test_biome_keys_unique():
    keys = [b.key for b in BIOMES]
    assert len(keys) == len(set(keys))


def test_biome_for_prestige_cycles():
    # First biome at prestige 0.
    assert biome_for_prestige(0) is BIOMES[0]
    # Cycles back around for prestige counts beyond the list.
    assert biome_for_prestige(len(BIOMES)) is BIOMES[0]
    assert biome_for_prestige(len(BIOMES) + 1) is BIOMES[1]


def test_each_biome_has_distinct_palette():
    palettes = {(b.bg_top, b.bg_bottom) for b in BIOMES}
    assert len(palettes) == len(BIOMES)
