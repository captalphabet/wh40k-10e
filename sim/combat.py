from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, Tuple

from .models import AttackModifiers, AttackStatistics, DiceExpression, SaveProfile, SimulationResult, UnitProfile, WeaponProfile


@dataclass
class AttackOutcome:
    damage: int
    kills: int
    stats: AttackStatistics


def roll_d6() -> int:
    return random.randint(1, 6)


def calculate_wound_target(strength: int, toughness: int) -> int:
    if strength >= toughness * 2:
        return 2
    if strength > toughness:
        return 3
    if strength == toughness:
        return 4
    if strength * 2 <= toughness:
        return 6
    return 5


def apply_save(save: SaveProfile, ap: int, damage: int) -> int:
    effective_save = save.armour - ap
    if save.invulnerable:
        effective_save = min(effective_save, save.invulnerable)
    effective_save = max(2, min(6, effective_save))

    save_roll = roll_d6()
    if save_roll >= effective_save:
        return 0
    return damage


def apply_feel_no_pain(damage: int, feel_no_pain: int | None) -> int:
    if not feel_no_pain:
        return damage

    prevented = 0
    for _ in range(damage):
        if roll_d6() >= feel_no_pain:
            prevented += 1
    return damage - prevented


def roll_to_hit(weapon: WeaponProfile, modifiers: AttackModifiers) -> Tuple[bool, bool]:
    roll = roll_d6()
    is_crit = roll >= modifiers.crit_hit_threshold
    modified = roll + modifiers.hit_modifier
    return modified >= weapon.skill, is_crit


def roll_to_wound(weapon: WeaponProfile, defender: UnitProfile, modifiers: AttackModifiers) -> Tuple[bool, bool]:
    target = calculate_wound_target(weapon.strength, defender.toughness)
    roll = roll_d6()
    is_crit = roll >= modifiers.crit_wound_threshold
    modified = roll + modifiers.wound_modifier
    return modified >= target, is_crit


def resolve_attack(weapon: WeaponProfile, attacker: UnitProfile, defender: UnitProfile, modifiers: AttackModifiers) -> AttackOutcome:
    stats = AttackStatistics()
    total_damage = 0
    kills = 0

    attack_count = weapon.attacks.roll()
    for _ in range(attack_count):
        success_hit, crit_hit = roll_to_hit(weapon, modifiers)
        if success_hit:
            stats.hits += 1
            if crit_hit:
                stats.crit_hits += 1

            auto_wound = crit_hit and any(k.lower() == "lethal hits" for k in weapon.keywords)
            success_wound = False
            crit_wound = False
            if auto_wound:
                success_wound = True
                crit_wound = True
            else:
                success_wound, crit_wound = roll_to_wound(weapon, defender, modifiers)

            if success_wound:
                stats.wounds += 1
                if crit_wound:
                    stats.crit_wounds += 1
                adjusted_ap = weapon.ap + modifiers.ap_modifier
                raw_damage = max(1, weapon.damage.roll() + modifiers.damage_modifier)
                unsaved = apply_save(defender.save, adjusted_ap, raw_damage)
                if unsaved:
                    stats.failed_saves += 1
                    final_damage = apply_feel_no_pain(unsaved, defender.save.feel_no_pain)
                    total_damage += final_damage
                    if final_damage >= defender.wounds:
                        kills += 1

    return AttackOutcome(damage=total_damage, kills=kills, stats=stats)


def run_simulation(attacker: UnitProfile, weapon: WeaponProfile, defender: UnitProfile, modifiers: AttackModifiers, iterations: int = 10000) -> SimulationResult:
    damage_rolls: list[int] = []
    total_kills = 0
    aggregate_stats = AttackStatistics()

    for _ in range(iterations):
        outcome = resolve_attack(weapon, attacker, defender, modifiers)
        damage_rolls.append(outcome.damage)
        total_kills += min(outcome.kills, 1)
        aggregate_stats.hits += outcome.stats.hits
        aggregate_stats.crit_hits += outcome.stats.crit_hits
        aggregate_stats.wounds += outcome.stats.wounds
        aggregate_stats.crit_wounds += outcome.stats.crit_wounds
        aggregate_stats.failed_saves += outcome.stats.failed_saves

    return SimulationResult(
        attacker=attacker.name,
        defender=defender.name,
        weapon=weapon.name,
        iterations=iterations,
        damage_distribution=damage_rolls,
        kills=total_kills,
        stats=aggregate_stats,
    )
