# CLAUDE.md

Project-specific notes for AI assistants working on **Crystal Cavern**, a
Python + Arcade 3.x idle/clicker game.

## What this project is

A complete idle game with a main clickable (giant mana crystal), 10
tiers of auto-producers, 29 leveled upgrades, save/load, offline
earnings, a prestige ("Descend Deeper") system, a permanent "crystal
aura" around the clicker, a 4-branch talent tree spent from essence, 28
achievements, procedurally synthesized chiptune SFX, 6 rotating biomes,
a mini-boss (Cavern Lord), random events (Golden Shards + Lucky
Critters), a combo-click multiplier, a settings modal, a stats modal,
onboarding, screen-shake + value-tween juice. Sprites and sounds are
both procedurally generated at startup — no binary assets in the repo.

The theme is dwarven-fantasy cavern mining; generator names run from
"Rusty Pickaxe" up to "Astral Collective". Replacing the theme would mean
swapping the names, colors, and sprite renderers — the math underneath is
theme-agnostic.

### New invariants to know

- **Audio is synthesized, not shipped.** `src/audio.py::AudioLibrary`
  generates every WAV on first construction and caches them under
  `assets/sounds/`. Delete the folder and they regenerate — safe.
- **`arcade.Sound` requires a window.** `AudioLibrary.__init__` is
  called from inside `GameView.__init__`, which itself is constructed
  after `arcade.Window.__init__` — do NOT build the library at module
  import time or you'll crash headless.
- **SFX and music are routed separately.** Names in `_MUSIC_SOUNDS` are
  loaded with `streaming=True` and played via `start_music` / looped;
  SFX go through `play(name, gain=...)`. Music volume changes update
  the live pyglet player's `.volume` attribute.
- **Pure-Python stays pure.** `audio.py`, `achievements.py`,
  `talents.py`, `biomes.py`, `game_state.py`, and the core math modules
  must not import `arcade`. Tests rely on this.
- **Unlock checks run every frame.** `achievements.newly_unlocked(state)`
  is cheap (< 30 O(1) predicates) and returns just the newly-met
  achievements so you can notify without re-scanning the full set.
- **Essence has two counters.** `state.essence` is spendable (drives
  the passive +2%/unit and talent purchases). `state.total_essence_earned`
  is the lifetime counter for achievements and the stats modal. Keep
  both up to date on descend / boss-defeat.
- **Boss state is session-only.** Don't persist `GameView._boss` —
  bosses re-gate on `state.total_earned` crossing the next threshold in
  `_BOSS_THRESHOLDS`, using `state.bosses_defeated` as the index. Bosses
  spawn at `y ≈ SCREEN_HEIGHT - 260` (above the crystal) and are drawn
  *after* the clicker in `on_draw` so they always read as the foreground
  element of a fight.
- **Generators have a `max_count` cap (default 200).** Any new purchase
  path must go through `GameState.buy_generator`, which refuses past the
  cap. Shop rows mirror the upgrade `MAX` badge when they hit it.
- **Clicks against bosses use a 50× multiplier.** If you tune this,
  do it in `GameView._damage_boss`, not in `click_power` — the crystal's
  own click path shouldn't change.
- **Biomes are derived, not stored.** `biome_for_prestige(prestige_count)`
  is the single source of truth; `GameView` regenerates the background
  texture and re-tints the ambient motes when the prestige count
  changes.
- **Settings live on the state.** `state.settings` is a plain dict with
  a small fixed schema. `SettingsModal` writes into it via
  `GameView._handle_settings_change`, which also re-applies them (audio
  volumes, screen shake, reduced motion).

### Core systems in brief

- **Generators** (`src/generators.py`): 10 tiers, geometric cost growth.
- **Upgrades** (`src/upgrades.py`): 29 entries, three effect kinds —
  `"click"`, `"gen:<key>"`, `"global"`. Each has `max_level` (3 or 5)
  and `cost_growth` (typically 4–6). Effect stacks multiplicatively per
  level (2x at Lv 3 = 8x). Visibility gated on the `requires_key`
  generator having ≥ `requires_count` owned *for the first level*;
  once any level is owned the row stays visible forever (including
  maxed, which shows as a dim `MAX` badge).
