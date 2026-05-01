"""Short-lived '+X' text that rises and fades from the click point."""

from __future__ import annotations

from dataclasses import dataclass

import arcade

from src.constants import COLOR_TEXT_GOLD, FLOATING_TEXT_LIFETIME


@dataclass
class FloatingText:
    text: str
    x: float
    y: float
    age: float = 0.0
    velocity_y: float = 60.0  # pixels per second

    def update(self, delta: float) -> None:
        self.age += delta
        self.y += self.velocity_y * delta
        # Decelerate so the text settles as it fades.
        self.velocity_y *= max(0.0, 1.0 - delta * 1.2)

    @property
    def alive(self) -> bool:
        return self.age < FLOATING_TEXT_LIFETIME

    def draw(self) -> None:
        t = self.age / FLOATING_TEXT_LIFETIME
        alpha = int(255 * (1.0 - t))
        color = (*COLOR_TEXT_GOLD, max(0, min(255, alpha)))
        # Font size eases up a touch early on for a little pop.
        scale = 1.0 + 0.3 * min(1.0, self.age * 4.0)
        arcade.draw_text(
            self.text,
            self.x,
            self.y,
            color,
            font_size=20 * scale,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )


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
