"""The main arcade.View that owns the whole game loop.

All state lives in ``GameState``; this view wires rendering, input,
timers, audio, animations, modals, and autosave around it.
"""

from __future__ import annotations

import json
import math
import random
import shutil
from pathlib import Path

import arcade
from PIL import Image, ImageDraw

from src.achievements import newly_unlocked
from src.audio import AudioLibrary
from src.biomes import biome_for_prestige
from src.constants import (
    AUTOSAVE_INTERVAL_SECONDS,
    CLICK_PARTICLE_COUNT,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_DIM,
    COLOR_TEXT_GOLD,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    PLAY_AREA_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.entities.cavern_lord import (
    CavernLord,
    boss_hp_for_index,
    boss_reward_for_index,
    spawn_boss,
)
from src.entities.crystal_aura import CrystalAura
from src.entities.main_clicker import MainClicker
from src.game_state import (
    CRYSTAL_MAX_TIER,
    GameState,
    default_settings,
)
from src.generators import GENERATORS, GENERATORS_BY_KEY
from src.number_format import format_number
from src.save_system import apply_offline_earnings, default_save_path, load_game, save_game
from src.sprite_factory import (
    generator_texture,
    main_crystal_texture,
    shard_particle_texture,
)
from src.ui.achievement_banner import AchievementBannerLayer
from src.ui.achievement_panel import AchievementPanel
from src.ui.button import Button
from src.ui.combo_meter import ComboMeter
from src.ui.descend_modal import DescendModal
from src.ui.floating_text import FloatingTextLayer
from src.ui.juice import ScreenShake, TweenedValue
from src.ui.onboarding import Onboarding
from src.ui.particles import ParticleBurst
from src.ui.random_events import RandomEventLayer
from src.ui.settings_modal import SettingsModal
from src.ui.shop_panel import ShopPanel
from src.ui.stats_modal import StatsModal
from src.ui.stats_panel import StatsPanel
from src.ui.talent_panel import TalentPanel
from src.ui.toast import ToastLayer
from src.ui.welcome_back import WelcomeBackModal
from src.upgrades import UPGRADES_BY_KEY


# Boss spawn thresholds (lifetime shards earned). Indexed by
# bosses_defeated so players who have dispatched N already face the
# N+1th at the appropriate tier.
_BOSS_THRESHOLDS = [
    1e6,        # 1M — reachable once you have a handful of carts/drills
    1e9,        # 1B
    1e12,       # 1T
    1e15,       # 1Qa
    1e18,       # 1Qi
    1e21, 1e24, 1e27, 1e30,
]


class _Ambient:
    """Lightweight drifting mote bed. Color is biome-driven."""

    def __init__(self, mote_color: tuple[int, int, int], count: int = 40) -> None:
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
        self._color = mote_color

    def set_color(self, color: tuple[int, int, int]) -> None:
        self._color = color

    def update(self, delta: float) -> None:
        self._time += delta
        for m in self._motes:
            m["y"] += m["speed"] * delta
            if m["y"] > SCREEN_HEIGHT - 140:
                m["y"] = 0
                m["x"] = random.uniform(0, PLAY_AREA_WIDTH)

    def draw(self) -> None:
        r, g, b = self._color
        for m in self._motes:
            twinkle = (math.sin(self._time * 2.0 + m["phase"]) + 1) / 2
            alpha = int(m["alpha_base"] * (0.4 + 0.6 * twinkle))
            arcade.draw_circle_filled(m["x"], m["y"], m["r"], (r, g, b, alpha))


def _make_background_texture(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> arcade.Texture:
    """Vertical gradient drawn once and blitted per frame."""
    w, h = 32, 256
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
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

        # --- Textures, biome-aware. ---
        self._biome = biome_for_prestige(self.state.prestige_count)
        self._bg_texture = _make_background_texture(self._biome.bg_top, self._biome.bg_bottom)
        self._crystal_textures: list[arcade.Texture] = [
            main_crystal_texture(t) for t in range(CRYSTAL_MAX_TIER + 1)
        ]
        self._particle_texture = shard_particle_texture()
        self._generator_textures: dict[str, arcade.Texture] = {
            g.key: generator_texture(g) for g in GENERATORS
        }

        # --- Audio (synthesized on first construction; cached thereafter). ---
        self._audio = AudioLibrary()
        self._audio.sfx_volume = self.state.settings.get("sfx_volume", 0.6)
        self._audio.music_volume = self.state.settings.get("music_volume", 0.4)

        # --- Entities / UI layers. ---
        self._ambient = _Ambient(self._biome.mote_color)
        initial_tier = self.state.crystal_tier()
        self._current_tier = initial_tier
        self._clicker = MainClicker(self._crystal_textures[initial_tier])
        self._aura = CrystalAura(self._generator_textures)
        self._particles = ParticleBurst(self._particle_texture)
        self._floating = FloatingTextLayer()
        self._toasts = ToastLayer()
        self._combo = ComboMeter()
        self._events = RandomEventLayer()
        self._banner = AchievementBannerLayer()
        self._onboarding = Onboarding()

        # Juice.
        self._shake = ScreenShake()
        self._shake.enabled = self.state.settings.get("screen_shake", True) and not self.state.settings.get("reduced_motion", False)
        self._wallet_tween = TweenedValue(self.state.shards, rate=7.0)
        self._wallet_tween.enabled = not self.state.settings.get("reduced_motion", False)

        # Shop + HUD.
        self._shop = ShopPanel(self._generator_textures)
        self._stats = StatsPanel(self._generator_textures)

        self._autosave_hint = arcade.Text(
            "Autosave every 15s • F5 save • Esc settings • T talents • A achievements • S stats",
            PLAY_AREA_WIDTH - 16, 12,
            COLOR_TEXT_DIM,
            font_size=10, anchor_x="right", anchor_y="baseline", italic=True,
        )

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
        self._descend_pulse = 0.0

        # Buff badge — only visible while a Lucky Critter buff is active.
        self._buff_text = arcade.Text(
            "",
            PLAY_AREA_WIDTH / 2, SCREEN_HEIGHT - 138 + 14,
            COLOR_TEXT_PRIMARY,
            font_size=12, anchor_x="center", anchor_y="center", bold=True,
        )

        # Top-right iconic buttons for quick access to the meta panels.
        # Positioned so they sit to the left of the essence badge.
        self._stats_button = Button(
            left=16, bottom=SCREEN_HEIGHT - 88, width=64, height=28,
        )
        self._achievements_button = Button(
            left=88, bottom=SCREEN_HEIGHT - 88, width=110, height=28,
        )
        self._talents_button = Button(
            left=206, bottom=SCREEN_HEIGHT - 88, width=80, height=28,
        )
        self._settings_button = Button(
            left=294, bottom=SCREEN_HEIGHT - 88, width=80, height=28,
        )
        self._stats_button_label = arcade.Text(
            "Stats", self._stats_button.center_x, self._stats_button.center_y,
            COLOR_TEXT_PRIMARY, font_size=11,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._ach_button_label = arcade.Text(
            "Achievements", self._achievements_button.center_x,
            self._achievements_button.center_y,
            COLOR_TEXT_PRIMARY, font_size=11,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._tal_button_label = arcade.Text(
            "Talents", self._talents_button.center_x, self._talents_button.center_y,
            COLOR_TEXT_PRIMARY, font_size=11,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._set_button_label = arcade.Text(
            "Settings", self._settings_button.center_x, self._settings_button.center_y,
            COLOR_TEXT_PRIMARY, font_size=11,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Modals.
        self._welcome: WelcomeBackModal | None = None
        if gained >= 1:
            self._welcome = WelcomeBackModal(elapsed, gained)
        self._descend_modal: DescendModal | None = None
        self._settings_modal = SettingsModal(
            on_change=self._handle_settings_change,
            on_export=self._handle_export,
            on_import=self._handle_import,
            on_reset=self._handle_reset,
        )
        self._stats_modal = StatsModal()
        self._achievement_panel = AchievementPanel()
        self._talent_panel = TalentPanel()

        # Mini-boss — session-scoped.
        self._boss: CavernLord | None = None

        # Periodic tasks.
        self._time_since_autosave = 0.0
        self._mouse_x = 0.0
        self._mouse_y = 0.0

    # ------------------------------------------------------------------
    # Settings callbacks.
    # ------------------------------------------------------------------

    def _handle_settings_change(self, changes: dict) -> None:
        self.state.settings.update(changes)
        self._audio.sfx_volume = self.state.settings.get("sfx_volume", 0.6)
        self._audio.music_volume = self.state.settings.get("music_volume", 0.4)
        self._shake.enabled = (
            self.state.settings.get("screen_shake", True)
            and not self.state.settings.get("reduced_motion", False)
        )
        self._wallet_tween.enabled = not self.state.settings.get("reduced_motion", False)
        save_game(self.state)

    def _handle_export(self) -> Path | None:
        src = default_save_path()
        if not src.exists():
            return None
        dest = src.parent / f"save_export_{int(self.state.last_saved_at or 0)}.json"
        try:
            shutil.copyfile(src, dest)
            return dest
        except OSError:
            return None

    def _handle_import(self) -> Path | None:
        """Best-effort import: look for a single file matching save_import*.json
        next to the save. Keeps the flow no-dialog so this stays portable."""
        src_dir = default_save_path().parent
        candidates = sorted(src_dir.glob("save_import*.json"))
        if not candidates:
            return None
        pick = candidates[0]
        try:
            data = json.loads(pick.read_text(encoding="utf-8"))
            self.state = GameState.from_dict(data)
            save_game(self.state)
            # Refresh dependent UI bits.
            self._handle_settings_change({})
            self._biome = biome_for_prestige(self.state.prestige_count)
            self._bg_texture = _make_background_texture(self._biome.bg_top, self._biome.bg_bottom)
            self._ambient.set_color(self._biome.mote_color)
            self._maybe_swap_crystal()
            return pick
        except (OSError, json.JSONDecodeError):
            return None

    def _handle_reset(self) -> None:
        self.state = GameState(settings=default_settings())
        save_game(self.state)
        self._biome = biome_for_prestige(0)
        self._bg_texture = _make_background_texture(self._biome.bg_top, self._biome.bg_bottom)
        self._ambient.set_color(self._biome.mote_color)
        self._maybe_swap_crystal()
        self._wallet_tween.set(0.0, snap=True)
        self._boss = None

    # ------------------------------------------------------------------
    # Input routing.
    # ------------------------------------------------------------------

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self._mouse_x, self._mouse_y = float(x), float(y)
        self._clicker.set_hover(self._clicker.contains(x, y))
        self._shop.on_mouse_motion(x, y)
        if self._welcome: self._welcome.on_mouse_motion(x, y)
        if self._descend_modal: self._descend_modal.on_mouse_motion(x, y)
        self._settings_modal.on_mouse_motion(x, y)
        self._stats_modal.on_mouse_motion(x, y)
        self._achievement_panel.on_mouse_motion(x, y)
        self._talent_panel.on_mouse_motion(x, y)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        self._settings_modal.on_mouse_release(x, y)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        if self._any_modal_visible():
            return
        self._shop.on_mouse_scroll(x, y, scroll_y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Modals first — they consume every click.
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
        if self._settings_modal.visible:
            self._settings_modal.handle_click(x, y, self.state)
            return
        if self._stats_modal.visible:
            self._stats_modal.handle_click(x, y)
            return
        if self._achievement_panel.visible:
            self._achievement_panel.handle_click(x, y)
            return
        if self._talent_panel.visible:
            key = self._talent_panel.handle_click(x, y, self.state)
            if key and self.state.buy_talent(key):
                self._audio.play("level_up", gain=0.8)
                self._toasts.spawn(f"Talent invested: +1", (255, 214, 110))
                save_game(self.state)
            return

        # Header bar buttons (stats / achievements / talents / settings).
        if self._stats_button.contains(x, y):
            self._stats_modal.open()
            return
        if self._achievements_button.contains(x, y):
            self._achievement_panel.open()
            return
        if self._talents_button.contains(x, y):
            self._talent_panel.open()
            return
        if self._settings_button.contains(x, y):
            self._settings_modal.open(self.state)
            return

        # Descend button.
        if self.state.can_descend() and self._descend_button.contains(x, y):
            self._descend_modal = DescendModal(self.state)
            return

        # Random events take priority over the crystal — they're time-critical.
        reward = self._events.handle_click(x, y, self.state)
        if reward is not None:
            self._toasts.spawn(reward, (255, 220, 120))
            self._audio.play("event")
            self._shake.bump(0.2)
            save_game(self.state)
            return

        # Boss click — damage it before the crystal behind it.
        if self._boss is not None and self._boss.contains(x, y):
            self._damage_boss(x, y)
            return

        # Shop row click.
        if self._shop.contains(x, y):
            intent = self._shop.handle_click(x, y, self.state)
            if intent is None:
                return
            if intent["kind"] == "buy_generator":
                self._try_buy_generator(intent["key"])
            elif intent["kind"] == "buy_upgrade":
                self._try_buy_upgrade(intent["key"])
            return

        # Crystal click — last resort.
        if self._clicker.contains(x, y):
            self._register_crystal_click(x, y)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == arcade.key.F5:
            save_game(self.state)
            self._toasts.spawn("Game saved.", (130, 230, 170))
            return
        if symbol == arcade.key.ESCAPE:
            if self._any_modal_visible():
                # Close whichever modal is on top.
                for m in (self._descend_modal, self._welcome):
                    if m and getattr(m, "visible", False):
                        # Welcome/descend dismiss on their own button, not Esc.
                        return
                self._settings_modal._visible = False
                self._stats_modal._visible = False
                self._achievement_panel._visible = False
                self._talent_panel._visible = False
            else:
                self._settings_modal.open(self.state)
            return
        if symbol == arcade.key.T:
            if not self._any_modal_visible():
                self._talent_panel.open()
        elif symbol == arcade.key.A:
            if not self._any_modal_visible():
                self._achievement_panel.open()
        elif symbol == arcade.key.S:
            if not self._any_modal_visible():
                self._stats_modal.open()

    # ------------------------------------------------------------------
    # Gameplay actions.
    # ------------------------------------------------------------------

    def _register_crystal_click(self, x: int, y: int) -> None:
        # Combo multiplier boosts the click's effective gain.
        self._combo.register_click()
        gained, was_crit = self.state.click()
        # Apply combo on top of state's computed click power.
        combo_mult = self._combo.bonus_multiplier
        event_buff = self._events.buff_multiplier
        total_mult = combo_mult * event_buff
        if total_mult > 1.0:
            bonus = gained * (total_mult - 1.0)
            self.state.shards += bonus
            self.state.total_earned += bonus
            gained += bonus

        self._clicker.register_click()
        self._audio.play("click", gain=0.5)
        self._shake.bump(0.08)
        self._particles.emit(
            self._clicker.center_x, self._clicker.center_y,
            CLICK_PARTICLE_COUNT + (6 if was_crit else 0),
            color=(255, 200, 100) if was_crit else (255, 255, 255),
        )
        label = f"+{format_number(gained)}"
        if was_crit:
            label += "!"
        self._floating.spawn(
            label,
            x + random.uniform(-20, 20),
            y + 20,
        )
        self._onboarding.notice_first_click(self.state)

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
        self._audio.play("purchase")
        self._onboarding.notice_first_purchase(self.state)
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
            self._audio.play("max_level")
            self._shake.bump(0.4)
        else:
            toast = f"{upgrade.name}  Lv {level}/{upgrade.max_level}"
            self._audio.play("level_up")
            self._shake.bump(0.15)
        self._on_purchase_feedback(key=key, toast_text=toast, accent=accent)
        self._onboarding.notice_first_purchase(self.state)
        save_game(self.state)

    def _upgrade_accent(self, upgrade) -> tuple[int, int, int]:
        if upgrade.effect.startswith("gen:"):
            gen = GENERATORS_BY_KEY.get(upgrade.effect.split(":", 1)[1])
            if gen is not None:
                return gen.color
        if upgrade.effect == "click":
            return (255, 214, 110)
        return (180, 150, 255)

    def _on_purchase_feedback(self, *, key: str, toast_text: str, accent: tuple[int, int, int]) -> None:
        self._shop.flash(key)
        self._toasts.spawn(toast_text, accent)
        self._clicker.register_purchase()
        self._particles.emit(
            self._clicker.center_x, self._clicker.center_y,
            CLICK_PARTICLE_COUNT + 6,
            color=accent,
        )
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
        self._audio.play("descend")
        self._shake.bump(1.0)
        self._particles.emit(
            self._clicker.center_x, self._clicker.center_y,
            40,
            color=(240, 220, 255),
        )
        self._clicker.register_purchase()

        # Biome rotates on descent.
        self._biome = biome_for_prestige(self.state.prestige_count)
        self._bg_texture = _make_background_texture(self._biome.bg_top, self._biome.bg_bottom)
        self._ambient.set_color(self._biome.mote_color)
        self._maybe_swap_crystal()
        self._wallet_tween.set(self.state.shards, snap=True)
        self._boss = None

        save_game(self.state)

    def _damage_boss(self, x: float, y: float) -> None:
        if self._boss is None:
            return
        damage = max(1.0, self.state.click_power() * self._combo.bonus_multiplier * 5)
        self._combo.register_click()
        killed = self._boss.take_hit(damage, click_x=x, click_y=y)
        self._audio.play("boss_hit", gain=0.6)
        self._shake.bump(0.25)
        self._particles.emit(x, y, 8, color=(255, 120, 90))
        self._floating.spawn(f"-{format_number(damage)}", x, y + 12)
        if killed:
            self._resolve_boss_defeat()

    def _resolve_boss_defeat(self) -> None:
        if self._boss is None:
            return
        index = self._boss.index
        reward = boss_reward_for_index(index)
        self.state.shards += reward
        self.state.total_earned += reward
        self.state.bosses_defeated = max(self.state.bosses_defeated, index + 1)
        self.state.essence += 1
        self.state.total_essence_earned += 1
        self._boss = None
        self._audio.play("boss_defeat")
        self._shake.bump(0.9)
        self._toasts.spawn(
            f"Cavern Lord defeated! +{format_number(reward)}  +1 essence",
            (255, 180, 120),
        )
        save_game(self.state)

    def _maybe_spawn_boss(self) -> None:
        """Trigger a boss once lifetime earnings cross the next threshold."""
        if self._boss is not None:
            return
        idx = self.state.bosses_defeated
        if idx >= len(_BOSS_THRESHOLDS):
            return
        if self.state.total_earned >= _BOSS_THRESHOLDS[idx]:
            self._boss = spawn_boss(idx)
            self._toasts.spawn("A Cavern Lord emerges!", (230, 120, 140))
            self._audio.play("event")
            self._shake.bump(0.5)

    def _any_modal_visible(self) -> bool:
        return (
            (self._welcome is not None and self._welcome.visible)
            or (self._descend_modal is not None and self._descend_modal.visible)
            or self._settings_modal.visible
            or self._stats_modal.visible
            or self._achievement_panel.visible
            or self._talent_panel.visible
        )

    # ------------------------------------------------------------------
    # Update loop.
    # ------------------------------------------------------------------

    def on_update(self, delta_time: float) -> None:
        self.state.tick(delta_time)
        # Playtime only advances while the window is focused enough to tick.
        self.state.playtime_seconds += delta_time

        self._ambient.update(delta_time)
        self._aura.update(delta_time)
        self._clicker.update(delta_time)
        self._particles.update(delta_time)
        self._floating.update(delta_time)
        self._toasts.update(delta_time)
        self._combo.update(delta_time)
        self._events.update(delta_time, self.state)
        self._banner.update(delta_time)
        self._onboarding.update(delta_time, self.state)
        self._shop.update(delta_time)
        self._shake.update(delta_time)
        self._wallet_tween.set(self.state.shards)
        self._wallet_tween.update(delta_time)

        if self._boss is not None:
            self._boss.update(delta_time)
        else:
            self._maybe_spawn_boss()

        # Achievements: check each tick. Cheap; 30 predicates.
        unlocks = newly_unlocked(self.state)
        for ach in unlocks:
            self._banner.spawn(ach)
            self._audio.play("event", gain=0.7)

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

        # Screen shake is applied as a camera-style translation. For the
        # static HUD and modals we want them rock-steady; we simply draw
        # the play-area contents with the offset and the HUD afterwards.
        ox, oy = self._shake.offset()

        bg_rect = arcade.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.draw_texture_rect(self._bg_texture, bg_rect)

        # Play area (subject to shake).
        self._ambient.draw()
        self._aura.draw(self.state)
        if self._boss is not None:
            self._boss.draw()
        self._clicker.draw()
        self._particles.draw()
        self._floating.draw()
        self._combo.draw()
        self._events.draw()
        self._toasts.draw()

        # HUD (not shaken).
        self._stats.draw(self.state, wallet_display=self._wallet_tween.value)
        self._shop.draw(self.state)
        self._draw_header_buttons()

        if self.state.can_descend():
            self._draw_descend_button()

        if self._events.buff_remaining > 0:
            self._draw_buff_badge()

        self._autosave_hint.draw()

        # Onboarding sits above HUD but below modals.
        self._onboarding.draw(self.state)
        self._banner.draw()

        # Modals last so they sit on top of everything.
        if self._welcome and self._welcome.visible: self._welcome.draw()
        if self._descend_modal and self._descend_modal.visible: self._descend_modal.draw()
        self._settings_modal.draw(self.state)
        self._stats_modal.draw(self.state)
        self._achievement_panel.draw(self.state)
        self._talent_panel.draw(self.state)

    def _draw_header_buttons(self) -> None:
        for btn, label in (
            (self._stats_button,        self._stats_button_label),
            (self._achievements_button, self._ach_button_label),
            (self._talents_button,      self._tal_button_label),
            (self._settings_button,     self._set_button_label),
        ):
            hovered = btn.contains(self._mouse_x, self._mouse_y)
            btn.draw_background(hovered=hovered, affordable=False)
            label.draw()

    def _draw_descend_button(self) -> None:
        hovered = self._descend_button.contains(self._mouse_x, self._mouse_y)
        self._descend_button.draw_background(hovered=hovered, affordable=True)
        glow = 0.5 + 0.5 * math.sin(self._descend_pulse * 4)
        border_alpha = int(80 + 120 * glow)
        outline = arcade.LBWH(
            self._descend_button.left - 3, self._descend_button.bottom - 3,
            self._descend_button.width + 6, self._descend_button.height + 6,
        )
        arcade.draw_rect_outline(outline, (255, 220, 140, border_alpha), border_width=2)

        pending = self.state.pending_essence()
        self._descend_label.text = "⬇  Descend Deeper"
        self._descend_sub.text = (
            f"+{pending} Essence  (next biome: "
            f"{biome_for_prestige(self.state.prestige_count + 1).name})"
        )
        self._descend_label.draw()
        self._descend_sub.draw()

    def _draw_buff_badge(self) -> None:
        """Small top-center indicator when a Lucky Critter buff is active."""
        w, h = 180, 28
        left = PLAY_AREA_WIDTH / 2 - w / 2
        bottom = SCREEN_HEIGHT - 138
        rect = arcade.LBWH(left, bottom, w, h)
        arcade.draw_rect_filled(rect, (180, 255, 200, 60))
        arcade.draw_rect_outline(rect, (180, 255, 200, 200), border_width=2)
        self._buff_text.text = (
            f"Lucky x{self._events.buff_multiplier:g} — "
            f"{self._events.buff_remaining:.0f}s"
        )
        self._buff_text.draw()

    def on_hide_view(self) -> None:
        save_game(self.state)
