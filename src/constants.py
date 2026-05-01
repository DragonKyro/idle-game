"""Central configuration: window, layout, palette, and gameplay tuning."""

from __future__ import annotations

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Crystal Cavern"

# Layout split: a wide play area on the left, a shop panel on the right.
SHOP_PANEL_WIDTH = 440
PLAY_AREA_WIDTH = SCREEN_WIDTH - SHOP_PANEL_WIDTH

# Palette — deep cavern purples and glowing crystal cyans.
COLOR_BG_TOP = (22, 18, 40)
COLOR_BG_BOTTOM = (8, 6, 18)
COLOR_PANEL_BG = (30, 24, 52)
COLOR_PANEL_BORDER = (88, 72, 140)
COLOR_PANEL_HIGHLIGHT = (58, 46, 98)
COLOR_TEXT_PRIMARY = (240, 236, 255)
COLOR_TEXT_SECONDARY = (180, 172, 210)
COLOR_TEXT_DIM = (130, 120, 160)
COLOR_TEXT_GOLD = (255, 214, 110)
COLOR_TEXT_OK = (130, 230, 170)
COLOR_TEXT_WARN = (230, 120, 140)

COLOR_BUTTON_IDLE = (70, 52, 120)
COLOR_BUTTON_HOVER = (98, 76, 160)
COLOR_BUTTON_DISABLED = (48, 42, 72)
COLOR_BUTTON_AFFORD = (90, 150, 110)
COLOR_BUTTON_AFFORD_HOVER = (120, 190, 140)

# Gameplay tuning.
COST_GROWTH = 1.15  # Standard idle-game cost multiplier per purchase.
OFFLINE_CAP_SECONDS = 8 * 60 * 60  # Cap offline earnings at 8 hours.
OFFLINE_EFFICIENCY = 0.5  # Offline produces at 50% of online rate — encourages play.
AUTOSAVE_INTERVAL_SECONDS = 15.0
CLICK_PARTICLE_COUNT = 10
FLOATING_TEXT_LIFETIME = 1.0
