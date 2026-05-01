"""Top-level arcade.Window wrapper."""

from __future__ import annotations

import arcade

from src.constants import SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH
from src.game_view import GameView
from src.save_system import save_game


class CrystalCavernWindow(arcade.Window):
    def __init__(self) -> None:
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.background_color = (8, 6, 18)
        self._view = GameView()
        self.show_view(self._view)

    def on_close(self) -> None:
        # Make sure the wallet is never lost when the player closes the window.
        try:
            save_game(self._view.state)
        finally:
            super().on_close()


def run() -> None:
    """Entry point — create the window and start the event loop."""
    window = CrystalCavernWindow()
    arcade.run()
