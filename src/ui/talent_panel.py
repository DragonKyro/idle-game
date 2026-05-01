"""Modal talent tree — spend essence on permanent perks."""

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
from src.game_state import GameState
from src.talents import TALENT_BRANCHES, TALENTS
from src.ui.button import Button


_PANEL_W = 960
_PANEL_H = 640
_BRANCH_COLORS = {
    "click":   (255, 214, 110),
    "idle":    (130, 230, 170),
    "offline": (120, 220, 255),
    "special": (180, 150, 255),
}
_ROW_H = 62


class TalentPanel:
    """Grid layout: one column per branch, talents listed under each."""

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
            "Talent Tree", left + _PANEL_W / 2, bottom + _PANEL_H - 28,
            COLOR_TEXT_PRIMARY, font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._essence_label = arcade.Text(
            "", left + _PANEL_W / 2, bottom + _PANEL_H - 56,
            COLOR_TEXT_GOLD, font_size=14,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._hint = arcade.Text(
            "Essence you spend here no longer contributes to the "
            "passive +2%/unit bonus — trade-off, not free power.",
            left + _PANEL_W / 2, bottom + 76,
            COLOR_TEXT_DIM, font_size=11,
            anchor_x="center", anchor_y="center", italic=True,
        )
        self._close_label = arcade.Text(
            "Close", self._close.center_x, self._close.center_y,
            COLOR_TEXT_PRIMARY, font_size=14,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Branch headers + per-talent text pools.
        self._branch_labels = {
            branch: arcade.Text(
                branch.title(), 0, 0, _BRANCH_COLORS[branch],
                font_size=15, anchor_x="center", anchor_y="baseline", bold=True,
            )
            for branch in TALENT_BRANCHES
        }
        self._name_texts: dict[str, arcade.Text] = {
            t.key: arcade.Text(
                t.name, 0, 0, COLOR_TEXT_PRIMARY,
                font_size=12, anchor_y="baseline", bold=True,
            )
            for t in TALENTS
        }
        self._desc_texts: dict[str, arcade.Text] = {
            t.key: arcade.Text(
                t.description, 0, 0, COLOR_TEXT_DIM,
                font_size=9, anchor_y="baseline",
            )
            for t in TALENTS
        }
        self._meta_texts: dict[str, arcade.Text] = {
            t.key: arcade.Text(
                "", 0, 0, COLOR_TEXT_SECONDARY,
                font_size=10, anchor_x="right", anchor_y="baseline", bold=True,
            )
            for t in TALENTS
        }

        # Recorded during draw for click routing.
        self._row_hits: list[tuple[str, Button]] = []

    @property
    def visible(self) -> bool:
        return self._visible

    def open(self) -> None:
        self._visible = True

    def on_mouse_motion(self, x: float, y: float) -> None:
        self._mouse_x = x
        self._mouse_y = y

    def handle_click(self, x: float, y: float, state: GameState) -> str | None:
        """Returns the talent key the player attempted to buy, or None."""
        if not self._visible:
            return None
        if self._close.contains(x, y):
            self._visible = False
            return None
        for key, btn in self._row_hits:
            if btn.contains(x, y):
                return key
        return None

    def draw(self, state: GameState) -> None:
        if not self._visible:
            return
        self._row_hits = []

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

        self._essence_label.text = (
            f"Essence available: {state.essence}   "
            f"(lifetime earned: {state.total_essence_earned})"
        )
        self._essence_label.draw()

        # Branch columns.
        col_w = (_PANEL_W - 80) / len(TALENT_BRANCHES)
        grid_top = self._bottom + _PANEL_H - 90
        for i, branch in enumerate(TALENT_BRANCHES):
            col_x = self._left + 40 + i * col_w
            self._branch_labels[branch].x = col_x + col_w / 2
            self._branch_labels[branch].y = grid_top - 20
            self._branch_labels[branch].draw()

            branch_talents = [t for t in TALENTS if t.branch == branch]
            for j, talent in enumerate(branch_talents):
                row_bottom = grid_top - 40 - (j + 1) * (_ROW_H + 6)
                self._draw_talent_row(state, talent, col_x, row_bottom, col_w)

        self._hint.draw()

        hovered_close = self._close.contains(self._mouse_x, self._mouse_y)
        self._close.draw_background(hovered=hovered_close, affordable=False)
        self._close_label.draw()

    def _draw_talent_row(self, state, talent, col_x, row_bottom, col_w) -> None:
        row = Button(left=col_x + 6, bottom=row_bottom, width=col_w - 12, height=_ROW_H)
        level = state.talent_level(talent.key)
        maxed = state.talent_is_maxed(talent.key)
        affordable = state.can_afford_talent(talent.key)
        hovered = row.contains(self._mouse_x, self._mouse_y)
        row.draw_background(
            hovered=hovered and not maxed,
            affordable=affordable,
            enabled=not maxed,
        )

        color = _BRANCH_COLORS[talent.branch]
        bar = arcade.LBWH(row.left, row.bottom, 4, row.height)
        arcade.draw_rect_filled(bar, color)

        name = self._name_texts[talent.key]
        name.x = row.left + 12
        name.y = row.top - 18
        name.color = COLOR_TEXT_DIM if maxed else COLOR_TEXT_PRIMARY
        name.draw()

        desc = self._desc_texts[talent.key]
        desc.x = row.left + 12
        desc.y = row.top - 34
        desc.draw()

        meta = self._meta_texts[talent.key]
        meta.x = row.right - 10
        meta.y = row.bottom + 8
        if maxed:
            meta.text = f"Lv {level}/{talent.max_level} — MAX"
            meta.color = COLOR_TEXT_GOLD
        else:
            next_cost = state.next_talent_cost(talent.key) or 0
            meta.text = f"Lv {level}/{talent.max_level} — {next_cost} essence"
            meta.color = COLOR_TEXT_OK if affordable else COLOR_TEXT_DIM
        meta.draw()

        if not maxed:
            self._row_hits.append((talent.key, row))
