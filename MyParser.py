
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ParseError(ValueError):
    pass


@dataclass
class Zone:
    name: str
    x: int
    y: int
    zone_type: str = "normal"
    max_drones: int = 1
    color: Optional[str] = None


@dataclass
class Connection:
    a: str
    b: str
    max_link_capacity: int = 1


@dataclass
class MapModel:
    nb_drones: int
    start: str
    end: str
    zones: Dict[str, Zone] = field(default_factory=dict)
    connections: List[Connection] = field(default_factory=list)

    def add_zone(self, zone: Zone) -> None:
        if zone.name in self.zones:
            raise ParseError(f"Duplicate zone name: '{zone.name}'")

        self.zones[zone.name] = zone

    def add_connection(self, a: str, b: str, cap: int = 1) -> None:
        if a == b:
            raise ParseError("A zone cannot connect to itself")

        if a not in self.zones:
            raise ParseError(f"Unknown zone: '{a}'")

        if b not in self.zones:
            raise ParseError(f"Unknown zone: '{b}'")

        for c in self.connections:
            same_direction = c.a == a and c.b == b
            opposite_direction = c.a == b and c.b == a

            if same_direction or opposite_direction:
                raise ParseError(f"Duplicate connection: '{a}-{b}'")

        self.connections.append(
            Connection(
                a=a,
                b=b,
                max_link_capacity=cap,
            )
        )


META_RE = re.compile(r"^\[(.*)\]$")


PAIR_RE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)=([^\s]+)")


def parse_metadata(meta: Optional[str]) -> Dict[str, str]:
    """
    Parse metadata string into a dictionary.

    Example:
        [zone=priority color=red max_drones=5]

    Returns:
        {
            "zone": "priority",
            "color": "red",
            "max_drones": "5"
        }
    """

    if not meta:
        return {}

    match = META_RE.fullmatch(meta.strip())

    if not match:
        raise ParseError(f"Invalid metadata format: '{meta}'")

    body = match.group(1).strip()

    if not body:
        return {}

    result: Dict[str, str] = {}

    pos = 0

    for m in PAIR_RE.finditer(body):

        invalid_chunk = body[pos:m.start()].strip()

        if invalid_chunk:
            raise ParseError(
                f"Invalid metadata near: '{invalid_chunk}'"
            )

        key, value = m.groups()

        if key in result:
            raise ParseError(f"Duplicate metadata key: '{key}'")

        result[key] = value

        pos = m.end()

    trailing = body[pos:].strip()

    if trailing:
        raise ParseError(
            f"Invalid trailing metadata: '{trailing}'"
        )

    return result


ALLOWED_ZONE_TYPES = {
    "normal",
    "blocked",
    "restricted",
    "priority",
}


def parse_map(path: str) -> MapModel:
    """
    Parse a map file and return a MapModel object.
    """

    try:
        with open(path) as f:
            lines = f.readlines()

    except FileNotFoundError:
        raise ParseError(f"File not found: '{path}'")

    model: Optional[MapModel] = None

    for idx, raw_line in enumerate(lines, start=1):

        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("nb_drones"):

            if model is not None:
                raise ParseError(
                    f"nb_drones already defined (line {idx})"
                )
            try:
                value = line.split(":", 1)[1].strip()
            except Exception:
                raise ParseError("nb_drones must be key:val")
            try:
                nb_drones = int(value)

            except ValueError:
                raise ParseError(
                    f"Invalid nb_drones value at line {idx}"
                )

            if nb_drones <= 0:
                raise ParseError(
                    "nb_drones must be greater than 0"
                )

            model = MapModel(
                nb_drones=nb_drones,
                start="",
                end="",
            )

            continue

        if model is None:
            raise ParseError(
                f"nb_drones must be defined first (line {idx})"
            )

        if (
            line.startswith("hub")
            or line.startswith("start_hub")
            or line.startswith("end_hub")
        ):
            try:
                kind, rest = line.split(":", 1)
            except Exception:
                raise ParseError(
                    f"line {idx} invalid format follow -> key:val")
            rest = rest.strip()
            kind = kind.strip()
            meta = None

            if "[" in rest:
                meta_start = rest.index("[")
                meta = rest[meta_start:].strip()
                rest = rest[:meta_start].strip()

            parts = rest.split()

            if len(parts) != 3:
                raise ParseError(
                    f"Invalid hub format at line {idx}"
                )

            name = parts[0]

            try:
                x = int(parts[1])
                y = int(parts[2])

            except ValueError:
                raise ParseError(
                    f"Invalid coordinates at line {idx}"
                )

            metadata = parse_metadata(meta)

            zone_type = metadata.get("zone", "normal")

            if zone_type not in ALLOWED_ZONE_TYPES:
                raise ParseError(
                    f"Unknown zone type '{zone_type}' "
                    f"at line {idx}"
                )

            color = metadata.get("color")

            try:
                max_drones = int(
                    metadata.get("max_drones", "1")
                )

            except ValueError:
                raise ParseError(
                    f"Invalid max_drones value at line {idx}"
                )

            if max_drones <= 0:
                raise ParseError(
                    f"max_drones must be > 0 at line {idx}"
                )

            zone = Zone(
                name=name,
                x=x,
                y=y,
                zone_type=zone_type,
                max_drones=max_drones,
                color=color,
            )

            model.add_zone(zone)

            if kind == "start_hub":

                if model.start:
                    raise ParseError(
                        f"Multiple start_hub definitions "
                        f"(line {idx})"
                    )

                model.start = name

            elif kind == "end_hub":

                if model.end:
                    raise ParseError(
                        f"Multiple end_hub definitions "
                        f"(line {idx})"
                    )

                model.end = name

            continue

        if line.startswith("connection"):
            try:
                rest = line.split(":", 1)[1].strip()
            except Exception:
                raise ParseError(f"Invalid format  at line {idx}")
            meta = None

            if "[" in rest:
                meta_start = rest.index("[")
                meta = rest[meta_start:].strip()
                rest = rest[:meta_start].strip()

            metadata = parse_metadata(meta)

            try:
                cap = int(
                    metadata.get(
                        "max_link_capacity",
                        "1",
                    )
                )

            except ValueError:
                raise ParseError(
                    f"Invalid max_link_capacity "
                    f"at line {idx}"
                )

            if cap <= 0:
                raise ParseError(
                    f"max_link_capacity must be > 0 "
                    f"at line {idx}"
                )

            if "-" not in rest:
                raise ParseError(
                    f"Invalid connection format "
                    f"at line {idx}"
                )

            a, b = rest.split("-", 1)

            a = a.strip()
            b = b.strip()

            if not a or not b:
                raise ParseError(
                    f"Invalid connection at line {idx}"
                )

            model.add_connection(a, b, cap)

            continue

        raise ParseError(
            f"Unknown instruction at line {idx}: '{line}'"
        )

    if model is None:
        raise ParseError("Missing nb_drones definition")

    if not model.start:
        raise ParseError("Missing start_hub")

    if not model.end:
        raise ParseError("Missing end_hub")

    if model.start not in model.zones:
        raise ParseError(
            "start_hub references unknown zone"
        )

    if model.end not in model.zones:
        raise ParseError(
            "end_hub references unknown zone"
        )

    return model
