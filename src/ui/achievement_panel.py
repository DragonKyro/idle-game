"""Full-screen panel showing every achievement's unlock status."""

from __future__ import annotations

import arcade

from src.achievements import ACHIEVEMENTS
from src.constants import (
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_PANEL_HIGHLIGHT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_GOLD,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.game_state import GameState
from src.ui.button import Button


_PANEL_W = 900
_PANEL_H = 640
_ROW_H = 54
_ROWS_PER_COL = 10


class AchievementPanel:
    """Modal list of every achievement with locked/unlocked state.

    Two columns for density. Unlocked rows use the achievement's accent
    color; locked rows are dimmed and show a generic lock blurb.
    """

    def __init__(self) -> None:
        self._visible = False
        self._mouse_x = 0.0
        self._mouse_y = 0.0

        left = (SCREEN_WIDTH - _PANEL_W) / 2
        bottom = (SCREEN_HEIGHT - _PANEL_H) / 2
        self._left = left
        self._bottom = bottom

        self._close = Button(
            left=left + _PANEL_W - 120, bottom=bottom + 20,
            width=100, height=40,
        )

        self._title = arcade.Text(
            "Achievements", left + _PANEL_W / 2, bottom + _PANEL_H - 28,
            COLOR_TEXT_PRIMARY, font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._progress = arcade.Text(
            "", left + _PANEL_W / 2, bottom + _PANEL_H - 56,
            COLOR_TEXT_GOLD, font_size=14,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._close_label = arcade.Text(
            "Close", self._close.center_x, self._close.center_y,
            COLOR_TEXT_PRIMARY, font_size=14,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Per-row label caches — each row has name + description text.
        self._row_names: list[arcade.Text] = [
            arcade.Text(
                ach.name, 0, 0, COLOR_TEXT_PRIMARY,
                font_size=13, anchor_y="baseline", bold=True,
            )
            for ach in ACHIEVEMENTS
        ]
        self._row_descs: list[arcade.Text] = [
            arcade.Text(
                ach.description, 0, 0, COLOR_TEXT_DIM,
                font_size=10, anchor_y="baseline", italic=True,
            )
            for ach in ACHIEVEMENTS
        ]

    @property
    def visible(self) -> bool:
        return self._visible

    def open(self) -> None:
        self._visible = True

    def on_mouse_motion(self, x: float, y: float) -> None:
        self._mouse_x = x
        self._mouse_y = y

    def handle_click(self, x: float, y: float) -> bool:
        if not self._visible:
            return False
        if self._close.contains(x, y):
            self._visible = False
        return True

    def draw(self, state: GameState) -> None:
        if not self._visible:
            return

        overlay = arcade.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.draw_rect_filled(overlay, (0, 0, 0, 180))

        panel = arcade.LBWH(self._left, self._bottom, _PANEL_W, _PANEL_H)
        arcade.draw_rect_filled(panel, COLOR_PANEL_BG)
        arcade.draw_rect_outline(panel, COLOR_PANEL_BORDER, border_width=3)

        header = arcade.LBWH(
            self._left, self._bottom + _PANEL_H - 70, _PANEL_W, 70
        )
        arcade.draw_rect_filled(header, COLOR_PANEL_HIGHLIGHT)
        self._title.draw()

        unlocked = sum(1 for a in ACHIEVEMENTS if a.key in state.achievements)
        self._progress.text = f"{unlocked} / {len(ACHIEVEMENTS)} unlocked"
        self._progress.draw()

        # Two columns of rows.
        col_w = (_PANEL_W - 60) / 2
        for i, ach in enumerate(ACHIEVEMENTS):
            col = i // _ROWS_PER_COL
            row_i = i % _ROWS_PER_COL
            row_left = self._left + 20 + col * (col_w + 20)
            row_bottom = self._bottom + _PANEL_H - 90 - (row_i + 1) * _ROW_H

            unlocked_row = ach.key in state.achievements
            # Background: soft card tint, accent-tinted for unlocked.
            rect = arcade.LBWH(row_left, row_bottom, col_w, _ROW_H - 6)
            if unlocked_row:
                arcade.draw_rect_filled(rect, (*ach.color, 28))
                arcade.draw_rect_outline(rect, (*ach.color, 160), border_width=1)
            else:
                arcade.draw_rect_filled(rect, (28, 22, 48, 160))
                arcade.draw_rect_outline(rect, (60, 48, 96, 200), border_width=1)

            # Trophy circle / lock circle.
            cx = row_left + 20
            cy = row_bottom + (_ROW_H - 6) / 2
            if unlocked_row:
                arcade.draw_circle_filled(cx, cy, 10, (*ach.color, 230))
                arcade.draw_circle_filled(cx - 1, cy + 1, 4, (255, 255, 255, 220))
            else:
                arcade.draw_circle_filled(cx, cy, 10, (60, 48, 96, 200))

            # Text.
            name_t = self._row_names[i]
            desc_t = self._row_descs[i]
            name_t.x = row_left + 40
            name_t.y = row_bottom + (_ROW_H - 6) - 20
            name_t.color = COLOR_TEXT_PRIMARY if unlocked_row else COLOR_TEXT_SECONDARY
            name_t.draw()
            desc_t.x = row_left + 40
            desc_t.y = row_bottom + 8
            desc_t.draw()

        # Close button.
        hovered = self._close.contains(self._mouse_x, self._mouse_y)
        self._close.draw_background(hovered=hovered, affordable=False)
        self._close_label.draw()
