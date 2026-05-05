from dataclasses import dataclass
from enum import Enum

class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

@dataclass
class Zone:
    name: str
    x: int
    y: int
    zone_type: ZoneType
    color: str | None
    max_drones: int

@dataclass(frozen=True)
class Connection:
    zone_a: str
    zone_b: str
    max_link_capacity: int

    def key(self) -> tuple[str, str]:
        return tuple(sorted((self.zone_a, self.zone_b)))
    

@dataclass
class ParsedMap:
    nb_drones: int
    zones: dict[str, Zone]
    connections: list[Connection]
    start: str
    end: str

