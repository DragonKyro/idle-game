"""Confirmation modal for the prestige/descent action.

Descending is irreversible within a run — it clears the wallet, helpers,
and upgrades — so we surface the tradeoff clearly before committing.
"""

from __future__ import annotations

import arcade

from src.constants import (
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_PANEL_HIGHLIGHT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_GOLD,
    COLOR_TEXT_OK,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.game_state import ESSENCE_PER_BONUS, GameState
from src.number_format import format_number
from src.ui.button import Button


_MODAL_W = 620
_MODAL_H = 320


class DescendModal:
    """Visible until the player confirms or cancels."""

    def __init__(self, state: GameState) -> None:
        self._visible = True
        self._confirmed = False
        self._mouse_x = 0.0
        self._mouse_y = 0.0

        left = (SCREEN_WIDTH - _MODAL_W) / 2
        bottom = (SCREEN_HEIGHT - _MODAL_H) / 2
        self._left = left
        self._bottom = bottom

        cx = left + _MODAL_W / 2

        pending = state.pending_essence()
        future_total = state.essence + pending
        current_bonus = state.essence_multiplier()
        future_bonus = 1.0 + ESSENCE_PER_BONUS * future_total

        # Confirm / Cancel buttons along the bottom.
        self._confirm = Button(
            left=cx - 240, bottom=bottom + 28, width=220, height=48,
        )
        self._cancel = Button(
            left=cx + 20, bottom=bottom + 28, width=220, height=48,
        )

        self._title = arcade.Text(
            "Descend Deeper?", cx, bottom + _MODAL_H - 30,
            COLOR_TEXT_PRIMARY, font_size=24,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._body1 = arcade.Text(
            "You'll lose all shards, helpers, and upgrades from this run.",
            cx, bottom + _MODAL_H - 76, COLOR_TEXT_SECONDARY, font_size=14,
            anchor_x="center", anchor_y="center",
        )
        self._body2 = arcade.Text(
            "In return, Ancient Essence — a permanent production boost.",
            cx, bottom + _MODAL_H - 100, COLOR_TEXT_SECONDARY, font_size=14,
            anchor_x="center", anchor_y="center",
        )
        self._reward_headline = arcade.Text(
            f"+{pending} Essence", cx, bottom + _MODAL_H - 148,
            COLOR_TEXT_GOLD, font_size=32,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._reward_detail = arcade.Text(
            f"Held: {state.essence}  →  {future_total}   "
            f"(production x{current_bonus:.2f}  →  x{future_bonus:.2f})",
            cx, bottom + _MODAL_H - 180, COLOR_TEXT_DIM, font_size=12,
            anchor_x="center", anchor_y="center",
        )
        self._confirm_label = arcade.Text(
            "Descend", self._confirm.center_x, self._confirm.center_y,
            COLOR_TEXT_PRIMARY, font_size=18,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._cancel_label = arcade.Text(
            "Not yet", self._cancel.center_x, self._cancel.center_y,
            COLOR_TEXT_PRIMARY, font_size=18,
            anchor_x="center", anchor_y="center",
        )

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def confirmed(self) -> bool:
        return self._confirmed

    def on_mouse_motion(self, x: float, y: float) -> None:
        self._mouse_x = x
        self._mouse_y = y

    def handle_click(self, x: float, y: float) -> bool:
        if not self._visible:
            return False
        if self._confirm.contains(x, y):
            self._confirmed = True
            self._visible = False
        elif self._cancel.contains(x, y):
            self._visible = False
        return True

    def draw(self) -> None:
        if not self._visible:
            return

        overlay = arcade.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.draw_rect_filled(overlay, (0, 0, 0, 170))

        modal = arcade.LBWH(self._left, self._bottom, _MODAL_W, _MODAL_H)
        arcade.draw_rect_filled(modal, COLOR_PANEL_BG)
        arcade.draw_rect_outline(modal, COLOR_PANEL_BORDER, border_width=3)

        header = arcade.LBWH(
            self._left, self._bottom + _MODAL_H - 56, _MODAL_W, 56
        )
        arcade.draw_rect_filled(header, COLOR_PANEL_HIGHLIGHT)

        self._title.draw()
        self._body1.draw()
        self._body2.draw()
        self._reward_headline.draw()
        self._reward_detail.draw()

        hovered_confirm = self._confirm.contains(self._mouse_x, self._mouse_y)
        hovered_cancel = self._cancel.contains(self._mouse_x, self._mouse_y)
        self._confirm.draw_background(hovered=hovered_confirm, affordable=True)
        self._cancel.draw_background(hovered=hovered_cancel, affordable=False)
        self._confirm_label.draw()
        self._cancel_label.draw()