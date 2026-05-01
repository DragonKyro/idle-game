"""First-run onboarding overlay.

Three stages, advanced by the player doing the expected action:
  0 (UNSEEN)       — big arrow points at the crystal with a "Tap to mine!"
                     hint, plus a glowing ring around it.
  1 (POST_CLICK)   — arrow swings over to the shop's first row with
                     "Spend shards to hire helpers" hint.
  2 (POST_BUY)     — short farewell message, auto-dismisses after ~3s.
  3 (DONE)         — the overlay never shows again.

Stage transitions are triggered by ``GameView`` based on observed
events, and the stage itself lives on ``GameState`` so it persists in
the save.
"""

from __future__ import annotations

import math

import arcade

from src.constants import (
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_GOLD,
    COLOR_TEXT_PRIMARY,
    PLAY_AREA_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHOP_PANEL_WIDTH,
)
from src.entities.main_clicker import CRYSTAL_BASE_SIZE, CRYSTAL_CENTER_X, CRYSTAL_CENTER_Y
from src.game_state import (
    ONBOARDING_DONE,
    ONBOARDING_POST_BUY,
    ONBOARDING_POST_CLICK,
    ONBOARDING_UNSEEN,
    GameState,
)


_FAREWELL_DURATION = 3.0


class Onboarding:
    """Overlay; state is owned by ``GameState.onboarding_stage``."""

    def __init__(self) -> None:
        self._time = 0.0
        self._farewell_remaining = 0.0  # only used in POST_BUY stage

        # Hint label cache.
        self._label = arcade.Text(
            "", 0, 0, COLOR_TEXT_PRIMARY,
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        self._sub = arcade.Text(
            "", 0, 0, COLOR_TEXT_GOLD,
            font_size=12, anchor_x="center", anchor_y="center",
        )

    def is_visible(self, state: GameState) -> bool:
        return state.onboarding_stage < ONBOARDING_DONE

    def update(self, delta: float, state: GameState) -> None:
        if not self.is_visible(state):
            return
        self._time += delta
        if state.onboarding_stage == ONBOARDING_POST_BUY:
            self._farewell_remaining = max(0.0, self._farewell_remaining - delta)
            if self._farewell_remaining <= 0:
                state.onboarding_stage = ONBOARDING_DONE

    def notice_first_click(self, state: GameState) -> None:
        if state.onboarding_stage == ONBOARDING_UNSEEN:
            state.onboarding_stage = ONBOARDING_POST_CLICK
            self._time = 0.0

    def notice_first_purchase(self, state: GameState) -> None:
        if state.onboarding_stage in (ONBOARDING_UNSEEN, ONBOARDING_POST_CLICK):
            state.onboarding_stage = ONBOARDING_POST_BUY
            self._farewell_remaining = _FAREWELL_DURATION
            self._time = 0.0

    def draw(self, state: GameState) -> None:
        if not self.is_visible(state):
            return
        stage = state.onboarding_stage
        pulse = 0.5 + 0.5 * math.sin(self._time * 3)

        if stage == ONBOARDING_UNSEEN:
            self._draw_crystal_prompt(pulse)
        elif stage == ONBOARDING_POST_CLICK:
            self._draw_shop_prompt(pulse)
        elif stage == ONBOARDING_POST_BUY:
            self._draw_farewell()

    # -- per-stage drawing --------------------------------------------

    def _draw_crystal_prompt(self, pulse: float) -> None:
        # Glowing ring around the crystal.
        ring_r = CRYSTAL_BASE_SIZE / 2 + 30 + 6 * pulse
        arcade.draw_circle_outline(
            CRYSTAL_CENTER_X, CRYSTAL_CENTER_Y, ring_r,
            (255, 220, 140, int(120 + 80 * pulse)), border_width=3,
        )

        # Bubble above the crystal.
        bubble_x = CRYSTAL_CENTER_X
        bubble_y = CRYSTAL_CENTER_Y + CRYSTAL_BASE_SIZE / 2 + 90
        self._draw_bubble(bubble_x, bubble_y, width=360, height=80)
        self._label.text = "Tap the crystal to mine!"
        self._label.x = bubble_x
        self._label.y = bubble_y + 14
        self._label.color = COLOR_TEXT_PRIMARY
        self._label.draw()
        self._sub.text = "Every tap earns you shards."
        self._sub.x = bubble_x
        self._sub.y = bubble_y - 12
        self._sub.draw()

        # Down-arrow beneath the bubble pointing at the crystal.
        self._draw_down_arrow(bubble_x, bubble_y - 40)

    def _draw_shop_prompt(self, pulse: float) -> None:
        # Highlight the shop's first row area with a pulsing outline.
        shop_left = SCREEN_WIDTH - SHOP_PANEL_WIDTH
        row_bottom = SCREEN_HEIGHT - 70 - 40 - 8 - 84  # mirrors shop_panel layout
        rect = arcade.LBWH(shop_left + 8, row_bottom, SHOP_PANEL_WIDTH - 16, 84)
        arcade.draw_rect_outline(
            rect, (255, 220, 140, int(140 + 80 * pulse)), border_width=3,
        )

        # Bubble to the left of the shop.
        bubble_x = shop_left - 200
        bubble_y = SCREEN_HEIGHT - 160
        self._draw_bubble(bubble_x, bubble_y, width=340, height=90)
        self._label.text = "Now hire a helper!"
        self._label.x = bubble_x
        self._label.y = bubble_y + 18
        self._label.color = COLOR_TEXT_PRIMARY
        self._label.draw()
        self._sub.text = "Helpers mine shards for you — forever."
        self._sub.x = bubble_x
        self._sub.y = bubble_y - 10
        self._sub.draw()

        # Right-arrow pointing at the shop row.
        self._draw_right_arrow(bubble_x + 180, bubble_y)

    def _draw_farewell(self) -> None:
        bubble_x = PLAY_AREA_WIDTH / 2
        bubble_y = SCREEN_HEIGHT - 180
        self._draw_bubble(bubble_x, bubble_y, width=420, height=70)
        self._label.text = "You're set! Good luck, miner."
        self._label.x = bubble_x
        self._label.y = bubble_y + 8
        self._label.color = COLOR_TEXT_PRIMARY
        self._label.draw()
        self._sub.text = "Tip: press F5 to save — and watch for Descend."
        self._sub.x = bubble_x
        self._sub.y = bubble_y - 14
        self._sub.draw()

    # -- primitives ----------------------------------------------------

    def _draw_bubble(self, cx: float, cy: float, *, width: float, height: float) -> None:
        rect = arcade.LBWH(cx - width / 2, cy - height / 2, width, height)
        arcade.draw_rect_filled(rect, (*COLOR_PANEL_BG, 230))
        arcade.draw_rect_outline(rect, COLOR_PANEL_BORDER, border_width=2)

    def _draw_down_arrow(self, cx: float, cy: float) -> None:
        arcade.draw_polygon_filled(
            [(cx - 16, cy + 12), (cx + 16, cy + 12), (cx, cy - 18)],
            COLOR_TEXT_GOLD,
        )

    def _draw_right_arrow(self, cx: float, cy: float) -> None:
        arcade.draw_polygon_filled(
            [(cx - 12, cy - 16), (cx - 12, cy + 16), (cx + 18, cy)],
            COLOR_TEXT_GOLD,
        )
