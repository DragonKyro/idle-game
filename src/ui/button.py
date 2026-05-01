"""Simple rectangular button rendered with arcade primitives.

Text labels live on whoever owns the button (as cached ``arcade.Text``
objects) so we avoid the per-frame cost of ``arcade.draw_text``.
"""

from __future__ import annotations

from dataclasses import dataclass

import arcade

from src.constants import (
    COLOR_BUTTON_AFFORD,
    COLOR_BUTTON_AFFORD_HOVER,
    COLOR_BUTTON_DISABLED,
    COLOR_BUTTON_HOVER,
    COLOR_BUTTON_IDLE,
    COLOR_PANEL_BORDER,
)


@dataclass
class Button:
    """Rectangular button with hover/affordability states.

    Coordinates are (left, bottom, width, height) in arcade's bottom-up
    window space.
    """

    left: float
    bottom: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def top(self) -> float:
        return self.bottom + self.height

    @property
    def center_x(self) -> float:
        return self.left + self.width / 2

    @property
    def center_y(self) -> float:
        return self.bottom + self.height / 2

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.bottom <= y <= self.top

    def draw_background(
        self,
        *,
        hovered: bool,
        affordable: bool,
        enabled: bool = True,
    ) -> None:
        if not enabled:
            fill = COLOR_BUTTON_DISABLED
        elif affordable:
            fill = COLOR_BUTTON_AFFORD_HOVER if hovered else COLOR_BUTTON_AFFORD
        else:
            fill = COLOR_BUTTON_HOVER if hovered else COLOR_BUTTON_IDLE
        rect = arcade.LBWH(self.left, self.bottom, self.width, self.height)
        arcade.draw_rect_filled(rect, fill)
        arcade.draw_rect_outline(rect, COLOR_PANEL_BORDER, border_width=2)
