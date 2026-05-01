# CLAUDE.md

Project-specific notes for AI assistants working on **Crystal Cavern**, a
Python + Arcade 3.x idle/clicker game.

## What this project is

A complete idle game with a main clickable (giant mana crystal), a tier
ladder of auto-producers, upgrades, save/load, offline earnings, and a
fully procedural art style (sprites generated with Pillow at startup).

The theme is dwarven-fantasy cavern mining; generator names run from
"Rusty Pickaxe" up to "Astral Collective". Replacing the theme would mean
swapping the names, colors, and sprite renderers — the math underneath is
theme-agnostic.

## Running and testing

```bash
pip install -r requirements.txt
python crystal_cavern.py   # launch the game
pytest                  # run unit tests (50 tests, all pure-Python)
```

Point the save file elsewhere to avoid clobbering a real playthrough:
```bash
CRYSTAL_CAVERN_SAVE=/tmp/dev.json python crystal_cavern.py
```

## Architecture at a glance

The hard rule: **pure-Python core, Arcade only in the view/UI layers.**
Anything under `src/` that doesn't import `arcade` must stay that way —
tests depend on it.

```
                 ┌───────────────────────────────────────┐
                 │        crystal_cavern.py (entry)      │
                 └───────────────────┬───────────────────┘
                                     │
                 ┌───────────────────▼───────────────────┐
                 │  src/game.py — arcade.Window wrapper  │
                 └───────────────────┬───────────────────┘
                                     │
                 ┌───────────────────▼───────────────────┐
                 │  src/game_view.py — arcade.View       │
                 │  owns timers, input routing, render   │
                 └──┬────────────────┬────────────────┬──┘
                    │                │                │
        ┌───────────▼───┐  ┌─────────▼────────┐  ┌────▼─────────────┐
        │ src/ui/*      │  │ src/entities/*   │  │ src/game_state.py│
        │ (Arcade draws)│  │ (Arcade draws)   │  │ (pure Python)    │
        └───────────────┘  └──────────────────┘  └────┬─────────────┘
                                                      │
                 ┌─────────────┬──────────────────────┼─────────────────┐
                 │             │                      │                 │
          ┌──────▼────┐  ┌─────▼──────┐      ┌────────▼──────┐  ┌───────▼────────┐
          │generators │  │ upgrades   │      │ save_system   │  │ number_format  │
          │  .py      │  │  .py       │      │  .py          │  │  .py           │
          └───────────┘  └────────────┘      └───────────────┘  └────────────────┘
```

Dependency direction is one-way top-to-bottom. Core modules never import
`arcade` and are safe to unit-test.

## Key files

| File | Why you'd touch it |
|------|-------------------|
| [src/constants.py](src/constants.py) | Palette, layout, balance knobs (cost growth, offline cap) |
| [src/generators.py](src/generators.py) | Add/edit tier definitions, tweak base cost/production |
| [src/upgrades.py](src/upgrades.py) | Add/edit upgrades and their multipliers |
| [src/game_state.py](src/game_state.py) | Core state + all production/cost/unlock logic |
| [src/save_system.py](src/save_system.py) | Atomic save/load + offline earnings calc |
| [src/sprite_factory.py](src/sprite_factory.py) | Procedural sprite rendering (add a new `sprite_shape`) |
| [src/ui/shop_panel.py](src/ui/shop_panel.py) | Shop list rendering and purchase intents |
| [src/ui/stats_panel.py](src/ui/stats_panel.py) | HUD wallet, rate, and owned roster |
| [src/entities/main_clicker.py](src/entities/main_clicker.py) | The big tappable crystal, its pulse and click anim |
| [src/game_view.py](src/game_view.py) | Top-level loop: input routing, update, draw, autosave |

## Things to know before editing

- **Arcade 3.x has a different drawing API from 2.x.** Use
  `arcade.draw_rect_filled(arcade.LBWH(...), color)` and
  `arcade.draw_texture_rect(texture, rect)`. `draw_rectangle_filled` /
  `draw_texture_rectangle` no longer exist.
- **State is canonical.** `GameState` holds everything that must be
  persisted; anything else (textures, floating text, particles, timers)
  lives on the view and is rebuilt on launch.
- **Cost math uses a geometric series.** See `bulk_cost` and
  `max_affordable` in [src/generators.py](src/generators.py) — closed-form
  formulas, not per-unit loops, so they stay fast at bulk sizes.
- **Saves are atomic.** `save_game` writes to a temp file and uses
  `os.replace` — don't short-circuit to `open('w')`; a crash mid-write
  would corrupt the save.
- **Offline earnings already get capped and discounted.** Cap is
  `OFFLINE_CAP_SECONDS` (8h), efficiency is `OFFLINE_EFFICIENCY` (50%) —
  both in `constants.py`.
- **Sprite caching is on disk under `assets/sprites/`.** These are
  regenerated on demand, so deleting the folder is safe.
- **Shop unlock gating** is based on `total_earned`, not current shards —
  so players don't see tiers disappear after a big purchase.

## Adding a new generator tier

1. Append a `GeneratorDef` to the `GENERATORS` tuple in
   [src/generators.py](src/generators.py).
2. If it uses a new visual, add a `_draw_<shape>` renderer in
   [src/sprite_factory.py](src/sprite_factory.py) and register it in
   `_SHAPE_RENDERERS`. Otherwise reuse an existing `sprite_shape`.
3. Consider adding matching upgrades in
   [src/upgrades.py](src/upgrades.py) gated on that new generator.
4. Run `pytest` — the monotonicity tests will tell you if the cost/rate
   ordering is off.

## Adding a new upgrade

1. Append an `UpgradeDef` to `UPGRADES` in
   [src/upgrades.py](src/upgrades.py).
2. The `effect` field determines behavior:
   - `"click"` — multiplies click power only.
   - `"gen:<generator_key>"` — multiplies that one generator's rate.
   - `"global"` — multiplies everything (click + idle).
3. `requires_key` + `requires_count` gate when the upgrade becomes
   visible in the shop.

## Conventions

- Keep the core pure-Python. If you find yourself importing `arcade`
  outside `src/ui/`, `src/entities/`, `src/game_view.py`, or
  `src/game.py`, reconsider.
- Keep `GameState.to_dict()` / `from_dict()` forward-compatible: ignore
  unknown keys on load rather than crashing. The `version` field is
  reserved for future migrations.
- Comments explain *why*, not *what*. Prefer renaming to commenting.
- Tests live under `tests/` and run without a graphics context. Don't
  add tests that need a window.
