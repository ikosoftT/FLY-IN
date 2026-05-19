from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from MyParser import MapModel, Zone, Connection
from colorama import Fore, Style, init as colorama_init

import sys

colorama_init()

COLOR_MAP: Dict[str, str] = {
    "black": Fore.BLACK,
    "red": Fore.RED,
    "green": Fore.GREEN,
    "yellow": Fore.YELLOW,
    "blue": Fore.BLUE,
    "magenta": Fore.MAGENTA,
    "cyan": Fore.CYAN,
    "white": Fore.WHITE,
}


def colorize(name: str, color: Optional[str]) -> str:
    """Return colored zone name.

    Supports named colors from COLOR_MAP and hex colors like #fff or #ffffff
    (converted to 24-bit ANSI escape sequences). Unknown values return the
    plain name (no color).
    """
    if not color:
        return name
    c = color.strip()
    code = COLOR_MAP.get(c.lower())
    if code:
        return f"{code}{name}{Style.RESET_ALL}"
    if c.startswith('#'):
        hexv = c[1:]
        if len(hexv) == 3:
            hexv = ''.join(ch*2 for ch in hexv)
        if len(hexv) == 6:
            try:
                r = int(hexv[0:2], 16)
                g = int(hexv[2:4], 16)
                b = int(hexv[4:6], 16)
                return f"\x1b[38;2;{r};{g};{b}m{name}\x1b[0m"
            except ValueError:
                return name
    return name


@dataclass
class DroneState:
    id: int
    pos: str
    path: List[str]
    delivered: bool = False
    transit_remaining: int = 0
    transit_target: Optional[str] = None
    transit_conn: Optional[Tuple[str, str]] = None


