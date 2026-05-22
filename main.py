import sys
from typing import List
from MyParser import parse_map
from simulator import Simulator


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: python main.py <map-file>")
        return 1
    path = argv[1]

    model = parse_map(path)

    full_pipline = Simulator(model)
    full_pipline.run()

    return 0


if __name__ == '__main__':
    try:
        main(sys.argv)
    except (Exception, KeyboardInterrupt) as e:
        print("ERORR:", e)
