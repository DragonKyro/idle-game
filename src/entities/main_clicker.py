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
        self._purchase_anim = 0.0  # stronger, slower pulse on purchases
        self._hover = False
        self._prompt = arcade.Text(
            "Tap the crystal to mine!",
            CRYSTAL_CENTER_X,
            CRYSTAL_CENTER_Y - CRYSTAL_BASE_SIZE / 2 - 40,
            COLOR_TEXT_SECONDARY,
            font_size=14, anchor_x="center", anchor_y="center", italic=True,
        )

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
        # Purchase animation decays more slowly so it reads as distinct.
        self._purchase_anim *= math.exp(-delta * 3.0)

    def register_click(self) -> None:
        self._click_anim = 1.0

    def register_purchase(self) -> None:
        """A bigger, slower pulse than a click — confirms a shop purchase."""
        self._purchase_anim = 1.0

    def set_texture(self, texture: arcade.Texture) -> None:
        """Swap the crystal appearance. Call when tier changes."""
        self._texture = texture

    def set_hover(self, hovered: bool) -> None:
        self._hover = hovered

    # ------------------------------------------------------------------
    # Rendering.
    # ------------------------------------------------------------------

    def draw(self) -> None:
        # Ambient + hover breathing.
        ambient = 1.0 + 0.03 * math.sin(self._time * 1.8)
        hover_boost = 1.04 if self._hover else 1.0
        click_bump = 1.0 + 0.18 * self._click_anim
        # Purchase bump is slightly larger; combines with click_anim when both fire.
        purchase_bump = 1.0 + 0.22 * self._purchase_anim
        scale = ambient * hover_boost * click_bump * purchase_bump
        size = CRYSTAL_BASE_SIZE * scale

        rect = arcade.LBWH(
            CRYSTAL_CENTER_X - size / 2,
            CRYSTAL_CENTER_Y - size / 2,
            size,
            size,
        )

        halo = max(
            self._click_anim,
            self._purchase_anim,
            0.6 if self._hover else 0.0,
        )
        if halo > 0.01:
            halo_size = size * (1.15 + 0.25 * max(self._click_anim, self._purchase_anim))
            halo_rect = arcade.LBWH(
                CRYSTAL_CENTER_X - halo_size / 2,
                CRYSTAL_CENTER_Y - halo_size / 2,
                halo_size,
                halo_size,
            )
            arcade.draw_texture_rect(
                self._texture,
                halo_rect,
                alpha=int(140 * halo),
            )

        arcade.draw_texture_rect(self._texture, rect)
        self._prompt.draw()
