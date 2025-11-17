from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .models import DiceExpression, SaveProfile, UnitProfile, WeaponProfile


BS_NS = {"bs": "http://www.battlescribe.net/schema/catalogueSchema"}


@dataclass
class LoadedUnit:
    unit: UnitProfile
    weapons: List[WeaponProfile]


def parse_int_from_characteristic(value: str) -> Optional[int]:
    match = re.match(r"(\d+)", value)
    return int(match.group(1)) if match else None


def parse_keywords(value: str | None) -> List[str]:
    if not value:
        return []
    return [kw.strip() for kw in value.split(",") if kw.strip()]


def _get_characteristic(profile: ET.Element, name: str) -> Optional[str]:
    for char in profile.findall("bs:characteristics/bs:characteristic", BS_NS):
        if char.get("name") == name:
            return (char.text or "").strip()
    return None


def load_weapon_profile(profile: ET.Element) -> Optional[WeaponProfile]:
    name = profile.get("name") or "Unnamed Weapon"
    type_name = (profile.get("typeName") or "").lower()

    attacks = _get_characteristic(profile, "A") or _get_characteristic(profile, "Attacks")
    strength = _get_characteristic(profile, "S") or _get_characteristic(profile, "Strength")
    ap = _get_characteristic(profile, "AP")
    damage = _get_characteristic(profile, "D") or _get_characteristic(profile, "Damage")
    skill = _get_characteristic(profile, "WS" if "melee" in type_name else "BS")

    if not all([attacks, strength, ap, damage, skill]):
        return None

    keyword_str = _get_characteristic(profile, "Keywords")
    return WeaponProfile(
        name=name,
        attacks=DiceExpression.from_value(attacks.replace("\u201d", "")),
        skill=parse_int_from_characteristic(skill) or 6,
        strength=int(parse_int_from_characteristic(strength) or 0),
        ap=int(ap),
        damage=DiceExpression.from_value(damage.replace("\u201d", "")),
        is_melee="melee" in type_name,
        keywords=parse_keywords(keyword_str),
    )


def load_unit_profile(profile: ET.Element, invulnerable: Optional[int], feel_no_pain: Optional[int]) -> UnitProfile:
    name = profile.get("name") or "Unnamed Unit"
    toughness = int(parse_int_from_characteristic(_get_characteristic(profile, "T") or "0") or 0)
    wounds = int(parse_int_from_characteristic(_get_characteristic(profile, "W") or "1") or 1)
    armour_str = _get_characteristic(profile, "SV") or "7+"
    armour = int(parse_int_from_characteristic(armour_str) or 7)

    save = SaveProfile(armour=armour, invulnerable=invulnerable, feel_no_pain=feel_no_pain)
    return UnitProfile(name=name, toughness=toughness, wounds=wounds, save=save)


def find_invulnerable_profile(root: ET.Element) -> Optional[int]:
    for profile in root.findall(".//bs:profile[@typeName='Invulnerable Save']", BS_NS):
        save_value = _get_characteristic(profile, "Save")
        parsed = parse_int_from_characteristic(save_value or "")
        if parsed:
            return parsed
    return None


def find_feel_no_pain(root: ET.Element) -> Optional[int]:
    for profile in root.findall(".//bs:profile[@typeName='Feel No Pain']", BS_NS):
        save_value = _get_characteristic(profile, "Save")
        parsed = parse_int_from_characteristic(save_value or "")
        if parsed:
            return parsed
    return None


def load_unit_from_catalogue(path: str | Path, unit_name: str, weapon_names: List[str]) -> LoadedUnit:
    tree = ET.parse(path)
    root = tree.getroot()

    invulnerable = find_invulnerable_profile(root)
    fnp = find_feel_no_pain(root)

    unit_profile_el = None
    for profile in root.findall(".//bs:profile[@typeName='Unit']", BS_NS):
        if (profile.get("name") or "").lower() == unit_name.lower():
            unit_profile_el = profile
            break

    if unit_profile_el is None:
        raise ValueError(f"Unit '{unit_name}' not found in {path}")

    weapons: List[WeaponProfile] = []
    for weapon_name in weapon_names:
        weapon_profile_el = None
        for profile in root.findall(".//bs:profile", BS_NS):
            if (profile.get("name") or "").lower() == weapon_name.lower() and "weapons" in (profile.get("typeName") or "").lower():
                weapon_profile_el = profile
                break
        if weapon_profile_el is None:
            raise ValueError(f"Weapon '{weapon_name}' not found in {path}")
        weapon = load_weapon_profile(weapon_profile_el)
        if weapon:
            weapons.append(weapon)

    unit = load_unit_profile(unit_profile_el, invulnerable=invulnerable, feel_no_pain=fnp)
    unit.weapons.extend(weapons)
    return LoadedUnit(unit=unit, weapons=weapons)
