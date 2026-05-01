"""The main arcade.View that owns the whole game loop.

All state lives in ``GameState``; this view wires rendering, input, timers,
and autosave around it.
"""

from __future__ import annotations

import math
import random

import arcade
from PIL import Image, ImageDraw

from src.constants import (
    AUTOSAVE_INTERVAL_SECONDS,
    CLICK_PARTICLE_COUNT,
    COLOR_BG_BOTTOM,
    COLOR_BG_TOP,
    COLOR_TEXT_DIM,
    COLOR_TEXT_GOLD,
    COLOR_TEXT_PRIMARY,
    PLAY_AREA_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.entities.crystal_aura import CrystalAura
from src.entities.main_clicker import MainClicker
from src.game_state import CRYSTAL_MAX_TIER, GameState
from src.generators import GENERATORS, GENERATORS_BY_KEY
from src.number_format import format_number
from src.save_system import apply_offline_earnings, load_game, save_game
from src.sprite_factory import (
    generator_texture,
    main_crystal_texture,
    shard_particle_texture,
)
from src.ui.button import Button
from src.ui.descend_modal import DescendModal
from src.ui.floating_text import FloatingTextLayer
from src.ui.particles import ParticleBurst
from src.ui.shop_panel import ShopPanel
from src.ui.stats_panel import StatsPanel
from src.ui.toast import ToastLayer
from src.ui.welcome_back import WelcomeBackModal
from src.upgrades import UPGRADES_BY_KEY


class _Ambient:
    """Lightweight drifting star/particle bed behind the play area."""

    def __init__(self, count: int = 40) -> None:
        self._motes = []
        for _ in range(count):
            self._motes.append({
                "x": random.uniform(0, PLAY_AREA_WIDTH),
                "y": random.uniform(0, SCREEN_HEIGHT - 140),
                "r": random.uniform(1, 2.2),
                "phase": random.uniform(0, math.tau),
                "speed": random.uniform(6, 18),
                "alpha_base": random.randint(80, 180),
            })
        self._time = 0.0

    def update(self, delta: float) -> None:
        self._time += delta
        for m in self._motes:
            m["y"] += m["speed"] * delta
            if m["y"] > SCREEN_HEIGHT - 140:
                m["y"] = 0
                m["x"] = random.uniform(0, PLAY_AREA_WIDTH)

    def draw(self) -> None:
        for m in self._motes:
            twinkle = (math.sin(self._time * 2.0 + m["phase"]) + 1) / 2
            alpha = int(m["alpha_base"] * (0.4 + 0.6 * twinkle))
            arcade.draw_circle_filled(
                m["x"], m["y"], m["r"], (200, 220, 255, alpha)
            )


def _make_background_texture() -> arcade.Texture:
    """Vertical gradient drawn once and blitted per frame."""
    w, h = 32, 256
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        r = int(COLOR_BG_TOP[0] * (1 - t) + COLOR_BG_BOTTOM[0] * t)
        g = int(COLOR_BG_TOP[1] * (1 - t) + COLOR_BG_BOTTOM[1] * t)
        b = int(COLOR_BG_TOP[2] * (1 - t) + COLOR_BG_BOTTOM[2] * t)
        d.line([(0, y), (w, y)], fill=(r, g, b, 255))
    return arcade.Texture(img)


class GameView(arcade.View):
    def __init__(self) -> None:
        super().__init__()

        # --- Load or create state + grant offline earnings. ---
        loaded = load_game()
        self.state: GameState = loaded if loaded is not None else GameState()
        elapsed, gained = (0.0, 0.0)
        if loaded is not None:
            elapsed, gained = apply_offline_earnings(self.state)

        # --- Textures (one main-crystal texture per tier, pre-generated). ---
        self._bg_texture = _make_background_texture()
        self._crystal_textures: list[arcade.Texture] = [
            main_crystal_texture(t) for t in range(CRYSTAL_MAX_TIER + 1)
        ]
        self._particle_texture = shard_particle_texture()
        self._generator_textures: dict[str, arcade.Texture] = {
            g.key: generator_texture(g) for g in GENERATORS
        }

        # --- Entities / UI. ---
        self._ambient = _Ambient()
        initial_tier = self.state.crystal_tier()
        self._current_tier = initial_tier
        self._clicker = MainClicker(self._crystal_textures[initial_tier])
        self._aura = CrystalAura(self._generator_textures)
        self._particles = ParticleBurst(self._particle_texture)
        self._floating = FloatingTextLayer()
        self._toasts = ToastLayer()
        self._shop = ShopPanel(self._generator_textures)
        self._stats = StatsPanel(self._generator_textures)

        self._autosave_hint = arcade.Text(
            "Autosaves every 15s • F5 to save now",
            PLAY_AREA_WIDTH - 16, 12,
            COLOR_TEXT_DIM,
            font_size=10, anchor_x="right", anchor_y="baseline", italic=True,
        )

        # Descend button — bottom-center of the play area, above the
        # autosave hint. Rendered only when the player can descend.
        self._descend_button = Button(
            left=PLAY_AREA_WIDTH / 2 - 170, bottom=40, width=340, height=56,
        )
        self._descend_label = arcade.Text(
            "", self._descend_button.center_x, self._descend_button.center_y + 8,
            COLOR_TEXT_PRIMARY, font_size=16,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._descend_sub = arcade.Text(
            "", self._descend_button.center_x, self._descend_button.center_y - 12,
            COLOR_TEXT_GOLD, font_size=12,
            anchor_x="center", anchor_y="center",
        )
        self._descend_pulse = 0.0  # pulsing glow when button is active

        self._welcome: WelcomeBackModal | None = None
        if gained >= 1:
            self._welcome = WelcomeBackModal(elapsed, gained)
        self._descend_modal: DescendModal | None = None

        # --- Timers. ---
        self._time_since_autosave = 0.0
        self._mouse_x = 0.0
        self._mouse_y = 0.0

    # ------------------------------------------------------------------
    # Input.
    # ------------------------------------------------------------------

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self._mouse_x, self._mouse_y = float(x), float(y)
        self._clicker.set_hover(self._clicker.contains(x, y))
        self._shop.on_mouse_motion(x, y)
        if self._welcome:
            self._welcome.on_mouse_motion(x, y)
        if self._descend_modal:
            self._descend_modal.on_mouse_motion(x, y)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        if self._blocking_modal_visible():
            return
        self._shop.on_mouse_scroll(x, y, scroll_y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        if self._welcome and self._welcome.visible:
            self._welcome.handle_click(x, y)
            return
        if self._descend_modal and self._descend_modal.visible:
            self._descend_modal.handle_click(x, y)
            if self._descend_modal.confirmed:
                self._apply_descent()
            if not self._descend_modal.visible:
                self._descend_modal = None
            return

        if self.state.can_descend() and self._descend_button.contains(x, y):
            self._descend_modal = DescendModal(self.state)
            return

        if self._shop.contains(x, y):
            intent = self._shop.handle_click(x, y, self.state)
            if intent is None:
                return
            if intent["kind"] == "buy_generator":
                self._try_buy_generator(intent["key"])
            elif intent["kind"] == "buy_upgrade":
                self._try_buy_upgrade(intent["key"])
            return

        if self._clicker.contains(x, y):
            gained = self.state.click()
            self._clicker.register_click()
            self._particles.emit(
                self._clicker.center_x,
                self._clicker.center_y,
                CLICK_PARTICLE_COUNT,
            )
            self._floating.spawn(
                f"+{format_number(gained)}",
                x + random.uniform(-20, 20),
                y + 20,
            )

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        # F5 forces an immediate save — useful for debugging and for players
        # who want to be certain before closing.
        if symbol == arcade.key.F5:
            save_game(self.state)

    # ------------------------------------------------------------------
    # Purchase / descent plumbing.
    # ------------------------------------------------------------------

    def _try_buy_generator(self, key: str) -> None:
        gen = GENERATORS_BY_KEY.get(key)
        if gen is None or not self.state.buy_generator(gen):
            return
        owned = self.state.owned.get(key, 0)
        self._on_purchase_feedback(
            key=key,
            toast_text=f"+1 {gen.name}  (x{owned})",
            accent=gen.color,
        )
        save_game(self.state)

    def _try_buy_upgrade(self, key: str) -> None:
        if not self.state.buy_upgrade(key):
            return
        upgrade = UPGRADES_BY_KEY.get(key)
        if upgrade is None:
            return
        accent = self._upgrade_accent(upgrade)
        level = self.state.upgrade_level(key)
        if level >= upgrade.max_level:
            toast = f"{upgrade.name} MAXED! (Lv {level}/{upgrade.max_level})"
        else:
            toast = f"{upgrade.name}  Lv {level}/{upgrade.max_level}"
        self._on_purchase_feedback(key=key, toast_text=toast, accent=accent)
        save_game(self.state)

    def _upgrade_accent(self, upgrade) -> tuple[int, int, int]:
        """Gold for click/global upgrades; the generator's color for gen:* ones."""
        if upgrade.effect.startswith("gen:"):
            gen = GENERATORS_BY_KEY.get(upgrade.effect.split(":", 1)[1])
            if gen is not None:
                return gen.color
        if upgrade.effect == "click":
            return (255, 214, 110)  # warm gold
        return (180, 150, 255)  # global — violet

    def _on_purchase_feedback(
        self,
        *,
        key: str,
        toast_text: str,
        accent: tuple[int, int, int],
    ) -> None:
        """Fire every purchase confirmation effect at once."""
        self._shop.flash(key)
        self._toasts.spawn(toast_text, accent)
        self._clicker.register_purchase()
        self._particles.emit(
            self._clicker.center_x,
            self._clicker.center_y,
            CLICK_PARTICLE_COUNT + 6,
            color=accent,
        )
        # Tier may have just bumped thanks to the new upgrade.
        self._maybe_swap_crystal()

    def _maybe_swap_crystal(self) -> None:
        new_tier = self.state.crystal_tier()
        if new_tier != self._current_tier:
            self._current_tier = new_tier
            self._clicker.set_texture(self._crystal_textures[new_tier])

    def _apply_descent(self) -> None:
        gained = self.state.descend()
        if gained <= 0:
            return
        self._toasts.spawn(f"Descended! +{gained} Essence", (255, 220, 140))
        self._particles.emit(
            self._clicker.center_x,
            self._clicker.center_y,
            30,
            color=(240, 220, 255),
        )
        self._clicker.register_purchase()
        self._maybe_swap_crystal()
        save_game(self.state)

    def _blocking_modal_visible(self) -> bool:
        if self._welcome and self._welcome.visible:
            return True
        if self._descend_modal and self._descend_modal.visible:
            return True
        return False

    # ------------------------------------------------------------------
    # Update loop.
    # ------------------------------------------------------------------

    def on_update(self, delta_time: float) -> None:
        # Tick idle production first so click power/upgrades purchased this
        # frame apply to the next tick, not this one.
        self.state.tick(delta_time)

        self._ambient.update(delta_time)
        self._aura.update(delta_time)
        self._clicker.update(delta_time)
        self._particles.update(delta_time)
        self._floating.update(delta_time)
        self._toasts.update(delta_time)
        self._shop.update(delta_time)

        # Descend button pulse when active.
        if self.state.can_descend():
            self._descend_pulse = (self._descend_pulse + delta_time) % (math.tau / 2)

        self._time_since_autosave += delta_time
        if self._time_since_autosave >= AUTOSAVE_INTERVAL_SECONDS:
            self._time_since_autosave = 0.0
            save_game(self.state)

    # ------------------------------------------------------------------
    # Rendering.
    # ------------------------------------------------------------------

    def on_draw(self) -> None:
        self.clear()

        # Gradient background across the full window.
        bg_rect = arcade.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.draw_texture_rect(self._bg_texture, bg_rect)

        # Play area visuals. The aura draws BEHIND the crystal so the
        # upgrade ring reads as a frame and the orbiting emblems pass
        # behind the crystal faces.
        self._ambient.draw()
        self._aura.draw(self.state)
        self._clicker.draw()
        self._particles.draw()
        self._floating.draw()
        self._toasts.draw()

        # HUD and shop.
        self._stats.draw(self.state)
        self._shop.draw(self.state)

        if self.state.can_descend():
            self._draw_descend_button()

        # Save hint (bottom-right of play area).
        self._autosave_hint.draw()

        # Modals last so they sit on top of everything.
        if self._welcome and self._welcome.visible:
            self._welcome.draw()
        if self._descend_modal and self._descend_modal.visible:
            self._descend_modal.draw()

    def _draw_descend_button(self) -> None:
        hovered = self._descend_button.contains(self._mouse_x, self._mouse_y)
        self._descend_button.draw_background(hovered=hovered, affordable=True)
        # Outer pulsing border — subtle "something is available" cue.
        glow = 0.5 + 0.5 * math.sin(self._descend_pulse * 4)
        border_alpha = int(80 + 120 * glow)
        outline = arcade.LBWH(
            self._descend_button.left - 3, self._descend_button.bottom - 3,
            self._descend_button.width + 6, self._descend_button.height + 6,
        )
        arcade.draw_rect_outline(outline, (255, 220, 140, border_alpha), border_width=2)

        pending = self.state.pending_essence()
        self._descend_label.text = "⬇  Descend Deeper"
        self._descend_sub.text = f"+{pending} Essence  (x{(1 + 0.02 * (self.state.essence + pending)):.2f} total)"
        self._descend_label.draw()
        self._descend_sub.draw()

    # ------------------------------------------------------------------
    # Lifecycle.
    # ------------------------------------------------------------------

    def on_hide_view(self) -> None:
        save_game(self.state)
