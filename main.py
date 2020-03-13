import networkx as nx
from itertools import combinations as combos
from functools import lru_cache
import time
import sys

DIMS = [2, 2, 2, 2]

foxhole_graph = nx.grid_graph(DIMS)
nodes = sorted(list(foxhole_graph))
corner = nodes[0]
next_to_corner = nodes[1]
part_0, part_1 = nx.algorithms.bipartite.sets(foxhole_graph)
part_0, part_1 = sorted(list(part_0)), sorted(list(part_1))

product = 1
for d in DIMS:
    product *= d
EVEN = product % 2 == 0


class GraphError(Exception):
    pass


@lru_cache(maxsize=10000)
def manhatDist(v_0, v_1):
    return sum([abs(x_0-x_1) for x_0, x_1 in zip(v_0, v_1)])


def reduceByCheckCount(check_count, top_layer, bot_layer, top_reachable_idxs):
    fraction_reachable_top = (len(top_reachable_idxs) - 0.1)/len(top_layer)
    lowest = 10**6
    result = []
    for top_subset_idxs in combos(top_reachable_idxs, check_count):
        top_remaining = [top_layer[idx]
                         for idx in top_reachable_idxs
                         if idx not in top_subset_idxs]

        reachable_bot = [v for v in bot_layer
                         if any(manhatDist(u, v) == 1 for u in top_remaining)]

        # print(top_subset_idxs, reachable_bot)

        fraction_reachable_bot = len(reachable_bot) - 0.1
        fraction_reachable_bot /= len(bot_layer)

        isDecreasing = (fraction_reachable_bot < fraction_reachable_top)
        isMonotonic = (fraction_reachable_bot <= fraction_reachable_top)
        evenCond = EVEN and isDecreasing
        oddCond = not EVEN and isMonotonic
        if evenCond or oddCond:
            if fraction_reachable_bot < lowest:
                result = []
                lowest = fraction_reachable_bot
            bot_reachable_idxs = [bot_layer.index(v)
                                  for v in reachable_bot]
            result.append((check_count, sorted(bot_reachable_idxs)))
    return result


def findReducingSet(
        top_reachable_idxs,
        top_layer, bot_layer,
        parent_graph):
    top_reachable_nodes = [v for idx, v in enumerate(top_layer)
                           if idx in top_reachable_idxs]
    low_end = min(len(DIMS) - 1, len(top_reachable_nodes))
    high_end = max(low_end, len(top_reachable_nodes))
    check_range = list(range(low_end, high_end + 1))

    '''
    Execute a sort of binary search on the check ranges
    See the wikipedia page for details
    '''
    left = 0
    right = len(check_range)
    reducingCheckCounts = []
    reductionResults = {}

    allCheckCounts = []  # Mostly for debugging
    while left <= right:
        check_idx = (left + right)//2
        check_count = check_range[check_idx]
        allCheckCounts.append(check_count)
        reduceSet = reduceByCheckCount(
                        check_count, top_layer,
                        bot_layer, top_reachable_idxs)
        if not reduceSet:
            left = check_idx + 1
        if reduceSet:
            reducingCheckCounts.append(check_count)
            reductionResults[check_count] = reduceSet
            right = check_idx - 1

    reducingCheckCounts.sort()
    lowestReducingIndex = reducingCheckCounts[0]
    result = reductionResults[lowestReducingIndex]
    return result


def createEdges(checks_idxs_pairs, top_label, bot_label, origin_idx_tuple):
    edges = []
    for min_checks, bot_reachable_idxs in checks_idxs_pairs:
        origin = (top_label, tuple(origin_idx_tuple))
        dest = (bot_label, tuple(bot_reachable_idxs))
        weight = min_checks
        if not bot_reachable_idxs:
            dest = 'END'
        edges.append((origin, dest, {'weight': weight}))
    return edges


def switchPartLabels(edgeList):
    newEdges = []
    for origin, dest, attr in edgeList:
        if type(origin) == str or type(dest) == str:
            continue
        origin_part_label, origin_idxs = origin
        dest_part_label, dest_idxs = dest
        new_origin = (dest_part_label, origin_idxs)
        new_dest = (origin_part_label, dest_idxs)
        newEdges.append((new_origin, new_dest, attr))
    return newEdges


def calcEdges(top, bot, top_label, bot_label, isomorphic=False):
    start = time.time()
    edges = []
    top_idxs = list(range(len(top)))
    check_range = range(1, len(top) + 1)
    for checkCount in check_range:
        for checkIdxs in combos(top_idxs, checkCount):
            checks_idxs_pairs = findReducingSet(
                    checkIdxs,
                    top, bot,
                    foxhole_graph)
            edges += createEdges(
                    checks_idxs_pairs,
                    top_label, bot_label,
                    checkIdxs)
    if isomorphic:
        edges += switchPartLabels(edges)
    end = time.time()
    print(f'calcEdges time: {end-start:.5}')
    return edges


def findPathByMaxWeight(graph, weight):
    sp = nx.algorithms.shortest_paths.generic.shortest_path
    sub_edges = [(u, v) for u, v in all_edges
                 if checkGraph[u][v]['weight'] <= weight]
    sub_graph = checkGraph.edge_subgraph(sub_edges)
    path = sp(sub_graph, 'START', 'END', weight='weight')
    return path


if __name__ == '__main__':
    done = False
    top_reachable_idxs = tuple([idx for idx, _ in enumerate(part_0)])
    bot_reachable_idxs = tuple([idx for idx, _ in enumerate(part_1)])

    checkGraph = nx.DiGraph()
    # vertices are (part number, index tuple)
    # edges have check count as weight
    PART_0_LABEL = 0
    PART_1_LABEL = 1

    source_0 = (PART_0_LABEL, top_reachable_idxs)
    source_1 = (PART_1_LABEL, bot_reachable_idxs)
    checkGraph.add_edge('START', source_0, weight=0)
    checkGraph.add_edge('START', source_1, weight=0)

    edges = []

    subgraph_0 = checkGraph.subgraph(part_0)
    subgraph_1 = checkGraph.subgraph(part_1)
    isomorphic = nx.is_isomorphic(subgraph_0, subgraph_1)
    edges += calcEdges(
            part_0, part_1,
            PART_0_LABEL, PART_1_LABEL,
            isomorphic=isomorphic)
    if not isomorphic:
        edges += calcEdges(part_1, part_0, PART_1_LABEL, PART_0_LABEL)

    checkGraph.add_edges_from(edges)

    all_edges = checkGraph.edges()

    print('Fox hole graph dimensions', DIMS)
    max_checks = max([checkGraph[u][v]['weight'] for u, v in all_edges])
    found = False
    for checks in range(max_checks + 1):
        try:
            path = findPathByMaxWeight(checkGraph, checks)
            found = True
            print(f'Result: {checks} check(s) per day')
            break
        except:
            pass
    if not found:
        print('Error: no checking path found')
