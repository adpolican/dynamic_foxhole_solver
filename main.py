import networkx as nx
from itertools import combinations as combos
import numpy as np
from typing import List, Tuple
from multiprocessing import Pool
import time


DIMS = [3, 3, 3]

foxhole_graph = nx.grid_graph(DIMS)
nodes = sorted(list(foxhole_graph))
corner = nodes[0]
next_to_corner = nodes[1]
part_0, part_1 = nx.algorithms.bipartite.sets(foxhole_graph)
part_0, part_1 = sorted(list(part_0)), sorted(list(part_1))


class GraphError(Exception):
    pass


def findReducingSet(
        top_reachable_idxs,
        top_layer, bot_layer,
        parent_graph):
    top_reachable_nodes = [v for idx, v in enumerate(top_layer)
                           if idx in top_reachable_idxs]
    layer_graph = nx.subgraph(parent_graph, top_reachable_nodes + bot_layer)
    result = None
    fraction_reachable_top = (len(top_reachable_idxs) - 0.1)/len(top_layer)
    for check_count in range(1, len(top_reachable_nodes)+1):
        lowest = 10**6
        result = []
        for top_subset_idxs in combos(top_reachable_idxs, check_count):
            top_remaining = [top_layer[idx] for idx in top_reachable_idxs
                             if idx not in top_subset_idxs]
            ind_graph = nx.subgraph(layer_graph, top_remaining + bot_layer)
            isolates_after = list(nx.isolates(ind_graph))
            reachable_bot = [v for v in bot_layer if v not in isolates_after]

            fraction_reachable_bot = len(reachable_bot) - 0.1
            fraction_reachable_bot /= len(bot_layer)

            top_isolates = [i for i in isolates_after
                            if i in top_layer and i not in top_subset_idxs]

            if any(top_isolates):
                msg = 'Isolates in the top_layer of induced subgraph'
                raise GraphError(msg)

            if fraction_reachable_bot <= fraction_reachable_top:
                if fraction_reachable_bot < lowest:
                    result = []
                    lowest = fraction_reachable_bot
                bot_reachable_idxs = [bot_layer.index(v)
                                      for v in reachable_bot]
                result.append((check_count, sorted(bot_reachable_idxs)))
        if result:
            break

    if result is None:
        raise GraphError('No possible way to disconnect')

    return result


if __name__ == '__main__':
    done = False
    all_checks: List[Tuple[int, ...]] = []
    top_reachable_idxs = [idx for idx, _ in enumerate(part_0)]
    bot_reachable_idxs = [idx for idx, _ in enumerate(part_1)]

    checkGraph = nx.DiGraph()
    # vertices are (part number, index tuple)
    # edges have check count as weight
    PART_0 = 0
    PART_1 = 1

    checkGraph.add_edge('START', (PART_0, tuple(top_reachable_idxs)), weight=0)
    checkGraph.add_edge('START', (PART_1, tuple(bot_reachable_idxs)), weight=0)

    edges = []

    top = part_0
    bot = part_1
    start = time.time()
    for checkCount in range(1, len(top) + 1):
        for checkIdxs in combos(range(len(top)), checkCount):
            checks_and_idxs = findReducingSet(checkIdxs, top, bot, foxhole_graph)
            for min_checks, bot_reachable_idxs in checks_and_idxs:
                origin = (PART_0, tuple(checkIdxs))
                dest = (PART_1, tuple(bot_reachable_idxs))
                weight = min_checks
                if not bot_reachable_idxs:
                    dest = 'END'
                edges.append((origin, dest, {'weight': weight}))
    end = time.time()
    print(f'checkCount: {end-start:.5}')

    top = part_1
    bot = part_0
    start = time.time()
    for checkCount in range(1, len(top) + 1):
        for checkIdxs in combos(range(len(top)), checkCount):
            checks_and_idxs = findReducingSet(checkIdxs, top, bot, foxhole_graph)
            for min_checks, bot_reachable_idxs in checks_and_idxs:
                origin = (PART_1, tuple(checkIdxs))
                dest = (PART_0, tuple(bot_reachable_idxs))
                weight = min_checks
                if not bot_reachable_idxs:
                    dest = 'END'
                edges.append((origin, dest, {'weight': weight}))
    end = time.time()
    print(f'checkCount: {end-start:.5}')

    checkGraph.add_edges_from(edges)

    all_edges = checkGraph.edges()

    sp = nx.algorithms.shortest_paths.generic.shortest_path
    max_checks = max([checkGraph[u][v]['weight'] for u, v in all_edges])
    for checks in range(max_checks + 1):
        sub_edges = [(u, v) for u, v in all_edges
                     if checkGraph[u][v]['weight'] <= checks]
        sub_graph = checkGraph.edge_subgraph(sub_edges)
        try:
            path = sp(sub_graph, 'START', 'END', weight='weight')
            checkCount = 0
            for origin, dest in zip(path, path[1:]):
                checkCount = max(checkCount, checkGraph[origin][dest]['weight'])
            print('Fox hole graph dimensions', DIMS)
            print(f'Result: {checkCount} check{"s" if (checkCount-1) else ""} per day')
            break
        except:
            pass
