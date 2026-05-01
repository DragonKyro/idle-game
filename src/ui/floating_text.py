"""Short-lived '+X' text that rises and fades from the click point."""

from __future__ import annotations

import arcade

from src.constants import COLOR_TEXT_GOLD, FLOATING_TEXT_LIFETIME


class FloatingText:
    """One floating '+N' label. Owns a cached ``arcade.Text`` so the glyph
    layout only runs once (at spawn), and each subsequent frame only
    updates position and alpha — both cheap on a pre-laid-out Text.
    """

    __slots__ = ("_label", "age", "velocity_y")

    def __init__(self, text: str, x: float, y: float) -> None:
        self._label = arcade.Text(
            text, x, y, COLOR_TEXT_GOLD,
            font_size=22, anchor_x="center", anchor_y="center", bold=True,
        )
        self.age = 0.0
        self.velocity_y = 60.0  # pixels per second

    def update(self, delta: float) -> None:
        self.age += delta
        self._label.y += self.velocity_y * delta
        # Decelerate so the text settles as it fades.
        self.velocity_y *= max(0.0, 1.0 - delta * 1.2)

    @property
    def alive(self) -> bool:
        return self.age < FLOATING_TEXT_LIFETIME

    def draw(self) -> None:
        t = self.age / FLOATING_TEXT_LIFETIME
        alpha = max(0, min(255, int(255 * (1.0 - t))))
        # Setting .color is a cheap attribute write — no glyph layout.
        r, g, b = COLOR_TEXT_GOLD
        self._label.color = (r, g, b, alpha)
        self._label.draw()


class FloatingTextLayer:
    """Owns and renders all active floating texts."""

    def __init__(self) -> None:
        self._texts: list[FloatingText] = []

    def spawn(self, text: str, x: float, y: float) -> None:
        self._texts.append(FloatingText(text, x, y))

    def update(self, delta: float) -> None:
        for t in self._texts:
            t.update(delta)
        self._texts = [t for t in self._texts if t.alive]

    def draw(self) -> None:
        for t in self._texts:
            t.draw()
