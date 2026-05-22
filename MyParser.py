from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ParseError(ValueError):
    """
    Raised when the parser encounters invalid
    map syntax or invalid map logic.
    """

    pass


@dataclass
class Zone:
    """
    Represents a graph zone/hub.

    Attributes:
        name:
            Unique zone name.

        x:
            X coordinate.

        y:
            Y coordinate.

        zone_type:
            Zone category.

        max_drones:
            Maximum drones allowed simultaneously
            inside this zone.

        color:
            Optional visualization color.
    """

    name: str
    x: int
    y: int
    zone_type: str = "normal"
    max_drones: int = 1
    color: Optional[str] = None


@dataclass
class Connection:
    """
    Represents a bidirectional connection
    between two zones.

    Attributes:
        a:
            First zone.

        b:
            Second zone.

        max_link_capacity:
            Maximum drones allowed simultaneously
            traversing this connection.
    """

    a: str
    b: str
    max_link_capacity: int = 1


@dataclass
class MapModel:
    """
    Represents the parsed map.

    Attributes:
        nb_drones:
            Total number of drones.

        start:
            Start hub name.

        end:
            End hub name.

        zones:
            Dictionary of all zones.

        connections:
            List of graph connections.
    """

    nb_drones: int
    start: str
    end: str
    zones: Dict[str, Zone] = field(
        default_factory=dict
    )
    connections: List[Connection] = field(
        default_factory=list
    )

    def add_zone(self, zone: Zone) -> None:
        """
        Add a new zone.

        Args:
            zone:
                Zone object.

        Raises:
            ParseError:
                If the zone already exists.
        """

        if zone.name in self.zones:
            raise ParseError(
                f"Duplicate zone name: "
                f"'{zone.name}'"
            )

        self.zones[zone.name] = zone

    def add_connection(
        self,
        a: str,
        b: str,
        cap: int = 1,
    ) -> None:
        """
        Add a connection between two zones.

        Args:
            a:
                First zone name.

            b:
                Second zone name.

            cap:
                Maximum connection capacity.

        Raises:
            ParseError:
                If the connection is invalid.
        """

        if a == b:
            raise ParseError(
                "A zone cannot connect to itself"
            )

        if a not in self.zones:
            raise ParseError(
                f"Unknown zone: '{a}'"
            )

        if b not in self.zones:
            raise ParseError(
                f"Unknown zone: '{b}'"
            )

        for conn in self.connections:

            same_direction = (
                conn.a == a
                and conn.b == b
            )

            opposite_direction = (
                conn.a == b
                and conn.b == a
            )

            if same_direction or opposite_direction:
                raise ParseError(
                    f"Duplicate connection: "
                    f"'{a}-{b}'"
                )

        self.connections.append(
            Connection(
                a=a,
                b=b,
                max_link_capacity=cap,
            )
        )


