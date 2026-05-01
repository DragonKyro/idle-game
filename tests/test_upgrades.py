"""Integrity checks on the upgrade catalog."""

from __future__ import annotations

from src.generators import GENERATORS_BY_KEY
from src.upgrades import UPGRADES, UPGRADES_BY_KEY


def test_upgrade_count_is_plentiful():
    # We expanded the catalog to give at least a couple of upgrades per
    # generator plus click + global progression. Guard against accidental
    # regressions.
    assert len(UPGRADES) >= 25


def test_upgrade_keys_are_unique():
    keys = [u.key for u in UPGRADES]
    assert len(keys) == len(set(keys))


def test_upgrade_requires_key_references_real_generator():
    for upgrade in UPGRADES:
        if upgrade.requires_key is not None:
            assert upgrade.requires_key in GENERATORS_BY_KEY, (
                f"Upgrade {upgrade.key} references unknown generator "
                f"{upgrade.requires_key}"
            )


def test_upgrade_effect_is_well_formed():
    valid_prefixes = {"click", "global"}
    for upgrade in UPGRADES:
        if upgrade.effect in valid_prefixes:
            continue
        assert upgrade.effect.startswith("gen:"), (
            f"{upgrade.key} has unknown effect {upgrade.effect!r}"
        )
        target = upgrade.effect.split(":", 1)[1]
        assert target in GENERATORS_BY_KEY


def test_every_generator_has_at_least_one_upgrade():
    covered = set()
    for upgrade in UPGRADES:
        if upgrade.effect.startswith("gen:"):
            covered.add(upgrade.effect.split(":", 1)[1])
    missing = set(GENERATORS_BY_KEY) - covered
    assert not missing, f"Generators without upgrades: {missing}"


def test_at_least_four_click_upgrades():
    click_upgrades = [u for u in UPGRADES if u.effect == "click"]
    assert len(click_upgrades) >= 4


def test_at_least_three_global_upgrades():
    globals_ = [u for u in UPGRADES if u.effect == "global"]
    assert len(globals_) >= 3


def test_upgrades_by_key_is_complete():
    assert len(UPGRADES_BY_KEY) == len(UPGRADES)
