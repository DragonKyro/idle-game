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

        self._button = Button(
            left=(SCREEN_WIDTH - 220) / 2,
            bottom=(SCREEN_HEIGHT - _MODAL_H) / 2 + 24,
            width=220,
            height=46,
        )

    @property
    def visible(self) -> bool:
        return self._visible

    def on_mouse_motion(self, x: float, y: float) -> None:
        self._mouse_x = x
        self._mouse_y = y

    def handle_click(self, x: float, y: float) -> bool:
        """Return True if the click was consumed by the modal."""
        if not self._visible:
            return False
        if self._button.contains(x, y):
            self._visible = False
        # Any click inside the modal (or anywhere, really) consumes input so
        # it doesn't leak through to the crystal.
        return True

    def draw(self) -> None:
        if not self._visible:
            return

        # Dim overlay.
        overlay = arcade.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.draw_rect_filled(overlay, (0, 0, 0, 160))

        left = (SCREEN_WIDTH - _MODAL_W) / 2
        bottom = (SCREEN_HEIGHT - _MODAL_H) / 2
        modal = arcade.LBWH(left, bottom, _MODAL_W, _MODAL_H)
        arcade.draw_rect_filled(modal, COLOR_PANEL_BG)
        arcade.draw_rect_outline(modal, COLOR_PANEL_BORDER, border_width=3)

        # Header bar.
        header = arcade.LBWH(left, bottom + _MODAL_H - 52, _MODAL_W, 52)
        arcade.draw_rect_filled(header, COLOR_PANEL_HIGHLIGHT)
        arcade.draw_text(
            "Welcome back, miner!",
            left + _MODAL_W / 2,
            bottom + _MODAL_H - 26,
            COLOR_TEXT_PRIMARY,
            font_size=22,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

        # Body copy.
        arcade.draw_text(
            f"You were away for {format_duration(self._elapsed)}.",
            left + _MODAL_W / 2,
            bottom + _MODAL_H - 86,
            COLOR_TEXT_SECONDARY,
            font_size=14,
            anchor_x="center",
            anchor_y="center",
        )

        cap_hit = self._elapsed > OFFLINE_CAP_SECONDS
        subline = (
            "Your helpers mined away (capped at 8 hours):"
            if cap_hit
            else "Your helpers kept mining while you rested:"
        )
        arcade.draw_text(
            subline,
            left + _MODAL_W / 2,
            bottom + _MODAL_H - 108,
            COLOR_TEXT_SECONDARY,
            font_size=12,
            anchor_x="center",
            anchor_y="center",
        )

        # Prize.
        arcade.draw_text(
            f"+{format_number(self._shards)} shards",
            left + _MODAL_W / 2,
            bottom + _MODAL_H - 160,
            COLOR_TEXT_GOLD,
            font_size=34,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

        # Collect button.
        hovered = self._button.contains(self._mouse_x, self._mouse_y)
        self._button.draw_background(hovered=hovered, affordable=True)
        self._button.draw_label("Collect", font_size=18, bold=True)
