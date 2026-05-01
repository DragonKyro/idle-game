"""Modal shown on launch when there are offline earnings to report."""

from __future__ import annotations

import arcade

from src.constants import (
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_PANEL_HIGHLIGHT,
    COLOR_TEXT_GOLD,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    OFFLINE_CAP_SECONDS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.number_format import format_duration, format_number
from src.ui.button import Button


_MODAL_W = 560
_MODAL_H = 280


class WelcomeBackModal:
    """A dismissable modal. Lives until the player clicks 'Collect'."""

    def __init__(self, elapsed_seconds: float, shards_gained: float) -> None:
        self._elapsed = elapsed_seconds
        self._shards = shards_gained
        self._visible = True
        self._mouse_x = 0.0
        self._mouse_y = 0.0

        left = (SCREEN_WIDTH - _MODAL_W) / 2
        bottom = (SCREEN_HEIGHT - _MODAL_H) / 2
        self._left = left
        self._bottom = bottom

        self._button = Button(
            left=(SCREEN_WIDTH - 220) / 2,
            bottom=bottom + 24,
            width=220,
            height=46,
        )

        cap_hit = elapsed_seconds > OFFLINE_CAP_SECONDS
        subline = (
            "Your helpers mined away (capped at 8 hours):"
            if cap_hit
            else "Your helpers kept mining while you rested:"
        )

        # Pre-compute all labels since they never change after construction.
        cx = left + _MODAL_W / 2
        self._title = arcade.Text(
            "Welcome back, miner!", cx, bottom + _MODAL_H - 26,
            COLOR_TEXT_PRIMARY, font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._away = arcade.Text(
            f"You were away for {format_duration(elapsed_seconds)}.",
            cx, bottom + _MODAL_H - 86,
            COLOR_TEXT_SECONDARY, font_size=14,
            anchor_x="center", anchor_y="center",
        )
        self._subline = arcade.Text(
            subline, cx, bottom + _MODAL_H - 108,
            COLOR_TEXT_SECONDARY, font_size=12,
            anchor_x="center", anchor_y="center",
        )
        self._prize = arcade.Text(
            f"+{format_number(shards_gained)} shards",
            cx, bottom + _MODAL_H - 160,
            COLOR_TEXT_GOLD, font_size=34,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._collect_label = arcade.Text(
            "Collect",
            self._button.center_x, self._button.center_y,
            COLOR_TEXT_PRIMARY, font_size=18,
            anchor_x="center", anchor_y="center", bold=True,
        )

    @property
    def visible(self) -> bool:
        return self._visible

    def on_mouse_motion(self, x: float, y: float) -> None:
        self._mouse_x = x
        self._mouse_y = y

    def handle_click(self, x: float, y: float) -> bool:
        if not self._visible:
            return False
        if self._button.contains(x, y):
            self._visible = False
        return True

    def draw(self) -> None:
        if not self._visible:
            return

        overlay = arcade.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.draw_rect_filled(overlay, (0, 0, 0, 160))

        modal = arcade.LBWH(self._left, self._bottom, _MODAL_W, _MODAL_H)
        arcade.draw_rect_filled(modal, COLOR_PANEL_BG)
        arcade.draw_rect_outline(modal, COLOR_PANEL_BORDER, border_width=3)

        header = arcade.LBWH(
            self._left, self._bottom + _MODAL_H - 52, _MODAL_W, 52
        )
        arcade.draw_rect_filled(header, COLOR_PANEL_HIGHLIGHT)

        self._title.draw()
        self._away.draw()
        self._subline.draw()
        self._prize.draw()

        hovered = self._button.contains(self._mouse_x, self._mouse_y)
        self._button.draw_background(hovered=hovered, affordable=True)
        self._collect_label.draw()
