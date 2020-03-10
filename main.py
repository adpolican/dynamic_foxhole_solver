import networkx as nx
from itertools import combinations as combos
import numpy as np
from typing import List, Tuple


DIMS = [10, 1]


def mapping(x):
    return x


foxhole_graph = nx.relabel_nodes(nx.grid_graph(DIMS), mapping)
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
    '''
    top_reachable is a list of indices
    top_layer should be a subgraph of a component
    bot_layer should be a full compenent
    '''
    '''
    def l2(x):
        return sum(top_layer[x])
    top_reachable_idxs = sorted(top_reachable_idxs, key=l2)
    '''
    top_reachable_nodes = [v for idx, v in enumerate(top_layer)
                           if idx in top_reachable_idxs]
    layer_graph = nx.subgraph(parent_graph, top_reachable_nodes + bot_layer)
    result = None
    fraction_reachable_top = (len(top_reachable_idxs) - 0.1)/len(top_layer)
    for check_count in range(1, len(top_reachable_nodes)+1):
        lowest = 10**6
        '''
        print('Check count---------------', check_count)
        '''
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

            '''
            print('top_reachable_idxs', top_reachable_idxs)
            print('top_subset_idxs', top_subset_idxs)
            print('top_remaining', top_remaining)
            print('top_layer', top_layer)
            print('bot_layer', bot_layer)
            print('reachable_bot', reachable_bot)
            print('fraction_reachable_bot', fraction_reachable_bot)
            print('fraction_reachable_top', fraction_reachable_top)
            '''
            if any(top_isolates):
                msg = 'Isolates in the top_layer of induced subgraph'
                raise GraphError(msg)

            if fraction_reachable_bot < fraction_reachable_top:
                # if fraction_reachable_bot < lowest):
                bot_reachable_idxs = [bot_layer.index(v)
                                      for v in reachable_bot]
                result = check_count, sorted(bot_reachable_idxs)
        if result is not None:
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

    checkGraph.add_edge('START', ('part_0', tuple(top_reachable_idxs)), weight=0)
    checkGraph.add_edge('START', ('part_1', tuple(bot_reachable_idxs)), weight=0)

    top = part_0
    bot = part_1
    for checkCount in range(1, len(top) + 1):
        for checkIdxs in combos(range(len(top)), checkCount):
            _ = findReducingSet(checkIdxs, top, bot, foxhole_graph)
            min_checks, bot_reachable_idxs = _
            origin = ('part_0', tuple(checkIdxs))
            dest = ('part_1', tuple(bot_reachable_idxs))
            weight = min_checks
            if not bot_reachable_idxs:
                dest = 'END'
            print(origin, dest, weight)
            checkGraph.add_edge(origin, dest, weight=weight)

    top = part_1
    bot = part_0
    for checkCount in range(1, len(top) + 1):
        for checkIdxs in combos(range(len(top)), checkCount):
            _ = findReducingSet(checkIdxs, top, bot, foxhole_graph)
            min_checks, bot_reachable_idxs = _
            origin = ('part_1', tuple(checkIdxs))
            dest = ('part_0', tuple(bot_reachable_idxs))
            weight = min_checks
            if not bot_reachable_idxs:
                dest = 'END'
            print(origin, dest, weight)
            checkGraph.add_edge(origin, dest, weight=weight)

    sp = nx.algorithms.shortest_paths.generic.shortest_path
    path = sp(checkGraph, 'START', 'END', weight='weight')
    print('RESULT:', path)
    for origin, dest in zip(path, path[1:]):
        print(checkGraph[origin][dest]['weight'])

    

    '''
    top = part_0
    bot = part_1
    while not done:
        _ = findReducingSet(top_reachable_idxs, top, bot, foxhole_graph)
        top_check_idxs, bot_reachable_idxs = _
        top_reachable_idxs = bot_reachable_idxs
        done = not bot_reachable_idxs
        all_checks.append(top_check_idxs)
        top, bot = bot, top
    print(f'{max(all_checks)} checks per day')
    '''
