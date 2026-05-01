"""Juice helpers — screen shake and tweened values."""

from __future__ import annotations

import math

from src.ui.juice import ScreenShake, TweenedValue


def test_shake_starts_still():
    s = ScreenShake()
    assert s.offset() == (0.0, 0.0)


def test_shake_bump_produces_motion():
    s = ScreenShake()
    s.bump(1.0)
    s.update(0.0)
    dx, dy = s.offset(max_magnitude=10)
    # Expect a non-trivial offset within the configured magnitude.
    assert 0 < math.hypot(dx, dy) <= 10 * math.sqrt(2) + 1e-6


def test_shake_decays_over_time():
    s = ScreenShake()
    s.bump(1.0)
    s.update(5.0)  # plenty of time to decay
    assert s.offset() == (0.0, 0.0)


def test_shake_disabled_is_silent():
    s = ScreenShake()
    s.enabled = False
    s.bump(1.0)
    assert s.offset() == (0.0, 0.0)


def test_tween_eases_toward_target():
    v = TweenedValue(0.0, rate=5.0)
    v.set(100.0)
    # After one "half-life"-ish step we should be partway there.
    v.update(0.2)
    assert 0 < v.value < 100
    # Enough time and we snap.
    v.update(10.0)
    assert v.value == 100.0


def test_tween_snap_when_disabled():
    v = TweenedValue(0.0)
    v.enabled = False
    v.set(50.0)
    assert v.value == 50.0


def test_tween_explicit_snap():
    v = TweenedValue(0.0, rate=5.0)
    v.set(999.0, snap=True)
    assert v.value == 999.0
