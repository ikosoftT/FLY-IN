from __future__ import annotations

import sys
from typing import List

from MyParser import MapParser, ParseError
from simulator import Simulator


def main(argv: List[str]) -> int:
    """
    Application entry point.

    Args:
        argv:
            Command-line arguments.

    Returns:
        Exit status code.
    """

    if len(argv) != 2:
        print(
            "Usage: python main.py <map-file>"
        )
        return 1

    path = argv[1]

    parser = MapParser()

    model = parser.parse_map(path)

    simulation = Simulator(model)

    simulation.run()

    return 0


if __name__ == "__main__":

    try:

        raise SystemExit(
            main(sys.argv)
        )

    except (
        ParseError,
        FileNotFoundError,
        KeyboardInterrupt,
    ) as error:

        print(f"ERROR: {error}")

        raise SystemExit(1)

    except Exception as error:

        print(
            f"Unexpected error: {error}"
        )

        raise SystemExit(1)
