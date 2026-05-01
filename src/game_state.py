"""The canonical mutable game state.

Deliberately kept plain-Python and serializable so save/load and tests can
treat it as a dumb data bag. Anything not trivially JSON-safe (textures,
sprite objects, timers, audio buffers) lives on the game *view*, not here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from src.generators import GENERATORS, GENERATORS_BY_KEY, GeneratorDef, cost_for
from src.talents import TALENTS_BY_KEY, talent_level_cost
from src.upgrades import UPGRADES_BY_KEY, upgrade_cost_for_level


# Prestige tuning.
ESSENCE_THRESHOLD = 1e10
ESSENCE_PER_BONUS = 0.02  # 2% production per *unspent* essence

# Crystal tier climbs as upgrades are bought (each LEVEL counts) and every
# prestige adds another tier, capped so there's always room to grow.
CRYSTAL_MAX_TIER = 6
CRYSTAL_LEVELS_PER_TIER = 3

# Offline earnings tuning — tunable at runtime by talents.
DEFAULT_OFFLINE_EFFICIENCY = 0.5
DEFAULT_OFFLINE_CAP_SECONDS = 8 * 60 * 60

# Onboarding stages.
ONBOARDING_UNSEEN = 0
ONBOARDING_POST_CLICK = 1
ONBOARDING_POST_BUY = 2
ONBOARDING_DONE = 3


def default_settings() -> dict:
    return {
        "sfx_volume": 0.6,
        "music_volume": 0.4,
        "screen_shake": True,
        "reduced_motion": False,
    }


@dataclass
class GameState:
    # Wallet and running totals.
    shards: float = 0.0
    total_earned: float = 0.0
    total_clicks: int = 0

    owned: dict[str, int] = field(default_factory=dict)
    upgrade_levels: dict[str, int] = field(default_factory=dict)

    # Prestige state — essence is *spendable*. total_essence_earned is the
    # display stat and drives achievements.
    essence: int = 0
    total_essence_earned: int = 0
    last_descend_total: float = 0.0
    prestige_count: int = 0

    # Permanent meta-progress.
    talent_levels: dict[str, int] = field(default_factory=dict)
    achievements: set[str] = field(default_factory=set)

    # Lifetime stats that prestige doesn't reset.
    playtime_seconds: float = 0.0
    total_generators_bought: int = 0
    best_descent_essence: int = 0
    bosses_defeated: int = 0

    # UI / onboarding state.
    onboarding_stage: int = ONBOARDING_UNSEEN

    settings: dict = field(default_factory=default_settings)

    last_saved_at: float = 0.0

    # ------------------------------------------------------------------
    # Talent helpers.
    # ------------------------------------------------------------------

    def talent_level(self, key: str) -> int:
        return self.talent_levels.get(key, 0)

    def talent_is_maxed(self, key: str) -> bool:
        t = TALENTS_BY_KEY.get(key)
        return t is not None and self.talent_level(key) >= t.max_level

    def next_talent_cost(self, key: str) -> int | None:
        t = TALENTS_BY_KEY.get(key)
        if t is None:
            return None
        level = self.talent_level(key)
        if level >= t.max_level:
            return None
        return talent_level_cost(t, level + 1)

    def can_afford_talent(self, key: str) -> bool:
        cost = self.next_talent_cost(key)
        return cost is not None and self.essence >= cost

    def buy_talent(self, key: str) -> bool:
        if not self.can_afford_talent(key):
            return False
        cost = self.next_talent_cost(key)
        assert cost is not None
        self.essence -= cost
        self.talent_levels[key] = self.talent_level(key) + 1
        return True

    def _talent_value(self, effect: str) -> float:
        """Sum the `effect`-typed talent values across all owned levels."""
        total = 0.0
        for key, level in self.talent_levels.items():
            t = TALENTS_BY_KEY.get(key)
            if t and t.effect == effect and level > 0:
                total += t.value * level
        return total

    # ------------------------------------------------------------------
    # Upgrade helpers.
    # ------------------------------------------------------------------

    def upgrade_level(self, key: str) -> int:
        return self.upgrade_levels.get(key, 0)

    def upgrade_is_maxed(self, key: str) -> bool:
        upgrade = UPGRADES_BY_KEY.get(key)
        return upgrade is not None and self.upgrade_level(key) >= upgrade.max_level

    def next_upgrade_cost(self, key: str) -> float | None:
        upgrade = UPGRADES_BY_KEY.get(key)
        if upgrade is None:
            return None
        level = self.upgrade_level(key)
        if level >= upgrade.max_level:
            return None
        return upgrade_cost_for_level(upgrade, level + 1)

    def total_upgrade_levels(self) -> int:
        return sum(self.upgrade_levels.values())

    # ------------------------------------------------------------------
    # Derived values.
    # ------------------------------------------------------------------

    def click_power(self) -> float:
        power = 1.0
        for key, level in self.upgrade_levels.items():
            upgrade = UPGRADES_BY_KEY.get(key)
            if upgrade and upgrade.effect == "click" and level > 0:
                power *= upgrade.multiplier ** level
        # Talent: flat +X% click per level, stacks additively.
        power *= 1.0 + self._talent_value("click")
        return power * self._global_multiplier()

    def crit_chance(self) -> float:
        """Probability a click deals 5x — set by the crit_study talent."""
        return min(1.0, self._talent_value("crit_chance"))

    def generator_rate(self, gen: GeneratorDef) -> float:
        rate = gen.base_production
        effect_key = f"gen:{gen.key}"
        for key, level in self.upgrade_levels.items():
            upgrade = UPGRADES_BY_KEY.get(key)
            if upgrade and upgrade.effect == effect_key and level > 0:
                rate *= upgrade.multiplier ** level
        # Talent: Cavern Whisper buffs the lowest-tier helper the player owns.
        owned_tiers = [g for g in GENERATORS if self.owned.get(g.key, 0) > 0]
        if owned_tiers and gen is owned_tiers[0]:
            rate *= 1.0 + self._talent_value("lowest_tier_boost")
        # Idle-branch flat bonus.
        rate *= 1.0 + self._talent_value("idle")
        return rate * self._global_multiplier()

    def generator_total_rate(self, gen: GeneratorDef) -> float:
        return self.generator_rate(gen) * self.owned.get(gen.key, 0)

    def total_rate(self) -> float:
        return sum(self.generator_total_rate(g) for g in GENERATORS)

    def essence_multiplier(self) -> float:
        # Only *unspent* essence contributes to passive income; spending
        # on talents is a genuine opportunity cost.
        return 1.0 + ESSENCE_PER_BONUS * self.essence

    def offline_efficiency(self) -> float:
        return DEFAULT_OFFLINE_EFFICIENCY + self._talent_value("offline")

    def offline_cap_seconds(self) -> float:
        return DEFAULT_OFFLINE_CAP_SECONDS + self._talent_value("offline_cap")

    def event_rate_multiplier(self) -> float:
        """Random-event spawn rate modifier from the lucky_strike talent."""
        return 1.0 + self._talent_value("event_rate")

    def essence_bonus_multiplier(self) -> float:
        return 1.0 + self._talent_value("essence_bonus")

    def start_bonus_shards(self) -> float:
        """Shards granted on a fresh run (after descent). Talent-driven."""
        base = self._talent_value("start_bonus")
        # Scale with sqrt(prestige+1) so later runs grow, but not wildly.
        return base * math.sqrt(self.prestige_count + 1)

    def _global_multiplier(self) -> float:
        mult = self.essence_multiplier()
        for key, level in self.upgrade_levels.items():
            upgrade = UPGRADES_BY_KEY.get(key)
            if upgrade and upgrade.effect == "global" and level > 0:
                mult *= upgrade.multiplier ** level
        return mult

    def crystal_tier(self) -> int:
        tier = self.total_upgrade_levels() // CRYSTAL_LEVELS_PER_TIER
        tier += self.prestige_count
        return min(tier, CRYSTAL_MAX_TIER)

    # ------------------------------------------------------------------
    # Mutations.
    # ------------------------------------------------------------------

    def click(self, *, crit_roll: float | None = None) -> tuple[float, bool]:
        """Register a click. Returns (gained, was_crit).

        If ``crit_roll`` is None, the RNG is consulted; tests pass a
        deterministic value to pin down behavior.
        """
        base = self.click_power()
        crit = False
        chance = self.crit_chance()
        if chance > 0:
            import random
            roll = random.random() if crit_roll is None else crit_roll
            if roll < chance:
                base *= 5.0
                crit = True
        self.shards += base
        self.total_earned += base
        self.total_clicks += 1
        return base, crit

    def tick(self, delta_seconds: float) -> float:
        if delta_seconds <= 0:
            return 0.0
        gained = self.total_rate() * delta_seconds
        self.shards += gained
        self.total_earned += gained
        return gained

    def can_afford_generator(self, gen: GeneratorDef) -> bool:
        return self.shards >= cost_for(gen, self.owned.get(gen.key, 0))

    def buy_generator(self, gen: GeneratorDef) -> bool:
        owned_count = self.owned.get(gen.key, 0)
        price = cost_for(gen, owned_count)
        if self.shards < price:
            return False
        self.shards -= price
        self.owned[gen.key] = owned_count + 1
        self.total_generators_bought += 1
        return True

    def can_afford_upgrade(self, upgrade_key: str) -> bool:
        upgrade = UPGRADES_BY_KEY.get(upgrade_key)
        if upgrade is None or self.upgrade_is_maxed(upgrade_key):
            return False
        if upgrade.requires_key is not None:
            if self.owned.get(upgrade.requires_key, 0) < upgrade.requires_count:
                return False
        cost = self.next_upgrade_cost(upgrade_key)
        return cost is not None and self.shards >= cost

    def is_upgrade_visible(self, upgrade_key: str) -> bool:
        upgrade = UPGRADES_BY_KEY.get(upgrade_key)
        if upgrade is None:
            return False
        if self.upgrade_level(upgrade_key) > 0:
            return True
        if upgrade.requires_key is None:
            return True
        return self.owned.get(upgrade.requires_key, 0) >= upgrade.requires_count

    def buy_upgrade(self, upgrade_key: str) -> bool:
        if not self.can_afford_upgrade(upgrade_key):
            return False
        cost = self.next_upgrade_cost(upgrade_key)
        assert cost is not None
        self.shards -= cost
        self.upgrade_levels[upgrade_key] = self.upgrade_level(upgrade_key) + 1
        return True

    def is_generator_unlocked(self, gen: GeneratorDef) -> bool:
        if self.owned.get(gen.key, 0) > 0:
            return True
        idx = GENERATORS.index(gen)
        if idx == 0:
            return True
        return self.total_earned >= gen.base_cost * 0.25

    # ------------------------------------------------------------------
    # Prestige / descent.
    # ------------------------------------------------------------------

    def pending_essence(self) -> int:
        progress = max(0.0, self.total_earned - self.last_descend_total)
        if progress <= 0:
            return 0
        raw = math.floor(math.sqrt(progress / ESSENCE_THRESHOLD))
        # Talent boost rounds to nearest; players see a clean integer reward.
        boosted = raw * self.essence_bonus_multiplier()
        return int(math.floor(boosted))

    def can_descend(self) -> bool:
        return self.pending_essence() >= 1

    def descend(self) -> int:
        gained = self.pending_essence()
        if gained <= 0:
            return 0
        self.essence += gained
        self.total_essence_earned += gained
        if gained > self.best_descent_essence:
            self.best_descent_essence = gained
        self.last_descend_total = self.total_earned
        self.prestige_count += 1
        self.shards = self.start_bonus_shards()  # talent bonus seeds the run
        self.owned = {}
        self.upgrade_levels = {}
        return gained

    # ------------------------------------------------------------------
    # Serialization.
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "version": 4,
            "shards": self.shards,
            "total_earned": self.total_earned,
            "total_clicks": self.total_clicks,
            "owned": dict(self.owned),
            "upgrade_levels": dict(self.upgrade_levels),
            "essence": self.essence,
            "total_essence_earned": self.total_essence_earned,
            "last_descend_total": self.last_descend_total,
            "prestige_count": self.prestige_count,
            "talent_levels": dict(self.talent_levels),
            "achievements": sorted(self.achievements),
            "playtime_seconds": self.playtime_seconds,
            "total_generators_bought": self.total_generators_bought,
            "best_descent_essence": self.best_descent_essence,
            "bosses_defeated": self.bosses_defeated,
            "onboarding_stage": self.onboarding_stage,
            "settings": dict(self.settings),
            "last_saved_at": self.last_saved_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        owned_raw = data.get("owned", {}) or {}
        owned = {k: int(v) for k, v in owned_raw.items() if k in GENERATORS_BY_KEY}

        # Upgrades — migrate old list-of-keys format to levels.
        if "upgrade_levels" in data:
            levels_raw = data.get("upgrade_levels") or {}
        else:
            legacy = data.get("purchased_upgrades") or []
            levels_raw = {k: 1 for k in legacy}
        levels = {
            k: max(0, int(v)) for k, v in levels_raw.items() if k in UPGRADES_BY_KEY
        }
        for k, v in list(levels.items()):
            levels[k] = min(v, UPGRADES_BY_KEY[k].max_level)

        # Talents.
        talents_raw = data.get("talent_levels") or {}
        talents = {
            k: max(0, int(v)) for k, v in talents_raw.items() if k in TALENTS_BY_KEY
        }
        for k, v in list(talents.items()):
            talents[k] = min(v, TALENTS_BY_KEY[k].max_level)

        achievements = set(data.get("achievements") or [])

        settings = dict(default_settings())
        for k, v in (data.get("settings") or {}).items():
            if k in settings:
                settings[k] = v

        essence = int(data.get("essence", 0))
        # Older saves don't track the lifetime total — seed from current
        # unspent balance so prestige achievements still behave sensibly.
        total_essence_earned = int(data.get("total_essence_earned", essence))

        return cls(
            shards=float(data.get("shards", 0.0)),
            total_earned=float(data.get("total_earned", 0.0)),
            total_clicks=int(data.get("total_clicks", 0)),
            owned=owned,
            upgrade_levels=levels,
            essence=essence,
            total_essence_earned=total_essence_earned,
            last_descend_total=float(data.get("last_descend_total", 0.0)),
            prestige_count=int(data.get("prestige_count", 0)),
            talent_levels=talents,
            achievements=achievements,
            playtime_seconds=float(data.get("playtime_seconds", 0.0)),
            total_generators_bought=int(data.get("total_generators_bought", 0)),
            best_descent_essence=int(data.get("best_descent_essence", 0)),
            bosses_defeated=int(data.get("bosses_defeated", 0)),
            onboarding_stage=int(data.get("onboarding_stage", ONBOARDING_DONE)),
            settings=settings,
            last_saved_at=float(data.get("last_saved_at", 0.0)),
        )
