from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .battlescribe_loader import load_unit_from_catalogue
from .combat import run_simulation
from .models import AttackModifiers, DiceExpression, SaveProfile, UnitProfile, WeaponProfile


DEFAULT_ITERATIONS = 5000


def fallback_units() -> tuple[UnitProfile, WeaponProfile, UnitProfile]:
    attacker = UnitProfile(
        name="Demo Captain",
        toughness=4,
        wounds=5,
        save=SaveProfile(armour=2, invulnerable=4),
    )
    weapon = WeaponProfile(
        name="Tempest Blade",
        attacks=DiceExpression.from_value("6"),
        skill=2,
        strength=5,
        ap=-2,
        damage=DiceExpression.from_value("2"),
        is_melee=True,
        keywords=["Lethal Hits"],
    )
    target = UnitProfile(
        name="Demo Termagant",
        toughness=3,
        wounds=1,
        save=SaveProfile(armour=5),
    )
    attacker.weapons.append(weapon)
    return attacker, weapon, target


def build_units(args: argparse.Namespace) -> tuple[UnitProfile, WeaponProfile, UnitProfile]:
    try:
        attacker_loaded = load_unit_from_catalogue(args.attacker_catalogue, args.attacker, [args.weapon])
        defender_loaded = load_unit_from_catalogue(args.defender_catalogue, args.defender, [])
        weapon = attacker_loaded.weapons[0]
        return attacker_loaded.unit, weapon, defender_loaded.unit
    except Exception as exc:  # pragma: no cover - defensive fallback for datasets
        print(f"Falling back to demo profiles because: {exc}")
        return fallback_units()


def parse_modifiers(args: argparse.Namespace) -> AttackModifiers:
    return AttackModifiers(
        hit_modifier=args.hit_mod,
        wound_modifier=args.wound_mod,
        ap_modifier=args.ap_mod,
        damage_modifier=args.damage_mod,
        crit_hit_threshold=args.crit_hit,
        crit_wound_threshold=args.crit_wound,
    )


def plot_results(result, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(result.damage_distribution, bins=20, alpha=0.7, color="#1976d2")
    ax.set_title(f"{result.attacker} using {result.weapon} vs {result.defender}")
    ax.set_xlabel("Damage inflicted")
    ax.set_ylabel("Iterations")
    ax.axvline(result.average_damage, color="red", linestyle="--", label=f"Avg: {result.average_damage:.2f}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run a 10th edition combat simulation")
    parser.add_argument("--attacker-catalogue", default="Imperium - Ultramarines.cat")
    parser.add_argument("--attacker", default="Captain Sicarius")
    parser.add_argument("--weapon", default="Talassarian Tempest Blade")
    parser.add_argument("--defender-catalogue", default="Tyranids.cat")
    parser.add_argument("--defender", default="Termagants")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--output", type=Path, default=Path("simulation.png"))
    parser.add_argument("--hit-mod", type=int, default=0)
    parser.add_argument("--wound-mod", type=int, default=0)
    parser.add_argument("--ap-mod", type=int, default=0)
    parser.add_argument("--damage-mod", type=int, default=0)
    parser.add_argument("--crit-hit", type=int, default=6)
    parser.add_argument("--crit-wound", type=int, default=6)

    args = parser.parse_args(argv)

    attacker, weapon, defender = build_units(args)
    modifiers = parse_modifiers(args)

    result = run_simulation(attacker, weapon, defender, modifiers, iterations=args.iterations)

    summary = {
        "attacker": result.attacker,
        "defender": result.defender,
        "weapon": result.weapon,
        "iterations": result.iterations,
        "average_damage": result.average_damage,
        "kill_probability": result.kill_probability,
        "hits": result.stats.hits,
        "crit_hits": result.stats.crit_hits,
        "wounds": result.stats.wounds,
        "crit_wounds": result.stats.crit_wounds,
        "failed_saves": result.stats.failed_saves,
    }

    print(json.dumps(summary, indent=2))
    plot_results(result, args.output)
    print(f"Saved histogram to {args.output}")


if __name__ == "__main__":
    main()
