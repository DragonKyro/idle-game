"""Unit tests for generator cost math."""

from __future__ import annotations

import math

from src.constants import COST_GROWTH
from src.generators import (
    GENERATORS,
    GENERATORS_BY_KEY,
    bulk_cost,
    cost_for,
    max_affordable,
)


def test_every_tier_is_more_expensive_than_previous():
    costs = [g.base_cost for g in GENERATORS]
    assert costs == sorted(costs)


def test_every_tier_produces_more_than_previous_per_unit():
    rates = [g.base_production for g in GENERATORS]
    assert rates == sorted(rates)


def test_cost_growth_matches_formula():
    gen = GENERATORS[0]
    for owned in range(10):
        expected = gen.base_cost * (COST_GROWTH ** owned)
        assert math.isclose(cost_for(gen, owned), expected, rel_tol=1e-9)


def test_bulk_cost_matches_manual_sum():
    gen = GENERATORS[1]
    owned = 3
    count = 5
    manual = sum(cost_for(gen, owned + i) for i in range(count))
    assert math.isclose(bulk_cost(gen, owned, count), manual, rel_tol=1e-9)


def test_bulk_cost_zero_is_zero():
    assert bulk_cost(GENERATORS[0], 0, 0) == 0


def test_max_affordable_is_zero_when_broke():
    gen = GENERATORS[0]
    assert max_affordable(gen, owned=0, wallet=0) == 0


def test_max_affordable_matches_incremental_purchase():
    gen = GENERATORS[0]
    owned = 2
    wallet = 10_000
    n = max_affordable(gen, owned, wallet)
    # Cumulative cost of n purchases should fit; n+1 should not.
    assert bulk_cost(gen, owned, n) <= wallet + 1e-6
    assert bulk_cost(gen, owned, n + 1) > wallet


def test_generators_by_key_is_complete():
    assert len(GENERATORS_BY_KEY) == len(GENERATORS)
    for gen in GENERATORS:
        assert GENERATORS_BY_KEY[gen.key] is gen


def test_generator_count_matches_expansion_target():
    # Expansion brings the catalog to 20. Guard against accidental drops.
    assert len(GENERATORS) >= 20


def test_every_generator_has_a_registered_sprite():
    from src.sprite_factory import _SHAPE_RENDERERS
    for gen in GENERATORS:
        assert gen.sprite_shape in _SHAPE_RENDERERS, (
            f"{gen.key} references unknown sprite shape {gen.sprite_shape}"
        )


def test_generator_keys_unique():
    keys = [g.key for g in GENERATORS]
    assert len(keys) == len(set(keys))
