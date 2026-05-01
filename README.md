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

- **20 tiers of generators** with geometric cost scaling, a **cap of
  200 per tier** (so completionists have a clear finish line), and
  procedurally rendered pixel-art sprites. The ladder now runs from
  Rusty Pickaxe through Lantern Keeper, Apprentice Miner, Deep
  Digger, Cart Runner, Moonstone Mine, Crystal Drill, Clockwork
  Sapper, Stone Golem, Celestial Chorus, Arcane Wizard, Rift Anchor,
  Rune Forge, Crystal Dragon, Void Whale, Ancient Titan, Cosmic
  Weaver, Astral Collective, Primordial Hearth, and Universe Tree.
- **53 upgrades, each with its own max level** — two per generator
  (gated at 10 and 25 owned) plus six click-power tiers (Gloves →
  Gauntlet → Echo Tap → Mithril Knuckles → Resonant Strike → Divine
  Striker) and seven global-production capstones. Rows show `Lv N/M`
  and the next-level cost; maxed rows stay visible with a gold `MAX`
  badge. The emporium now has a visible **scrollbar**, rows scroll
  **behind** the tabs, and scroll is clamped to content height so you
  can't rubber-band past the end.
- **Prestige / Descent system** — reset the current run to earn permanent
  *Ancient Essence*. Unspent essence grants +2% all production (compounds);
  spent essence unlocks talents on the tree.
- **Talent tree with 16 talents across 4 branches** (Click, Idle,
  Offline, Special) rendered as a proper tree of circular nodes
  connected by trunk lines, each with a procedurally drawn icon and
  level pips. Highlights: **Synced Strike** (click scales with /s
  rate), **Boss Slayer** (extra boss damage per level), **Runed
  Harmony** (all production scales with distinct helper types owned),
  **Cavern Historian** (all production scales with achievements
  unlocked). Hover any node for a tooltip; click to invest.
- **Achievements** — **50 trackable badges** across clicks, earnings,
  roster, upgrades (incl. "max every click upgrade" / "max every
  global upgrade"), prestige, talents (per-branch max + full max),
  bosses (1/10/50 slain), playtime (1h/10h/100h), and a biome-cycle
  milestone. An animated banner slides in on each unlock; a full panel
  (keybind `A`) shows the whole catalog.
- **Procedurally synthesized chiptune audio** — all 8 sound effects
  (click, purchase, level-up, max-level flourish, descend fanfare, event
  chime, boss hit, boss defeat) *plus* a 20-second looping cave-ambient
  music bed (low drone + C-major pad + sparse bells) are generated from
  sine/triangle/square waves with ADSR envelopes at first launch, then
  cached to `assets/sounds/`. No binary audio assets in the repo.
  Music and SFX volumes can be adjusted independently in Settings.
- **Evolving main crystal with real rewards** — seven procedurally
  rendered tiers (Cavern → Verdant → Dusk → Golden → Rose → Prismatic
  → Cosmic). **Each tier grants +15% to all production** (additive,
  stacks with every other multiplier) — Cosmic alone is +90%. Advance
  by buying 3 upgrade levels **or** descending, with both paths shown
  in the tier label beneath the crystal (`Crystal: Verdant  —  +15%
  all production` / `Next: Dusk in 2 upgrade level(s) — or on next
  descent`). Tier-ups fire a toast + chime.
- **Six biomes** that rotate with each descent — the whole play area
  re-themes itself (Cavern → Verdant Hollows → Dusk Grotto → Ember Deep
  → Abyssal Rift → Astral Expanse).
- **Mini-bosses** — the Cavern Lord emerges above the crystal at
  earnings milestones. Clicks deal 50× click power as damage (plus
  combo), so hitting the boss actually moves its HP bar. Defeating it
  rains shards and grants a bonus essence.
- **Random events** — Golden Shards (click-for-big-bonus) and Lucky
  Critters (clicking grants 2× production for 30s) spawn between
  stretches of idle play. The Lucky Strike talent spawns them more often.
- **Combo clicks** — rapid-clicking the crystal builds a decaying charge
  up to a 5× multiplier on active clicks without invalidating idle play.
- **Permanent progression aura** — orbiting emblems around the crystal
  (one per generator tier owned) and gold stars on an outer ring (one
  per upgrade level). Every purchase leaves a lasting mark.
- **Transient feedback layer** — row flashes gold, toast banner with the
  item's accent color, crystal pulse with colored particle burst, screen
  shake for big moments.
- **Onboarding** — first-time players see arrow-pointer hints at the
  crystal, then at the shop, then a short farewell. Dismissed
  automatically as you progress and remembered in the save.
- **Settings modal** (`Esc`) — SFX and music volume sliders, screen
  shake toggle, reduced-motion toggle (disables shake + value tweens),
  save export/import, and reset-game with two-click confirmation.
- **Stats modal** (`S`) — playtime, total clicks, total earned, helpers
  bought, upgrade levels, descents, best descent, lifetime essence,
  bosses defeated, achievement progress.
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
  number formatting, generator math, prestige, leveled upgrades,
  talents, achievements, biomes, boss math, audio synthesis, juice
  helpers) with 113 unit tests; Arcade is only touched by the view /
  UI layers.

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

