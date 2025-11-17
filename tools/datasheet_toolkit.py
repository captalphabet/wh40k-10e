#!/usr/bin/env python3
"""
Utilities for parsing datasheets from BattleScribe catalogues.

Example usage:
    python tools/datasheet_toolkit.py --catalogue "Chaos - Chaos Space Marines.cat" --unit "Abaddon the Despoiler"
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import xml.etree.ElementTree as ET

CATALOGUE_NS = "http://www.battlescribe.net/schema/catalogueSchema"
GAME_SYSTEM_NS = "http://www.battlescribe.net/schema/gameSystemSchema"


def tag(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


@dataclass
class ProfileDefinition:
    id: str
    name: str
    characteristic_names: List[str]


@dataclass
class CostType:
    id: str
    name: str


@dataclass
class Profile:
    name: str
    type_id: str
    type_name: str
    characteristics: Dict[str, str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "type_id": self.type_id,
            "type_name": self.type_name,
            "characteristics": self.characteristics,
        }


@dataclass
class SelectionNode:
    id: str
    name: str
    type: str
    categories: List[str]
    costs: Dict[str, float]
    profiles: List[Profile] = field(default_factory=list)
    children: List["SelectionNode"] = field(default_factory=list)
    linked_from: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "linked_from": self.linked_from,
            "categories": self.categories,
            "costs": self.costs,
            "profiles": [profile.to_dict() for profile in self.profiles],
            "children": [child.to_dict() for child in self.children],
        }


class CatalogueParser:
    def __init__(self, game_system_path: Path):
        self.profile_definitions = self._load_profile_definitions(game_system_path)
        self.cost_types = self._load_cost_types(game_system_path)

    def _load_profile_definitions(self, game_system_path: Path) -> Dict[str, ProfileDefinition]:
        tree = ET.parse(game_system_path)
        root = tree.getroot()
        definitions: Dict[str, ProfileDefinition] = {}

        for profile_type in root.findall(tag(GAME_SYSTEM_NS, "profileType")):
            char_types = profile_type.find(tag(GAME_SYSTEM_NS, "characteristicTypes"))
            characteristic_names = []
            if char_types is not None:
                for char_type in char_types.findall(tag(GAME_SYSTEM_NS, "characteristicType")):
                    characteristic_names.append(char_type.attrib["name"])

            definition = ProfileDefinition(
                id=profile_type.attrib["id"],
                name=profile_type.attrib["name"],
                characteristic_names=characteristic_names,
            )
            definitions[definition.id] = definition

        return definitions

    def _load_cost_types(self, game_system_path: Path) -> Dict[str, CostType]:
        tree = ET.parse(game_system_path)
        root = tree.getroot()
        cost_types: Dict[str, CostType] = {}

        for cost_type in root.findall(tag(GAME_SYSTEM_NS, "costType")):
            definition = CostType(id=cost_type.attrib["id"], name=cost_type.attrib["name"])
            cost_types[definition.id] = definition

        return cost_types

    def parse_catalogue(self, catalogue_path: Path) -> ET.Element:
        tree = ET.parse(catalogue_path)
        return tree.getroot()

    def find_unit_entry(self, catalogue_root: ET.Element, name: str) -> Optional[ET.Element]:
        name_lower = name.casefold()
        for entry in catalogue_root.findall(f".//{tag(CATALOGUE_NS, 'selectionEntry')}"):
            if entry.attrib.get("type") not in {"unit", "model"}:
                continue
            if entry.attrib.get("name", "").casefold() == name_lower:
                return entry
        return None

    def build_selection_index(self, catalogue_root: ET.Element) -> Dict[str, ET.Element]:
        index: Dict[str, ET.Element] = {}
        for entry in catalogue_root.findall(f".//{tag(CATALOGUE_NS, 'selectionEntry')}"):
            entry_id = entry.attrib.get("id")
            if entry_id:
                index[entry_id] = entry
        return index

    def parse_profiles(self, element: ET.Element) -> List[Profile]:
        profiles: List[Profile] = []
        profiles_el = element.find(tag(CATALOGUE_NS, "profiles"))
        if profiles_el is None:
            return profiles

        for profile_el in profiles_el.findall(tag(CATALOGUE_NS, "profile")):
            type_id = profile_el.attrib.get("typeId", "")
            profile_def = self.profile_definitions.get(type_id)
            characteristics: Dict[str, str] = {}

            characteristics_el = profile_el.find(tag(CATALOGUE_NS, "characteristics"))
            if characteristics_el is not None:
                for characteristic in characteristics_el.findall(tag(CATALOGUE_NS, "characteristic")):
                    characteristics[characteristic.attrib["name"]] = (characteristic.text or "").strip()

            profiles.append(
                Profile(
                    name=profile_el.attrib.get("name", ""),
                    type_id=type_id,
                    type_name=profile_el.attrib.get("typeName", profile_def.name if profile_def else ""),
                    characteristics=characteristics,
                )
            )

        return profiles

    def parse_categories(self, element: ET.Element) -> List[str]:
        categories: List[str] = []
        category_links_el = element.find(tag(CATALOGUE_NS, "categoryLinks"))
        if category_links_el is None:
            return categories

        for category_link in category_links_el.findall(tag(CATALOGUE_NS, "categoryLink")):
            categories.append(category_link.attrib.get("name", ""))
        return categories

    def parse_costs(self, element: ET.Element) -> Dict[str, float]:
        costs: Dict[str, float] = {}
        costs_el = element.find(tag(CATALOGUE_NS, "costs"))
        if costs_el is None:
            return costs

        for cost_el in costs_el.findall(tag(CATALOGUE_NS, "cost")):
            cost_type_id = cost_el.attrib.get("costTypeId", "")
            value_str = cost_el.attrib.get("value", "0")
            try:
                value = float(value_str)
            except ValueError:
                value = 0.0
            type_name = self.cost_types.get(cost_type_id, CostType(id=cost_type_id, name=cost_type_id)).name
            costs[type_name] = value
        return costs

    def parse_selection_entry(
        self,
        element: ET.Element,
        selection_index: Dict[str, ET.Element],
        linked_from: Optional[str] = None,
        visited: Optional[Iterable[str]] = None,
    ) -> SelectionNode:
        visited_ids = set(visited or [])
        entry_id = element.attrib.get("id", "")
        visited_ids.add(entry_id)

        node = SelectionNode(
            id=entry_id,
            name=element.attrib.get("name", ""),
            type=element.attrib.get("type", ""),
            linked_from=linked_from,
            categories=self.parse_categories(element),
            costs=self.parse_costs(element),
            profiles=self.parse_profiles(element),
        )

        children: List[SelectionNode] = []

        selection_entries_el = element.find(tag(CATALOGUE_NS, "selectionEntries"))
        if selection_entries_el is not None:
            for child_el in selection_entries_el.findall(tag(CATALOGUE_NS, "selectionEntry")):
                child_node = self.parse_selection_entry(child_el, selection_index, visited=visited_ids)
                children.append(child_node)

        entry_links_el = element.find(tag(CATALOGUE_NS, "entryLinks"))
        if entry_links_el is not None:
            for entry_link in entry_links_el.findall(tag(CATALOGUE_NS, "entryLink")):
                target_id = entry_link.attrib.get("targetId")
                if not target_id or target_id in visited_ids:
                    continue
                target = selection_index.get(target_id)
                if target is None:
                    continue
                child_node = self.parse_selection_entry(
                    target,
                    selection_index,
                    linked_from=entry_link.attrib.get("name"),
                    visited=visited_ids,
                )
                children.append(child_node)

        node.children = children
        return node

    def build_datasheet(self, catalogue_root: ET.Element, unit_name: str) -> Dict[str, object]:
        target_entry = self.find_unit_entry(catalogue_root, unit_name)
        if target_entry is None:
            available_units = sorted(
                entry.attrib.get("name", "")
                for entry in catalogue_root.findall(f".//{tag(CATALOGUE_NS, 'selectionEntry')}")
                if entry.attrib.get("type") in {"unit", "model"}
            )
            raise ValueError(f"Unit '{unit_name}' not found. Available units: {', '.join(available_units)}")

        selection_index = self.build_selection_index(catalogue_root)
        root_node = self.parse_selection_entry(target_entry, selection_index)

        used_profile_ids = self._collect_profile_types(root_node)
        profile_schemas = {
            pid: self.profile_definitions[pid]
            for pid in used_profile_ids
            if pid in self.profile_definitions
        }

        return {
            "unit": root_node.to_dict(),
            "profile_definitions": {
                pid: {
                    "name": definition.name,
                    "characteristics": definition.characteristic_names,
                }
                for pid, definition in profile_schemas.items()
            },
        }

    def _collect_profile_types(self, node: SelectionNode) -> List[str]:
        profile_ids = {profile.type_id for profile in node.profiles}
        for child in node.children:
            profile_ids.update(self._collect_profile_types(child))
        return list(profile_ids)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract datasheets from BattleScribe catalogues")
    parser.add_argument("--catalogue", type=Path, required=True, help="Path to a .cat file")
    parser.add_argument("--game-system", type=Path, default=Path("Warhammer 40,000.gst"), help="Path to Warhammer 40,000.gst")
    parser.add_argument("--unit", required=True, help="Unit name to extract")
    parser.add_argument("--indent", type=int, default=2, help="Indentation for JSON output")
    args = parser.parse_args()

    parser_obj = CatalogueParser(args.game_system)
    catalogue_root = parser_obj.parse_catalogue(args.catalogue)
    datasheet = parser_obj.build_datasheet(catalogue_root, args.unit)
    print(json.dumps(datasheet, indent=args.indent))


if __name__ == "__main__":
    main()
