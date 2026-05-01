# Crystal Cavern

A cozy idle/clicker game built in Python with the [Arcade](https://api.arcade.academy/) library.
Tap the glowing mana crystal to mine shards, then hire an ever-sillier roster
of helpers — Rusty Pickaxes, Stone Golems, Crystal Dragons, and eventually the
Ancient Titans themselves — to mine for you while you sip your cocoa. When
you're rich enough, **descend deeper** to trade your current run for
permanent Ancient Essence and an ever-evolving crystal.

![made with python](https://img.shields.io/badge/made%20with-python-3776AB?logo=python&logoColor=white)
![arcade 3](https://img.shields.io/badge/arcade-3.x-6A4CFF)

## Features

- **10 tiers of generators** with geometric cost scaling and procedurally
  rendered pixel-art sprites.
- **29 upgrades, each with its own max level** — buy each upgrade 3–5
  times for multiplicative effect stacking. Rows show `Lv N/M` and the
  next-level cost; maxed rows stay visible with a gold `MAX` badge so
  completionists can see the full catalog of remaining work.
- **Prestige / Descent system** — reset the current run to earn permanent
  *Ancient Essence* (+2% all production per essence, compounding). Each
  descent also bumps the main crystal up a visual tier.
- **Evolving main crystal** — seven procedurally rendered tiers (Cavern →
  Verdant → Dusk → Golden → Rose → Prismatic → Cosmic). It levels up as
  you buy upgrades and as you prestige, so you can see your progression
  at a glance.
- **Satisfying purchase feedback (transient + permanent)** — on every
  buy, the row flashes gold, a toast banner names what you bought, the
  main crystal pulses with a colored particle burst, *and* a lasting
  mark appears on the crystal aura: a new orbiting emblem the first time
  you own a given generator tier, and a new star on the outer ring for
  each upgrade level purchased.
- **Friendly large-number formatting** — 1.23K, 4.56M, 7.89B, up through
  Dc, then graceful fallback to scientific notation.
- **Save & load** with atomic writes so a crash can never corrupt your
  save.
- **Offline farming** — helpers keep mining while the game is closed
  (capped at 8 hours at 50% efficiency), with a welcome-back modal on
  return.
- **Polished feel** — ambient floating motes, click particles, floating
  "+N" text, pulsing crystal, hover effects, and a gradient cavern
  backdrop.
- **Organized, testable codebase** — pure-Python core (state, saves,
  number formatting, generator math, prestige, leveled upgrades) with
  72 unit tests; Arcade is only touched by the view / UI layers.

## Getting started

You'll need Python 3.10+.

```bash
pip install -r requirements.txt        # classic pip workflow
#   --OR--
pip install -e .                        # uses pyproject.toml, exposes
                                        # the `crystal-cavern` command
python crystal_cavern.py
```

That's it. The window opens, the game loads any prior save, credits
offline earnings, and you're mining.

## Controls

| Input                              | Effect                             |
|------------------------------------|------------------------------------|
| Left-click the big crystal         | Mine one shard (×click power)      |
| Left-click a shop row              | Buy that helper or upgrade         |
| Mouse-wheel over the shop          | Scroll the shop list               |
| Left-click the **Descend** button  | Prestige (when you can afford it)  |
| `F5`                               | Force-save immediately             |
| Close the window                   | Auto-saves on exit                 |

The game also autosaves every 15 seconds in the background.

## How prestige works

Once your *lifetime* earnings since the last descent reach 10 billion
shards, a glowing **Descend Deeper** button appears above the save hint.
Descending:

- **Resets** your shards, owned helpers, and purchased upgrades.
- **Keeps** your lifetime earnings, click count, and accumulated
  Ancient Essence.
- **Awards** ⌊√(earnings since last descent / 10B)⌋ essence — so the
  first descent typically gives a few, and later descents pay much more.
- **Grants** +2% production per essence (permanent, compounding), and
  bumps the main crystal to a fancier tier.

All shop tiers stay unlocked across descents because those are gated on
lifetime earned, not current shards.

## Save location

Saves live at `~/.crystal_cavern/save.json`. You can override the path
with the `CRYSTAL_CAVERN_SAVE` environment variable — handy for running
a second fresh playthrough without losing your main save:

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
│   ├── upgrades.py          # 29 upgrade definitions (with max_level)
│   ├── game_state.py        # Canonical serializable state (inc. prestige)
│   ├── save_system.py       # Atomic JSON save/load + offline earnings
│   ├── sprite_factory.py    # Pillow-based procedural pixel-art sprites
│   ├── game_view.py         # arcade.View owning the whole game loop
│   ├── game.py              # arcade.Window wrapper + run()
│   ├── ui/
│   │   ├── button.py
│   │   ├── shop_panel.py    # Lv N/M rows, next-level cost, MAX badge
│   │   ├── stats_panel.py
│   │   ├── floating_text.py
│   │   ├── particles.py
│   │   ├── toast.py         # Purchase confirmation banner
│   │   ├── welcome_back.py  # Offline-earnings modal
│   │   └── descend_modal.py # Prestige confirmation modal
│   └── entities/
│       ├── main_clicker.py  # The big tappable crystal (tier-aware)
│       └── crystal_aura.py  # Permanent progression ring around the crystal
├── assets/
│   ├── sprites/             # Auto-populated on first run
│   └── fonts/
└── tests/
    ├── test_number_format.py
    ├── test_generators.py
    ├── test_upgrades.py
    ├── test_game_state.py   # Includes prestige / descent tests
    └── test_save_system.py
```

`assets/sprites/` is populated the first time the game launches — the
`sprite_factory` module draws each sprite with Pillow and caches the
PNGs there. Deleting a sprite just causes it to be regenerated on next
launch.

## Running the tests

The core game logic (number formatting, cost math, state transitions,
prestige, save/load, offline earnings) is fully covered by pure-Python
unit tests that don't need a graphics context:

```bash
pytest
```

Expected: `72 passed`.

## Tuning

Most gameplay knobs live in [`src/constants.py`](src/constants.py):

- `COST_GROWTH` — cost multiplier per purchase (default `1.15`, the
  idle-game standard).
- `OFFLINE_CAP_SECONDS` — maximum time offline earnings accumulate.
- `OFFLINE_EFFICIENCY` — fraction of online rate applied while offline.
- `AUTOSAVE_INTERVAL_SECONDS` — time between background saves.

Prestige tuning lives in [`src/game_state.py`](src/game_state.py):

- `ESSENCE_THRESHOLD` — shards needed (per-run) before `pending_essence`
  increments; default `1e10`.
- `ESSENCE_PER_BONUS` — permanent production boost per essence held;
  default `0.02` (2%).
- `CRYSTAL_UPGRADES_PER_TIER` — how many upgrades bump the crystal a
  visual tier (before prestige stacks on top).

Balance values (base costs, base production, color accents) live
alongside the generator definitions in
[`src/generators.py`](src/generators.py) and the upgrade definitions in
[`src/upgrades.py`](src/upgrades.py).

## License

MIT — use it, fork it, rename the dragons, whatever you like.
