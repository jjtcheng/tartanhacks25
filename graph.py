import networkx as nx
import numpy as np
import matplotlib.pyplot as plt



def analyze_source_shock(G, s, sources, reduction_factor=0.5):
    ls = [G.out_degree(source, weight="weight") for source in sources]
    all_produce = sum(ls)
    s_produce = G.out_degree(s, weight="weight")
    stat = s_produce*100 / all_produce

    # explored = set()
    frontier = [edge for edge in G.out_edges(s, data=True)]


    inflow = {}
    for node in G.nodes():
        inflow[node] = sum(G[u][node]['weight'] for u in G.predecessors(node))

    final_inflow = inflow.copy()

    G_new = G.copy()
    topo_order = list(nx.topological_sort(G))
    s_found = False
    for u in topo_order:
        if u != s and not s_found:
            continue

        if u == s:
            s_found = True
            out_edges = list(G.out_edges(u, data=True))
            for _, v, attr in out_edges:
                final_inflow[v] = final_inflow[v] - attr['weight']*reduction_factor
                G_new[u][v]['weight'] = G_new[u][v]['weight'] - attr['weight']*reduction_factor

        elif final_inflow[u] < inflow[u]:
            factor = 1-(final_inflow[u] / inflow[u])

            out_edges = list(G.out_edges(u, data=True))
            for _, v, attr in out_edges:
                final_inflow[v] -= attr['weight'] * factor
                G_new[u][v]['weight'] -= attr['weight']*factor

    return stat, G_new


    
def display_graph(G, dag=False, block=False):
    if dag:
        for layer, nodes in enumerate(nx.topological_generations(G)):
            for node in nodes:
                G.nodes[node]["layer"] = layer
        pos = nx.multipartite_layout(G, subset_key="layer")
    else:
        pos = nx.circular_layout(G)
    labels = nx.get_edge_attributes(G, 'weight')
    labels = {(u, v) : round(w, 2) for (u, v), w in labels.items()}
    fig = plt.figure()
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    nx.draw_networkx(G, pos)

    return fig

def construct_graph(transactions):
    G = nx.DiGraph()
    for transaction in transactions:
        source, dest, num_eggs = transaction[0], transaction[1], float(transaction[2])
        G.add_edge(source, dest, weight=num_eggs)
    return G


        
def analyze_transactions(transactions):
    G_weighted = nx.DiGraph()
    G_unweighted = nx.DiGraph()
    for transaction in transactions:
        source, dest, num_eggs = transaction[0], transaction[1], float(transaction[2])
        G_weighted.add_edge(source, dest, weight=num_eggs)
        G_unweighted.add_edge(source, dest)

    nodes = nx.betweenness_centrality(G_unweighted)
    # Dictionary of node->betweenness centrality score
    return nodes