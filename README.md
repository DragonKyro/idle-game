# Crystal Cavern

A cozy idle/clicker game built in Python with the [Arcade](https://api.arcade.academy/) library.
Tap the glowing mana crystal to mine shards, then hire an ever-sillier roster
of helpers — Rusty Pickaxes, Stone Golems, Crystal Dragons, and eventually the
Ancient Titans themselves — to mine for you while you sip your cocoa.

![made with python](https://img.shields.io/badge/made%20with-python-3776AB?logo=python&logoColor=white)
![arcade 3](https://img.shields.io/badge/arcade-3.x-6A4CFF)

## Features

- **10 tiers of generators** with geometric cost scaling and procedurally
  rendered pixel-art sprites.
- **12 unlockable upgrades** that boost click power, a specific generator,
  or every source of production at once.
- **Friendly large-number formatting** — 1.23K, 4.56M, 7.89B, up through Dc,
  then graceful fallback to scientific notation.
- **Save & load** with atomic writes so a crash can never corrupt your save.
- **Offline farming** — helpers keep mining while the game is closed
  (capped at 8 hours at 50% efficiency), with a welcome-back modal on return.
- **Polished feel** — ambient floating motes, click particles, floating
  "+N" text, pulsing crystal, hover effects, and a gradient cavern backdrop.
- **Organized, testable codebase** — pure-Python core (state, saves, number
  formatting, generator math) with 50 unit tests; Arcade is only touched by
  the view / UI layers.

## Getting started

You'll need Python 3.10+.

```bash
pip install -r requirements.txt
python crystal_cavern.py
```

That's it. The window opens, the game loads any prior save, credits offline
earnings, and you're mining.

## Controls

| Input                              | Effect                        |
|------------------------------------|-------------------------------|
| Left-click the big crystal         | Mine one shard (×click power) |
| Left-click a shop row              | Buy that helper or upgrade    |
| Mouse-wheel over the shop          | Scroll the shop list          |
| `F5`                               | Force-save immediately        |
| Close the window                   | Auto-saves on exit            |

The game also autosaves every 15 seconds in the background.

## Save location

Saves live at `~/.crystal_cavern/save.json`. You can override the path with
the `CRYSTAL_CAVERN_SAVE` environment variable — handy for running a
second fresh playthrough without losing your main save:

```bash
CRYSTAL_CAVERN_SAVE=/tmp/second.json python crystal_cavern.py
```

Deleting the save file starts a new game.

## Project layout

```
idle-game/
├── crystal_cavern.py        # Entry point — just calls src.game.run
├── requirements.txt
├── README.md
├── CLAUDE.md                # Notes for AI assistants working on this repo
├── src/
│   ├── constants.py         # Colors, layout, tuning knobs
│   ├── number_format.py     # K/M/B/T/Qa… abbreviation
│   ├── generators.py        # Generator tier definitions + cost math
│   ├── upgrades.py          # Upgrade definitions
│   ├── game_state.py        # Canonical serializable game state
│   ├── save_system.py       # Atomic JSON save/load + offline earnings
│   ├── sprite_factory.py    # Pillow-based procedural pixel-art sprites
│   ├── game_view.py         # arcade.View owning the whole game loop
│   ├── game.py              # arcade.Window wrapper + run()
│   ├── ui/
│   │   ├── button.py
│   │   ├── shop_panel.py
│   │   ├── stats_panel.py
│   │   ├── floating_text.py
│   │   ├── particles.py
│   │   └── welcome_back.py
│   └── entities/
│       └── main_clicker.py
├── assets/
│   ├── sprites/             # Auto-populated on first run
│   └── fonts/
└── tests/
    ├── test_number_format.py
    ├── test_generators.py
    ├── test_game_state.py
    └── test_save_system.py
```

`assets/sprites/` is populated the first time the game launches — the
`sprite_factory` module draws each sprite with Pillow and caches the PNGs
there. Deleting a sprite just causes it to be regenerated on next launch.

## Running the tests

The core game logic (number formatting, cost math, state transitions,
save/load, offline earnings) is fully covered by pure-Python unit tests
that don't need a graphics context:

```bash
pytest
```

Expected: `50 passed`.

## Tuning

Most gameplay knobs live in [`src/constants.py`](src/constants.py):

- `COST_GROWTH` — cost multiplier per purchase (default `1.15`, the
  idle-game standard).
- `OFFLINE_CAP_SECONDS` — maximum time offline earnings accumulate.
- `OFFLINE_EFFICIENCY` — fraction of online rate applied while offline.
- `AUTOSAVE_INTERVAL_SECONDS` — time between background saves.

Balance values (base costs, base production, color accents) live alongside
the generator definitions in [`src/generators.py`](src/generators.py) and
the upgrade definitions in [`src/upgrades.py`](src/upgrades.py).

## License

MIT — use it, fork it, rename the dragons, whatever you like.
