"""Cavern Lord (mini-boss) math."""

from __future__ import annotations

from src.entities.cavern_lord import (
    boss_hp_for_index,
    boss_reward_for_index,
    spawn_boss,
)


def test_hp_scales_super_linearly_with_index():
    a, b, c = boss_hp_for_index(0), boss_hp_for_index(1), boss_hp_for_index(2)
    assert b > a * 10
    assert c > b * 10


def test_reward_is_proportional_to_hp():
    for i in range(3):
        assert boss_reward_for_index(i) > 0
        assert boss_reward_for_index(i) < boss_hp_for_index(i)


def test_spawned_boss_has_full_hp():
    boss = spawn_boss(0)
    assert boss.hp == boss.max_hp
    assert boss.alive
    assert boss.hp_fraction() == 1.0


def test_take_hit_reduces_hp_and_tracks_kill():
    boss = spawn_boss(0)
    damage = boss.max_hp / 2
    killed = boss.take_hit(damage, click_x=0, click_y=0)
    assert not killed
    assert boss.hp_fraction() == 0.5
    killed = boss.take_hit(damage, click_x=0, click_y=0)
    assert killed
    assert boss.hp == 0
    assert not boss.alive


def test_hits_after_death_do_not_resurrect():
    boss = spawn_boss(0)
    boss.take_hit(boss.max_hp * 2, click_x=0, click_y=0)
    assert not boss.alive
    killed = boss.take_hit(1, click_x=0, click_y=0)
    assert not killed
    assert boss.hp == 0
