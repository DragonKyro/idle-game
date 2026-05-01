"""The canonical mutable game state.

Deliberately kept plain-Python and serializable so save/load and tests can
treat it as a dumb data bag. Anything not trivially JSON-safe (textures,
sprite objects, timers) lives on the game *view*, not here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from src.generators import GENERATORS, GENERATORS_BY_KEY, GeneratorDef, cost_for
from src.upgrades import UPGRADES_BY_KEY, upgrade_cost_for_level


# Prestige tuning.
ESSENCE_THRESHOLD = 1e10
ESSENCE_PER_BONUS = 0.02  # 2% production per essence held

# Crystal tier climbs as upgrades are bought (each LEVEL counts) and every
# prestige adds another tier, capped so there's always room to grow.
CRYSTAL_MAX_TIER = 6
CRYSTAL_LEVELS_PER_TIER = 3


@dataclass
class GameState:
    # Wallet and running totals.
    shards: float = 0.0
    total_earned: float = 0.0  # lifetime; never resets on prestige
    total_clicks: int = 0

    # How many of each generator the player owns, keyed by GeneratorDef.key.
    owned: dict[str, int] = field(default_factory=dict)

    # Current level per upgrade key (missing / 0 means unpurchased).
    upgrade_levels: dict[str, int] = field(default_factory=dict)

    # Prestige state.
    essence: int = 0
    last_descend_total: float = 0.0
    prestige_count: int = 0

    last_saved_at: float = 0.0

    # ------------------------------------------------------------------
    # Upgrade helpers.
    # ------------------------------------------------------------------

    def upgrade_level(self, key: str) -> int:
        return self.upgrade_levels.get(key, 0)

    def upgrade_is_maxed(self, key: str) -> bool:
        upgrade = UPGRADES_BY_KEY.get(key)
        return upgrade is not None and self.upgrade_level(key) >= upgrade.max_level

    def next_upgrade_cost(self, key: str) -> float | None:
        """Cost to buy the next level of `key`, or None if already maxed."""
        upgrade = UPGRADES_BY_KEY.get(key)
        if upgrade is None:
            return None
        level = self.upgrade_level(key)
        if level >= upgrade.max_level:
            return None
        return upgrade_cost_for_level(upgrade, level + 1)

    def total_upgrade_levels(self) -> int:
        """Sum of levels across every upgrade — drives crystal tier."""
        return sum(self.upgrade_levels.values())

    # ------------------------------------------------------------------
    # Derived values — cheap enough to compute on demand each frame.
    # ------------------------------------------------------------------

    def click_power(self) -> float:
        power = 1.0
        for key, level in self.upgrade_levels.items():
            upgrade = UPGRADES_BY_KEY.get(key)
            if upgrade and upgrade.effect == "click" and level > 0:
                power *= upgrade.multiplier ** level
        return power * self._global_multiplier()

    def generator_rate(self, gen: GeneratorDef) -> float:
        rate = gen.base_production
        effect_key = f"gen:{gen.key}"
        for key, level in self.upgrade_levels.items():
            upgrade = UPGRADES_BY_KEY.get(key)
            if upgrade and upgrade.effect == effect_key and level > 0:
                rate *= upgrade.multiplier ** level
        return rate * self._global_multiplier()

    def generator_total_rate(self, gen: GeneratorDef) -> float:
        return self.generator_rate(gen) * self.owned.get(gen.key, 0)

    def total_rate(self) -> float:
        return sum(self.generator_total_rate(g) for g in GENERATORS)

    def essence_multiplier(self) -> float:
        return 1.0 + ESSENCE_PER_BONUS * self.essence

    def _global_multiplier(self) -> float:
        mult = self.essence_multiplier()
        for key, level in self.upgrade_levels.items():
            upgrade = UPGRADES_BY_KEY.get(key)
            if upgrade and upgrade.effect == "global" and level > 0:
                mult *= upgrade.multiplier ** level
        return mult

    def crystal_tier(self) -> int:
        """Which crystal appearance to show. Driven by total upgrade levels
        purchased plus prestige count."""
        tier = self.total_upgrade_levels() // CRYSTAL_LEVELS_PER_TIER
        tier += self.prestige_count
        return min(tier, CRYSTAL_MAX_TIER)

    # ------------------------------------------------------------------
    # Mutations.
    # ------------------------------------------------------------------

    def click(self) -> float:
        gained = self.click_power()
        self.shards += gained
        self.total_earned += gained
        self.total_clicks += 1
        return gained

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
        """Whether the upgrade row should appear in the shop.

        Maxed upgrades stay visible (as dimmed "MAX" rows) so completionists
        can see their full catalog progress. Unpurchased upgrades only appear
        once their generator requirement is met.
        """
        upgrade = UPGRADES_BY_KEY.get(upgrade_key)
        if upgrade is None:
            return False
        if self.upgrade_level(upgrade_key) > 0:
            return True
        if upgrade.requires_key is None:
            return True
        return self.owned.get(upgrade.requires_key, 0) >= upgrade.requires_count

    def buy_upgrade(self, upgrade_key: str) -> bool:
        """Purchase the next level of `upgrade_key`. Returns True on success."""
        if not self.can_afford_upgrade(upgrade_key):
            return False
        cost = self.next_upgrade_cost(upgrade_key)
        assert cost is not None  # guarded by can_afford_upgrade
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
        return int(math.floor(math.sqrt(progress / ESSENCE_THRESHOLD)))

    def can_descend(self) -> bool:
        return self.pending_essence() >= 1

    def descend(self) -> int:
        gained = self.pending_essence()
        if gained <= 0:
            return 0
        self.essence += gained
        self.last_descend_total = self.total_earned
        self.prestige_count += 1
        self.shards = 0.0
        self.owned = {}
        self.upgrade_levels = {}
        return gained

    # ------------------------------------------------------------------
    # Serialization.
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "version": 3,
            "shards": self.shards,
            "total_earned": self.total_earned,
            "total_clicks": self.total_clicks,
            "owned": dict(self.owned),
            "upgrade_levels": dict(self.upgrade_levels),
            "essence": self.essence,
            "last_descend_total": self.last_descend_total,
            "prestige_count": self.prestige_count,
            "last_saved_at": self.last_saved_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        owned_raw = data.get("owned", {}) or {}
        owned = {k: int(v) for k, v in owned_raw.items() if k in GENERATORS_BY_KEY}

        # v1/v2 saves used purchased_upgrades (a set of keys). v3 uses
        # upgrade_levels. Migrate transparently so old saves still load.
        if "upgrade_levels" in data:
            levels_raw = data.get("upgrade_levels") or {}
        else:
            legacy = data.get("purchased_upgrades") or []
            levels_raw = {k: 1 for k in legacy}
        levels = {
            k: max(0, int(v)) for k, v in levels_raw.items() if k in UPGRADES_BY_KEY
        }
        # Clamp to max_level in case an upgrade's cap was lowered after save.
        for k, v in list(levels.items()):
            levels[k] = min(v, UPGRADES_BY_KEY[k].max_level)

        return cls(
            shards=float(data.get("shards", 0.0)),
            total_earned=float(data.get("total_earned", 0.0)),
            total_clicks=int(data.get("total_clicks", 0)),
            owned=owned,
            upgrade_levels=levels,
            essence=int(data.get("essence", 0)),
            last_descend_total=float(data.get("last_descend_total", 0.0)),
            prestige_count=int(data.get("prestige_count", 0)),
            last_saved_at=float(data.get("last_saved_at", 0.0)),
        )
