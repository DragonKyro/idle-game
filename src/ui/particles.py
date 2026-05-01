"""Small burst of glittering shards emitted on each click."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import arcade
from arcade.types import Color


@dataclass
class _Particle:
    x: float
    y: float
    vx: float
    vy: float
    rotation: float
    spin: float
    color: tuple[int, int, int]
    age: float = 0.0
    lifetime: float = 0.9
    scale: float = 1.0

    @property
    def alive(self) -> bool:
        return self.age < self.lifetime


_DEFAULT_COLOR = (255, 255, 255)


class ParticleBurst:
    """A pool of small glittering shard sprites."""

    def __init__(self, texture: arcade.Texture) -> None:
        self._texture = texture
        self._particles: list[_Particle] = []

    def emit(
        self,
        x: float,
        y: float,
        count: int,
        color: tuple[int, int, int] = _DEFAULT_COLOR,
    ) -> None:
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 220)
            self._particles.append(_Particle(
                x=x,
                y=y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed + 80,  # slight upward bias
                rotation=random.uniform(0, 360),
                spin=random.uniform(-360, 360),
                color=color,
                lifetime=random.uniform(0.6, 1.1),
                scale=random.uniform(0.6, 1.2),
            ))

    def update(self, delta: float) -> None:
        gravity = -360.0
        for p in self._particles:
            p.age += delta
            p.vy += gravity * delta
            p.x += p.vx * delta
            p.y += p.vy * delta
            p.rotation += p.spin * delta
        self._particles = [p for p in self._particles if p.alive]

    def draw(self) -> None:
        # We draw each as a textured rectangle so we can fade, tint, and
        # rotate them individually without keeping a full SpriteList in sync.
        for p in self._particles:
            t = p.age / p.lifetime
            alpha = int(255 * (1.0 - t * t))  # ease out
            size = 16 * p.scale * (1.0 - 0.3 * t)
            rect = arcade.LBWH(p.x - size / 2, p.y - size / 2, size, size)
            r, g, b = p.color
            # arcade.draw_texture_rect wants a Color() — plain tuples blow up.
            arcade.draw_texture_rect(
                self._texture,
                rect,
                color=Color(r, g, b, 255),
                alpha=max(0, min(255, alpha)),
                angle=p.rotation,
            )
