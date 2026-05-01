"""Short-lived banner that slides in when an achievement unlocks."""

from __future__ import annotations

import math

import arcade

from src.achievements import AchievementDef
from src.constants import (
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_DIM,
    COLOR_TEXT_PRIMARY,
    PLAY_AREA_WIDTH,
)


_BANNER_LIFETIME = 3.5
_BANNER_W = 360
_BANNER_H = 72


class _Banner:
    __slots__ = ("_ach", "_title", "_desc", "age")

    def __init__(self, ach: AchievementDef) -> None:
        self._ach = ach
        self._title = arcade.Text(
            f"★  {ach.name}", 0, 0, COLOR_TEXT_PRIMARY,
            font_size=14, anchor_y="baseline", bold=True,
        )
        self._desc = arcade.Text(
            ach.description, 0, 0, COLOR_TEXT_DIM,
            font_size=11, anchor_y="baseline", italic=True,
        )
        self.age = 0.0

    @property
    def alive(self) -> bool:
        return self.age < _BANNER_LIFETIME

    def update(self, delta: float) -> None:
        self.age += delta

    def draw(self, *, slot: int) -> None:
        # Slide-in from the left over 0.3s, then hold, then fade out over
        # the last 0.6s. Slots stack vertically beneath the HUD strip.
        t = self.age / _BANNER_LIFETIME
        slide = min(1.0, self.age / 0.3)
        eased_slide = 1 - (1 - slide) ** 3  # ease-out cubic
        offset_x = -_BANNER_W * (1 - eased_slide)

        if self.age > _BANNER_LIFETIME - 0.6:
            fade = max(0.0, (_BANNER_LIFETIME - self.age) / 0.6)
        else:
            fade = 1.0
        alpha = int(255 * fade)

        left = 18 + offset_x
        bottom = 240 - slot * (_BANNER_H + 10)
        rect = arcade.LBWH(left, bottom, _BANNER_W, _BANNER_H)
        arcade.draw_rect_filled(rect, (*COLOR_PANEL_BG, alpha))
        arcade.draw_rect_outline(rect, (*COLOR_PANEL_BORDER, alpha), border_width=2)
        # Accent stripe in the achievement's color.
        stripe = arcade.LBWH(left, bottom, 6, _BANNER_H)
        arcade.draw_rect_filled(stripe, (*self._ach.color, alpha))

        # Subtle pulsing glow on the star for extra celebration.
        pulse = 0.5 + 0.5 * math.sin(self.age * 7)
        glow_alpha = int(120 * pulse * fade)
        arcade.draw_circle_filled(
            left + 26, bottom + _BANNER_H - 22, 14,
            (*self._ach.color, glow_alpha),
        )

        self._title.x = left + 16
        self._title.y = bottom + _BANNER_H - 28
        r, g, b = COLOR_TEXT_PRIMARY
        self._title.color = (r, g, b, alpha)
        self._title.draw()

        self._desc.x = left + 16
        self._desc.y = bottom + 14
        dr, dg, db = COLOR_TEXT_DIM
        self._desc.color = (dr, dg, db, alpha)
        self._desc.draw()


class AchievementBannerLayer:
    """Stacks up to 3 banners. Older ones slide off as new ones arrive."""

    MAX_VISIBLE = 3

    def __init__(self) -> None:
        self._banners: list[_Banner] = []

    def spawn(self, ach: AchievementDef) -> None:
        self._banners.append(_Banner(ach))
        if len(self._banners) > self.MAX_VISIBLE:
            # Oldest drops off immediately (it's already on its way out).
            self._banners = self._banners[-self.MAX_VISIBLE:]

    def update(self, delta: float) -> None:
        for b in self._banners:
            b.update(delta)
        self._banners = [b for b in self._banners if b.alive]

    def draw(self) -> None:
        for i, banner in enumerate(self._banners):
            banner.draw(slot=i)