class Simulator:

    def __init__(self, model: MapModel):
        self.model = model
        self.turn = 0
        self.drones: List[DroneState] = []
        for i in range(1, model.nb_drones + 1):
            self.drones.append(DroneState(id=i, pos=model.start, path=[]))

        self.zone_occupancy: Dict[str, int] = {name: 0 for name in model.zones}
        self.zone_occupancy[model.start] = model.nb_drones

        self.adj: Dict[str, List[Tuple[str, Connection]]] = {}
        for c in model.connections:
            self.adj.setdefault(c.a, []).append((c.b, c))
            self.adj.setdefault(c.b, []).append((c.a, c))
        self.active_transits: Dict[Tuple[str, str], List[int]] = {}
        self.reserved_arrivals: Dict[str, int] = {}

    def _decrement_transits(self) -> None:
        for key in list(self.active_transits.keys()):
            lst = self.active_transits[key]

            lst = [r - 1 for r in lst]

            lst = [r for r in lst if r > 0]

            if lst:

                self.active_transits[key] = lst

            else:

                del self.active_transits[key]

    def _link_usage(self, link_key: Tuple[str, str]) -> int:
        return len(self.active_transits.get(link_key, []))

    def zone_cost(self, zone: Zone) -> float:
        if zone.zone_type == "restricted":
            return 2.0
        if zone.zone_type == "priority":
            return 0.9
        return 1.0

    def _find_path_with_penalty(
        self,
        start: str,
        end: str,
        penalties: Dict[str, float],
    ) -> Optional[List[str]]:

        import heapq

        zones = self.model.zones

        dist: Dict[str, float] = {n: float("inf") for n in zones}

        prev: Dict[str, Optional[str]] = {n: None for n in zones}

        dist[start] = 0.0

        pq: List[Tuple[float, str]] = [(0.0, start)]

        while pq:

            d, u = heapq.heappop(pq)

            if d != dist[u]:

                continue

            if u == end:

                break

            for v, _ in self.adj.get(u, []):

                if zones[v].zone_type == "blocked":

                    continue

                nd = d + self.zone_cost(zones[v]) + penalties.get(v, 0.0)

                if nd < dist[v]:

                    dist[v] = nd

                    prev[v] = u

                    heapq.heappush(pq, (nd, v))

        if dist[end] == float("inf"):

            return None

        path: List[str] = []

        cur_node: str = end

        path.append(cur_node)

        while True:

            pred = prev[cur_node]

            if pred is None:

                break

            path.append(pred)

            cur_node = pred

        path.reverse()

        return path

    def generate_alternative_paths(self, k: int = 4) -> List[List[str]]:

        penalties: Dict[str, float] = {}

        paths: List[List[str]] = []

        for _ in range(k):

            p = self._find_path_with_penalty(

                self.model.start,

                self.model.end,

                penalties,

            )

            if p is None:

                break

            if p in paths:

                break

            paths.append(p)

            for node in p[1:-1]:

                penalties[node] = penalties.get(node, 0.0) + 1.0

        return paths

    def plan_paths(self) -> None:

        paths = self.generate_alternative_paths(k=min(6, self.model.nb_drones))

        if not paths:

            raise RuntimeError("No path from start to end")

        for idx, d in enumerate(self.drones):

            d.path = paths[idx % len(paths)].copy()

    def _format_moves_colored(self, moves: List[str]) -> str:

        parts: List[str] = []

        for mv in moves:

            if "-" not in mv:

                parts.append(mv)

                continue

            try:
                did, dest = mv.split("-", 1)

            except ValueError:

                parts.append(mv)

                continue

            if "-" in dest:

                a, b = dest.split("-", 1)

                col_a = self.model.zones.get(a)

                col_b = self.model.zones.get(b)

                a_c = colorize(a, col_a.color if col_a else None)

                b_c = colorize(b, col_b.color if col_b else None)

                parts.append(f"{did}-{a_c}-{b_c}")

            else:

                z = self.model.zones.get(dest)

                zc = colorize(dest, z.color if z else None)

                parts.append(f"{did}-{zc}")

        return " ".join(parts)

    def step(self) -> List[str]:

        self._decrement_transits()

        moves: List[str] = []

        for d in self.drones:

            if d.delivered:

                continue

            if d.transit_remaining > 0:

                pass

        for d in self.drones:

            if d.delivered:

                continue

            if d.transit_remaining == 0 and d.transit_target is not None:

                cur_res = self.reserved_arrivals.get(d.transit_target, 0)

                new_res = max(0, cur_res - 1)

                self.reserved_arrivals[d.transit_target] = new_res

                self.zone_occupancy[d.transit_target] = (

                    self.zone_occupancy.get(d.transit_target, 0) + 1

                )

                d.pos = d.transit_target

                d.transit_target = None

                d.transit_conn = None

                mv = f"D{d.id}-{d.pos}"

                moves.append(mv)

                if d.pos == self.model.end:

                    d.delivered = True

        for d in self.drones:

            if d.delivered or d.transit_remaining > 0:

                continue

            if d.pos == self.model.end:

                d.delivered = True

                continue

            if not d.path:

                continue

            try:

                idx = d.path.index(d.pos)

            except ValueError:

                idx = 0

            if idx + 1 >= len(d.path):

                continue

            nxt = d.path[idx + 1]

            zone = self.model.zones[nxt]

            if nxt != self.model.end:

                available = (

                    zone.max_drones

                    - self.zone_occupancy.get(nxt, 0)

                    - self.reserved_arrivals.get(nxt, 0)

                )

                if available <= 0:

                    continue

            conn = None

            for v, c in self.adj.get(d.pos, []):

                if v == nxt:

                    conn = c

                    break

            if conn is None:
                continue

            link_key = (min(d.pos, nxt), max(d.pos, nxt))

            used = self._link_usage(link_key)

            if used >= conn.max_link_capacity:

                continue

            cost = int(self.zone_cost(zone))

            if zone.zone_type == "restricted":

                if nxt != self.model.end:

                    cur = self.reserved_arrivals.get(nxt, 0)

                    self.reserved_arrivals[nxt] = cur + 1

                cur_occ = self.zone_occupancy.get(d.pos, 0)

                self.zone_occupancy[d.pos] = max(0, cur_occ - 1)

                d.transit_remaining = cost - 1

                d.transit_target = nxt

                d.transit_conn = (d.pos, nxt)

                self.active_transits.setdefault(link_key, []).append(cost)

                mv = f"D{d.id}-{d.pos}-{nxt}"

                moves.append(mv)

            else:

                cur_occ2 = self.zone_occupancy.get(d.pos, 0)

                self.zone_occupancy[d.pos] = max(0, cur_occ2 - 1)

                self.zone_occupancy[nxt] = self.zone_occupancy.get(nxt, 0) + 1

                d.pos = nxt

                self.active_transits.setdefault(link_key, []).append(1)

                mv = f"D{d.id}-{d.pos}"

                moves.append(mv)

                if d.pos == self.model.end:

                    d.delivered = True

        for d in self.drones:

            if d.transit_remaining > 0:

                d.transit_remaining -= 1

                if d.transit_remaining > 0 and d.transit_conn is not None:

                    a, b = d.transit_conn

                    mv = f"D{d.id}-{a}-{b}"

                    moves.append(mv)

        self.turn += 1

        if moves:

            try:

                colored = self._format_moves_colored(moves)

                print(colored, file=sys.stdout)

            except Exception:

                pass

        return moves

    def run(self) -> List[List[str]]:

        self.plan_paths()

        history: List[List[str]] = []

        while not all(d.delivered for d in self.drones):

            moves = self.step()

            history.append(moves)

            if self.turn > 10000:

                raise RuntimeError("Simulation exceeded turn limit")

        print("tottal turns: ", self.turn)

        return history
