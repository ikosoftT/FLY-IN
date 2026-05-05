from typing import Dict, List, Tuple
from models import Connection, ParsedMap, Zone

class Graph:
    def __init__(self, parsed_map: ParsedMap) -> None:
        self.zones = parsed_map.zones
        self.nb_drones = parsed_map.nb_drones
        self.start = self.zones[parsed_map.start]
        self.end = self.zones[parsed_map.end]
        self.adj = {
            name: [] for name in self.zones
        }
        self.connections = {}
        self.__build_connections(parsed_map.connections)

    def __build_connections(self, connections: list[Connection]) -> None:
        for conn in connections:
            a = conn.zone_a
            b = conn.zone_b

            if a not in self.zones or b not in self.zones:
                raise ValueError(f"Invalid connection: {a}-{b}")
            if a == b:
                raise ValueError("Self-Loop not allowed")
            key = tuple(sorted((a, b)))
            if key in self.connections:
                raise ValueError(f"Duplicate connection: {a}-{b}")
            self.connections[(a, b)] = conn
            self.connections[(b, a)] = conn

          
            self.adj[a].append(b)
            self.adj[b].append(a)

    def get_neighbors(self, zone_name: str) -> List[str]:
        return self.adj.get(zone_name, [])

    def get_connections(self, a: str, b: str) -> Connection:
        try:
            return self.connections[(a,b)]
        except KeyError:
            raise ValueError(f"No connection between {a} and {b}")
    

