"""Settings modal — volume sliders, toggles, save export/import, reset."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import arcade

from src.constants import (
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_PANEL_HIGHLIGHT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_GOLD,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_WARN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.game_state import GameState, default_settings
from src.ui.button import Button


_PANEL_W = 620
_PANEL_H = 560


class _Slider:
    """Horizontal slider with a draggable knob."""

    def __init__(self, left: float, bottom: float, width: float) -> None:
        self.left = left
        self.bottom = bottom
        self.width = width
        self.height = 20
        self._dragging = False
        self.value: float = 0.5

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def top(self) -> float:
        return self.bottom + self.height

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.bottom <= y <= self.top

    def begin_drag(self, x: float, y: float) -> bool:
        if self.contains(x, y):
            self._dragging = True
            self._set_from_x(x)
            return True
        return False

    def update_drag(self, x: float) -> None:
        if self._dragging:
            self._set_from_x(x)

    def end_drag(self) -> None:
        self._dragging = False

    def _set_from_x(self, x: float) -> None:
        self.value = max(0.0, min(1.0, (x - self.left) / self.width))

    def draw(self) -> None:
        track = arcade.LBWH(self.left, self.bottom + 8, self.width, 4)
        arcade.draw_rect_filled(track, COLOR_TEXT_DIM)
        fill = arcade.LBWH(self.left, self.bottom + 8, self.width * self.value, 4)
        arcade.draw_rect_filled(fill, COLOR_TEXT_GOLD)
        knob_x = self.left + self.width * self.value
        arcade.draw_circle_filled(knob_x, self.bottom + 10, 8, COLOR_TEXT_PRIMARY)
        arcade.draw_circle_outline(
            knob_x, self.bottom + 10, 8, COLOR_PANEL_BORDER, border_width=2,
        )


class SettingsModal:
    """Visible while open. Calls registered callbacks for export/import/
    reset actions so GameView can handle the heavy lifting (file IO,
    state reset, etc.)."""

    def __init__(
        self,
        *,
        on_change: Callable[[dict], None],
        on_export: Callable[[], Path | None],
        on_import: Callable[[], Path | None],
        on_reset: Callable[[], None],
    ) -> None:
        self._on_change = on_change
        self._on_export = on_export
        self._on_import = on_import
        self._on_reset = on_reset

        self._visible = False
        self._mouse_x = 0.0
        self._mouse_y = 0.0

        left = (SCREEN_WIDTH - _PANEL_W) / 2
        bottom = (SCREEN_HEIGHT - _PANEL_H) / 2
        self._left = left
        self._bottom = bottom

        # Slider layout.
        slider_width = _PANEL_W - 280
        slider_x = left + 200
        self._sfx = _Slider(slider_x, bottom + _PANEL_H - 130, slider_width)
        self._music = _Slider(slider_x, bottom + _PANEL_H - 180, slider_width)

        # Toggle buttons.
        self._shake = Button(
            left=slider_x, bottom=bottom + _PANEL_H - 230, width=140, height=32,
        )
        self._reduced_motion = Button(
            left=slider_x, bottom=bottom + _PANEL_H - 280, width=140, height=32,
        )

        # Action buttons.
        self._export = Button(
            left=left + 30, bottom=bottom + 100, width=170, height=42,
        )
        self._import = Button(
            left=left + 220, bottom=bottom + 100, width=170, height=42,
        )
        self._reset = Button(
            left=left + 410, bottom=bottom + 100, width=170, height=42,
        )
        self._close = Button(
            left=left + _PANEL_W - 130, bottom=bottom + 30, width=100, height=40,
        )

        # Cached text labels.
        self._title = arcade.Text(
            "Settings", left + _PANEL_W / 2, bottom + _PANEL_H - 28,
            COLOR_TEXT_PRIMARY, font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._sfx_label = arcade.Text(
            "SFX Volume", left + 30, self._sfx.bottom + 10,
            COLOR_TEXT_SECONDARY, font_size=13, anchor_y="center",
        )
        self._music_label = arcade.Text(
            "Music Volume", left + 30, self._music.bottom + 10,
            COLOR_TEXT_SECONDARY, font_size=13, anchor_y="center",
        )
        self._shake_label = arcade.Text(
            "Screen Shake", left + 30, self._shake.center_y,
            COLOR_TEXT_SECONDARY, font_size=13, anchor_y="center",
        )
        self._reduced_label = arcade.Text(
            "Reduced Motion", left + 30, self._reduced_motion.center_y,
            COLOR_TEXT_SECONDARY, font_size=13, anchor_y="center",
        )
        # Dynamic value labels next to sliders.
        self._sfx_value = arcade.Text(
            "", self._sfx.right + 16, self._sfx.bottom + 10,
            COLOR_TEXT_GOLD, font_size=13, anchor_y="center", bold=True,
        )
        self._music_value = arcade.Text(
            "", self._music.right + 16, self._music.bottom + 10,
            COLOR_TEXT_GOLD, font_size=13, anchor_y="center", bold=True,
        )
        self._shake_value = arcade.Text(
            "", self._shake.center_x, self._shake.center_y,
            COLOR_TEXT_PRIMARY, font_size=13,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._reduced_value = arcade.Text(
            "", self._reduced_motion.center_x, self._reduced_motion.center_y,
            COLOR_TEXT_PRIMARY, font_size=13,
            anchor_x="center", anchor_y="center", bold=True,
        )

        self._export_label = arcade.Text(
            "Export Save", self._export.center_x, self._export.center_y,
            COLOR_TEXT_PRIMARY, font_size=13,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._import_label = arcade.Text(
            "Import Save", self._import.center_x, self._import.center_y,
            COLOR_TEXT_PRIMARY, font_size=13,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._reset_label = arcade.Text(
            "Reset Game", self._reset.center_x, self._reset.center_y,
            COLOR_TEXT_WARN, font_size=13,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._close_label = arcade.Text(
            "Close", self._close.center_x, self._close.center_y,
            COLOR_TEXT_PRIMARY, font_size=13,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Status line (last action taken).
        self._status = arcade.Text(
            "", left + _PANEL_W / 2, bottom + 68,
            COLOR_TEXT_DIM, font_size=11,
            anchor_x="center", anchor_y="center", italic=True,
        )

        # Second-press reset confirmation.
        self._reset_armed: bool = False

    @property
    def visible(self) -> bool:
        return self._visible

    def open(self, state: GameState) -> None:
        self._visible = True
        self._sfx.value = state.settings.get("sfx_volume", 0.6)
        self._music.value = state.settings.get("music_volume", 0.4)
        self._reset_armed = False
        self._status.text = ""

    def on_mouse_motion(self, x: float, y: float) -> None:
        self._mouse_x = x
        self._mouse_y = y
        self._sfx.update_drag(x)
        self._music.update_drag(x)

    def on_mouse_release(self, x: float, y: float) -> None:
        self._sfx.end_drag()
        self._music.end_drag()
        self._push_settings()

    def handle_click(self, x: float, y: float, state: GameState) -> bool:
        if not self._visible:
            return False
        # Sliders take priority (they consume the press as drag start).
        if self._sfx.begin_drag(x, y) or self._music.begin_drag(x, y):
            self._push_settings()
            return True
        if self._shake.contains(x, y):
            state.settings["screen_shake"] = not state.settings.get("screen_shake", True)
            self._push_settings()
            return True
        if self._reduced_motion.contains(x, y):
            state.settings["reduced_motion"] = not state.settings.get("reduced_motion", False)
            self._push_settings()
            return True
        if self._export.contains(x, y):
            path = self._on_export()
            self._status.text = f"Exported to {path}" if path else "Export cancelled"
            return True
        if self._import.contains(x, y):
            path = self._on_import()
            self._status.text = f"Imported {path}" if path else "Import cancelled"
            return True
        if self._reset.contains(x, y):
            if self._reset_armed:
                self._on_reset()
                self._visible = False
                self._reset_armed = False
            else:
                self._reset_armed = True
                self._status.text = "Click 'Reset Game' again to confirm — this can't be undone."
            return True
        if self._close.contains(x, y):
            self._visible = False
            return True
        # Clicking anywhere else inside the modal still eats the click to
        # avoid leaking into the play area.
        if (self._left <= x <= self._left + _PANEL_W and
                self._bottom <= y <= self._bottom + _PANEL_H):
            return True
        return False

    def _push_settings(self) -> None:
        self._on_change({
            "sfx_volume": self._sfx.value,
            "music_volume": self._music.value,
        })

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

        # Sliders.
        self._sfx.draw()
        self._music.draw()
        self._sfx_label.draw()
        self._music_label.draw()
        self._sfx_value.text = f"{int(self._sfx.value * 100)}%"
        self._music_value.text = f"{int(self._music.value * 100)}%"
        self._sfx_value.draw()
        self._music_value.draw()

        # Toggles.
        shake_on = state.settings.get("screen_shake", True)
        self._shake.draw_background(
            hovered=self._shake.contains(self._mouse_x, self._mouse_y),
            affordable=shake_on,
        )
        self._shake_value.text = "ON" if shake_on else "OFF"
        self._shake_label.draw()
        self._shake_value.draw()

        rm_on = state.settings.get("reduced_motion", False)
        self._reduced_motion.draw_background(
            hovered=self._reduced_motion.contains(self._mouse_x, self._mouse_y),
            affordable=rm_on,
        )
        self._reduced_value.text = "ON" if rm_on else "OFF"
        self._reduced_label.draw()
        self._reduced_value.draw()

        # Actions.
        for btn, label, warn in (
            (self._export, self._export_label, False),
            (self._import, self._import_label, False),
            (self._reset,  self._reset_label,  True),
        ):
            hovered = btn.contains(self._mouse_x, self._mouse_y)
            btn.draw_background(hovered=hovered, affordable=(warn and self._reset_armed))
            label.draw()

        self._close.draw_background(
            hovered=self._close.contains(self._mouse_x, self._mouse_y),
            affordable=False,
        )
        self._close_label.draw()

        if self._status.text:
            self._status.draw()

    @staticmethod
    def default_settings() -> dict:
        return default_settings()
