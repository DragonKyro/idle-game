"""The big tappable crystal in the center of the play area."""

from __future__ import annotations

import math

import arcade

from src.constants import (
    COLOR_TEXT_SECONDARY,
    PLAY_AREA_WIDTH,
    SCREEN_HEIGHT,
)


CRYSTAL_CENTER_X = PLAY_AREA_WIDTH / 2
CRYSTAL_CENTER_Y = (SCREEN_HEIGHT - 140) / 2 + 20  # below the HUD
CRYSTAL_BASE_SIZE = 320  # visible pixel diameter of the sprite


class MainClicker:
    """Renders and animates the primary clickable crystal.

    Visual states:
      - Ambient: gentle sine-wave pulse.
      - Click:   quick squish-and-pop overlaid on the ambient pulse.
    """

    def __init__(self, texture: arcade.Texture) -> None:
        self._texture = texture
        self._time = 0.0
        self._click_anim = 0.0  # decays from 1 -> 0 after a click
        self._hover = False

    # ------------------------------------------------------------------
    # Geometry helpers.
    # ------------------------------------------------------------------

    @property
    def center_x(self) -> float:
        return CRYSTAL_CENTER_X

    @property
    def center_y(self) -> float:
        return CRYSTAL_CENTER_Y

    def contains(self, x: float, y: float) -> bool:
        # Approximate the hex as a circle for hit testing — close enough.
        dx = x - CRYSTAL_CENTER_X
        dy = y - CRYSTAL_CENTER_Y
        return dx * dx + dy * dy <= (CRYSTAL_BASE_SIZE * 0.45) ** 2

    # ------------------------------------------------------------------
    # Updates.
    # ------------------------------------------------------------------

    def update(self, delta: float) -> None:
        self._time += delta
        # Click animation decays exponentially — snappy feel without a cliff.
        self._click_anim *= math.exp(-delta * 7.0)

    def register_click(self) -> None:
        self._click_anim = 1.0

    def set_hover(self, hovered: bool) -> None:
        self._hover = hovered

    # ------------------------------------------------------------------
    # Rendering.
    # ------------------------------------------------------------------

    def draw(self) -> None:
        # Ambient + hover breathing.
        ambient = 1.0 + 0.03 * math.sin(self._time * 1.8)
        hover_boost = 1.04 if self._hover else 1.0
        # Click squish: briefly bigger, then back.
        click_bump = 1.0 + 0.18 * self._click_anim
        scale = ambient * hover_boost * click_bump
        size = CRYSTAL_BASE_SIZE * scale

        rect = arcade.LBWH(
            CRYSTAL_CENTER_X - size / 2,
            CRYSTAL_CENTER_Y - size / 2,
            size,
            size,
        )

        # Glow halo when hovered or freshly clicked.
        halo = max(self._click_anim, 0.6 if self._hover else 0.0)
        if halo > 0.01:
            halo_size = size * (1.15 + 0.2 * self._click_anim)
            halo_rect = arcade.LBWH(
                CRYSTAL_CENTER_X - halo_size / 2,
                CRYSTAL_CENTER_Y - halo_size / 2,
                halo_size,
                halo_size,
            )
            arcade.draw_texture_rect(
                self._texture,
                halo_rect,
                alpha=int(120 * halo),
            )

        arcade.draw_texture_rect(self._texture, rect)

        # Prompt text beneath the crystal when the game is first starting.
        arcade.draw_text(
            "Tap the crystal to mine!",
            CRYSTAL_CENTER_X,
            CRYSTAL_CENTER_Y - CRYSTAL_BASE_SIZE / 2 - 40,
            COLOR_TEXT_SECONDARY,
            font_size=14,
            anchor_x="center",
            anchor_y="center",
            italic=True,
        )
