"""Brief banner shown near the top of the play area after a purchase."""

from __future__ import annotations

import arcade

from src.constants import (
    COLOR_PANEL_BORDER,
    COLOR_TEXT_PRIMARY,
    PLAY_AREA_WIDTH,
    SCREEN_HEIGHT,
)


_TOAST_LIFETIME = 2.0
_TOAST_WIDTH = 380
_TOAST_HEIGHT = 46
_TOAST_TOP_MARGIN = 140  # below the HUD strip


class Toast:
    """A single toast — text + accent color stripe. Fades out by itself."""

    __slots__ = ("_label", "_accent", "age")

    def __init__(self, text: str, accent: tuple[int, int, int]) -> None:
        self._label = arcade.Text(
            text,
            PLAY_AREA_WIDTH / 2,
            SCREEN_HEIGHT - _TOAST_TOP_MARGIN + _TOAST_HEIGHT / 2,
            COLOR_TEXT_PRIMARY,
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        self._accent = accent
        self.age = 0.0

    @property
    def alive(self) -> bool:
        return self.age < _TOAST_LIFETIME

    def update(self, delta: float) -> None:
        self.age += delta

    def draw(self) -> None:
        # Alpha easing: quick fade in (0-0.15s), steady, fade out (last 0.5s).
        t = self.age / _TOAST_LIFETIME
        if t < 0.08:
            alpha = t / 0.08
        elif t > 0.75:
            alpha = max(0.0, 1.0 - (t - 0.75) / 0.25)
        else:
            alpha = 1.0
        a8 = int(max(0, min(255, 230 * alpha)))

        left = (PLAY_AREA_WIDTH - _TOAST_WIDTH) / 2
        bottom = SCREEN_HEIGHT - _TOAST_TOP_MARGIN
        rect = arcade.LBWH(left, bottom, _TOAST_WIDTH, _TOAST_HEIGHT)
        arcade.draw_rect_filled(rect, (20, 16, 36, a8))
        arcade.draw_rect_outline(rect, (*COLOR_PANEL_BORDER, a8), border_width=2)
        # Left accent stripe in the item's color.
        stripe = arcade.LBWH(left, bottom, 6, _TOAST_HEIGHT)
        arcade.draw_rect_filled(stripe, (*self._accent, a8))

        r, g, b = COLOR_TEXT_PRIMARY
        self._label.color = (r, g, b, a8)
        self._label.draw()


class ToastLayer:
    """Shows one toast at a time. Spawning a new one replaces the old so
    rapid purchases don't pile up banners on-screen."""

    def __init__(self) -> None:
        self._current: Toast | None = None

    def spawn(self, text: str, accent: tuple[int, int, int]) -> None:
        self._current = Toast(text, accent)

    def update(self, delta: float) -> None:
        if self._current is None:
            return
        self._current.update(delta)
        if not self._current.alive:
            self._current = None

    def draw(self) -> None:
        if self._current is not None:
            self._current.draw()
