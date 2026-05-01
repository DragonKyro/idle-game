"""Procedural sprite generation.

We render tiny pixel-art style sprites with Pillow at startup and wrap them
in arcade Textures. This keeps the repo free of binary assets while still
giving each tier its own distinct look.

Generated sprites are cached on disk under ``assets/sprites/`` so runs after
the first don't pay the generation cost, and so curious users can peek at
the art.
"""

from __future__ import annotations

import random
from pathlib import Path

import arcade
from PIL import Image, ImageDraw, ImageFilter

from src.generators import GeneratorDef

# Repo-root/assets/sprites. Resolved from this file's location so the path
# works regardless of the current working directory.
_SPRITE_DIR = Path(__file__).resolve().parent.parent / "assets" / "sprites"

# Uniform logical sprite size. Upscaled 4x for chunky pixel-art feel.
_BASE_SIZE = 32
_SCALE = 4
_OUT_SIZE = _BASE_SIZE * _SCALE


def _mix(color: tuple[int, int, int], other: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(color[0] * (1 - t) + other[0] * t),
        int(color[1] * (1 - t) + other[1] * t),
        int(color[2] * (1 - t) + other[2] * t),
    )


def _shade(color: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    """Lighten (t>0) or darken (t<0) a color by factor `t` in [-1, 1]."""
    if t >= 0:
        return _mix(color, (255, 255, 255), t)
    return _mix(color, (0, 0, 0), -t)


def _new_canvas() -> Image.Image:
    return Image.new("RGBA", (_BASE_SIZE, _BASE_SIZE), (0, 0, 0, 0))


def _finalize(img: Image.Image) -> Image.Image:
    # Nearest-neighbor upscale preserves the pixel-art crispness.
    return img.resize((_OUT_SIZE, _OUT_SIZE), Image.NEAREST)


# ----------------------------------------------------------------------
# Per-shape renderers. Each paints a 32x32 RGBA image centered at (16,16).
# ----------------------------------------------------------------------

def _draw_pick(accent: tuple[int, int, int]) -> Image.Image:
    img = _new_canvas()
    d = ImageDraw.Draw(img)
    # Wooden handle diagonal.
    handle = (120, 80, 40)
    for i, x in enumerate(range(6, 26)):
        y = 26 - i
        d.point((x, y), fill=handle)
        d.point((x - 1, y), fill=_shade(handle, -0.25))
    # Metal head.
    head = accent
    d.polygon([(22, 4), (28, 8), (24, 14), (18, 10)], fill=head)
    d.polygon([(18, 10), (24, 14), (20, 16), (14, 12)], fill=_shade(head, -0.3))
    # Highlight glint.
    d.point((25, 7), fill=_shade(head, 0.6))
    return _finalize(img)


def _draw_dwarf(accent: tuple[int, int, int]) -> Image.Image:
    img = _new_canvas()
    d = ImageDraw.Draw(img)
    skin = (240, 200, 160)
    beard = (230, 220, 210)
    tunic = accent
    boots = (60, 42, 30)
    # Boots.
    d.rectangle((10, 26, 14, 29), fill=boots)
    d.rectangle((17, 26, 21, 29), fill=boots)
    # Tunic body.
    d.rectangle((8, 16, 23, 26), fill=tunic)
    d.rectangle((8, 16, 23, 17), fill=_shade(tunic, 0.3))
    d.rectangle((8, 25, 23, 26), fill=_shade(tunic, -0.3))
    # Belt.
    d.rectangle((8, 22, 23, 23), fill=(90, 60, 30))
    # Head.
    d.rectangle((11, 7, 20, 16), fill=skin)
    # Helmet.
    d.rectangle((10, 5, 21, 9), fill=_shade(accent, -0.4))
    d.rectangle((10, 4, 21, 5), fill=_shade(accent, 0.2))
    # Beard.
    d.rectangle((11, 13, 20, 17), fill=beard)
    d.rectangle((12, 12, 19, 14), fill=beard)
    # Eyes.
    d.point((13, 11), fill=(20, 20, 20))
    d.point((18, 11), fill=(20, 20, 20))
    return _finalize(img)


def _draw_cart(accent: tuple[int, int, int]) -> Image.Image:
    img = _new_canvas()
    d = ImageDraw.Draw(img)
    body = accent
    rim = _shade(accent, -0.4)
    # Cart body (trapezoid).
    d.polygon([(6, 14), (26, 14), (24, 22), (8, 22)], fill=body)
    d.line([(6, 14), (26, 14)], fill=_shade(body, 0.3))
    d.line([(8, 22), (24, 22)], fill=rim)
    # Contents: glowing shards peek over the top.
    d.polygon([(10, 13), (12, 9), (14, 13)], fill=(120, 220, 255))
    d.polygon([(15, 14), (18, 8), (21, 14)], fill=(170, 235, 255))
    # Wheels.
    d.ellipse((7, 22, 13, 28), fill=(40, 30, 20))
    d.ellipse((19, 22, 25, 28), fill=(40, 30, 20))
    d.ellipse((9, 24, 11, 26), fill=(180, 180, 180))
    d.ellipse((21, 24, 23, 26), fill=(180, 180, 180))
    return _finalize(img)


def _draw_drill(accent: tuple[int, int, int]) -> Image.Image:
    img = _new_canvas()
    d = ImageDraw.Draw(img)
    chassis = accent
    # Drill bit pointing down-right.
    d.polygon([(6, 6), (18, 6), (18, 10), (6, 10)], fill=_shade(chassis, -0.3))
    d.polygon([(18, 5), (24, 8), (26, 12), (18, 11)], fill=chassis)
    # Teeth zigzag.
    for i in range(5):
        x = 19 + i
        d.line([(x, 11 + (i % 2)), (x, 14 + (i % 2))], fill=(200, 200, 220))
    # Tracks.
    d.rectangle((4, 20, 28, 26), fill=(50, 50, 60))
    d.rectangle((4, 20, 28, 21), fill=(90, 90, 110))
    for x in range(6, 28, 3):
        d.line([(x, 21), (x, 26)], fill=(30, 30, 40))
    # Cockpit window.
    d.rectangle((10, 12, 16, 18), fill=(120, 220, 255))
    d.rectangle((10, 12, 16, 13), fill=(200, 240, 255))
    return _finalize(img)


def _draw_golem(accent: tuple[int, int, int]) -> Image.Image:
    img = _new_canvas()
    d = ImageDraw.Draw(img)
    body = accent
    # Legs.
    d.rectangle((9, 22, 13, 29), fill=body)
    d.rectangle((18, 22, 22, 29), fill=body)
    # Torso.
    d.rectangle((6, 12, 25, 24), fill=body)
    d.rectangle((6, 12, 25, 13), fill=_shade(body, 0.3))
    d.rectangle((6, 23, 25, 24), fill=_shade(body, -0.3))
    # Head.
    d.rectangle((10, 5, 21, 13), fill=body)
    d.rectangle((10, 5, 21, 6), fill=_shade(body, 0.3))
    # Glowing runic eyes.
    d.rectangle((12, 8, 14, 10), fill=(120, 220, 255))
    d.rectangle((17, 8, 19, 10), fill=(120, 220, 255))
    # Chest rune.
    d.polygon([(15, 15), (18, 18), (15, 21), (12, 18)], fill=(120, 220, 255))
    # Arms.
    d.rectangle((3, 14, 6, 22), fill=body)
    d.rectangle((25, 14, 28, 22), fill=body)
    return _finalize(img)


def _draw_wizard(accent: tuple[int, int, int]) -> Image.Image:
    img = _new_canvas()
    d = ImageDraw.Draw(img)
    robe = accent
    skin = (240, 210, 170)
    beard = (250, 250, 255)
    # Robe (triangle).
    d.polygon([(15, 12), (5, 29), (26, 29)], fill=robe)
    d.polygon([(15, 12), (5, 29), (15, 29)], fill=_shade(robe, -0.2))
    # Belt.
    d.line([(8, 24), (23, 24)], fill=_shade(robe, -0.5))
    # Head.
    d.rectangle((12, 8, 19, 14), fill=skin)
    # Beard.
    d.polygon([(12, 12), (19, 12), (17, 18), (14, 18)], fill=beard)
    # Hat (cone).
    d.polygon([(10, 9), (15, 0), (20, 9)], fill=_shade(robe, -0.3))
    d.point((15, 0), fill=(255, 240, 120))  # star tip
    # Eyes.
    d.point((13, 11), fill=(20, 20, 20))
    d.point((17, 11), fill=(20, 20, 20))
    # Staff with glowing orb.
    d.line([(24, 8), (22, 28)], fill=(90, 60, 30))
    d.ellipse((22, 4, 28, 10), fill=(120, 220, 255))
    d.ellipse((24, 5, 26, 7), fill=(230, 250, 255))
    return _finalize(img)


def _draw_forge(accent: tuple[int, int, int]) -> Image.Image:
    img = _new_canvas()
    d = ImageDraw.Draw(img)
    stone = (90, 80, 100)
    # Anvil base.
    d.rectangle((6, 20, 25, 26), fill=stone)
    d.rectangle((6, 26, 25, 29), fill=_shade(stone, -0.3))
    d.rectangle((6, 20, 25, 21), fill=_shade(stone, 0.3))
    # Top of the anvil.
    d.rectangle((4, 18, 27, 21), fill=_shade(stone, 0.1))
    d.polygon([(27, 18), (30, 19), (30, 21), (27, 21)], fill=_shade(stone, 0.1))
    # Fire.
    d.polygon([(10, 14), (14, 4), (18, 10), (22, 6), (22, 18), (10, 18)], fill=accent)
    d.polygon([(12, 14), (15, 8), (18, 14), (20, 10), (20, 18), (12, 18)],
              fill=_shade(accent, 0.4))
    d.polygon([(14, 16), (16, 12), (18, 16)], fill=(255, 240, 180))
    return _finalize(img)


def _draw_dragon(accent: tuple[int, int, int]) -> Image.Image:
    img = _new_canvas()
    d = ImageDraw.Draw(img)
    scale = accent
    # Tail curling right-to-left.
    d.polygon([(26, 24), (22, 26), (18, 24), (22, 22)], fill=scale)
    # Body.
    d.ellipse((8, 16, 24, 28), fill=scale)
    d.ellipse((8, 16, 24, 20), fill=_shade(scale, 0.25))
    # Belly scales.
    d.ellipse((10, 20, 22, 27), fill=_shade(scale, 0.3))
    # Neck.
    d.polygon([(10, 16), (6, 8), (12, 10), (14, 18)], fill=scale)
    # Head.
    d.ellipse((3, 4, 13, 12), fill=scale)
    # Horns.
    d.polygon([(5, 4), (4, 0), (7, 3)], fill=_shade(scale, -0.4))
    d.polygon([(10, 4), (11, 0), (12, 3)], fill=_shade(scale, -0.4))
    # Eye.
    d.point((9, 8), fill=(20, 20, 20))
    d.point((10, 8), fill=(255, 80, 80))
    # Wing.
    d.polygon([(14, 14), (26, 6), (24, 18)], fill=_shade(scale, -0.25))
    d.polygon([(16, 14), (24, 10), (22, 17)], fill=_shade(scale, -0.1))
    return _finalize(img)


def _draw_titan(accent: tuple[int, int, int]) -> Image.Image:
    img = _new_canvas()
    d = ImageDraw.Draw(img)
    body = _shade(accent, -0.2)
    glow = accent
    # Massive legs.
    d.rectangle((9, 20, 14, 30), fill=body)
    d.rectangle((18, 20, 23, 30), fill=body)
    # Torso.
    d.rectangle((5, 10, 27, 22), fill=body)
    d.rectangle((5, 10, 27, 11), fill=_shade(body, 0.3))
    # Shoulders.
    d.rectangle((2, 11, 6, 18), fill=body)
    d.rectangle((26, 11, 30, 18), fill=body)
    # Head.
    d.rectangle((11, 2, 20, 11), fill=body)
    d.rectangle((11, 2, 20, 3), fill=_shade(body, 0.4))
    # Crown/horns.
    d.polygon([(11, 2), (13, 0), (14, 2)], fill=(255, 230, 120))
    d.polygon([(17, 2), (18, 0), (20, 2)], fill=(255, 230, 120))
    # Glowing cracks.
    d.line([(8, 14), (14, 18)], fill=glow)
    d.line([(18, 13), (24, 19)], fill=glow)
    d.line([(15, 5), (15, 9)], fill=glow)
    # Eyes.
    d.rectangle((13, 6, 14, 7), fill=glow)
    d.rectangle((17, 6, 18, 7), fill=glow)
    return _finalize(img)


def _draw_astral(accent: tuple[int, int, int]) -> Image.Image:
    img = _new_canvas()
    d = ImageDraw.Draw(img)
    # Swirling nebula ring.
    for r, shade in ((13, -0.5), (10, -0.2), (7, 0.1), (4, 0.5)):
        bbox = (16 - r, 16 - r, 16 + r, 16 + r)
        d.ellipse(bbox, outline=_shade(accent, shade))
    # Central glowing core.
    d.ellipse((12, 12, 20, 20), fill=accent)
    d.ellipse((14, 14, 18, 18), fill=(255, 255, 255))
    # Scatter stars.
    rng = random.Random(42)
    for _ in range(12):
        x = rng.randint(1, 30)
        y = rng.randint(1, 30)
        d.point((x, y), fill=(255, 255, 255))
    img = img.filter(ImageFilter.SMOOTH)
    return _finalize(img)


# Crystal tier palettes and names. Tier 0 is the starting crystal; higher
# tiers are unlocked by purchased upgrades / prestige. Picked for clear
# visual distinction at a glance.
_CRYSTAL_TIER_ACCENTS: list[tuple[int, int, int]] = [
    (160, 230, 255),  # 0: cyan — default cavern
    (150, 240, 200),  # 1: mint — after first few upgrades
    (200, 170, 255),  # 2: lavender
    (255, 220, 130),  # 3: gold
    (255, 160, 200),  # 4: rose
    (220, 200, 255),  # 5: prismatic
    (240, 240, 255),  # 6: cosmic (with star speckles)
]
CRYSTAL_TIER_NAMES: list[str] = [
    "Cavern", "Verdant", "Dusk", "Golden", "Rose", "Prismatic", "Cosmic",
]


def _crystal_accent_for_tier(tier: int) -> tuple[int, int, int]:
    return _CRYSTAL_TIER_ACCENTS[max(0, min(tier, len(_CRYSTAL_TIER_ACCENTS) - 1))]


def _draw_crystal(
    accent: tuple[int, int, int] = (160, 230, 255),
    *,
    tier: int = 0,
    size: int = 160,
) -> Image.Image:
    """Main clicker crystal — bigger and smoother than the shop icons."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    # Crystal silhouette (hexagonal gem).
    points = [
        (cx, cy - size // 2 + 8),
        (cx + size // 3, cy - size // 4),
        (cx + size // 3, cy + size // 4),
        (cx, cy + size // 2 - 8),
        (cx - size // 3, cy + size // 4),
        (cx - size // 3, cy - size // 4),
    ]
    d.polygon(points, fill=accent)
    # Facet lines for depth.
    light = _shade(accent, 0.4)
    dark = _shade(accent, -0.3)
    d.polygon([points[0], points[1], (cx, cy), points[5]], fill=light)
    d.polygon([points[3], points[4], (cx, cy), points[5]], fill=dark)

    # Tier-specific flourishes layered on top of the base crystal.
    if tier >= 2:
        # Extra diagonal facet for a "shaped" gem look.
        d.polygon([points[1], points[2], (cx, cy)], fill=_shade(accent, -0.1))
    if tier >= 3:
        # Sparkle inside the upper facet.
        d.ellipse((cx - 3, cy - size // 3, cx + 3, cy - size // 3 + 6),
                  fill=(255, 255, 255, 230))
    if tier >= 4:
        # Aurora line sweeping through.
        d.line([(cx - size // 3, cy), (cx + size // 3, cy)],
               fill=_shade(accent, 0.6), width=2)
    if tier >= 5:
        # Prismatic facet tips in complementary hues.
        rainbow = [(255, 120, 140), (140, 255, 180), (140, 180, 255)]
        for i, color in enumerate(rainbow):
            tip = points[i * 2 % len(points)]
            d.polygon([tip, (cx, cy), points[(i * 2 + 1) % len(points)]],
                      fill=(*color, 90))
    if tier >= 6:
        # Cosmic tier: star speckles floating inside the crystal body.
        rng = random.Random(7)
        for _ in range(18):
            sx = rng.randint(cx - size // 4, cx + size // 4)
            sy = rng.randint(cy - size // 3, cy + size // 3)
            d.point((sx, sy), fill=(255, 255, 255))
            if rng.random() < 0.3:
                d.point((sx + 1, sy), fill=(255, 255, 255))

    d.line([points[0], (cx, cy)], fill=(255, 255, 255), width=2)
    d.line([points[1], (cx, cy)], fill=(255, 255, 255), width=1)
    # Inner highlight.
    d.polygon(
        [(cx - 6, cy - size // 4), (cx + 2, cy - size // 4), (cx - 2, cy - 4)],
        fill=(255, 255, 255, 180),
    )
    # Soft outer glow — brighter at higher tiers.
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    glow_alpha = min(180, 80 + tier * 16)
    gd.polygon(points, fill=(*accent, glow_alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=6 + tier))
    out = Image.alpha_composite(glow, img)
    return out


# ----------------------------------------------------------------------
# Public API — each returns an arcade.Texture and caches PNGs on disk.
# ----------------------------------------------------------------------

_SHAPE_RENDERERS = {
    "pick": _draw_pick,
    "dwarf": _draw_dwarf,
    "cart": _draw_cart,
    "drill": _draw_drill,
    "golem": _draw_golem,
    "wizard": _draw_wizard,
    "forge": _draw_forge,
    "dragon": _draw_dragon,
    "titan": _draw_titan,
    "astral": _draw_astral,
}


def _cache_and_wrap(img: Image.Image, filename: str) -> arcade.Texture:
    _SPRITE_DIR.mkdir(parents=True, exist_ok=True)
    path = _SPRITE_DIR / filename
    # Best-effort cache — failure to save is non-fatal.
    try:
        img.save(path)
    except OSError:
        pass
    return arcade.Texture(img)


def generator_texture(gen: GeneratorDef) -> arcade.Texture:
    renderer = _SHAPE_RENDERERS.get(gen.sprite_shape, _draw_pick)
    img = renderer(gen.color)
    return _cache_and_wrap(img, f"gen_{gen.key}.png")


def main_crystal_texture(tier: int = 0) -> arcade.Texture:
    """Render the main clickable crystal for a given tier.

    Tiers are stable visual presets. Pre-generate all of them at startup
    and swap references on the ``MainClicker`` when the tier changes.
    """
    accent = _crystal_accent_for_tier(tier)
    img = _draw_crystal(accent, tier=tier)
    return _cache_and_wrap(img, f"main_crystal_tier_{tier}.png")


def shard_particle_texture() -> arcade.Texture:
    """Tiny glittering shard used in the click particle burst."""
    size = 16
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon(
        [(size // 2, 1), (size - 2, size // 2), (size // 2, size - 1), (1, size // 2)],
        fill=(200, 240, 255),
    )
    d.polygon(
        [(size // 2, 3), (size - 4, size // 2), (size // 2, size - 3), (3, size // 2)],
        fill=(255, 255, 255),
    )
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    return _cache_and_wrap(img, "shard_particle.png")
