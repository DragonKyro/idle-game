"""The right-side shop listing generators and available upgrades."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

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
    SHOP_PANEL_WIDTH,
)
from src.game_state import GameState
from src.generators import GENERATORS, GeneratorDef, cost_for
from src.number_format import format_number, format_rate
from src.ui.button import Button
from src.upgrades import UPGRADES, UpgradeDef


class ShopTab(Enum):
    GENERATORS = "generators"
    UPGRADES = "upgrades"


# Layout constants.
_PANEL_LEFT = SCREEN_WIDTH - SHOP_PANEL_WIDTH
_HEADER_HEIGHT = 70
_TAB_HEIGHT = 40
_ROW_HEIGHT = 84
_ROW_MARGIN = 8
_ROW_PADDING = 12
_ICON_SIZE = 48
_SCROLL_STEP = 40.0


@dataclass
class _RowHit:
    kind: str  # "gen" or "upgrade"
    key: str
    button: Button


class ShopPanel:
    """Renders and handles input for the shop UI.

    This class is deliberately pure UI — it doesn't own the GameState. The
    caller hands state in for rendering and receives purchase intents via
    `handle_click`.
    """

    def __init__(self, generator_textures: dict[str, arcade.Texture]) -> None:
        self._generator_textures = generator_textures
        self._tab = ShopTab.GENERATORS
        self._scroll: dict[ShopTab, float] = {
            ShopTab.GENERATORS: 0.0,
            ShopTab.UPGRADES: 0.0,
        }
        self._mouse_x = 0.0
        self._mouse_y = 0.0
        self._row_hits: list[_RowHit] = []  # recomputed each draw

        # Tab buttons sit just under the header.
        tab_width = SHOP_PANEL_WIDTH / 2
        tab_bottom = SCREEN_HEIGHT - _HEADER_HEIGHT - _TAB_HEIGHT
        self._tab_buttons = {
            ShopTab.GENERATORS: Button(
                _PANEL_LEFT, tab_bottom, tab_width, _TAB_HEIGHT
            ),
            ShopTab.UPGRADES: Button(
                _PANEL_LEFT + tab_width, tab_bottom, tab_width, _TAB_HEIGHT
            ),
        }

    # ------------------------------------------------------------------
    # Input.
    # ------------------------------------------------------------------

    def contains(self, x: float, y: float) -> bool:
        return x >= _PANEL_LEFT

    def on_mouse_motion(self, x: float, y: float) -> None:
        self._mouse_x = x
        self._mouse_y = y

    def on_mouse_scroll(self, x: float, y: float, dy: float) -> None:
        if not self.contains(x, y):
            return
        # dy > 0 means scroll up — which in a top-anchored list should
        # reveal *earlier* items, i.e. shrink the scroll offset.
        self._scroll[self._tab] = max(0.0, self._scroll[self._tab] - dy * _SCROLL_STEP)

    def handle_click(self, x: float, y: float, state: GameState) -> dict | None:
        """Return a dict describing what was clicked, or None.

        Shapes:
            {"kind": "buy_generator", "key": ...}
            {"kind": "buy_upgrade", "key": ...}
            {"kind": "switch_tab"}  (handled internally, returns None after switch)
        """
        if not self.contains(x, y):
            return None

        for tab, btn in self._tab_buttons.items():
            if btn.contains(x, y):
                self._tab = tab
                return None

        for hit in self._row_hits:
            if hit.button.contains(x, y):
                if hit.kind == "gen":
                    return {"kind": "buy_generator", "key": hit.key}
                if hit.kind == "upgrade":
                    return {"kind": "buy_upgrade", "key": hit.key}
        return None

    # ------------------------------------------------------------------
    # Rendering.
    # ------------------------------------------------------------------

    def draw(self, state: GameState) -> None:
        self._draw_panel_background()
        self._draw_header()
        self._draw_tabs()
        self._row_hits = []
        if self._tab is ShopTab.GENERATORS:
            self._draw_generator_rows(state)
        else:
            self._draw_upgrade_rows(state)

    def _draw_panel_background(self) -> None:
        rect = arcade.LBWH(_PANEL_LEFT, 0, SHOP_PANEL_WIDTH, SCREEN_HEIGHT)
        arcade.draw_rect_filled(rect, COLOR_PANEL_BG)
        # Left-edge accent.
        accent = arcade.LBWH(_PANEL_LEFT, 0, 2, SCREEN_HEIGHT)
        arcade.draw_rect_filled(accent, COLOR_PANEL_BORDER)

    def _draw_header(self) -> None:
        header = arcade.LBWH(
            _PANEL_LEFT, SCREEN_HEIGHT - _HEADER_HEIGHT,
            SHOP_PANEL_WIDTH, _HEADER_HEIGHT,
        )
        arcade.draw_rect_filled(header, COLOR_PANEL_HIGHLIGHT)
        arcade.draw_text(
            "Cavern Emporium",
            _PANEL_LEFT + SHOP_PANEL_WIDTH / 2,
            SCREEN_HEIGHT - _HEADER_HEIGHT / 2,
            COLOR_TEXT_PRIMARY,
            font_size=22,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

    def _draw_tabs(self) -> None:
        for tab, btn in self._tab_buttons.items():
            hovered = btn.contains(self._mouse_x, self._mouse_y)
            active = tab is self._tab
            btn.draw_background(hovered=hovered, affordable=active)
            btn.draw_label(tab.value.title(), font_size=14, bold=active)

    # Shared clip region for scrolling lists.
    def _list_bounds(self) -> tuple[float, float]:
        """Return (top, bottom) of the visible list area."""
        top = SCREEN_HEIGHT - _HEADER_HEIGHT - _TAB_HEIGHT - _ROW_MARGIN
        bottom = 12
        return top, bottom

    def _draw_generator_rows(self, state: GameState) -> None:
        top, bottom = self._list_bounds()
        scroll = self._scroll[ShopTab.GENERATORS]
        y = top + scroll  # rows are laid out going down from here

        visible: list[tuple[GeneratorDef, int, float]] = []
        for gen in GENERATORS:
            if not state.is_generator_unlocked(gen):
                continue
            owned = state.owned.get(gen.key, 0)
            price = cost_for(gen, owned)
            visible.append((gen, owned, price))

        # Clip by culling rows that fall outside the list area. (Arcade 3.x
        # makes scissoring tricky, so we just don't draw offscreen rows.)
        for gen, owned, price in visible:
            row_top = y
            row_bottom = row_top - _ROW_HEIGHT
            y = row_bottom - _ROW_MARGIN

            if row_top < bottom or row_bottom > top:
                # Still register the hit so scrolling math stays consistent.
                continue

            self._draw_generator_row(state, gen, owned, price, row_bottom)

        if not visible:
            arcade.draw_text(
                "Keep mining to unlock helpers!",
                _PANEL_LEFT + SHOP_PANEL_WIDTH / 2,
                (top + bottom) / 2,
                COLOR_TEXT_DIM,
                font_size=14,
                anchor_x="center",
                anchor_y="center",
                italic=True,
            )

    def _draw_generator_row(
        self,
        state: GameState,
        gen: GeneratorDef,
        owned: int,
        price: float,
        row_bottom: float,
    ) -> None:
        row = Button(
            left=_PANEL_LEFT + _ROW_MARGIN,
            bottom=row_bottom,
            width=SHOP_PANEL_WIDTH - 2 * _ROW_MARGIN,
            height=_ROW_HEIGHT,
        )
        affordable = state.shards >= price
        hovered = row.contains(self._mouse_x, self._mouse_y)
        row.draw_background(hovered=hovered, affordable=affordable)

        # Sprite icon.
        tex = self._generator_textures.get(gen.key)
        if tex is not None:
            icon_rect = arcade.LBWH(
                row.left + _ROW_PADDING,
                row.center_y - _ICON_SIZE / 2,
                _ICON_SIZE,
                _ICON_SIZE,
            )
            arcade.draw_texture_rect(tex, icon_rect)

        text_left = row.left + _ROW_PADDING + _ICON_SIZE + 10

        # Name and owned count.
        arcade.draw_text(
            gen.name,
            text_left,
            row.top - 22,
            COLOR_TEXT_PRIMARY,
            font_size=15,
            anchor_y="baseline",
            bold=True,
        )
        arcade.draw_text(
            f"Owned: {owned}",
            row.right - _ROW_PADDING,
            row.top - 22,
            COLOR_TEXT_SECONDARY,
            font_size=13,
            anchor_x="right",
            anchor_y="baseline",
        )

        # Per-unit rate.
        per_unit = state.generator_rate(gen)
        arcade.draw_text(
            f"+{format_rate(per_unit)} each",
            text_left,
            row.top - 42,
            COLOR_TEXT_SECONDARY,
            font_size=12,
            anchor_y="baseline",
        )

        # Price.
        price_color = COLOR_TEXT_OK if affordable else COLOR_TEXT_DIM
        arcade.draw_text(
            f"{format_number(price)}",
            row.right - _ROW_PADDING,
            row.bottom + 10,
            price_color,
            font_size=16,
            anchor_x="right",
            anchor_y="baseline",
            bold=True,
        )
        arcade.draw_text(
            "shards",
            row.right - _ROW_PADDING,
            row.bottom + 4,
            COLOR_TEXT_DIM,
            font_size=9,
            anchor_x="right",
            anchor_y="baseline",
        )

        # Flavor text, dim so names read first.
        arcade.draw_text(
            gen.flavor,
            text_left,
            row.bottom + 8,
            COLOR_TEXT_DIM,
            font_size=10,
            italic=True,
            anchor_y="baseline",
        )

        self._row_hits.append(_RowHit(kind="gen", key=gen.key, button=row))

    def _draw_upgrade_rows(self, state: GameState) -> None:
        top, bottom = self._list_bounds()
        scroll = self._scroll[ShopTab.UPGRADES]
        y = top + scroll

        visible: list[UpgradeDef] = [
            u for u in UPGRADES if state.is_upgrade_visible(u.key)
        ]

        for upgrade in visible:
            row_top = y
            row_bottom = row_top - _ROW_HEIGHT
            y = row_bottom - _ROW_MARGIN
            if row_top < bottom or row_bottom > top:
                continue
            self._draw_upgrade_row(state, upgrade, row_bottom)

        if not visible:
            arcade.draw_text(
                "No upgrades yet — keep buying helpers to unlock them.",
                _PANEL_LEFT + SHOP_PANEL_WIDTH / 2,
                (top + bottom) / 2,
                COLOR_TEXT_DIM,
                font_size=13,
                width=SHOP_PANEL_WIDTH - 40,
                anchor_x="center",
                anchor_y="center",
                multiline=True,
                align="center",
                italic=True,
            )

    def _draw_upgrade_row(
        self,
        state: GameState,
        upgrade: UpgradeDef,
        row_bottom: float,
    ) -> None:
        row = Button(
            left=_PANEL_LEFT + _ROW_MARGIN,
            bottom=row_bottom,
            width=SHOP_PANEL_WIDTH - 2 * _ROW_MARGIN,
            height=_ROW_HEIGHT,
        )
        affordable = state.can_afford_upgrade(upgrade.key)
        hovered = row.contains(self._mouse_x, self._mouse_y)
        row.draw_background(hovered=hovered, affordable=affordable)

        arcade.draw_text(
            upgrade.name,
            row.left + _ROW_PADDING,
            row.top - 22,
            COLOR_TEXT_PRIMARY,
            font_size=15,
            anchor_y="baseline",
            bold=True,
        )

        # Effect description.
        effect_text = self._describe_effect(upgrade)
        arcade.draw_text(
            effect_text,
            row.left + _ROW_PADDING,
            row.top - 42,
            COLOR_TEXT_GOLD,
            font_size=12,
            anchor_y="baseline",
            bold=True,
        )

        arcade.draw_text(
            upgrade.flavor,
            row.left + _ROW_PADDING,
            row.bottom + 8,
            COLOR_TEXT_DIM,
            font_size=10,
            italic=True,
            anchor_y="baseline",
        )

        price_color = COLOR_TEXT_OK if affordable else COLOR_TEXT_DIM
        arcade.draw_text(
            f"{format_number(upgrade.cost)}",
            row.right - _ROW_PADDING,
            row.bottom + 10,
            price_color,
            font_size=16,
            anchor_x="right",
            anchor_y="baseline",
            bold=True,
        )
        arcade.draw_text(
            "shards",
            row.right - _ROW_PADDING,
            row.bottom + 4,
            COLOR_TEXT_DIM,
            font_size=9,
            anchor_x="right",
            anchor_y="baseline",
        )

        self._row_hits.append(_RowHit(kind="upgrade", key=upgrade.key, button=row))

    @staticmethod
    def _describe_effect(upgrade: UpgradeDef) -> str:
        if upgrade.effect == "click":
            return f"x{upgrade.multiplier:g} click power"
        if upgrade.effect == "global":
            return f"x{upgrade.multiplier:g} all production"
        if upgrade.effect.startswith("gen:"):
            return f"x{upgrade.multiplier:g} production"
        return ""