- **Prestige / Descent** (`src/game_state.py`): permanent *Ancient
  Essence* currency. `pending_essence = floor(sqrt((total_earned -
  last_descend_total) / 1e10))`. Each essence = +2% global production
  (compounds with all other multipliers). Descent clears `shards`,
  `owned`, `purchased_upgrades`; preserves `total_earned` (so shop
  unlocks stick), `essence`, `prestige_count`, `total_clicks`.
- **Crystal tiers** (`src/sprite_factory.py`): 7 tier presets rendered
  up front; `GameState.crystal_tier()` selects one based on upgrades
  owned and prestige count. `GameView` watches the tier and swaps the
  `MainClicker` texture when it changes.
- **Purchase feedback** (`src/game_view.py`): every successful purchase
  calls `_on_purchase_feedback` which (a) flashes the row via
  `ShopPanel.flash`, (b) spawns a `Toast` with the item's accent color,
  (c) triggers `MainClicker.register_purchase` + a colored particle
  burst, and (d) runs `_maybe_swap_crystal` in case the tier ticked up.
- **Crystal aura** (`src/entities/crystal_aura.py`): the *permanent*
  counterpart to the transient feedback above. Reads directly from
  `GameState` every frame — one small orbiting emblem per distinct
  generator tier owned (inner ring), plus one gold star per total
  upgrade level purchased on a wider ring (capped at 48 so the ring
  stays readable). This is how players see lasting evidence of a
  purchase in the play area, not just in the bottom-left roster.

## Running and testing

