"""The canonical mutable game state.

Deliberately kept plain-Python and serializable so save/load and tests can
treat it as a dumb data bag. Anything not trivially JSON-safe (textures,
sprite objects, timers) lives on the game *view*, not here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.generators import GENERATORS, GENERATORS_BY_KEY, GeneratorDef, cost_for
from src.upgrades import UPGRADES_BY_KEY


@dataclass
class GameState:
    # Wallet and running totals.
    shards: float = 0.0
    total_earned: float = 0.0
    total_clicks: int = 0

    # How many of each generator the player owns, keyed by GeneratorDef.key.
    owned: dict[str, int] = field(default_factory=dict)

    # Upgrades the player has purchased, keyed by UpgradeDef.key.
    purchased_upgrades: set[str] = field(default_factory=set)

    # Wall-clock seconds since the epoch for the most recent save. Used to
    # compute offline earnings when a save is loaded.
    last_saved_at: float = 0.0

    # ------------------------------------------------------------------
    # Derived values — cheap enough to compute on demand each frame.
    # ------------------------------------------------------------------

    def click_power(self) -> float:
        """Shards earned per manual tap of the main crystal."""
        power = 1.0
        for key in self.purchased_upgrades:
            upgrade = UPGRADES_BY_KEY.get(key)
            if upgrade and upgrade.effect == "click":
                power *= upgrade.multiplier
        return power * self._global_multiplier()

    def generator_rate(self, gen: GeneratorDef) -> float:
        """Shards/sec produced by ONE unit of `gen`, including all upgrades."""
        rate = gen.base_production
        effect_key = f"gen:{gen.key}"
        for key in self.purchased_upgrades:
            upgrade = UPGRADES_BY_KEY.get(key)
            if upgrade and upgrade.effect == effect_key:
                rate *= upgrade.multiplier
        return rate * self._global_multiplier()

    def generator_total_rate(self, gen: GeneratorDef) -> float:
        """Shards/sec produced by ALL owned units of `gen`."""
        return self.generator_rate(gen) * self.owned.get(gen.key, 0)

    def total_rate(self) -> float:
        """Aggregate idle shards per second across every generator."""
        return sum(self.generator_total_rate(g) for g in GENERATORS)

    def _global_multiplier(self) -> float:
        mult = 1.0
        for key in self.purchased_upgrades:
            upgrade = UPGRADES_BY_KEY.get(key)
            if upgrade and upgrade.effect == "global":
                mult *= upgrade.multiplier
        return mult

    # ------------------------------------------------------------------
    # Mutations.
    # ------------------------------------------------------------------

    def click(self) -> float:
        """Register a click; return the shards earned from it."""
        gained = self.click_power()
        self.shards += gained
        self.total_earned += gained
        self.total_clicks += 1
        return gained

    def tick(self, delta_seconds: float) -> float:
        """Advance idle production by `delta_seconds`; return shards earned."""
        if delta_seconds <= 0:
            return 0.0
        gained = self.total_rate() * delta_seconds
        self.shards += gained
        self.total_earned += gained
        return gained

    def can_afford_generator(self, gen: GeneratorDef) -> bool:
        return self.shards >= cost_for(gen, self.owned.get(gen.key, 0))

    def buy_generator(self, gen: GeneratorDef) -> bool:
        """Purchase one unit of `gen`. Returns True on success."""
        owned_count = self.owned.get(gen.key, 0)
        price = cost_for(gen, owned_count)
        if self.shards < price:
            return False
        self.shards -= price
        self.owned[gen.key] = owned_count + 1
        return True

    def can_afford_upgrade(self, upgrade_key: str) -> bool:
        upgrade = UPGRADES_BY_KEY.get(upgrade_key)
        if upgrade is None or upgrade_key in self.purchased_upgrades:
            return False
        if upgrade.requires_key is not None:
            if self.owned.get(upgrade.requires_key, 0) < upgrade.requires_count:
                return False
        return self.shards >= upgrade.cost

    def is_upgrade_visible(self, upgrade_key: str) -> bool:
        """Whether an upgrade should appear in the shop (requirements met)."""
        upgrade = UPGRADES_BY_KEY.get(upgrade_key)
        if upgrade is None or upgrade_key in self.purchased_upgrades:
            return False
        if upgrade.requires_key is None:
            return True
        return self.owned.get(upgrade.requires_key, 0) >= upgrade.requires_count

    def buy_upgrade(self, upgrade_key: str) -> bool:
        if not self.can_afford_upgrade(upgrade_key):
            return False
        upgrade = UPGRADES_BY_KEY[upgrade_key]
        self.shards -= upgrade.cost
        self.purchased_upgrades.add(upgrade_key)
        return True

    def is_generator_unlocked(self, gen: GeneratorDef) -> bool:
        """Shop reveals tiers gradually so the early game isn't overwhelming."""
        if self.owned.get(gen.key, 0) > 0:
            return True
        # Always reveal the first tier.
        idx = GENERATORS.index(gen)
        if idx == 0:
            return True
        # Reveal a tier once the player has seen ~25% of its cost at any point.
        return self.total_earned >= gen.base_cost * 0.25

    # ------------------------------------------------------------------
    # Serialization.
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "shards": self.shards,
            "total_earned": self.total_earned,
            "total_clicks": self.total_clicks,
            "owned": dict(self.owned),
            "purchased_upgrades": sorted(self.purchased_upgrades),
            "last_saved_at": self.last_saved_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        # Ignore unknown generator/upgrade keys — avoids crashes if we rename
        # something in a future version of the game.
        owned_raw = data.get("owned", {}) or {}
        owned = {k: int(v) for k, v in owned_raw.items() if k in GENERATORS_BY_KEY}
        upgrades = {
            k for k in (data.get("purchased_upgrades") or []) if k in UPGRADES_BY_KEY
        }
        return cls(
            shards=float(data.get("shards", 0.0)),
            total_earned=float(data.get("total_earned", 0.0)),
            total_clicks=int(data.get("total_clicks", 0)),
            owned=owned,
            purchased_upgrades=upgrades,
            last_saved_at=float(data.get("last_saved_at", 0.0)),
        )
