*This project has been created as part of the 42 curriculum by yikoubaz.*

# Fly-in

## Description

Fly-in is a turn-based drone routing simulator developed in Python.

The project simulates multiple drones navigating through a network of interconnected zones while respecting movement constraints and traffic rules. Each drone must travel from a start hub to an end hub using the most efficient available route while avoiding congestion, blocked areas, and traversal conflicts.

The simulator combines concepts from:

- Graph theory
- Pathfinding algorithms
- Turn-based simulation systems
- Resource and traffic management
- Object-oriented programming

The primary objective is to efficiently distribute drones across the graph while preventing deadlocks, minimizing congestion, and maintaining valid movement constraints during each simulation turn.

---

# Features

- Object-oriented architecture
- Dijkstra shortest-path algorithm
- Alternative route generation
- Dynamic congestion handling
- Multi-drone path distribution
- Restricted and blocked zone support
- Turn-by-turn simulation engine
- ANSI terminal color rendering
- Rainbow text rendering mode
- Web color validation using `webcolors`
- Google-style docstrings and type annotations

---

# Instructions

## Requirements

Before running the project, ensure the following are installed:

- Python 3.10 or higher
- pip

---

## Installation

Clone the repository and install the required dependencies.

### Install dependencies

```bash
pip install -r requirements.txt
```

Or install the required package manually:

```bash
pip install webcolors
```

---

## Running the Project

Execute the simulator with:

```bash
python3 main.py example.map
```

You may replace `example.map` with any valid map configuration file.

---

# Example Input

## Example Map File

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

# Expected Output

```text
D1-waypoint1 D2-waypoint1
D1-waypoint2 D2-waypoint2
D1-goal D2-goal
```

Colored zones are rendered directly inside the terminal using ANSI escape sequences.

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

# Algorithm Explanation

## Graph Representation

The map is represented internally as a graph using an adjacency-list structure.

- Each zone acts as a graph node
- Each connection acts as an edge between nodes

This representation provides efficient traversal, neighbor lookup, and path computation.

---

## Pathfinding Strategy

The simulator uses Dijkstra’s shortest-path algorithm to compute the optimal route between the start hub and the destination hub.

Traversal costs depend on zone types:

| Zone Type | Cost |
|---|---|
| normal | 1.0 |
| priority | 0.9 |
| restricted | 2.0 |
| blocked | inaccessible |

Blocked zones are excluded from traversal completely.

The algorithm guarantees that drones select the lowest-cost available path according to the graph constraints.

---

## Alternative Path Generation

To improve drone distribution and reduce congestion, the simulator generates alternative routes dynamically.

After a path is selected:

- Intermediate nodes receive temporary penalty values
- Future path calculations become less likely to reuse the same route
- Drones spread across multiple available paths

This design improves:

- Traffic balancing
- Parallel movement efficiency
- Congestion reduction
- Deadlock prevention

---

## Simulation Design

The simulation executes turn-by-turn.

During each turn:

1. Active drone transits are updated
2. Moving drones continue progressing
3. Waiting drones attempt new movements
4. Occupancy and connection capacities are validated
5. Successful moves are recorded and displayed

The simulation ends once all drones successfully reach the destination hub.

---

# Visual Representation

The project includes ANSI terminal color rendering to improve readability and visualization.

Zones may define colors using standard web color names such as:

```text
red
blue
gold
deepskyblue
```

Colors are converted into RGB ANSI escape sequences and rendered directly in the terminal.

This improves:

- Readability
- Visual distinction between zones
- Simulation tracking
- Overall user experience

---

# Rainbow Rendering Mode

The simulator also supports a special `rainbow` rendering mode.

Instead of applying a single color to text, each character receives a different RGB color, creating a rainbow effect.

Example:

```text
ZONE
```

This feature enhances terminal visualization and makes simulation output easier to follow during execution.

---

# Technical Choices

## Object-Oriented Design

The project follows an object-oriented architecture to separate responsibilities clearly.

| Component | Responsibility |
|---|---|
| `DroneState` | Stores drone runtime state |
| `Simulator` | Handles routing and simulation |
| `MyParser` | Parses map configuration files |
| `Zone` | Represents graph nodes |
| `Connection` | Represents graph edges |

This design improves:

- Maintainability
- Scalability
- Code readability
- Modularity

---

## Color Validation

The project uses the `webcolors` library to validate user-defined color names.

Invalid colors generate parsing errors to ensure deterministic and safe terminal rendering behavior.

---

# Documentation Standards

The project follows:

- PEP 257 docstring conventions
- Google-style documentation
- Static type annotations
- Modular programming principles

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

# AI Usage

AI tools were used during development for:

- Documentation improvements
- README structure organization
- Refactoring suggestions
- Debugging assistance

All final algorithms, architecture decisions, and implementations were manually validated and integrated by the project author me Yikoubaz.