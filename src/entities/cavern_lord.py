"""Mini-boss entity — the Cavern Lord.

Appears at thresholds of total earnings. Players click it to damage its
HP bar; when defeated it awards a large shard bounty plus 1 essence
fragment. Stays until defeated or until the player descends.

Session-scoped — not persisted. The next boss is triggered by
``GameView`` based on ``state.total_earned`` crossing progressively
larger thresholds.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import arcade
from arcade.types import Color

from src.constants import PLAY_AREA_WIDTH, SCREEN_HEIGHT


# HP thresholds roughly follow ``10^(2 * bosses_defeated + 6)`` so the
# first boss has 1M HP, next 100M, etc. Reward scales accordingly.
def boss_hp_for_index(index: int) -> float:
    return 1_000_000 * (100 ** index)


def boss_reward_for_index(index: int) -> float:
    return boss_hp_for_index(index) * 0.5


@dataclass
class CavernLord:
    index: int              # 0 for first boss, 1 for second, ...
    max_hp: float
    hp: float
    x: float
    y: float
    age: float = 0.0
    spawn_scale: float = 0.0  # 0 -> 1 as it drops in
    hit_flash: float = 0.0    # decays 1 -> 0 after each click
    defeated: bool = False
    last_hit_positions: list[tuple[float, float, float]] = field(default_factory=list)

    @property
    def alive(self) -> bool:
        return not self.defeated

    def contains(self, x: float, y: float) -> bool:
        dx = x - self.x
        dy = y - self.y
        size = self._size()
        return dx * dx + dy * dy <= (size * 0.55) ** 2

    def hp_fraction(self) -> float:
        return max(0.0, self.hp / self.max_hp)

    def _size(self) -> float:
        return 160 * (0.6 + 0.4 * self.spawn_scale)

    def update(self, delta: float) -> None:
        self.age += delta
        # Spring in over ~0.4s.
        self.spawn_scale = min(1.0, self.spawn_scale + delta / 0.4)
        self.hit_flash = max(0.0, self.hit_flash - delta * 3)
        # Fade floating damage numbers.
        self.last_hit_positions = [
            (x, y + delta * 60, age + delta)
            for x, y, age in self.last_hit_positions
            if age < 0.6
        ]

    def take_hit(self, damage: float, *, click_x: float, click_y: float) -> bool:
        """Apply damage. Returns True iff this hit was the killing blow."""
        if self.defeated:
            return False
        self.hp -= damage
        self.hit_flash = 1.0
        self.last_hit_positions.append((click_x, click_y, 0.0))
        if self.hp <= 0:
            self.hp = 0
            self.defeated = True
            return True
        return False

    # -- rendering ------------------------------------------------------

    def draw(self) -> None:
        size = self._size()
        cx, cy = self.x, self.y

        # Shadow ring underneath.
        arcade.draw_circle_filled(cx, cy - size * 0.4, size * 0.35,
                                  (0, 0, 0, 120))

        # Body: a brooding obsidian eye with glowing iris.
        body_color = (40, 20, 60)
        iris_color = (255, 120, 90)
        flash_mix = int(self.hit_flash * 200)
        body = (
            min(255, body_color[0] + flash_mix),
            min(255, body_color[1] + flash_mix),
            min(255, body_color[2] + flash_mix),
        )

        arcade.draw_circle_filled(cx, cy, size * 0.55, body)
        arcade.draw_circle_outline(cx, cy, size * 0.55,
                                   (120, 80, 180), border_width=3)

        # Iris + pupil, rocking with age to look "alive".
        iris_dx = math.cos(self.age * 0.6) * size * 0.1
        iris_dy = math.sin(self.age * 0.5) * size * 0.08
        arcade.draw_circle_filled(cx + iris_dx, cy + iris_dy, size * 0.25, iris_color)
        arcade.draw_circle_filled(cx + iris_dx, cy + iris_dy, size * 0.1,
                                  (20, 10, 30))

        # Jagged crown of spikes.
        n_spikes = 8
        for i in range(n_spikes):
            ang = i / n_spikes * math.tau + self.age * 0.2
            r_inner = size * 0.55
            r_outer = size * 0.75
            pts = [
                (cx + r_inner * math.cos(ang - 0.08),
                 cy + r_inner * math.sin(ang - 0.08)),
                (cx + r_outer * math.cos(ang),
                 cy + r_outer * math.sin(ang)),
                (cx + r_inner * math.cos(ang + 0.08),
                 cy + r_inner * math.sin(ang + 0.08)),
            ]
            arcade.draw_polygon_filled(pts, (100, 60, 140))

        # HP bar.
        bar_w, bar_h = 220, 12
        bar_left = cx - bar_w / 2
        bar_bottom = cy - size * 0.75 - 20
        arcade.draw_rect_filled(
            arcade.LBWH(bar_left - 2, bar_bottom - 2, bar_w + 4, bar_h + 4),
            (0, 0, 0, 200),
        )
        arcade.draw_rect_filled(
            arcade.LBWH(bar_left, bar_bottom, bar_w, bar_h),
            (40, 20, 40),
        )
        frac = self.hp_fraction()
        arcade.draw_rect_filled(
            arcade.LBWH(bar_left, bar_bottom, bar_w * frac, bar_h),
            (230, 80, 100),
        )
        arcade.draw_rect_outline(
            arcade.LBWH(bar_left, bar_bottom, bar_w, bar_h),
            (200, 160, 200), border_width=1,
        )


def spawn_boss(index: int) -> CavernLord:
    # Drop it in slightly off-center so it reads as its own entity,
    # not an extension of the crystal.
    x = PLAY_AREA_WIDTH / 2 + random.uniform(-60, 60)
    y = (SCREEN_HEIGHT - 140) / 2 + 20
    hp = boss_hp_for_index(index)
    return CavernLord(index=index, max_hp=hp, hp=hp, x=x, y=y)
