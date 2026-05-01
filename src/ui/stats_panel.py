"""The left-side HUD: wallet, per-second rate, and owned roster."""

from __future__ import annotations

import arcade

from src.constants import (
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_DIM,
    COLOR_TEXT_GOLD,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    PLAY_AREA_WIDTH,
    SCREEN_HEIGHT,
)
from src.game_state import GameState
from src.generators import GENERATORS
from src.number_format import format_number, format_rate


_STATS_HEIGHT = 120
_ROSTER_ROW_HEIGHT = 24


class StatsPanel:
    """Top HUD + bottom roster strip. No input handling.

    Uses cached ``arcade.Text`` objects for every label so glyph layout only
    rebuilds when values actually change.
    """

    def __init__(self, generator_textures: dict[str, arcade.Texture]) -> None:
        self._generator_textures = generator_textures

        top = SCREEN_HEIGHT
        bottom = SCREEN_HEIGHT - _STATS_HEIGHT

        # Static labels — created once and never updated.
        self._title = arcade.Text(
            "Crystal Cavern", 16, top - 28, COLOR_TEXT_PRIMARY,
            font_size=18, anchor_y="baseline", bold=True,
        )
        self._wallet_sub = arcade.Text(
            "mana shards", PLAY_AREA_WIDTH / 2, top - 62, COLOR_TEXT_SECONDARY,
            font_size=12, anchor_x="center", anchor_y="baseline",
        )

        # Dynamic labels — same font/anchors, but `.text` changes each frame.
        self._wallet = arcade.Text(
            "0", PLAY_AREA_WIDTH / 2, top - 44, COLOR_TEXT_GOLD,
            font_size=38, anchor_x="center", anchor_y="baseline", bold=True,
        )
        self._click_power = arcade.Text(
            "Click power: 1", 16, top - 46, COLOR_TEXT_SECONDARY,
            font_size=11, anchor_y="baseline",
        )
        # Essence badge — only drawn when essence > 0 or player has prestiged.
        self._essence_label = arcade.Text(
            "", PLAY_AREA_WIDTH - 16, top - 28, COLOR_TEXT_GOLD,
            font_size=13, anchor_x="right", anchor_y="baseline", bold=True,
        )
        self._essence_sub = arcade.Text(
            "", PLAY_AREA_WIDTH - 16, top - 46, COLOR_TEXT_SECONDARY,
            font_size=11, anchor_x="right", anchor_y="baseline",
        )
        self._rate = arcade.Text(
            "+0/s", PLAY_AREA_WIDTH / 2, bottom + 18, COLOR_TEXT_PRIMARY,
            font_size=16, anchor_x="center", anchor_y="baseline", bold=True,
        )
        self._total_earned = arcade.Text(
            "Total earned: 0", 16, bottom + 14, COLOR_TEXT_DIM,
            font_size=11, anchor_y="baseline",
        )
        self._total_clicks = arcade.Text(
            "Clicks: 0", PLAY_AREA_WIDTH - 16, bottom + 14, COLOR_TEXT_DIM,
            font_size=11, anchor_x="right", anchor_y="baseline",
        )

        # One pre-allocated pair of Text objects per generator for the roster
        # strip. We show/hide by only drawing the rows whose owned > 0.
        self._roster_name: dict[str, arcade.Text] = {}
        self._roster_rate: dict[str, arcade.Text] = {}
        for gen in GENERATORS:
            self._roster_name[gen.key] = arcade.Text(
                "", 28, 0, COLOR_TEXT_PRIMARY,
                font_size=11, anchor_y="center",
            )
            self._roster_rate[gen.key] = arcade.Text(
                "", 254, 0, COLOR_TEXT_GOLD,
                font_size=11, anchor_x="right", anchor_y="center",
            )

    def draw(self, state: GameState) -> None:
        self._draw_top_hud(state)
        self._draw_bottom_roster(state)

    def _draw_top_hud(self, state: GameState) -> None:
        top = SCREEN_HEIGHT
        bottom = SCREEN_HEIGHT - _STATS_HEIGHT
        rect = arcade.LBWH(0, bottom, PLAY_AREA_WIDTH, _STATS_HEIGHT)
        arcade.draw_rect_filled(rect, COLOR_PANEL_BG)
        border = arcade.LBWH(0, bottom, PLAY_AREA_WIDTH, 2)
        arcade.draw_rect_filled(border, COLOR_PANEL_BORDER)

        self._wallet.text = format_number(state.shards)
        self._click_power.text = f"Click power: {format_number(state.click_power())}"
        self._rate.text = f"+{format_rate(state.total_rate())}"
        self._total_earned.text = f"Total earned: {format_number(state.total_earned)}"
        self._total_clicks.text = f"Clicks: {format_number(state.total_clicks)}"

        self._title.draw()
        self._click_power.draw()
        self._wallet.draw()
        self._wallet_sub.draw()
        self._rate.draw()
        self._total_earned.draw()
        self._total_clicks.draw()

        # Essence / prestige info, top-right of the HUD.
        if state.essence > 0 or state.prestige_count > 0:
            self._essence_label.text = f"Essence: {state.essence}"
            self._essence_sub.text = (
                f"x{state.essence_multiplier():.2f} prod • Descents: "
                f"{state.prestige_count}"
            )
            self._essence_label.draw()
            self._essence_sub.draw()

    def _draw_bottom_roster(self, state: GameState) -> None:
        owned_tiers = [g for g in GENERATORS if state.owned.get(g.key, 0) > 0]
        if not owned_tiers:
            return

        height = len(owned_tiers) * _ROSTER_ROW_HEIGHT + 16
        rect = arcade.LBWH(0, 0, 260, height)
        arcade.draw_rect_filled(rect, COLOR_PANEL_BG)
        arcade.draw_rect_outline(rect, COLOR_PANEL_BORDER, border_width=1)

        for i, gen in enumerate(owned_tiers):
            row_y = height - 14 - i * _ROSTER_ROW_HEIGHT
            tex = self._generator_textures.get(gen.key)
            if tex is not None:
                icon_rect = arcade.LBWH(6, row_y - 8, 16, 16)
                arcade.draw_texture_rect(tex, icon_rect)

            name_t = self._roster_name[gen.key]
            rate_t = self._roster_rate[gen.key]
            name_t.y = row_y
            rate_t.y = row_y
            name_t.text = f"{gen.name}  x{state.owned.get(gen.key, 0)}"
            rate_t.text = f"+{format_rate(state.generator_total_rate(gen))}"
            name_t.draw()
            rate_t.draw()
