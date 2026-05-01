"""Combo charge system for rapid-click bonuses.

Each click within ``_COMBO_WINDOW`` seconds of the previous click adds
``_COMBO_PER_CLICK`` to the charge (capped at 1.0). Charge decays
steadily between clicks. The effective multiplier applied to clicks is
``1 + charge * _MAX_BONUS``, so at full charge the player gets a 5x
click — which feels great without invalidating the idle half of the
game (since it only affects *active* clicks, not the per-second rate).
"""

from __future__ import annotations

import arcade

from src.constants import (
    COLOR_PANEL_BORDER,
    COLOR_TEXT_GOLD,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    PLAY_AREA_WIDTH,
    SCREEN_HEIGHT,
)


_COMBO_WINDOW = 1.0         # seconds between clicks to keep combo alive
_COMBO_PER_CLICK = 0.09     # charge added per click
_COMBO_DECAY_RATE = 0.35    # charge lost per second when idle
_MAX_BONUS = 4.0            # 1 + 4 = up to 5x effective click

_METER_WIDTH = 260
_METER_HEIGHT = 14
_METER_MARGIN_BOTTOM = 110


class ComboMeter:
    """Tracks combo charge and renders a meter under the crystal."""

    def __init__(self) -> None:
        self._charge: float = 0.0
        self._time_since_click: float = 0.0

        # Pre-built label shown above the meter.
        self._label = arcade.Text(
            "", 0, 0, COLOR_TEXT_PRIMARY,
            font_size=12, anchor_x="center", anchor_y="baseline", bold=True,
        )
        self._sub = arcade.Text(
            "combo", 0, 0, COLOR_TEXT_SECONDARY,
            font_size=9, anchor_x="center", anchor_y="baseline",
        )

    @property
    def charge(self) -> float:
        return self._charge

    @property
    def bonus_multiplier(self) -> float:
        """Multiplier to apply to a click's base power right now."""
        return 1.0 + self._charge * _MAX_BONUS

    def register_click(self) -> None:
        # If it's been too long since the last click, start fresh.
        if self._time_since_click > _COMBO_WINDOW:
            self._charge = _COMBO_PER_CLICK
        else:
            self._charge = min(1.0, self._charge + _COMBO_PER_CLICK)
        self._time_since_click = 0.0

    def update(self, delta: float) -> None:
        self._time_since_click += delta
        if self._time_since_click > _COMBO_WINDOW:
            # Decay only after the grace window has elapsed.
            self._charge = max(0.0, self._charge - _COMBO_DECAY_RATE * delta)

    def draw(self) -> None:
        if self._charge <= 0.01:
            return

        meter_left = PLAY_AREA_WIDTH / 2 - _METER_WIDTH / 2
        meter_bottom = _METER_MARGIN_BOTTOM
        # Frame.
        frame = arcade.LBWH(meter_left, meter_bottom, _METER_WIDTH, _METER_HEIGHT)
        arcade.draw_rect_filled(frame, (20, 16, 36, 220))
        arcade.draw_rect_outline(frame, COLOR_PANEL_BORDER, border_width=1)

        # Fill gradient-ish: two rectangles stacked for a gold-to-red hot streak.
        fill_w = _METER_WIDTH * self._charge
        cold = (255, 220, 120, 230)
        hot = (255, 140, 100, 230)
        # Blend based on charge.
        blend = self._charge
        r = int(cold[0] * (1 - blend) + hot[0] * blend)
        g = int(cold[1] * (1 - blend) + hot[1] * blend)
        b = int(cold[2] * (1 - blend) + hot[2] * blend)
        fill = arcade.LBWH(meter_left, meter_bottom, fill_w, _METER_HEIGHT)
        arcade.draw_rect_filled(fill, (r, g, b, 230))

        # Label.
        self._label.x = PLAY_AREA_WIDTH / 2
        self._label.y = meter_bottom + _METER_HEIGHT + 4
        self._label.text = f"x{self.bonus_multiplier:.1f}"
        self._label.color = COLOR_TEXT_GOLD
        self._label.draw()

        self._sub.x = PLAY_AREA_WIDTH / 2
        self._sub.y = meter_bottom - 10
        self._sub.draw()
