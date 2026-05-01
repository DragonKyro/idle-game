"""Juice helpers — screen shake and value tweening.

Keeping the math centralized means every caller gets the same feel, and
turning ``reduced_motion`` on from settings in one place disables them
globally.
"""

from __future__ import annotations

import math
import random


class ScreenShake:
    """Short, decaying 2D offset applied to the render transform.

    Larger ``trauma`` values mean bigger, longer shakes. Trauma is
    squared when applied so small nudges feel subtle while big events
    really rattle.
    """

    def __init__(self) -> None:
        self._trauma = 0.0
        self._time = 0.0
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = bool(value)
        if not value:
            self._trauma = 0.0

    def bump(self, trauma: float) -> None:
        """Add trauma to the shake. Values ~0.3 for a click, ~0.8 for a
        boss defeat, ~1.0 for a descent."""
        if not self._enabled:
            return
        self._trauma = min(1.0, self._trauma + trauma)

    def update(self, delta: float) -> None:
        if self._trauma > 0:
            self._trauma = max(0.0, self._trauma - delta * 1.5)
        self._time += delta

    def offset(self, *, max_magnitude: float = 12.0) -> tuple[float, float]:
        if self._trauma <= 0:
            return 0.0, 0.0
        shake = (self._trauma ** 2) * max_magnitude
        # Perlin-style pseudo-noise from sin with irrational frequencies.
        t = self._time * 20
        return (
            shake * math.sin(t * 1.3 + 1.7),
            shake * math.sin(t * 1.7 + 3.1),
        )


class TweenedValue:
    """Eases toward a target value — handy for wallet displays so they
    count up rather than snap.

    ``rate`` is the fraction of the remaining gap closed per second, so
    ``rate=6`` means 63% of the gap closes in ~0.17s. Linear + a floor
    keep the final digits from lingering forever.
    """

    __slots__ = ("_value", "_target", "_rate", "_enabled")

    def __init__(self, initial: float = 0.0, *, rate: float = 6.0) -> None:
        self._value = float(initial)
        self._target = float(initial)
        self._rate = rate
        self._enabled = True

    @property
    def value(self) -> float:
        return self._value

    @property
    def target(self) -> float:
        return self._target

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = bool(value)
        if not value:
            self._value = self._target

    def set(self, target: float, *, snap: bool = False) -> None:
        self._target = float(target)
        if snap or not self._enabled:
            self._value = self._target

    def update(self, delta: float) -> None:
        if not self._enabled or self._value == self._target:
            self._value = self._target
            return
        gap = self._target - self._value
        step = gap * (1.0 - math.exp(-self._rate * delta))
        self._value += step
        # Floor so tiny deltas snap (otherwise the last 0.01 takes forever).
        if abs(self._target - self._value) < 1.0:
            self._value = self._target
