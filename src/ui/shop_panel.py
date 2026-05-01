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


def _describe_effect(upgrade: UpgradeDef) -> str:
    # Each level applies the multiplier once; callers know to call out the
    # "per level" semantics in the UI.
    if upgrade.effect == "click":
        return f"x{upgrade.multiplier:g} click power / level"
    if upgrade.effect == "global":
        return f"x{upgrade.multiplier:g} all production / level"
    if upgrade.effect.startswith("gen:"):
        return f"x{upgrade.multiplier:g} production / level"
    return ""


class _GenRowTexts:
    """Cached Text objects for a single generator row. Static text (name,
    flavor, 'shards' label) is set once at construction; dynamic text
    (owned, rate, price) is updated each frame."""

    def __init__(self, gen: GeneratorDef) -> None:
        self.name = arcade.Text(
            gen.name, 0, 0, COLOR_TEXT_PRIMARY,
            font_size=15, anchor_y="baseline", bold=True,
        )
        self.flavor = arcade.Text(
            gen.flavor, 0, 0, COLOR_TEXT_DIM,
            font_size=10, italic=True, anchor_y="baseline",
        )
        self.owned = arcade.Text(
            "Owned: 0", 0, 0, COLOR_TEXT_SECONDARY,
            font_size=13, anchor_x="right", anchor_y="baseline",
        )
        self.rate = arcade.Text(
            "+0/s each", 0, 0, COLOR_TEXT_SECONDARY,
            font_size=12, anchor_y="baseline",
        )
        self.price = arcade.Text(
            "0", 0, 0, COLOR_TEXT_OK,
            font_size=16, anchor_x="right", anchor_y="baseline", bold=True,
        )
        self.price_label = arcade.Text(
            "shards", 0, 0, COLOR_TEXT_DIM,
            font_size=9, anchor_x="right", anchor_y="baseline",
        )


