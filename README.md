
*This project has been created as part of the 42 curriculum by yikoubaz.*

# Fly-in

## Description

Fly-in is a turn-based drone routing simulator written in Python.

The goal of the project is to simulate multiple drones navigating through a network of connected zones while respecting movement constraints such as:

- Zone occupancy limits
- Link capacity limits
- Restricted traversal zones
- Blocked areas
- Dynamic routing conflicts

The simulator computes paths between a start zone and an end zone and executes the movement of drones turn-by-turn until all drones successfully arrive at the destination.

The project focuses on:

- Graph theory
- Pathfinding algorithms
- Turn-based simulations
- Object-oriented programming
- Resource management
- Terminal visualization

---

# Features

- Object-oriented architecture
- Dijkstra shortest-path algorithm
- Alternative path generation using node penalties
- Dynamic congestion reduction
- Multi-drone simulation
- Restricted and blocked zone handling
- ANSI terminal colored output
- Rainbow text rendering support
- Web color validation using `webcolors`
- Google-style docstrings following PEP 257

---

# Instructions

## Requirements

- Python 3.10+
- pip

---

## Installation

Install project dependencies:

```bash
pip install -r requirements.txt
```

Or manually install the required package:

```bash
pip install webcolors
```

---

## Execution

Run the simulator using:

```bash
python3 main.py example.map
```

---

## Example Map

```text
# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal

```

---

# Project Structure

```text
.
├── main.py
├── simulator.py
├── MyParser.py
├── requirements.txt
├── README.md
└── example.map
```

---

# Algorithm Choices

## Graph Representation

The map is represented as an adjacency list.

Each zone is stored as a graph node, while each connection between zones is represented as an edge containing:

- Link capacity
- Connected zones

This representation allows efficient traversal and neighbor lookup.

---

## Pathfinding Strategy

The simulator uses Dijkstra’s algorithm to compute the shortest path between the start zone and the destination zone.

The traversal cost of each zone depends on its type:

| Zone Type | Cost |
|---|---|
| normal | 1.0 |
| priority | 0.9 |
| restricted | 2.0 |
| blocked | inaccessible |

Blocked zones are ignored during traversal.

---

## Alternative Path Generation

To avoid congestion and distribute drones efficiently, the simulator generates multiple alternative paths.

This is achieved by applying dynamic penalties to previously used nodes.

After a path is generated, intermediate nodes receive additional penalty values, encouraging the next path computation to explore different routes.

This approach improves:

- Load balancing
- Congestion reduction
- Parallel drone movement efficiency

---

## Simulation Strategy

The simulation executes in turns.

At each turn:

1. Active transits are updated
2. Drones already in transit continue moving
3. Available drones attempt movement
4. Occupancy and link capacities are validated
5. Successful moves are recorded and displayed

The simulation continues until all drones reach the destination.

---

# Visual Representation

The project includes ANSI terminal color rendering to improve readability and visualization.

Each zone may define a color using standard web color names.

Example:

```text
red
blue
gold
deepskyblue
```

Zones are rendered directly in the terminal using RGB ANSI escape sequences.

---

## Rainbow Rendering

The simulator also supports a special `rainbow` rendering mode.

Instead of applying a single color to the text, each character receives a different RGB color, producing a rainbow visual effect.

Example:

```text
ZONE
```

This improves:

- Terminal readability
- Zone distinction
- Simulation visualization
- User experience during execution

---

# Output Example

```text
D1-A D2-C D3-D
D1-B D2-D D3-B
```

Colored zones appear directly in the terminal during execution.

---

# Technical Choices

## Object-Oriented Design

The project follows an object-oriented architecture.

Main components include:

| Component | Responsibility |
|---|---|
| `DroneState` | Stores runtime drone state |
| `Simulator` | Handles routing and simulation |
| `MyParser` | Parses map configuration |
| `Zone` | Represents graph nodes |
| `Connection` | Represents graph edges |

---

## Color Validation

The project uses the `webcolors` library to validate user-defined colors.

Invalid colors raise parsing errors to ensure deterministic rendering behavior.

---

# Documentation

The codebase follows:

- PEP 257 docstring conventions
- Google-style documentation
- Type annotations
- Modular design principles

---

# Resources

## Algorithms and Graph Theory

- https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
- https://www.geeksforgeeks.org/dijkstras-shortest-path-algorithm-greedy-algo-7/
- https://www.redblobgames.com/pathfinding/a-star/introduction.html

---

## Python Documentation

- https://docs.python.org/3/
- https://peps.python.org/pep-0257/
- https://google.github.io/styleguide/pyguide.html

---

## ANSI Terminal Colors

- https://en.wikipedia.org/wiki/ANSI_escape_code

---

## AI Usage

AI tools were used during development for:

- Documentation generation
- README structure improvements
- Refactoring suggestions
- PEP 257 docstring formatting
- ANSI color rendering ideas
- General debugging assistance

AI was not used to automatically generate the full project architecture or final algorithms without manual validation and implementation.