import csv
import json
import bisect
import time

class Node:
    def __init__(self, geo_id, val = 0):
        self.geo_id = geo_id
        self.value = val
        self.neighbors = []

    def set_val(self, val):
        self.value = val

    def get_val(self):
        return self.value

    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)

    def get_neighbors(self):
        return self.neighbors

    def get_id(self):
        return self.geo_id

    def get_total_value(self):
        val = self.value
        for neighbor in self.neighbors:
            val += neighbor.get_val()
        return val

class Network:
    def __init__(self):
        self.nodes = {}
        self.sorted_list = []

    def add_node(self, node):
        self.nodes[node.get_id()] = node

    def has_node(self, geo_id):
        return geo_id in self.nodes

    def add_neighbors(self, geo_id, neighbor_ids):
        for neighbor in neighbor_ids:
            if neighbor in self.nodes:
                self.nodes[geo_id].add_neighbor(self.nodes[neighbor])
            else:
                self.add_node(Node(neighbor))
                self.nodes[geo_id].add_neighbor(self.nodes[neighbor])

    def get_val(self, arr):
        return arr[1]

    def initial_sort(self):
        self.sorted_list = [[n_id, node.get_total_value()] for n_id, node in self.nodes.items()]
        self.sorted_list.sort(key=self.get_val)

    def take(self):
        node_id = self.sorted_list[-1][0]
        val = self.nodes[node_id].get_total_value()
        self.nodes[node_id].set_val(0.0)
        for neighbor in self.nodes[node_id].get_neighbors():
            neighbor.set_val(0.0)
        return node_id, val

    def sort_single(self):
        node_summary = self.sorted_list[-1]
        node_summary[1] = self.nodes[node_summary[0]].get_total_value()
        self.sorted_list = self.sorted_list[:-1]
        index = bisect.bisect_left([item[1] for item in self.sorted_list], node_summary[1])
        self.sorted_list = self.sorted_list[:index] + [node_summary] + self.sorted_list[index:]
        return self.sorted_list[-1][1]==node_summary[1]

def read_network(json_filename, csv_file, census_file, compute_weight):
    json_file = open(json_filename)
    start = time.time()
    nodes = json.load(json_file)
    end = time.time()
    print('Reading JSON took ' + str(end - start) + ' seconds')
    weights = {}
    net = Network()
    features = {}
    
    start = time.time()
    with open(census_file) as featuresfile:
        featuresreader = csv.DictReader(featuresfile, delimiter=',')
        for row in featuresreader:
            working_pop = float(row['Population 16 Years and Over: in Labor Force'])
            salary = (float(row['Median Household Income (In 2017 Inflation Adjusted Dollars)'])*float(row['Households:.3']))/float(row['Population 16 Years and Over: in Labor Force']) if working_pop > 0 else float(row['Median Household Income (In 2017 Inflation Adjusted Dollars)'])
            features[row['geoID']] = [row['Total Population:'], salary, float(row['Pct. Population 25 Years and Over: Bachelor\'s Degree'])]
    end = time.time()
    print('Reading features CSV took ' + str(end - start) + ' seconds')

    start = time.time()
    num = 0
    with open(csv_file) as weightfile:
        weightreader = csv.DictReader(weightfile, delimiter=',')
        for row in weightreader:
            pop, salary, pct = features[row['geoID']]
            try:
                weights[row['geoID']] = compute_weight(pop, salary, pct, float(row['pred_pct_bachelors']))
                if float(row['pred_pct_bachelors']) < pct:
                    num+=1
            except:
                weights[row['geoID']] = compute_weight(pop, salary, pct, 0.0)
    end = time.time()
    print('Reading weights CSV took ' + str(end - start) + ' seconds')

    start = time.time()
    for key in nodes.keys():
        if net.has_node(key):
            net.nodes[key].set_val(weights[key] if key in weights else 0.0)
        else:
            net.add_node(Node(key, weights[key] if key in weights else 0.0))
        net.add_neighbors(key, nodes[key])
    end = time.time()
    print('Building graph took ' + str(end - start) + ' seconds')

    return net