class _UpgradeRowTexts:
    """Cached Text objects for a single upgrade row."""

    def __init__(self, upgrade: UpgradeDef) -> None:
        self.name = arcade.Text(
            upgrade.name, 0, 0, COLOR_TEXT_PRIMARY,
            font_size=15, anchor_y="baseline", bold=True,
        )
        # Level badge ("Lv 3/5"). Dynamic text, updated each frame.
        self.level = arcade.Text(
            f"Lv 0/{upgrade.max_level}", 0, 0, COLOR_TEXT_SECONDARY,
            font_size=12, anchor_x="right", anchor_y="baseline",
        )
        self.effect = arcade.Text(
            _describe_effect(upgrade), 0, 0, COLOR_TEXT_GOLD,
            font_size=12, anchor_y="baseline", bold=True,
        )
        self.flavor = arcade.Text(
            upgrade.flavor, 0, 0, COLOR_TEXT_DIM,
            font_size=10, italic=True, anchor_y="baseline",
        )
        self.price = arcade.Text(
            format_number(upgrade.cost), 0, 0, COLOR_TEXT_OK,
            font_size=16, anchor_x="right", anchor_y="baseline", bold=True,
        )
        self.price_label = arcade.Text(
            "shards", 0, 0, COLOR_TEXT_DIM,
            font_size=9, anchor_x="right", anchor_y="baseline",
        )
        # Shown instead of the price when the upgrade is at max level.
        self.maxed_badge = arcade.Text(
            "MAX", 0, 0, COLOR_TEXT_GOLD,
            font_size=14, anchor_x="right", anchor_y="baseline", bold=True,
        )


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
        # Row-flash timers, keyed by generator/upgrade key. Set to 1.0 on a
        # successful purchase and decays in update(); while > 0, the row is
        # overlaid with a soft gold tint to draw the player's eye there.
        self._flashes: dict[str, float] = {}

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

        # --- Cached text objects. ---
        self._header_text = arcade.Text(
            "Cavern Emporium",
            _PANEL_LEFT + SHOP_PANEL_WIDTH / 2,
            SCREEN_HEIGHT - _HEADER_HEIGHT / 2,
            COLOR_TEXT_PRIMARY,
            font_size=22, anchor_x="center", anchor_y="center", bold=True,
        )
        self._tab_labels = {
            tab: arcade.Text(
                tab.value.title(),
                self._tab_buttons[tab].center_x,
                self._tab_buttons[tab].center_y,
                COLOR_TEXT_PRIMARY,
                font_size=14, anchor_x="center", anchor_y="center",
                bold=(tab is ShopTab.GENERATORS),
            )
            for tab in ShopTab
        }
        self._empty_gens_text = arcade.Text(
            "Keep mining to unlock helpers!",
            _PANEL_LEFT + SHOP_PANEL_WIDTH / 2, 0,
            COLOR_TEXT_DIM,
            font_size=14, anchor_x="center", anchor_y="center", italic=True,
        )
        self._empty_upgrades_text = arcade.Text(
            "No upgrades yet — keep buying helpers to unlock them.",
            _PANEL_LEFT + SHOP_PANEL_WIDTH / 2, 0,
            COLOR_TEXT_DIM,
            font_size=13,
            width=SHOP_PANEL_WIDTH - 40,
            anchor_x="center", anchor_y="center",
            multiline=True, align="center", italic=True,
        )

        # Per-row text pools — one set per defined generator / upgrade.
        self._gen_texts: dict[str, _GenRowTexts] = {
            g.key: _GenRowTexts(g) for g in GENERATORS
        }
        self._upgrade_texts: dict[str, _UpgradeRowTexts] = {
            u.key: _UpgradeRowTexts(u) for u in UPGRADES
        }

    # ------------------------------------------------------------------
    # Input.
    # ------------------------------------------------------------------

    def contains(self, x: float, y: float) -> bool:
        return x >= _PANEL_LEFT

    def on_mouse_motion(self, x: float, y: float) -> None:
        self._mouse_x = x
        self._mouse_y = y

    def update(self, delta: float) -> None:
        """Decay any active row flashes. Call once per frame."""
        if not self._flashes:
            return
        decay = 1.0 / 0.55  # 0.55s fade
        new: dict[str, float] = {}
        for key, value in self._flashes.items():
            value -= delta * decay
            if value > 0:
                new[key] = value
        self._flashes = new

    def flash(self, key: str) -> None:
        """Trigger a purchase flash on a given row."""
        self._flashes[key] = 1.0

    def on_mouse_scroll(self, x: float, y: float, dy: float) -> None:
        if not self.contains(x, y):
            return
        # dy > 0 means scroll up — which in a top-anchored list should
        # reveal *earlier* items, i.e. shrink the scroll offset.
        self._scroll[self._tab] = max(0.0, self._scroll[self._tab] - dy * _SCROLL_STEP)

    def handle_click(self, x: float, y: float, state: GameState) -> dict | None:
        """Return a dict describing what was clicked, or None."""
        if not self.contains(x, y):
            return None

        for tab, btn in self._tab_buttons.items():
            if btn.contains(x, y):
                if self._tab is not tab:
                    self._tab = tab
                    # Bolding follows the active tab.
                    for t, label in self._tab_labels.items():
                        label.bold = (t is self._tab)
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
        accent = arcade.LBWH(_PANEL_LEFT, 0, 2, SCREEN_HEIGHT)
        arcade.draw_rect_filled(accent, COLOR_PANEL_BORDER)

    def _draw_header(self) -> None:
        header = arcade.LBWH(
            _PANEL_LEFT, SCREEN_HEIGHT - _HEADER_HEIGHT,
            SHOP_PANEL_WIDTH, _HEADER_HEIGHT,
        )
        arcade.draw_rect_filled(header, COLOR_PANEL_HIGHLIGHT)
        self._header_text.draw()

    def _draw_tabs(self) -> None:
        for tab, btn in self._tab_buttons.items():
            hovered = btn.contains(self._mouse_x, self._mouse_y)
            active = tab is self._tab
            btn.draw_background(hovered=hovered, affordable=active)
            self._tab_labels[tab].draw()

    def _draw_flash_overlay(self, key: str, row: Button) -> None:
        """Soft gold overlay while a row's flash timer is above zero."""
        strength = self._flashes.get(key, 0.0)
        if strength <= 0:
            return
        alpha = int(180 * strength)
        rect = arcade.LBWH(row.left, row.bottom, row.width, row.height)
        arcade.draw_rect_filled(rect, (255, 220, 140, alpha))

    def _list_bounds(self) -> tuple[float, float]:
        top = SCREEN_HEIGHT - _HEADER_HEIGHT - _TAB_HEIGHT - _ROW_MARGIN
        bottom = 12
        return top, bottom

    def _draw_generator_rows(self, state: GameState) -> None:
        top, bottom = self._list_bounds()
        scroll = self._scroll[ShopTab.GENERATORS]
        y = top + scroll

        visible: list[tuple[GeneratorDef, int, float]] = []
        for gen in GENERATORS:
            if not state.is_generator_unlocked(gen):
                continue
            owned = state.owned.get(gen.key, 0)
            price = cost_for(gen, owned)
            visible.append((gen, owned, price))

        for gen, owned, price in visible:
            row_top = y
            row_bottom = row_top - _ROW_HEIGHT
            y = row_bottom - _ROW_MARGIN

            if row_top < bottom or row_bottom > top:
                continue

            self._draw_generator_row(state, gen, owned, price, row_bottom)

        if not visible:
            self._empty_gens_text.y = (top + bottom) / 2
            self._empty_gens_text.draw()

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
        self._draw_flash_overlay(gen.key, row)

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
        t = self._gen_texts[gen.key]

        t.name.x = text_left
        t.name.y = row.top - 22
        t.name.draw()

        t.owned.x = row.right - _ROW_PADDING
        t.owned.y = row.top - 22
        t.owned.text = f"Owned: {owned}"
        t.owned.draw()

        per_unit = state.generator_rate(gen)
        t.rate.x = text_left
        t.rate.y = row.top - 42
        t.rate.text = f"+{format_rate(per_unit)} each"
        t.rate.draw()

        t.price.x = row.right - _ROW_PADDING
        t.price.y = row.bottom + 10
        t.price.text = format_number(price)
        t.price.color = COLOR_TEXT_OK if affordable else COLOR_TEXT_DIM
        t.price.draw()

        t.price_label.x = row.right - _ROW_PADDING
        t.price_label.y = row.bottom + 4
        t.price_label.draw()

        t.flavor.x = text_left
        t.flavor.y = row.bottom + 8
        t.flavor.draw()

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
            self._empty_upgrades_text.y = (top + bottom) / 2
            self._empty_upgrades_text.draw()

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
        level = state.upgrade_level(upgrade.key)
        maxed = state.upgrade_is_maxed(upgrade.key)
        affordable = state.can_afford_upgrade(upgrade.key)
        hovered = row.contains(self._mouse_x, self._mouse_y)
        # Maxed rows render in the "idle" palette regardless of hover so they
        # read as "done" rather than "clickable".
        row.draw_background(
            hovered=hovered and not maxed,
            affordable=affordable,
            enabled=not maxed,
        )
        if not maxed:
            self._draw_flash_overlay(upgrade.key, row)

        t = self._upgrade_texts[upgrade.key]

        t.name.x = row.left + _ROW_PADDING
        t.name.y = row.top - 22
        t.name.color = COLOR_TEXT_DIM if maxed else COLOR_TEXT_PRIMARY
        t.name.draw()

        # Level badge in the top-right of the row.
        t.level.x = row.right - _ROW_PADDING
        t.level.y = row.top - 22
        t.level.text = f"Lv {level}/{upgrade.max_level}"
        t.level.color = COLOR_TEXT_GOLD if maxed else COLOR_TEXT_SECONDARY
        t.level.draw()

        t.effect.x = row.left + _ROW_PADDING
        t.effect.y = row.top - 42
        t.effect.draw()

        t.flavor.x = row.left + _ROW_PADDING
        t.flavor.y = row.bottom + 8
        t.flavor.draw()

        if maxed:
            # Replace the price column with a prominent "MAX" badge.
            t.maxed_badge.x = row.right - _ROW_PADDING
            t.maxed_badge.y = row.bottom + 10
            t.maxed_badge.draw()
        else:
            next_cost = state.next_upgrade_cost(upgrade.key) or 0.0
            t.price.x = row.right - _ROW_PADDING
            t.price.y = row.bottom + 10
            t.price.text = format_number(next_cost)
            t.price.color = COLOR_TEXT_OK if affordable else COLOR_TEXT_DIM
            t.price.draw()

            t.price_label.x = row.right - _ROW_PADDING
            t.price_label.y = row.bottom + 4
            t.price_label.draw()

        self._row_hits.append(_RowHit(kind="upgrade", key=upgrade.key, button=row))
