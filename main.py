from parser import parse_file
from graph import Graph

def main():
    parsed_data = parse_file("maps/easy/01_linear_path.txt")

    graph = Graph(parsed_data)

    print(graph.get_neighbors(graph.start.name))
    print(graph.get_connections("waypoint1", "waypoint2"))
  

main()