| Input                              | Effect                                     |
|------------------------------------|--------------------------------------------|
| Left-click the big crystal         | Mine one shard (×click power × combo)      |
| Left-click a shop row              | Buy that helper or upgrade level           |
| Mouse-wheel over the shop          | Scroll the shop list                       |
| Click Golden Shards / Critters     | Collect event reward                       |
| Click the Cavern Lord when it appears | Damage it — defeat for a big bounty     |
| Left-click **Descend Deeper**      | Prestige (when available)                  |
| `S`                                | Open the Stats modal                       |
| `A`                                | Open the Achievements panel                |
| `T`                                | Open the Talent tree                       |
| `Esc`                              | Open / close the Settings modal            |
| `F5`                               | Force-save immediately                     |
| Close the window                   | Auto-saves on exit                         |

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
│   ├── upgrades.py          # 29 leveled upgrade definitions
│   ├── talents.py           # 9 talent definitions across 4 branches
│   ├── achievements.py      # 28 achievement definitions + unlock check
│   ├── biomes.py            # 6 biome palettes for prestige rotation
│   ├── audio.py             # Procedural WAV synth + AudioLibrary facade
│   ├── game_state.py        # Canonical serializable state
│   ├── save_system.py       # Atomic JSON save/load + offline earnings
│   ├── sprite_factory.py    # Pillow-based procedural pixel-art sprites
│   ├── game_view.py         # arcade.View owning the whole game loop
│   ├── game.py              # arcade.Window wrapper + run()
│   ├── ui/
│   │   ├── button.py
│   │   ├── shop_panel.py           # Lv N/M rows, MAX badge
│   │   ├── stats_panel.py
│   │   ├── floating_text.py
│   │   ├── particles.py
│   │   ├── combo_meter.py          # Rapid-click combo bar
│   │   ├── random_events.py        # Golden Shard + Lucky Critter
│   │   ├── toast.py                # Purchase confirmation banner
│   │   ├── achievement_banner.py   # Unlock slide-in
│   │   ├── achievement_panel.py    # Full catalog modal
│   │   ├── talent_panel.py         # Talent tree modal
│   │   ├── stats_modal.py          # Lifetime stats modal
│   │   ├── settings_modal.py       # Volume / toggles / export / reset
│   │   ├── onboarding.py           # First-run pointer overlay
│   │   ├── welcome_back.py         # Offline-earnings modal
│   │   ├── descend_modal.py        # Prestige confirmation modal
│   │   └── juice.py                # ScreenShake + TweenedValue
│   └── entities/
│       ├── main_clicker.py  # The big tappable crystal (tier-aware)
│       ├── crystal_aura.py  # Permanent progression ring around the crystal
│       └── cavern_lord.py   # Mini-boss entity (HP + click-damage)
├── assets/
│   ├── sprites/             # Auto-populated on first run
│   ├── sounds/              # Auto-populated on first run (synth'd WAVs)
│   └── fonts/
└── tests/
    ├── test_number_format.py
    ├── test_generators.py
    ├── test_upgrades.py
    ├── test_game_state.py
    ├── test_save_system.py
    ├── test_achievements.py
    ├── test_talents.py
    ├── test_biomes.py
    ├── test_audio.py
    ├── test_boss.py
    └── test_juice.py
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

Expected: `134 passed`.

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