```bash
pip install -r requirements.txt        # or `pip install -e .` (pyproject.toml)
python crystal_cavern.py   # launch the game
pytest                  # run unit tests (120 tests, all pure-Python)
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
| [src/ui/shop_panel.py](src/ui/shop_panel.py) | Shop list, `Lv N/M` + MAX badge, purchase intents, row-flash state |
| [src/ui/stats_panel.py](src/ui/stats_panel.py) | HUD wallet (tweened), rate, essence/prestige badge, owned roster |
| [src/ui/toast.py](src/ui/toast.py) | Purchase / event banner at the top of the play area |
| [src/ui/descend_modal.py](src/ui/descend_modal.py) | Prestige confirmation modal |
| [src/ui/settings_modal.py](src/ui/settings_modal.py) | Volumes, toggles, export/import, reset |
| [src/ui/stats_modal.py](src/ui/stats_modal.py) | Lifetime stats + achievement progress |
| [src/ui/achievement_panel.py](src/ui/achievement_panel.py) | Full achievement catalog with lock state |
| [src/ui/achievement_banner.py](src/ui/achievement_banner.py) | Slide-in banner on unlock |
| [src/ui/talent_panel.py](src/ui/talent_panel.py) | Talent tree modal with branch columns |
| [src/ui/onboarding.py](src/ui/onboarding.py) | First-run pointer overlay (3 stages) |
| [src/ui/combo_meter.py](src/ui/combo_meter.py) | Rapid-click combo charge + decay + meter |
| [src/ui/random_events.py](src/ui/random_events.py) | Golden Shard + Lucky Critter spawn, click, reward |
| [src/ui/juice.py](src/ui/juice.py) | ScreenShake + TweenedValue (reduced-motion friendly) |
| [src/entities/main_clicker.py](src/entities/main_clicker.py) | The big tappable crystal, pulse, click/purchase anim, texture swap |
| [src/entities/crystal_aura.py](src/entities/crystal_aura.py) | Permanent generator emblems + upgrade stars ringing the crystal |
| [src/entities/cavern_lord.py](src/entities/cavern_lord.py) | Mini-boss entity: spawn, HP, click-damage, death sequence |
| [src/audio.py](src/audio.py) | Procedural WAV synth + AudioLibrary facade |
| [src/achievements.py](src/achievements.py) | 28 achievement defs + per-frame unlock check |
| [src/talents.py](src/talents.py) | Talent definitions across 4 branches |
| [src/biomes.py](src/biomes.py) | Biome palette list + `biome_for_prestige` |
| [src/game_view.py](src/game_view.py) | Top-level loop: routes input, drives every subsystem, handles purchase feedback + prestige + boss + events |

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
  so players don't see tiers disappear after a big purchase. This also
  means prestige keeps all tiers visible across descents, which is
  intentional: prestige shouldn't hide content.
- **Crystal textures are pre-generated** for every tier at launch
  (`GameView._crystal_textures`). Don't re-generate them at runtime;
  swap references on `MainClicker` via `set_texture`.
- **Purchase feedback has one entry point.** Any new purchase path
  should call `GameView._on_purchase_feedback(...)` so row flash, toast,
  particle burst, and crystal pulse all stay in sync.
- **`arcade.draw_texture_rect`'s `color=` param wants an
  `arcade.types.Color`, not a plain tuple.** See `src/ui/particles.py`
  — passing `(r, g, b, a)` directly raises `AttributeError` on
  `normalized`.

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
3. `requires_key` + `requires_count` gate when the upgrade first
   becomes visible in the shop.
4. `max_level` caps how many times the player can buy it; `multiplier`
   is applied once per level (so stacking is multiplicative).
5. `cost_growth` scales the price per level — level N costs
   `cost * cost_growth^(N-1)`.
6. Bumping `max_level` up is always safe; lowering it is too (old
   saves are clamped in `GameState.from_dict`).
7. The tests in `tests/test_upgrades.py` enforce that every generator
   has at least one upgrade and that every `effect` string is
   well-formed — pytest will tell you if you break those invariants.

## Adding a new achievement

1. Append an `AchievementDef` to `ACHIEVEMENTS` in
   [src/achievements.py](src/achievements.py).
2. The `predicate` is a plain callable `(GameState) -> bool`. Helpers
   for common cases (`_owned`, `_clicks`, `_earned`, `_prestige`) are
   right above the list.
3. The `color` accent is used on both the unlock banner and the panel
   row trophy circle.
4. Unlocks are checked every frame by `newly_unlocked(state)`, which
   mutates `state.achievements` so the check stays idempotent.

## Adding a new talent

1. Append a `TalentDef` to `TALENTS` in
   [src/talents.py](src/talents.py), picking one of the four branches.
2. The `effect` string is what `GameState._talent_value(effect)` sums
   over — either reuse an existing effect (e.g. `"click"`, `"idle"`,
   `"offline"`, `"offline_cap"`, `"crit_chance"`, `"start_bonus"`,
   `"event_rate"`, `"essence_bonus"`, `"lowest_tier_boost"`) or add a
   new one AND a call-site that consumes it.
3. Costs scale as `base_cost * level`; max_level caps purchases.

## Adding a new biome

1. Append a `Biome` to `BIOMES` in [src/biomes.py](src/biomes.py).
2. `biome_for_prestige` uses modulo so the cycle length is just
   `len(BIOMES)`. Players who prestige past the list just see the
   rotation repeat.

## Adding a new sound

1. Write a recipe function in [src/audio.py](src/audio.py) that returns
   `list[float]` in `[-1, 1]` at `_SAMPLE_RATE`.
2. Register it in `_SOUND_RECIPES` under a stable name.
3. If it's a looping music bed (not a SFX), also add the name to
   `_MUSIC_SOUNDS` so it loads in streaming mode and starts via
   `start_music`.
4. Call `self._audio.play("name")` from the game view at the event.
5. Delete `assets/sounds/<name>.wav` if you change the recipe — it's
   cached, and the file wins over the recipe.

## Tuning prestige

Prestige math lives at the top of [src/game_state.py](src/game_state.py):

- `ESSENCE_THRESHOLD` (default `1e10`): divisor inside the sqrt. Lower
  values mean more essence earlier; higher values delay the first
  descent.
- `ESSENCE_PER_BONUS` (default `0.02`): linear bonus per held essence.
  Stacks multiplicatively with global upgrades, so even a small value
  compounds to meaningful late-game gains.
- `CRYSTAL_MAX_TIER` / `CRYSTAL_UPGRADES_PER_TIER`: govern the visual
  evolution of the main crystal. `crystal_tier() = min(MAX,
  upgrades_count // PER_TIER + prestige_count)`.

When you change the save schema (adding prestige fields, renaming
something), bump the `version` field in `GameState.to_dict()`.
`GameState.from_dict()` must stay tolerant of missing / unknown keys so
older saves still load.

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
