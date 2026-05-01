"""Random events — Golden Shard + Lucky Critter.

These spawn at random intervals in the play area. Clicking them grants
a reward (shards or a temporary production buff). Missing them lets
them expire; no penalty.

The spawn cadence is shaped by ``GameState.event_rate_multiplier()``
so the ``lucky_strike`` talent actually matters.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import arcade
from arcade.types import Color

from src.constants import PLAY_AREA_WIDTH, SCREEN_HEIGHT
from src.game_state import GameState


_BASE_SPAWN_INTERVAL = (45.0, 120.0)  # seconds; randomized between these bounds
_GOLDEN_SHARD_LIFETIME = 10.0
_CRITTER_LIFETIME = 8.0
_BUFF_DURATION = 30.0
_BUFF_MULTIPLIER = 2.0

# Events spawn somewhere in the play area, avoiding the HUD and the
# crystal's hit zone. These bounds are intentionally generous.
_SPAWN_X_MIN = 80
_SPAWN_X_MAX_OFFSET = 80  # from PLAY_AREA_WIDTH
_SPAWN_Y_MIN = 140        # above the descend button
_SPAWN_Y_MAX_OFFSET = 180  # from SCREEN_HEIGHT (below HUD)


@dataclass
class ActiveEvent:
    kind: str        # "golden" or "critter"
    x: float
    y: float
    age: float = 0.0
    lifetime: float = _GOLDEN_SHARD_LIFETIME
    hit: bool = False

    @property
    def alive(self) -> bool:
        return not self.hit and self.age < self.lifetime

    def contains(self, x: float, y: float) -> bool:
        dx = x - self.x
        dy = y - self.y
        return dx * dx + dy * dy <= 30 ** 2


class RandomEventLayer:
    """Session-scoped (not saved). Buff timers are kept here so talents
    stay in save state and buffs don't accidentally persist across runs."""

    def __init__(self) -> None:
        self._active: list[ActiveEvent] = []
        self._time_until_next: float = random.uniform(*_BASE_SPAWN_INTERVAL)
        self._buff_remaining: float = 0.0
        self._time: float = 0.0
        self._recent_event_reward: str | None = None
        self._recent_buff_remaining_cache: float = 0.0

    # -- public interface ----------------------------------------------

    @property
    def buff_multiplier(self) -> float:
        return _BUFF_MULTIPLIER if self._buff_remaining > 0 else 1.0

    @property
    def buff_remaining(self) -> float:
        return self._buff_remaining

    def update(self, delta: float, state: GameState) -> None:
        self._time += delta
        if self._buff_remaining > 0:
            self._buff_remaining = max(0.0, self._buff_remaining - delta)

        # Age out events.
        for e in self._active:
            e.age += delta
        self._active = [e for e in self._active if e.alive]

        # Spawn cadence — multiplier compresses the countdown when the
        # lucky_strike talent is owned.
        rate_mult = state.event_rate_multiplier()
        self._time_until_next -= delta * rate_mult
        if self._time_until_next <= 0 and len(self._active) < 2:
            self._spawn()
            lo, hi = _BASE_SPAWN_INTERVAL
            self._time_until_next = random.uniform(lo, hi)

    def handle_click(self, x: float, y: float, state: GameState) -> str | None:
        """Process a click. Returns a short description of the reward if
        one was granted, else None (click falls through to other
        handlers)."""
        for e in self._active:
            if e.hit:
                continue
            if e.contains(x, y):
                return self._apply_reward(e, state)
        return None

    def draw(self) -> None:
        for e in self._active:
            self._draw_event(e)

    # -- spawning + rewards --------------------------------------------

    def _spawn(self) -> None:
        kind = random.choice(("golden", "critter"))
        x = random.uniform(_SPAWN_X_MIN, PLAY_AREA_WIDTH - _SPAWN_X_MAX_OFFSET)
        y = random.uniform(_SPAWN_Y_MIN, SCREEN_HEIGHT - _SPAWN_Y_MAX_OFFSET)
        lifetime = _GOLDEN_SHARD_LIFETIME if kind == "golden" else _CRITTER_LIFETIME
        self._active.append(ActiveEvent(kind=kind, x=x, y=y, lifetime=lifetime))

    def _apply_reward(self, event: ActiveEvent, state: GameState) -> str:
        event.hit = True
        if event.kind == "golden":
            # 60 seconds of current production, minimum 10.
            gained = max(10.0, state.total_rate() * 60.0)
            state.shards += gained
            state.total_earned += gained
            from src.number_format import format_number
            return f"Golden Shard! +{format_number(gained)}"
        else:
            self._buff_remaining = _BUFF_DURATION
            return f"Lucky Critter! x{_BUFF_MULTIPLIER:g} production for "\
                   f"{int(_BUFF_DURATION)}s"

    # -- rendering -----------------------------------------------------

    def _draw_event(self, event: ActiveEvent) -> None:
        # Fade in and out at the edges of lifetime so missing one looks
        # intentional, not buggy.
        t = event.age / event.lifetime
        if t < 0.1:
            fade = t / 0.1
        elif t > 0.8:
            fade = max(0.0, (1.0 - t) / 0.2)
        else:
            fade = 1.0
        alpha = max(0, min(255, int(255 * fade)))

        # Gentle hover bob.
        bob = math.sin(self._time * 3 + event.age * 4) * 4
        y = event.y + bob

        if event.kind == "golden":
            color = (255, 215, 100)
            self._draw_shard(event.x, y, color, alpha)
        else:
            color = (180, 255, 200)
            self._draw_critter(event.x, y, color, alpha)

    def _draw_shard(self, x, y, color, alpha) -> None:
        # Glowing diamond.
        for r, a_mul in ((26, 0.35), (18, 0.7), (12, 1.0)):
            arcade.draw_circle_filled(
                x, y, r, Color(color[0], color[1], color[2], int(alpha * a_mul * 0.5)),
            )
        # Diamond shape (rotated square) via two filled triangles.
        pts = [(x, y + 14), (x + 10, y), (x, y - 14), (x - 10, y)]
        arcade.draw_polygon_filled(pts, Color(*color, alpha))
        arcade.draw_polygon_outline(pts, Color(255, 255, 255, alpha), line_width=2)

    def _draw_critter(self, x, y, color, alpha) -> None:
        # Small round body with two antennae and two eyes.
        arcade.draw_circle_filled(x, y, 20, Color(*color, alpha))
        arcade.draw_circle_outline(x, y, 20, Color(40, 40, 60, alpha), border_width=2)
        # Eyes.
        arcade.draw_circle_filled(x - 6, y + 2, 3, Color(30, 30, 45, alpha))
        arcade.draw_circle_filled(x + 6, y + 2, 3, Color(30, 30, 45, alpha))
        # Antennae.
        arcade.draw_line(x - 6, y + 14, x - 10, y + 22, Color(40, 40, 60, alpha), 2)
        arcade.draw_line(x + 6, y + 14, x + 10, y + 22, Color(40, 40, 60, alpha), 2)
        arcade.draw_circle_filled(x - 10, y + 22, 2, Color(*color, alpha))
        arcade.draw_circle_filled(x + 10, y + 22, 2, Color(*color, alpha))
