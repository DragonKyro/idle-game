"""Stats modal — lifetime stats + achievement progress at a glance."""

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
from src.number_format import format_duration, format_number
from src.ui.button import Button


_PANEL_W = 540
_PANEL_H = 540
_ROW_H = 32


class StatsModal:
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
            "Lifetime Stats", left + _PANEL_W / 2, bottom + _PANEL_H - 28,
            COLOR_TEXT_PRIMARY, font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._close_label = arcade.Text(
            "Close", self._close.center_x, self._close.center_y,
            COLOR_TEXT_PRIMARY, font_size=14,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Row label/value text pools — labels on the left, values on the right.
        self._keys = [
            "playtime",
            "total_clicks",
            "total_earned",
            "helpers_bought",
            "upgrade_levels",
            "descents",
            "best_descent",
            "total_essence",
            "bosses",
            "achievements",
        ]
        self._labels: dict[str, arcade.Text] = {
            k: arcade.Text(
                "", 0, 0, COLOR_TEXT_SECONDARY, font_size=13, anchor_y="center",
            ) for k in self._keys
        }
        self._values: dict[str, arcade.Text] = {
            k: arcade.Text(
                "", 0, 0, COLOR_TEXT_GOLD, font_size=14,
                anchor_x="right", anchor_y="center", bold=True,
            ) for k in self._keys
        }

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

        modal = arcade.LBWH(self._left, self._bottom, _PANEL_W, _PANEL_H)
        arcade.draw_rect_filled(modal, COLOR_PANEL_BG)
        arcade.draw_rect_outline(modal, COLOR_PANEL_BORDER, border_width=3)
        header = arcade.LBWH(
            self._left, self._bottom + _PANEL_H - 56, _PANEL_W, 56
        )
        arcade.draw_rect_filled(header, COLOR_PANEL_HIGHLIGHT)
        self._title.draw()

        # Rows.
        row_left = self._left + 40
        row_right = self._left + _PANEL_W - 40
        row_top = self._bottom + _PANEL_H - 90

        unlocked = sum(1 for a in ACHIEVEMENTS if a.key in state.achievements)
        data = {
            "playtime":       ("Playtime",           format_duration(state.playtime_seconds)),
            "total_clicks":   ("Total clicks",       format_number(state.total_clicks)),
            "total_earned":   ("Total earned",       format_number(state.total_earned)),
            "helpers_bought": ("Helpers bought",     format_number(state.total_generators_bought)),
            "upgrade_levels": ("Upgrade levels",     str(state.total_upgrade_levels())),
            "descents":       ("Descents",           str(state.prestige_count)),
            "best_descent":   ("Best descent",       f"{state.best_descent_essence} essence"),
            "total_essence":  ("Lifetime essence",   str(state.total_essence_earned)),
            "bosses":         ("Bosses defeated",    str(state.bosses_defeated)),
            "achievements":   ("Achievements",       f"{unlocked} / {len(ACHIEVEMENTS)}"),
        }

        for i, key in enumerate(self._keys):
            label_text, value_text = data[key]
            y = row_top - i * _ROW_H - 20
            # Subtle alternating row background for readability.
            if i % 2 == 0:
                bg = arcade.LBWH(row_left - 12, y - 14, row_right - row_left + 24, _ROW_H - 6)
                arcade.draw_rect_filled(bg, (40, 32, 64, 100))

            self._labels[key].text = label_text
            self._labels[key].x = row_left
            self._labels[key].y = y
            self._labels[key].draw()

            self._values[key].text = value_text
            self._values[key].x = row_right
            self._values[key].y = y
            self._values[key].draw()

        hovered = self._close.contains(self._mouse_x, self._mouse_y)
        self._close.draw_background(hovered=hovered, affordable=False)
        self._close_label.draw()
