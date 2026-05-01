"""Talent tree — rendered as a visual tree with per-branch columns.

Each talent is a circular node with an icon inside and level pips below.
Nodes in the same branch are connected by a line so the column reads
as an actual tree rather than a flat list. Descriptions are moved into
a hover tooltip so the text never runs out of the panel.
"""

from __future__ import annotations

import math

import arcade
from arcade.types import Color

from src.constants import (
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_PANEL_HIGHLIGHT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_GOLD,
    COLOR_TEXT_OK,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_WARN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.game_state import GameState
from src.talents import TALENT_BRANCHES, TALENTS, TalentDef
from src.ui.button import Button


# Per-branch palette — also used for the node fill and connector line.
_BRANCH_COLORS: dict[str, tuple[int, int, int]] = {
    "click":   (255, 214, 110),
    "idle":    (130, 230, 170),
    "offline": (120, 220, 255),
    "special": (180, 150, 255),
}
_BRANCH_DESCRIPTIONS: dict[str, str] = {
    "click":   "Make each tap count for more.",
    "idle":    "Boost your passive shard production.",
    "offline": "Reward you for coming back after a break.",
    "special": "Event rewards, starting bonuses, and essence gains.",
}

_PANEL_W = 980
_PANEL_H = 660
_NODE_RADIUS = 30
_NODE_SPACING = 150   # vertical distance between node centers in a branch
_BRANCH_HEADER_H = 70


class TalentPanel:
    def __init__(self) -> None:
        self._visible = False
        self._mouse_x = 0.0
        self._mouse_y = 0.0

        left = (SCREEN_WIDTH - _PANEL_W) / 2
        bottom = (SCREEN_HEIGHT - _PANEL_H) / 2
        self._left = left
        self._bottom = bottom

        self._close = Button(
            left=left + _PANEL_W - 120, bottom=bottom + 20,
            width=100, height=40,
        )

        self._title = arcade.Text(
            "Talent Tree", left + _PANEL_W / 2, bottom + _PANEL_H - 28,
            COLOR_TEXT_PRIMARY, font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._essence_label = arcade.Text(
            "", left + _PANEL_W / 2, bottom + _PANEL_H - 54,
            COLOR_TEXT_GOLD, font_size=14,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._hint = arcade.Text(
            "Hover a node to see what it does. Click to invest 1 level.",
            left + _PANEL_W / 2, bottom + 76,
            COLOR_TEXT_DIM, font_size=11,
            anchor_x="center", anchor_y="center", italic=True,
        )
        self._close_label = arcade.Text(
            "Close", self._close.center_x, self._close.center_y,
            COLOR_TEXT_PRIMARY, font_size=14,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Per-branch header labels + per-talent name labels under each node.
        self._branch_titles = {
            branch: arcade.Text(
                branch.title(), 0, 0, _BRANCH_COLORS[branch],
                font_size=16, anchor_x="center", anchor_y="baseline", bold=True,
            )
            for branch in TALENT_BRANCHES
        }
        self._branch_blurbs = {
            branch: arcade.Text(
                _BRANCH_DESCRIPTIONS[branch], 0, 0, COLOR_TEXT_DIM,
                font_size=10, anchor_x="center", anchor_y="baseline", italic=True,
            )
            for branch in TALENT_BRANCHES
        }
        self._node_names: dict[str, arcade.Text] = {
            t.key: arcade.Text(
                t.name, 0, 0, COLOR_TEXT_PRIMARY,
                font_size=12, anchor_x="center", anchor_y="baseline", bold=True,
            )
            for t in TALENTS
        }

        # Single tooltip whose text/position is updated when a node is hovered.
        self._tooltip_name = arcade.Text(
            "", 0, 0, COLOR_TEXT_PRIMARY,
            font_size=13, anchor_y="baseline", bold=True,
        )
        self._tooltip_desc = arcade.Text(
            "", 0, 0, COLOR_TEXT_SECONDARY,
            font_size=11, anchor_y="baseline",
            width=240, multiline=True,
        )
        self._tooltip_meta = arcade.Text(
            "", 0, 0, COLOR_TEXT_GOLD,
            font_size=11, anchor_y="baseline", bold=True,
        )

        # Recorded each draw for click routing / hover tooltip.
        self._node_hits: list[tuple[TalentDef, float, float]] = []

    @property
    def visible(self) -> bool:
        return self._visible

    def open(self) -> None:
        self._visible = True

    def on_mouse_motion(self, x: float, y: float) -> None:
        self._mouse_x = x
        self._mouse_y = y

    def handle_click(self, x: float, y: float, state: GameState) -> str | None:
        if not self._visible:
            return None
        if self._close.contains(x, y):
            self._visible = False
            return None
        for talent, nx, ny in self._node_hits:
            dx = x - nx
            dy = y - ny
            if dx * dx + dy * dy <= _NODE_RADIUS * _NODE_RADIUS:
                return talent.key
        return None

    def draw(self, state: GameState) -> None:
        if not self._visible:
            return
        self._node_hits = []

        # Dim the world and draw the modal chrome.
        overlay = arcade.LBWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.draw_rect_filled(overlay, (0, 0, 0, 180))
        panel = arcade.LBWH(self._left, self._bottom, _PANEL_W, _PANEL_H)
        arcade.draw_rect_filled(panel, COLOR_PANEL_BG)
        arcade.draw_rect_outline(panel, COLOR_PANEL_BORDER, border_width=3)
        header = arcade.LBWH(
            self._left, self._bottom + _PANEL_H - 70, _PANEL_W, 70
        )
        arcade.draw_rect_filled(header, COLOR_PANEL_HIGHLIGHT)
        self._title.draw()

        self._essence_label.text = (
            f"Essence available: {state.essence}   "
            f"(lifetime earned: {state.total_essence_earned})"
        )
        self._essence_label.draw()

        # Branch columns.
        col_w = (_PANEL_W - 80) / len(TALENT_BRANCHES)
        trunk_top = self._bottom + _PANEL_H - _BRANCH_HEADER_H - 60
        for i, branch in enumerate(TALENT_BRANCHES):
            col_center = self._left + 40 + col_w * i + col_w / 2
            self._draw_branch(state, branch, col_center, trunk_top)

        self._hint.draw()

        # Hover tooltip on top of everything except the close button.
        hovered = self._node_at(self._mouse_x, self._mouse_y)
        if hovered is not None:
            self._draw_tooltip(state, hovered)

        hovered_close = self._close.contains(self._mouse_x, self._mouse_y)
        self._close.draw_background(hovered=hovered_close, affordable=False)
        self._close_label.draw()

    # ------------------------------------------------------------------
    # Branch drawing.
    # ------------------------------------------------------------------

    def _draw_branch(self, state, branch, col_center, trunk_top) -> None:
        color = _BRANCH_COLORS[branch]
        branch_talents = [t for t in TALENTS if t.branch == branch]

        title = self._branch_titles[branch]
        title.x = col_center
        title.y = trunk_top + 22
        title.draw()
        blurb = self._branch_blurbs[branch]
        blurb.x = col_center
        blurb.y = trunk_top + 6
        blurb.draw()

        # Trunk line running through every node in this branch.
        if branch_talents:
            top_y = trunk_top - _NODE_SPACING / 2 + _NODE_RADIUS
            bot_y = trunk_top - _NODE_SPACING * (len(branch_talents) - 0.5)
            arcade.draw_line(
                col_center, top_y, col_center, bot_y,
                Color(color[0], color[1], color[2], 140), 3,
            )

        for j, talent in enumerate(branch_talents):
            node_y = trunk_top - _NODE_SPACING * (j + 0.5)
            self._draw_node(state, talent, col_center, node_y)

    def _draw_node(self, state, talent: TalentDef, x: float, y: float) -> None:
        level = state.talent_level(talent.key)
        maxed = state.talent_is_maxed(talent.key)
        affordable = state.can_afford_talent(talent.key)
        color = _BRANCH_COLORS[talent.branch]

        hover = (
            (self._mouse_x - x) ** 2 + (self._mouse_y - y) ** 2
            <= _NODE_RADIUS * _NODE_RADIUS
        )

        # Outer glow when affordable (not maxed).
        if affordable:
            for r, alpha in ((_NODE_RADIUS + 8, 30),
                             (_NODE_RADIUS + 4, 60)):
                arcade.draw_circle_filled(x, y, r, Color(*color, alpha))

        # Base disc — dimmed if still locked (level 0 + can't afford first).
        locked = level == 0 and not affordable
        if locked:
            fill = (46, 38, 72)
            border = (90, 76, 130)
        elif maxed:
            fill = (int(color[0] * 0.6), int(color[1] * 0.6), int(color[2] * 0.6))
            border = color
        else:
            fill = (int(color[0] * 0.35), int(color[1] * 0.35), int(color[2] * 0.35))
            border = color

        arcade.draw_circle_filled(x, y, _NODE_RADIUS, fill)
        border_width = 3 if hover or maxed else 2
        arcade.draw_circle_outline(x, y, _NODE_RADIUS, border, border_width=border_width)

        # Icon inside the disc.
        _draw_talent_icon(talent.icon, x, y, _NODE_RADIUS * 0.9,
                          color if not locked else (120, 110, 150))

        # Small MAX badge at top-right of the node.
        if maxed:
            arcade.draw_circle_filled(
                x + _NODE_RADIUS - 4, y + _NODE_RADIUS - 4,
                8, COLOR_TEXT_GOLD,
            )

        # Name under the node.
        name = self._node_names[talent.key]
        name.x = x
        name.y = y - _NODE_RADIUS - 18
        name.color = COLOR_TEXT_DIM if locked else COLOR_TEXT_PRIMARY
        name.draw()

        # Level pips beneath the name.
        pip_y = y - _NODE_RADIUS - 32
        pip_spacing = 10
        total_w = pip_spacing * (talent.max_level - 1)
        for i in range(talent.max_level):
            px = x - total_w / 2 + i * pip_spacing
            filled = i < level
            arcade.draw_circle_filled(
                px, pip_y, 3,
                color if filled else (80, 70, 110),
            )

        self._node_hits.append((talent, x, y))

    # ------------------------------------------------------------------
    # Tooltip.
    # ------------------------------------------------------------------

    def _node_at(self, x: float, y: float) -> TalentDef | None:
        for talent, nx, ny in self._node_hits:
            if (x - nx) ** 2 + (y - ny) ** 2 <= _NODE_RADIUS * _NODE_RADIUS:
                return talent
        return None

    def _draw_tooltip(self, state: GameState, talent: TalentDef) -> None:
        level = state.talent_level(talent.key)
        maxed = state.talent_is_maxed(talent.key)
        affordable = state.can_afford_talent(talent.key)

        tip_w = 270
        tip_h = 108
        # Keep the tooltip inside the modal bounds.
        tip_x = min(self._mouse_x + 16, self._left + _PANEL_W - tip_w - 8)
        tip_y = max(self._mouse_y - tip_h - 16, self._bottom + 8)

        arcade.draw_rect_filled(
            arcade.LBWH(tip_x, tip_y, tip_w, tip_h),
            (18, 14, 32, 235),
        )
        arcade.draw_rect_outline(
            arcade.LBWH(tip_x, tip_y, tip_w, tip_h),
            _BRANCH_COLORS[talent.branch], border_width=2,
        )

        self._tooltip_name.text = talent.name
        self._tooltip_name.x = tip_x + 12
        self._tooltip_name.y = tip_y + tip_h - 22
        self._tooltip_name.color = COLOR_TEXT_PRIMARY
        self._tooltip_name.draw()

        self._tooltip_desc.text = talent.description
        self._tooltip_desc.x = tip_x + 12
        self._tooltip_desc.y = tip_y + tip_h - 40
        self._tooltip_desc.draw()

        if maxed:
            meta_text = f"Lv {level}/{talent.max_level} — MAXED"
            color = COLOR_TEXT_GOLD
        else:
            cost = state.next_talent_cost(talent.key) or 0
            meta_text = f"Lv {level}/{talent.max_level} — next level: {cost} essence"
            color = COLOR_TEXT_OK if affordable else COLOR_TEXT_WARN
        self._tooltip_meta.text = meta_text
        self._tooltip_meta.x = tip_x + 12
        self._tooltip_meta.y = tip_y + 12
        self._tooltip_meta.color = color
        self._tooltip_meta.draw()


# ----------------------------------------------------------------------
# Procedural icons — drawn with arcade primitives so they scale cleanly
# and stay in sync with the branch color.
# ----------------------------------------------------------------------

def _draw_talent_icon(
    kind: str,
    cx: float,
    cy: float,
    size: float,
    color: tuple[int, int, int],
) -> None:
    """Draw a small iconic shape inside a talent node."""
    r = size / 2
    col = Color(*color)

    if kind == "fist":
        # Stylized upward punch: rounded square + knuckle bumps.
        w = size * 0.55
        h = size * 0.45
        arcade.draw_rect_filled(
            arcade.LBWH(cx - w / 2, cy - h / 2, w, h), col,
        )
        for i in range(3):
            x = cx - w / 2 + (i + 1) * w / 4
            arcade.draw_circle_filled(x, cy + h / 2, 3, col)
        # Arm.
        arcade.draw_line(cx, cy - h / 2, cx, cy - h / 2 - r * 0.6, col, 3)

    elif kind == "crosshair":
        arcade.draw_circle_outline(cx, cy, r * 0.7, col, border_width=2)
        arcade.draw_line(cx - r * 0.9, cy, cx + r * 0.9, cy, col, 2)
        arcade.draw_line(cx, cy - r * 0.9, cx, cy + r * 0.9, col, 2)
        arcade.draw_circle_filled(cx, cy, 2, col)

    elif kind == "vein":
        # Downward-pointing triangle with a wavy streak (ore vein).
        pts = [(cx, cy - r * 0.8), (cx + r * 0.6, cy + r * 0.4),
               (cx - r * 0.6, cy + r * 0.4)]
        arcade.draw_polygon_filled(pts, col)
        arcade.draw_line(
            cx - r * 0.2, cy + r * 0.2, cx + r * 0.2, cy - r * 0.3, (255, 255, 255), 2,
        )

    elif kind == "wave":
        # Three stacked sine-like arcs.
        for i, y_off in enumerate((-r * 0.5, 0, r * 0.5)):
            y = cy + y_off
            arcade.draw_arc_outline(
                cx - r * 0.1, y, r * 1.2, r * 0.4,
                col, start_angle=0, end_angle=180, border_width=2,
            )

    elif kind == "zzz":
        # Three nested Z shapes, scaling down — classic "sleep" motif.
        for i, (dx, dy, scale) in enumerate(
            ((-r * 0.4, -r * 0.5, 0.7),
             (0, 0, 0.9),
             (r * 0.3, r * 0.4, 0.7)),
        ):
            s = r * 0.5 * scale
            arcade.draw_line(cx + dx - s, cy + dy + s, cx + dx + s, cy + dy + s, col, 2)
            arcade.draw_line(cx + dx + s, cy + dy + s, cx + dx - s, cy + dy - s, col, 2)
            arcade.draw_line(cx + dx - s, cy + dy - s, cx + dx + s, cy + dy - s, col, 2)

    elif kind == "clock":
        arcade.draw_circle_outline(cx, cy, r * 0.75, col, border_width=2)
        # Hour + minute hand.
        arcade.draw_line(cx, cy, cx, cy + r * 0.55, col, 2)
        arcade.draw_line(cx, cy, cx + r * 0.4, cy + r * 0.1, col, 2)
        arcade.draw_circle_filled(cx, cy, 2, col)

    elif kind == "coins":
        # Three stacked coin discs.
        for i, dy in enumerate((-r * 0.5, -r * 0.15, r * 0.2)):
            arcade.draw_ellipse_filled(cx, cy + dy, r * 1.0, r * 0.3, col)
            arcade.draw_ellipse_outline(
                cx, cy + dy, r * 1.0, r * 0.3,
                (0, 0, 0, 220), border_width=1,
            )

    elif kind == "clover":
        # Four circular leaves around a center.
        for dx, dy in ((0, r * 0.35), (0, -r * 0.35),
                       (r * 0.35, 0), (-r * 0.35, 0)):
            arcade.draw_circle_filled(cx + dx, cy + dy, r * 0.32, col)
        arcade.draw_circle_filled(cx, cy, r * 0.18, (40, 30, 60))

    elif kind == "magnet":
        # Horseshoe: two vertical bars joined at the top by an arc.
        bar_w = r * 0.3
        bar_h = r * 0.9
        arcade.draw_rect_filled(
            arcade.LBWH(cx - r * 0.65, cy - bar_h / 2, bar_w, bar_h), col,
        )
        arcade.draw_rect_filled(
            arcade.LBWH(cx + r * 0.35, cy - bar_h / 2, bar_w, bar_h), col,
        )
        arcade.draw_arc_filled(
            cx, cy + bar_h / 2 - r * 0.15, r * 1.3, r * 0.6, col,
            start_angle=0, end_angle=180,
        )
        # Poles: red/white tips.
        arcade.draw_rect_filled(
            arcade.LBWH(cx - r * 0.65, cy - bar_h / 2, bar_w, 4),
            (255, 120, 120),
        )
        arcade.draw_rect_filled(
            arcade.LBWH(cx + r * 0.35, cy - bar_h / 2, bar_w, 4),
            (240, 240, 255),
        )

    else:
        # Fallback — a plain dot, still readable.
        arcade.draw_circle_filled(cx, cy, r * 0.4, col)
