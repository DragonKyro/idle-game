"""Persistent decorative ring of progress around the main crystal.

Every time the player buys something, this aura gains a *permanent* visual
element — a small generator emblem joins the orbit the first time they buy
a new tier, and a gold star appears on the outer ring for each upgrade
level purchased. The transient toast/flash/particle pulse still fires for
immediate feedback, but the aura gives the play area a lasting record of
progression that the bottom-left roster alone couldn't convey.
"""

from __future__ import annotations

import math

import arcade
from arcade.types import Color

from src.entities.main_clicker import (
    CRYSTAL_BASE_SIZE,
    CRYSTAL_CENTER_X,
    CRYSTAL_CENTER_Y,
)
from src.game_state import GameState
from src.generators import GENERATORS


# Inner ring — generator tier emblems orbit here.
_EMBLEM_RADIUS = CRYSTAL_BASE_SIZE * 0.62
_EMBLEM_SIZE = 36
_EMBLEM_ORBIT_PERIOD = 30.0  # seconds for a full rotation

# Outer ring — a gold star per purchased upgrade level.
_STAR_RADIUS = CRYSTAL_BASE_SIZE * 0.78
_MAX_STARS = 48  # caps visual clutter; more than enough to feel earned
_STAR_COLOR = Color(255, 220, 120, 255)


class CrystalAura:
    """Purely visual — derives everything from ``GameState`` each frame."""

    def __init__(self, generator_textures: dict[str, arcade.Texture]) -> None:
        self._generator_textures = generator_textures
        self._time = 0.0

    def update(self, delta: float) -> None:
        self._time += delta

    def draw(self, state: GameState) -> None:
        self._draw_upgrade_stars(state)
        self._draw_generator_emblems(state)

    # ------------------------------------------------------------------
    # Layers.
    # ------------------------------------------------------------------

    def _draw_generator_emblems(self, state: GameState) -> None:
        """One small tier emblem per distinct generator type owned.

        Arranged evenly on a slowly rotating orbit. An emblem appears the
        first time a generator type is bought and stays forever.
        """
        owned_tiers = [g for g in GENERATORS if state.owned.get(g.key, 0) > 0]
        if not owned_tiers:
            return

        count = len(owned_tiers)
        base_angle = (self._time / _EMBLEM_ORBIT_PERIOD) * math.tau
        for i, gen in enumerate(owned_tiers):
            angle = base_angle + (i / count) * math.tau
            x = CRYSTAL_CENTER_X + _EMBLEM_RADIUS * math.cos(angle)
            y = CRYSTAL_CENTER_Y + _EMBLEM_RADIUS * math.sin(angle)
            tex = self._generator_textures.get(gen.key)
            if tex is None:
                continue
            # Subtle backing disc ties each emblem to the aura visually.
            arcade.draw_circle_filled(x, y, _EMBLEM_SIZE * 0.45, (30, 24, 52, 180))
            arcade.draw_circle_outline(
                x, y, _EMBLEM_SIZE * 0.45, (110, 96, 160, 200), border_width=1,
            )
            rect = arcade.LBWH(
                x - _EMBLEM_SIZE / 2, y - _EMBLEM_SIZE / 2,
                _EMBLEM_SIZE, _EMBLEM_SIZE,
            )
            arcade.draw_texture_rect(tex, rect)

    def _draw_upgrade_stars(self, state: GameState) -> None:
        """One tiny star per upgrade level purchased, evenly spaced on a
        wider ring. Once you hit ``_MAX_STARS`` levels, later levels still
        register (via game mechanics and the crystal-tier bump) but don't
        add more dots — the ring stays visually readable."""
        total = min(state.total_upgrade_levels(), _MAX_STARS)
        if total <= 0:
            return

        # A gentle counter-rotation makes the rings feel alive.
        base_angle = -(self._time / (_EMBLEM_ORBIT_PERIOD * 1.5)) * math.tau
        for i in range(total):
            angle = base_angle + (i / _MAX_STARS) * math.tau
            x = CRYSTAL_CENTER_X + _STAR_RADIUS * math.cos(angle)
            y = CRYSTAL_CENTER_Y + _STAR_RADIUS * math.sin(angle)
            arcade.draw_circle_filled(x, y, 3, _STAR_COLOR)
            # Tiny highlight for a 'gem' feel.
            arcade.draw_circle_filled(x - 1, y + 1, 1, (255, 255, 255, 220))
