from network_reader import read_network

def compute_added_average_salary(_, salary, pct, pct_pred):
    diff = (pct_pred - pct) if (pct_pred-pct) > 0 else 0
    return salary*(1-diff) + 50516*diff

def compute_added_total_salary(pop, salary, pct, pct_pred):
    diff = (pct_pred - pct) if (pct_pred-pct) > 0 else 0
    return salary*(1-diff)*pop + 50516*diff*pop

def top_k_locations(graph_file, prediction_file, census_file, k, compute_weight):
    network = read_network(graph_file, prediction_file, census_file, compute_weight)
    network.initial_sort()
    outtext = ""
    for i in range(k)-1:
        top, value = network.take()
        outtext += top + ": " + str(value) + "\n"
        outtext
        while(True):
            if network.sort_single():
                break
    top, value = network.take()
    outtext += top + ": " + str(value)
    f = open("output.txt", "w+")
    f.write(outtext)
    f.close()


if(__name__=='__main__'):
    top_k_locations('../data/tracts_in_buffer.json', '../data/pct_bachelors_predictions.csv', '../data/census_tract_feats.csv', 100, compute_added_average_salary)