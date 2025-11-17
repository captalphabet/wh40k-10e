# Datasheet parsing toolkit

## Schema highlights
- The game system file defines the shared profile schemas. For example, the `Unit` profile lists characteristics for Move, Toughness, Save, Wounds, Leadership, and Objective Control, while weapon and ability profile types enumerate their own characteristic names. These type IDs are reused by every catalogue entry. 【F:Warhammer 40,000.gst†L51-L94】
- Individual catalogue files provide the datasheet content. A unit entry is stored as a `selectionEntry` of type `unit` or `model` and carries its statline, abilities, keywords, and wargear as nested profiles and child selection entries. The Abaddon the Despoiler entry shows the pattern: a Unit profile, several Abilities profiles, category links for keywords, and nested weapon selections. 【F:Chaos - Chaos Space Marines.cat†L2955-L3044】

## Toolkit usage
- Run `python tools/datasheet_toolkit.py --catalogue "<file>.cat" --unit "<Unit Name>"` to extract a unit. The script loads profile and cost definitions from `Warhammer 40,000.gst`, parses the requested unit, and returns JSON containing the unit tree plus the profile schemas used. 【F:tools/datasheet_toolkit.py†L78-L189】【F:tools/datasheet_toolkit.py†L277-L288】
- Linked entries are resolved automatically via `entryLink` references, so datasheets include embedded weapon options or reusable components even when they are defined elsewhere in the catalogue. 【F:tools/datasheet_toolkit.py†L190-L235】
