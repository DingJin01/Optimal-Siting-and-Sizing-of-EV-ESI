import pandas as pd
import numpy as np
import os
import networkx as nx

def process_csv(file_path):
    data = pd.read_csv(file_path, skiprows=3, header=0, delimiter=',')
    data = data.astype(str).replace('nan', '')

    return data.values

def generate_R():
    highway_node = pd.read_csv("data/Node.csv", header=None, delimiter=',')
    R = np.zeros((14, 24, 30))
    # Iterate over each node
    for k in range(1, 15):
        A = highway_node[highway_node.iloc[:, 6] == k].index.tolist()
        for i in A:
            file_path = os.path.join('data', highway_node.iloc[i, 5])
            Data = process_csv(file_path)
            for n in range(30):
                for t in range(6, 24):
                    try:
                        start_row = 96 * n + 4 * (t-1) + 4
                        end_row = start_row + 4
                        R[k-1, t-1, n] += np.sum(pd.to_numeric(Data[start_row:end_row, 4]))
                    except Exception as e:
                        print(f"Error processing data for node {k}, day {n}, time {t}: {e}")
                        continue
    R = np.nan_to_num(R,nan=0)

    return R


def generate_G(edges):
    G = nx.Graph()
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
    G = nx.convert_node_labels_to_integers(G, first_label=0)
    num_nodes = G.number_of_nodes()
    d = np.zeros((num_nodes, num_nodes))
    a = np.zeros((num_nodes, num_nodes, num_nodes), dtype=int)
    for i in range(num_nodes):
        lengths, paths = nx.single_source_dijkstra(G, i)
        for j in range(num_nodes):
            if i != j:
                d[i, j] = lengths[j]
                path = paths[j]
                for k in range(1, len(path) - 1):
                    intermediate = path[k]
                    a[i, j, intermediate] = 1
    Tij = d / 100
    
    return d, a, Tij

def generate_Vkt(observed_days, epsilon, R):
    R_n = np.sum(R, axis=(0, 1))
    position = int(np.ceil(observed_days * epsilon)) - 1
    n = np.argpartition(R_n, position)[position]
    subset = R[:, :, n]
    V_kt = np.ceil(0.005 * subset)

    return V_kt