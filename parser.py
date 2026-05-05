from models import Connection, ParsedMap, Zone, ZoneType
from typing import Any

VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}


def parse_metadata(raw: str) -> dict[str, str]:
    metadata = {}
    raw = raw.strip()
    if not raw:
        return metadata
    if not raw.startswith('[') or not raw.endswith(']'):
        raise ValueError("metadata must be inside []")

    content = raw[1:-1].strip()

    if not content:
        return metadata
    parts = content.split()
    for part in parts:
        if "=" not in part:
            raise ValueError(f"Invalid metadata item: {part}")
        key, val = part.split("=", 1)
        if not key or not val:
            raise ValueError(f"invalid metadata item {part}")
        metadata[key] = val
    return metadata


def nb_drones_parser(data: list[str]) -> int:
    if len(data) != 2:
        raise ValueError("nb_drones: invalid format")
    val = data[1].strip()
    try:
        n = int(val)
    except ValueError as e:
        raise ValueError("nb_drones: must be valid int") from e
    if n <= 0:
        raise ValueError("nb_drones must be > 0")
    return n


def hub_parser(data: list[str]) -> dict[str, Any]:
    if len(data) != 2:
        raise ValueError("Invalid format")

    prefix = data[0].strip()
    val = data[1].strip()

    parts = val.split(maxsplit=3)

    if len(parts) < 3:
        raise ValueError(f"{prefix}: expected name x y")
    name = parts[0]
    raw_x = parts[1]
    raw_y = parts[2]
    raw_metadata = parts[3] if len(parts) == 4 else ""

    if "-" in name or " " in name:
        raise ValueError("zone name cannot contain dash or space")
    try:
        x = int(raw_x)
        y = int(raw_y)
    except ValueError as e:
        raise ValueError("x and y must be valid int") from e

    metadata = parse_metadata(raw_metadata)

    zone_type = metadata.get("zone", "normal")
    color = metadata.get("color", "none")
    max_drones_raw = metadata.get("max_drones", "1")

    if zone_type not in VALID_ZONE_TYPES:
        raise ValueError(f"Invalid zone type: {zone_type}")

    try:
        max_drones = int(max_drones_raw)
    except ValueError as e:
        raise ValueError("max_drones must be valid int") from e
    if max_drones <= 0:
        raise ValueError("max_drones: must be > 0")
    return {
        "kind": prefix,
        "name": name,
        "x": x,
        "y": y,
        "zone": zone_type,
        "color": color,
        "max_drones": max_drones
    }


def connection_parser(data: list[str]) -> dict[str, Any]:
    if len(data) != 2:
        raise ValueError("invalid format!")

    val = data[1].strip()
    parts = val.split(maxsplit=1)
    connection_part = parts[0]
    raw_metadata = parts[1] if len(parts) == 2 else ""

    if "-" not in connection_part:
        raise ValueError("Connection  must use format zone1-zone2")
    zone_a, zone_b = connection_part.split("-", 1)
    if not zone_a or not zone_b:
        raise ValueError('connection zones cannot be empty')

    metadata = parse_metadata(raw_metadata)

    capacity_raw = metadata.get("max_link_capacity", "1")

    try:
        max_link_capacity = int(capacity_raw)
    except ValueError as e:
        raise ValueError("max_link_capacity: msut be valid int") from e

    if max_link_capacity <= 0:
        raise ValueError("max_link_capacity: must be > 0")
    return {
        "zone_a": zone_a,
        "zone_b": zone_b,
        "max_link_capacity": max_link_capacity
    }


def parse_file(file: str) -> ParsedMap:
    result = {
        "nb_drones": 0,
        "zones": {},
        "connections": [],
        "start": None,
        "end": None
    }
    with open(file) as f:
        lines = f.readlines()
        for line_num, raw_line in enumerate(lines, 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#")[0].strip()
            data = line.split(":", 1)
            if len(data) != 2:
                raise ValueError(f"line {line_num}: missing ':'")
            key = data[0].strip()

            try:
                if key == "nb_drones":
                    result[key] = nb_drones_parser(data)
                elif key in {"start_hub", "end_hub", "hub"}:
                    zone = hub_parser(data)
                    zone_name = zone["name"]
                    if zone_name in result["zones"]:
                        raise ValueError(f"duplicates zone name: {zone_name}")
                    result["zones"][zone_name] = zone
                    if key == "start_hub":
                        if result["start"] is not None:
                            raise ValueError("multiple start_hub definitions")
                        result["start"] = zone_name
                    elif key == "end_hub":
                        if result["end"] is not None:
                            raise ValueError("multiple end_hub definitions")
                        result["end"] = zone_name
                elif key == "connection":
                    connection = connection_parser(data)
                    result["connections"].append(connection)
                else:
                    raise ValueError(f"unknown option: {key}")

            except ValueError as e:
                raise ValueError(f"line {line_num}: {e}") from e
        if result["nb_drones"] <= 0:
            raise ValueError("missing nb_drones")
        if result["start"] is None:
            raise ValueError("missing start_hub")
        if result["end"] is None:
            raise ValueError("missing end_hub")
        seen_connections = set()

        for conne in result["connections"]:
            zone_a = conne["zone_a"]
            zone_b = conne["zone_b"]

            if zone_a not in result["zones"]:
                raise ValueError(f"connection uses unknown zone: {zone_a}")
            if zone_b not in result["zones"]:
                raise ValueError(f"connection uses unknown zone: {zone_b}")

            connection_key = tuple(sorted((zone_a, zone_b)))

            if connection_key in seen_connections:
                raise ValueError(f"duplicates connection: {zone_a}-{zone_b}")

            seen_connections.add(connection_key)

        zones_obj = {}

        for zone_name, zone_data in result["zones"].items():
            zones_obj[zone_name] = Zone(
                name=zone_data["name"],
                x=zone_data["x"],
                y=zone_data["y"],
                zone_type=ZoneType(zone_data["zone"]),
                color=zone_data["color"],
                max_drones=zone_data["max_drones"]
            )

        connection_obj = []

        for conn in result["connections"]:
            connection_obj.append(
                Connection(
                    zone_a=conn["zone_a"],
                    zone_b=conn["zone_b"],
                    max_link_capacity=conn["max_link_capacity"],
                )
            )

        return ParsedMap(
            nb_drones=result["nb_drones"],
            zones=zones_obj,
            connections=connection_obj,
            start=result["start"],
            end=result["end"],
        )
