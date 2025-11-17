from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional


@dataclass
class DiceExpression:
    """Represents a numeric value that may involve dice (e.g., 2D6+1).

    The :meth:`roll` method executes the dice expression for a single trial.
    """

    raw: str

    dice_pattern = re.compile(r"^(?:(?P<count>\d*)d(?P<faces>\d+))(?P<modifier>[+-]\d+)?$", re.IGNORECASE)

    def roll(self) -> int:
        cleaned = self.raw.strip().lower()
        if cleaned.isdigit():
            return int(cleaned)

        match = self.dice_pattern.match(cleaned)
        if not match:
            raise ValueError(f"Unsupported dice expression: {self.raw}")

        count_str = match.group("count")
        faces = int(match.group("faces"))
        modifier_str = match.group("modifier")

        count = int(count_str) if count_str else 1
        modifier = int(modifier_str) if modifier_str else 0

        total = modifier
        for _ in range(count):
            total += random.randint(1, faces)
        return total

    @classmethod
    def from_value(cls, value: str | int | float) -> "DiceExpression":
        if isinstance(value, (int, float)):
            return cls(str(int(value)))
        return cls(str(value))


@dataclass
class AttackModifiers:
    hit_modifier: int = 0
    wound_modifier: int = 0
    ap_modifier: int = 0
    damage_modifier: int = 0
    crit_hit_threshold: int = 6
    crit_wound_threshold: int = 6


@dataclass
class SaveProfile:
    armour: int
    invulnerable: Optional[int] = None
    feel_no_pain: Optional[int] = None


@dataclass
class WeaponProfile:
    name: str
    attacks: DiceExpression
    skill: int
    strength: int
    ap: int
    damage: DiceExpression
    is_melee: bool = False
    keywords: List[str] = field(default_factory=list)


@dataclass
class UnitProfile:
    name: str
    toughness: int
    wounds: int
    save: SaveProfile
    weapons: List[WeaponProfile] = field(default_factory=list)


@dataclass
class AttackStatistics:
    hits: int = 0
    crit_hits: int = 0
    wounds: int = 0
    crit_wounds: int = 0
    failed_saves: int = 0


@dataclass
class SimulationResult:
    attacker: str
    defender: str
    weapon: str
    iterations: int
    damage_distribution: List[int]
    kills: int
    stats: AttackStatistics

    @property
    def average_damage(self) -> float:
        return sum(self.damage_distribution) / self.iterations

    @property
    def kill_probability(self) -> float:
        return self.kills / self.iterations


def percentile(values: Iterable[int], percent: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = (len(ordered) - 1) * (percent / 100)
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight
