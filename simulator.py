
from __future__ import annotations

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from MyParser import MapModel, Zone, Connection
from webcolors import name_to_rgb

import sys


@dataclass
class DroneState:
    """Represents the runtime state of a drone.

    Attributes:
        id: Unique drone identifier.
        pos: Current drone position.
        path: Planned route for the drone.
        delivered: Indicates whether the drone reached destination.
        transit_remaining: Remaining turns while crossing a restricted zone.
        transit_target: Destination zone while in transit.
        transit_conn: Connection currently used during transit.
    """

    id: int
    pos: str
    path: List[str]
    delivered: bool = False
    transit_remaining: int = 0
    transit_target: Optional[str] = None
    transit_conn: Optional[Tuple[str, str]] = None


class Simulator:
    """Handles drone routing and turn-based simulation execution.

    The simulator is responsible for:
        - Path generation
        - Zone occupancy management
        - Link capacity management
        - Drone movement simulation
        - Colored terminal rendering
    """

    def __init__(self, model: MapModel) -> None:
        """Initialize the simulation state.

        Args:
            model: Parsed map model containing zones and connections.
        """

        self.model = model
        self.turn = 0
        self.drones: List[DroneState] = []

        for i in range(1, model.nb_drones + 1):
            self.drones.append(
                DroneState(
                    id=i,
                    pos=model.start,
                    path=[],
                )
            )

        self.zone_occupancy: Dict[str, int] = {
            name: 0 for name in model.zones
        }

        self.zone_occupancy[model.start] = model.nb_drones

        self.adj: Dict[str, List[Tuple[str, Connection]]] = {}

        for c in model.connections:

            self.adj.setdefault(c.a, []).append((c.b, c))
            self.adj.setdefault(c.b, []).append((c.a, c))

        self.active_transits: Dict[
            Tuple[str, str],
            List[int],
        ] = {}

        self.reserved_arrivals: Dict[str, int] = {}

        for zone in self.model.zones.values():

            if zone.color:

                self._validate_color(zone.color)

    def _rainbow_text(self, text: str) -> str:
        """Render text using rainbow ANSI terminal colors.

        Args:
            text: Text to colorize.

        Returns:
            Rainbow-colored ANSI formatted string.
        """

        colors = [
            (255, 0, 0),
            (255, 127, 0),
            (255, 255, 0),
            (0, 255, 0),
            (0, 0, 255),
            (75, 0, 130),
            (148, 0, 211),
        ]

        out = []

        for i, ch in enumerate(text):

            r, g, b = colors[i % len(colors)]

            out.append(
                f"\x1b[38;2;{r};{g};{b}m{ch}"
            )

        out.append("\x1b[0m")

        return "".join(out)

    def _validate_color(self, color: str) -> str | None:
        """Validate a user-defined color.

        Args:
            color: Color name provided by the parser.

        Raises:
            ValueError: If the color is invalid.

        Returns:
            Rainbow-colored text when color is rainbow.
            Otherwise None.
        """

        c = color.strip().lower()

        if c == "rainbow":

            return self._rainbow_text(c)

        try:

            name_to_rgb(color.strip().lower())

        except ValueError:

            raise ValueError(
                f"Invalid color: {color}"
            )

        return None

    def _colorize(
        self,
        name: str,
        color: Optional[str],
    ) -> str:
        """Apply ANSI color formatting to a zone name.

        Args:
            name: Zone name to display.
            color: Requested color name.

        Returns:
            ANSI formatted colored string.
        """

        if not color:

            return name

        c = color.strip().lower()

        if c == "rainbow":

            return self._rainbow_text(name)

        rgb = name_to_rgb(c)

        return (
            f"\x1b[38;2;{rgb.red};{rgb.green};{rgb.blue}m"
            f"{name}\x1b[0m"
        )

    def _decrement_transits(self) -> None:
        """Update remaining transit durations for active links."""

        for key in list(self.active_transits.keys()):

            lst = self.active_transits[key]

            lst = [r - 1 for r in lst]

            lst = [r for r in lst if r > 0]

            if lst:

                self.active_transits[key] = lst

            else:

                del self.active_transits[key]

    def _link_usage(
        self,
        link_key: Tuple[str, str],
    ) -> int:
        """Return active usage count for a connection.

        Args:
            link_key: Canonical link identifier.

        Returns:
            Number of drones currently using the link.
        """

        return len(
            self.active_transits.get(link_key, [])
        )

    def zone_cost(self, zone: Zone) -> float:
        """Return movement cost associated with a zone.

        Args:
            zone: Target zone.

        Returns:
            Zone traversal cost.
        """

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
        """Find shortest path using Dijkstra with penalties.

        Args:
            start: Starting zone.
            end: Destination zone.
            penalties: Dynamic node penalties.

        Returns:
            Computed path or None if unreachable.
        """

        import heapq

        zones = self.model.zones

        dist: Dict[str, float] = {
            n: float("inf") for n in zones
        }

        prev: Dict[str, Optional[str]] = {
            n: None for n in zones
        }

        dist[start] = 0.0

        pq: List[Tuple[float, str]] = [
            (0.0, start)
        ]

        while pq:

            d, u = heapq.heappop(pq)

            if d != dist[u]:

                continue

            if u == end:

                break

            for v, _ in self.adj.get(u, []):

                if zones[v].zone_type == "blocked":

                    continue

                nd = (
                    d
                    + self.zone_cost(zones[v])
                    + penalties.get(v, 0.0)
                )

                if nd < dist[v]:

                    dist[v] = nd

                    prev[v] = u

                    heapq.heappush(
                        pq,
                        (nd, v),
                    )

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

    def generate_alternative_paths(
        self,
        k: int = 4,
    ) -> List[List[str]]:
        """Generate alternative paths using node penalties.

        Args:
            k: Maximum number of paths.

        Returns:
            List of generated paths.
        """

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

                penalties[node] = (
                    penalties.get(node, 0.0) + 1.0
                )

        return paths

    def plan_paths(self) -> None:
        """Assign planned routes to all drones."""

        paths = self.generate_alternative_paths(
            k=min(6, self.model.nb_drones)
        )

        if not paths:

            raise RuntimeError(
                "No path from start to end"
            )

        for idx, d in enumerate(self.drones):

            d.path = paths[
                idx % len(paths)
            ].copy()

    def _format_moves_colored(
        self,
        moves: List[str],
    ) -> str:
        """Format simulation output with ANSI colors.

        Args:
            moves: Raw move strings.

        Returns:
            Colorized terminal output.
        """

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

                a_c = self._colorize(
                    a,
                    col_a.color if col_a else None,
                )

                b_c = self._colorize(
                    b,
                    col_b.color if col_b else None,
                )

                parts.append(
                    f"{did}-{a_c}-{b_c}"
                )

            else:

                z = self.model.zones.get(dest)

                zc = self._colorize(
                    dest,
                    z.color if z else None,
                )

                parts.append(f"{did}-{zc}")

        return " ".join(parts)

    def step(self) -> List[str]:
        """Execute one simulation turn.

        Returns:
            List of generated move strings.
        """

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

            if (
                d.transit_remaining == 0
                and d.transit_target is not None
            ):

                cur_res = self.reserved_arrivals.get(
                    d.transit_target,
                    0,
                )

                new_res = max(0, cur_res - 1)

                self.reserved_arrivals[
                    d.transit_target
                ] = new_res

                self.zone_occupancy[
                    d.transit_target
                ] = (
                    self.zone_occupancy.get(
                        d.transit_target,
                        0,
                    ) + 1
                )

                d.pos = d.transit_target

                d.transit_target = None

                d.transit_conn = None

                mv = f"D{d.id}-{d.pos}"

                moves.append(mv)

                if d.pos == self.model.end:

                    d.delivered = True

        for d in self.drones:

            if (
                d.delivered
                or d.transit_remaining > 0
            ):

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
                    - self.zone_occupancy.get(
                        nxt,
                        0,
                    )
                    - self.reserved_arrivals.get(
                        nxt,
                        0,
                    )
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

            link_key = (
                min(d.pos, nxt),
                max(d.pos, nxt),
            )

            used = self._link_usage(link_key)

            if used >= conn.max_link_capacity:

                continue

            cost = int(self.zone_cost(zone))

            if zone.zone_type == "restricted":

                if nxt != self.model.end:

                    cur = self.reserved_arrivals.get(
                        nxt,
                        0,
                    )

                    self.reserved_arrivals[
                        nxt
                    ] = cur + 1

                cur_occ = self.zone_occupancy.get(
                    d.pos,
                    0,
                )

                self.zone_occupancy[d.pos] = max(
                    0,
                    cur_occ - 1,
                )

                d.transit_remaining = cost - 1

                d.transit_target = nxt

                d.transit_conn = (d.pos, nxt)

                self.active_transits.setdefault(
                    link_key,
                    [],
                ).append(cost)

                mv = f"D{d.id}-{d.pos}-{nxt}"

                moves.append(mv)

            else:

                cur_occ2 = self.zone_occupancy.get(
                    d.pos,
                    0,
                )

                self.zone_occupancy[d.pos] = max(
                    0,
                    cur_occ2 - 1,
                )

                self.zone_occupancy[nxt] = (
                    self.zone_occupancy.get(
                        nxt,
                        0,
                    ) + 1
                )

                d.pos = nxt

                self.active_transits.setdefault(
                    link_key,
                    [],
                ).append(1)

                mv = f"D{d.id}-{d.pos}"

                moves.append(mv)

                if d.pos == self.model.end:

                    d.delivered = True

        for d in self.drones:

            if d.transit_remaining > 0:

                d.transit_remaining -= 1

                if (
                    d.transit_remaining > 0
                    and d.transit_conn is not None
                ):

                    a, b = d.transit_conn

                    mv = f"D{d.id}-{a}-{b}"

                    moves.append(mv)

        self.turn += 1

        if moves:

            try:

                colored = self._format_moves_colored(
                    moves
                )

                print(
                    colored,
                    file=sys.stdout,
                )

            except Exception:

                pass

        return moves

    def run(self) -> List[List[str]]:
        """Run the simulation until all drones arrive.

        Returns:
            Complete simulation move history.
        """

        self.plan_paths()

        history: List[List[str]] = []

        while not all(
            d.delivered for d in self.drones
        ):

            moves = self.step()

            history.append(moves)

            if self.turn > 10000:

                raise RuntimeError(
                    "Simulation exceeded turn limit"
                )

        return history
