from network_reader import read_network

def compute_added_average_salary(_, salary, pct, pct_pred):
    diff = (pct_pred - pct) if (pct_pred-pct) > 0 else 0
    return salary*(1-diff) + 50516*diff

def compute_added_total_salary(pop, salary, pct, pct_pred):
    diff = (pct_pred - pct) if (pct_pred-pct) > 0 else 0
    return salary*(1-diff)*pop + 50516*diff*pop