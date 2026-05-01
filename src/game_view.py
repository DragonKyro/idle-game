"""The main arcade.View that owns the whole game loop.

All state lives in ``GameState``; this view wires rendering, input, timers,
and autosave around it.
"""

from __future__ import annotations

import math
import random
import time

import arcade
from PIL import Image, ImageDraw

from src.constants import (
    AUTOSAVE_INTERVAL_SECONDS,
    CLICK_PARTICLE_COUNT,
    COLOR_BG_BOTTOM,
    COLOR_BG_TOP,
    COLOR_TEXT_DIM,
    PLAY_AREA_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.entities.main_clicker import MainClicker
from src.game_state import GameState
from src.generators import GENERATORS, GENERATORS_BY_KEY
from src.number_format import format_number
from src.save_system import apply_offline_earnings, load_game, save_game
from src.sprite_factory import (
    generator_texture,
    main_crystal_texture,
    shard_particle_texture,
)
from src.ui.floating_text import FloatingTextLayer
from src.ui.particles import ParticleBurst
from src.ui.shop_panel import ShopPanel
from src.ui.stats_panel import StatsPanel
from src.ui.welcome_back import WelcomeBackModal


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
    """Vertical gradient drawn once and blitted per frame.

    Cheaper than drawing dozens of horizontal strips every frame.
    """
    # Keep it small; we'll stretch at blit time.
    w, h = 32, 256
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        r = int(COLOR_BG_TOP[0] * (1 - t) + COLOR_BG_BOTTOM[0] * t)
        g = int(COLOR_BG_TOP[1] * (1 - t) + COLOR_BG_BOTTOM[1] * t)
        b = int(COLOR_BG_TOP[2] * (1 - t) + COLOR_BG_BOTTOM[2] * t)
        # Arcade treats image y=0 as top; we want top color at the top of
        # the screen, so draw directly without flipping.
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

        # --- Textures. ---
        self._bg_texture = _make_background_texture()
        self._crystal_texture = main_crystal_texture()
        self._particle_texture = shard_particle_texture()
        self._generator_textures: dict[str, arcade.Texture] = {
            g.key: generator_texture(g) for g in GENERATORS
        }

        # --- Entities / UI. ---
        self._ambient = _Ambient()
        self._clicker = MainClicker(self._crystal_texture)
        self._particles = ParticleBurst(self._particle_texture)
        self._floating = FloatingTextLayer()
        self._shop = ShopPanel(self._generator_textures)
        self._stats = StatsPanel(self._generator_textures)
        self._welcome: WelcomeBackModal | None = None
        if gained >= 1:
            self._welcome = WelcomeBackModal(elapsed, gained)

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

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        if self._welcome and self._welcome.visible:
            return
        self._shop.on_mouse_scroll(x, y, scroll_y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        if self._welcome and self._welcome.visible:
            self._welcome.handle_click(x, y)
            return

        if self._shop.contains(x, y):
            intent = self._shop.handle_click(x, y, self.state)
            if intent is None:
                return
            if intent["kind"] == "buy_generator":
                gen = GENERATORS_BY_KEY.get(intent["key"])
                if gen and self.state.buy_generator(gen):
                    save_game(self.state)
            elif intent["kind"] == "buy_upgrade":
                if self.state.buy_upgrade(intent["key"]):
                    save_game(self.state)
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
    # Update loop.
    # ------------------------------------------------------------------

    def on_update(self, delta_time: float) -> None:
        # Tick idle production first so click power/upgrades purchased this
        # frame apply to the next tick, not this one.
        self.state.tick(delta_time)

        self._ambient.update(delta_time)
        self._clicker.update(delta_time)
        self._particles.update(delta_time)
        self._floating.update(delta_time)

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

        # Play area visuals.
        self._ambient.draw()
        self._clicker.draw()
        self._particles.draw()
        self._floating.draw()

        # HUD and shop.
        self._stats.draw(self.state)
        self._shop.draw(self.state)

        # Save hint (bottom-right of play area).
        arcade.draw_text(
            "Autosaves every 15s • F5 to save now",
            PLAY_AREA_WIDTH - 16,
            12,
            COLOR_TEXT_DIM,
            font_size=10,
            anchor_x="right",
            anchor_y="baseline",
            italic=True,
        )

        # Modal last so it sits on top of everything.
        if self._welcome and self._welcome.visible:
            self._welcome.draw()

    # ------------------------------------------------------------------
    # Lifecycle.
    # ------------------------------------------------------------------

    def on_hide_view(self) -> None:
        # View-level catch — Window.on_close is the primary save trigger.
        save_game(self.state)
