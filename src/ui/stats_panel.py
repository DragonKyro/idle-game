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
    """Top HUD + bottom roster strip. No input handling."""

    def __init__(self, generator_textures: dict[str, arcade.Texture]) -> None:
        self._generator_textures = generator_textures

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

        # Wallet — big and gold in the center.
        arcade.draw_text(
            f"{format_number(state.shards)}",
            PLAY_AREA_WIDTH / 2,
            top - 44,
            COLOR_TEXT_GOLD,
            font_size=38,
            anchor_x="center",
            anchor_y="baseline",
            bold=True,
        )
        arcade.draw_text(
            "mana shards",
            PLAY_AREA_WIDTH / 2,
            top - 62,
            COLOR_TEXT_SECONDARY,
            font_size=12,
            anchor_x="center",
            anchor_y="baseline",
        )

        # Per-second rate — bottom center of the HUD.
        rate_text = f"+{format_rate(state.total_rate())}"
        arcade.draw_text(
            rate_text,
            PLAY_AREA_WIDTH / 2,
            bottom + 18,
            COLOR_TEXT_PRIMARY,
            font_size=16,
            anchor_x="center",
            anchor_y="baseline",
            bold=True,
        )

        # Lifetime stats flanking the rate.
        arcade.draw_text(
            f"Total earned: {format_number(state.total_earned)}",
            16,
            bottom + 14,
            COLOR_TEXT_DIM,
            font_size=11,
            anchor_y="baseline",
        )
        arcade.draw_text(
            f"Clicks: {format_number(state.total_clicks)}",
            PLAY_AREA_WIDTH - 16,
            bottom + 14,
            COLOR_TEXT_DIM,
            font_size=11,
            anchor_x="right",
            anchor_y="baseline",
        )

        # Title banner at the very top.
        arcade.draw_text(
            "Crystal Cavern",
            16,
            top - 28,
            COLOR_TEXT_PRIMARY,
            font_size=18,
            anchor_y="baseline",
            bold=True,
        )
        arcade.draw_text(
            "Click power: " + format_number(state.click_power()),
            16,
            top - 46,
            COLOR_TEXT_SECONDARY,
            font_size=11,
            anchor_y="baseline",
        )

    def _draw_bottom_roster(self, state: GameState) -> None:
        """Thin strip showing owned counts and per-tier contribution."""
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
            owned = state.owned.get(gen.key, 0)
            arcade.draw_text(
                f"{gen.name}  x{owned}",
                28,
                row_y,
                COLOR_TEXT_PRIMARY,
                font_size=11,
                anchor_y="center",
            )
            arcade.draw_text(
                f"+{format_rate(state.generator_total_rate(gen))}",
                254,
                row_y,
                COLOR_TEXT_GOLD,
                font_size=11,
                anchor_x="right",
                anchor_y="center",
            )