class MapParser:
    """
    Fly-in map parser.

    Responsible for:
        - Reading map files
        - Validating syntax
        - Validating metadata
        - Building the graph model
    """

    META_RE = re.compile(
        r"^\[(.*)\]$"
    )

    PAIR_RE = re.compile(
        r"([a-zA-Z_][a-zA-Z0-9_]*)=([^\s]+)"
    )

    ZONE_NAME_RE = re.compile(
        r"^[^\s-]+$"
    )

    ALLOWED_ZONE_TYPES = {
        "normal",
        "blocked",
        "restricted",
        "priority",
    }

    ALLOWED_ZONE_METADATA = {
        "zone",
        "color",
        "max_drones",
    }

    ALLOWED_CONNECTION_METADATA = {
        "max_link_capacity",
    }

    def __init__(self) -> None:
        """
        Initialize parser state.
        """

        self.model: Optional[MapModel] = None

    def validate_zone_name(
        self,
        name: str,
        line: int,
    ) -> None:
        """
        Validate a zone name.

        Args:
            name:
                Zone name.

            line:
                Current line number.

        Raises:
            ParseError:
                If name is invalid.
        """

        if not self.ZONE_NAME_RE.fullmatch(name):
            raise ParseError(
                f"Invalid zone name '{name}' "
                f"at line {line}"
            )

    def validate_metadata_keys(
        self,
        metadata: Dict[str, str],
        allowed: set[str],
        line: int,
        target: str,
    ) -> None:
        """
        Validate metadata keys.

        Args:
            metadata:
                Parsed metadata.

            allowed:
                Allowed keys.

            line:
                Current line number.

            target:
                Human-readable target name.

        Raises:
            ParseError:
                If invalid metadata keys exist.
        """

        invalid_keys = (
            set(metadata.keys()) - allowed
        )

        if invalid_keys:

            invalid = ", ".join(
                sorted(invalid_keys)
            )

            raise ParseError(
                f"Invalid {target} metadata "
                f"key(s): {invalid} "
                f"at line {line}"
            )

    def parse_metadata(
        self,
        meta: Optional[str],
    ) -> Dict[str, str]:
        """
        Parse metadata block.

        Args:
            meta:
                Raw metadata string.

        Returns:
            Parsed metadata dictionary.

        Raises:
            ParseError:
                If metadata syntax is invalid.
        """

        if not meta:
            return {}

        match = self.META_RE.fullmatch(
            meta.strip()
        )

        if not match:
            raise ParseError(
                f"Invalid metadata format: "
                f"'{meta}'"
            )

        body = match.group(1).strip()

        if not body:
            return {}

        result: Dict[str, str] = {}

        pos = 0

        for match in self.PAIR_RE.finditer(body):

            invalid_chunk = (
                body[pos:match.start()]
                .strip()
            )

            if invalid_chunk:
                raise ParseError(
                    f"Invalid metadata near: "
                    f"'{invalid_chunk}'"
                )

            key, value = match.groups()

            if key in result:
                raise ParseError(
                    f"Duplicate metadata key: "
                    f"'{key}'"
                )

            result[key] = value

            pos = match.end()

        trailing = body[pos:].strip()

        if trailing:
            raise ParseError(
                f"Invalid trailing metadata: "
                f"'{trailing}'"
            )

        return result

    def extract_metadata(
        self,
        text: str,
    ) -> tuple[str, Dict[str, str]]:
        """
        Extract metadata from text.

        Args:
            text:
                Raw text line.

        Returns:
            Tuple containing:
                - Clean text
                - Parsed metadata
        """

        meta = None

        if "[" in text:

            meta_start = text.index("[")

            meta = text[meta_start:].strip()

            text = text[:meta_start].strip()

        metadata = self.parse_metadata(meta)

        return text, metadata

    def _require_model(self) -> MapModel:
        """
        Ensure parser model exists.

        Returns:
            Current MapModel.

        Raises:
            ParseError:
                If nb_drones has not been defined.
        """

        if self.model is None:
            raise ParseError(
                "nb_drones must be defined first"
            )

        return self.model

    def parse_map(
        self,
        path: str,
    ) -> MapModel:
        """
        Parse a Fly-in map file.

        Args:
            path:
                Map file path.

        Returns:
            Parsed MapModel object.

        Raises:
            ParseError:
                If parsing fails.
        """

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
            ) as file:

                lines = file.readlines()

        except FileNotFoundError:

            raise ParseError(
                f"File not found: '{path}'"
            )

        if not lines:
            raise ParseError(
                "Map file cannot be empty"
            )

        for idx, raw_line in enumerate(
            lines,
            start=1,
        ):

            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if "#" in line:
                line = (
                    line.split("#", 1)[0]
                    .strip()
                )

            line = line.lower()

            if line.startswith("nb_drones"):

                if self.model is not None:
                    raise ParseError(
                        f"nb_drones already defined "
                        f"(line {idx})"
                    )

                try:
                    value = (
                        line.split(":", 1)[1]
                        .strip()
                    )

                except Exception:
                    raise ParseError(
                        f"Invalid nb_drones "
                        f"syntax at line {idx}"
                    )

                try:
                    nb_drones = int(value)

                except ValueError:
                    raise ParseError(
                        f"Invalid nb_drones value "
                        f"at line {idx}"
                    )

                if nb_drones <= 0:
                    raise ParseError(
                        "nb_drones must be > 0"
                    )

                self.model = MapModel(
                    nb_drones=nb_drones,
                    start="",
                    end="",
                )

                continue

            model = self._require_model()

            if (
                line.startswith("hub:")
                or line.startswith(
                    "start_hub:"
                )
                or line.startswith(
                    "end_hub:"
                )
            ):

                try:
                    kind, rest = line.split(
                        ":",
                        1,
                    )

                except Exception:
                    raise ParseError(
                        f"Invalid hub syntax "
                        f"at line {idx}"
                    )

                kind = kind.strip()

                rest = rest.strip()

                rest, metadata = (
                    self.extract_metadata(rest)
                )

                self.validate_metadata_keys(
                    metadata,
                    self.ALLOWED_ZONE_METADATA,
                    idx,
                    "zone",
                )

                parts = rest.split()

                if len(parts) != 3:
                    raise ParseError(
                        f"Invalid hub format "
                        f"at line {idx}"
                    )

                name = parts[0]

                self.validate_zone_name(
                    name,
                    idx,
                )

                try:
                    x = int(parts[1])
                    y = int(parts[2])

                except ValueError:
                    raise ParseError(
                        f"Invalid coordinates "
                        f"at line {idx}"
                    )

                zone_type = metadata.get(
                    "zone",
                    "normal",
                )

                if (
                    zone_type
                    not in self.ALLOWED_ZONE_TYPES
                ):
                    raise ParseError(
                        f"Unknown zone type "
                        f"'{zone_type}' "
                        f"at line {idx}"
                    )

                color = metadata.get(
                    "color"
                )

                try:
                    max_drones = int(
                        metadata.get(
                            "max_drones",
                            "1",
                        )
                    )

                except ValueError:
                    raise ParseError(
                        f"Invalid max_drones "
                        f"value at line {idx}"
                    )

                if max_drones <= 0:
                    raise ParseError(
                        f"max_drones must be > 0 "
                        f"at line {idx}"
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
                            f"Multiple "
                            f"start_hub "
                            f"definitions "
                            f"(line {idx})"
                        )

                    model.start = name

                elif kind == "end_hub":

                    if model.end:
                        raise ParseError(
                            f"Multiple "
                            f"end_hub "
                            f"definitions "
                            f"(line {idx})"
                        )

                    model.end = name

                continue

            if line.startswith("connection"):

                try:
                    rest = (
                        line.split(":", 1)[1]
                        .strip()
                    )

                except Exception:
                    raise ParseError(
                        f"Invalid connection "
                        f"syntax at line {idx}"
                    )

                rest, metadata = (
                    self.extract_metadata(rest)
                )

                self.validate_metadata_keys(
                    metadata,
                    self.ALLOWED_CONNECTION_METADATA,
                    idx,
                    "connection",
                )

                try:
                    cap = int(
                        metadata.get(
                            "max_link_capacity",
                            "1",
                        )
                    )

                except ValueError:
                    raise ParseError(
                        f"Invalid "
                        f"max_link_capacity "
                        f"at line {idx}"
                    )

                if cap <= 0:
                    raise ParseError(
                        f"max_link_capacity "
                        f"must be > 0 "
                        f"at line {idx}"
                    )

                if "-" not in rest:
                    raise ParseError(
                        f"Invalid connection "
                        f"format at line {idx}"
                    )

                a, b = rest.split(
                    "-",
                    1,
                )

                a = a.strip()
                b = b.strip()

                if not a or not b:
                    raise ParseError(
                        f"Invalid connection "
                        f"at line {idx}"
                    )

                self.validate_zone_name(
                    a,
                    idx,
                )

                self.validate_zone_name(
                    b,
                    idx,
                )

                model.add_connection(
                    a,
                    b,
                    cap,
                )

                continue

            raise ParseError(
                f"Unknown instruction "
                f"at line {idx}: '{line}'"
            )

        model = self._require_model()

        if not model.start:
            raise ParseError(
                "Missing start_hub"
            )

        if not model.end:
            raise ParseError(
                "Missing end_hub"
            )

        if model.start not in model.zones:
            raise ParseError(
                "start_hub references "
                "unknown zone"
            )

        if model.end not in model.zones:
            raise ParseError(
                "end_hub references "
                "unknown zone"
            )

        return model
