import csv
import json

class Node:
    def __init__(val, geo_id):
        self.geo_id = geo_id
        self.value = val
        self.neighbors = []

    def __init__(geo_id):
        self.geo_id = geo_id
        self.value = 0
        self.neighbors = []

    def set_val(val):
        self.value = val

    def get_val():
        return self.value

    def add_neighbor(neighbor):
        self.neighbors.append(neighbor)

    def get_neighbors():
        return self.neighbors

    def get_id():
        return self.geo_id

    def get_total_value(taken):
        val = self.value
        for neighbor in self.neighbors:
            if not taken[neighbor]:
                val += neighbor.get_val()
        return val

class Network:
    def __init__():
        self.nodes = {}

    def add_node(node):
        self.nodes[node.get_id()] = node

    def has_node(geo_id):
        return geo_id in self.nodes

    def add_neighbors(geo_id, neighbor_ids):
        for neighbor in neighbor_ids:
            if neighbor in self.nodes:
                self.nodes[geo_id].add_neighbor(self.nodes[neighbor])
            else:
                self.add_node(Node(neighbor))
                self.nodes[geo_id].add_neighbor(self.nodes[neighbor])

    def get_val(node_id):
        return self.nodes[node_id].get_val()

    def initial_sort():
        self.sorted_list = self.nodes.keys()
        self.sorted_list.sort(key=self.get_val, reverse=true)

def read_network(json_file, csv_file, compute_weight):
    nodes = json.loads(json_file)
    weights = {}
    net = Network()
    with open(csv_file) as weightfile:
        weightreader = csv.reader(weightfile, delimiter=',')
        for row in weightreader[1:]:
            try:
                weights[row[0]] = compute_weight(pop, salary, pct, float(row[1]))
            except:
                weights[row[0]] = compute_weight(pop, salary, pct, 0.0)
    for key in nodes.keys():
        if net.has_node(key):
            net.nodes[key].set_val(weights[key])
        else:
            net.add_node(Node(key, weights[key]))
        net.add_neighbors(key, nodes[key])
    return net