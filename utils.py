import math
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import config


# compute difference between two solutions
def distance(market, centroid):
    return math.sqrt(math.pow((market['x_coord'] - centroid[0]), 2) + math.pow((market['y_coord'] - centroid[1]), 2))


# compute distance between two nodes
def distance_from_nodes(market1, market2):
    return math.sqrt(math.pow((market1['x_coord'] - market2['x_coord']), 2) + math.pow((market1['y_coord'] - market2['y_coord']), 2))


def compute_distances_and_sort(markets, centroid):
    for market in markets:
        market['distance'] = distance(market, centroid)
    markets.sort(key=lambda x: x['distance'], reverse=False)
    return markets


def compute_centroid(markets):
    x = 0
    y = 0
    for market in markets:
        x = x + market['x_coord']
        y = y + market['y_coord']
    x = x / len(markets);
    y = y / len(markets);
    return (x, y)

def markets_to_string(markets):
    #tmp = ""
    for market in markets:
        print(str(market['x_coord']) + '-' + str(market['y_coord']))


def compute_costs(tot_installation_cost, n_track_used, driver_cost, routes, cost_per_kilometer):
    tot_routes_distance = 0
    for route in routes:
        i = 0
        while i < (len(route) - 1):
            tot_routes_distance += distance_from_nodes(route[i], route[i + 1])
            i += 1

    tot_driver_cost = n_track_used * driver_cost
    tot_routes_cost = tot_routes_distance * cost_per_kilometer
    tot_cost = tot_installation_cost + tot_driver_cost + tot_routes_cost
    return tot_cost, tot_installation_cost, tot_driver_cost + tot_routes_cost

def add_max_minimart_param(filename,param): #function to edit the max_minimart param
    f = open(filename, 'r')  # pass an appropriate path of the required file
    lines = f.readlines()
    lines[5] = "param max_minimart:=  " + str(param) + " ;\n"
    f.close()
    f = open(filename, 'w')
    f.writelines(lines)
    f.close()

def restore_file(filename): #function to edit the max_minimart param
    f = open(filename, 'r')  # pass an appropriate path of the required file
    lines = f.readlines()
    lines[5] = "\n"
    f.close()
    f = open(filename, 'w')
    f.writelines(lines)
    f.close()

def write_solution_file():
    for index_dat in range(len(config.DATFILES)):
        f = open(config.DATFILES[index_dat].replace('.dat', '.txt'), 'w')  # pass an appropriate path of the required file
        lines = []

        lines.append(str(config.SOLUTIONS_COSTS[index_dat][0]) + '\n')
        lines.append(str(config.SOLUTIONS_COSTS[index_dat][1]) + '\n')
        lines.append(str(config.SOLUTIONS_COSTS[index_dat][2]) + '\n')

        opening = '1'
        for cluster in config.SOLUTION_CLUSTERS[index_dat]:
            for market in cluster:
                opening += ',' + str(market['idx'])
        opening += '\n'

        lines.append(opening)

        for route in config.SOLUTIONS_ROUTES[index_dat]:
            line = ''
            for node in route:
                line += str(node['idx']) + ','
            line = line[:-1] + '\n'
            lines.append(line)

        f.writelines(lines)
        f.close()

def get_market_data(ampl):
    parameters_df = []

    installed_df = ampl.getVariable('x').getValues().toPandas()
    installed_df.rename(columns={'x.val': 'installed'}, inplace=True)

    parameters_df.append(ampl.getParameter('Cx').getValues().toPandas())
    parameters_df.append(ampl.getParameter('Cy').getValues().toPandas())
    parameters_df.append(ampl.getParameter('Dc').getValues().toPandas())
    parameters_df.append(installed_df)

    parameters_df = pd.concat(parameters_df, axis=1, join='inner')
    parameters_df.reset_index(inplace=True, drop=True)
    parameters_df.rename(columns={'Cx': 'x_coord', 'Cy': 'y_coord'}, inplace=True)

    parameters_df = parameters_df[parameters_df.installed > 0]
    parameters_df.drop(columns='installed', inplace=True)

    return parameters_df

def get_capacity(ampl):
    return int(ampl.getParameter('capacity').getValues().toPandas().values)

def get_cost_per_kilometer(ampl):
    return int(ampl.getParameter('Vc').getValues().toPandas().values)

def get_driver_cost(ampl):
    return int(ampl.getParameter('Fc').getValues().toPandas().values)

def get_number_of_usable_markets(ampl):
    usable_df = ampl.getParameter('usable').getValues().toPandas()
    usable_df = usable_df[usable_df.usable > 0]
    return int(usable_df.shape[0])

def populate_node_clusters(markets, clusters, cluster_cardinality):
    central_market = markets[0]
    centroid = (central_market['x_coord'], central_market['y_coord'])
    markets = markets[1:]

    while len(markets) != 0:
        if len(markets) >= cluster_cardinality:  # if we have enough nodes left
            tmp = compute_distances_and_sort(markets=markets, centroid=centroid)
            
            # removing the nodes to be inserted into the current cluster from the list of all nodes
            markets = markets[cluster_cardinality:] 
                
            centroid = compute_centroid(tmp[:cluster_cardinality])  # updating the centroid
            clusters.append(tmp[:cluster_cardinality])  # appending the current cluster to the list of clusters
        else:  # putting the remaining nodes in the last cluster
            clusters.append(markets)
            markets = []

    return clusters

def compute_nearest_node(node, cluster):
    min_idx = np.inf
    min_dist = np.inf
    

    for idx in range(len(cluster)):
        tmp_dist = distance_from_nodes(node, cluster[idx])
        if tmp_dist < min_dist:
            nearest_node = cluster[idx]
            min_idx = idx
            min_dist = tmp_dist
    
    return min_idx, nearest_node  

def plot_solution(dafile_name, central_market, clusters, routes):
    fig_name = dafile_name.replace('.dat', '.png')

    for cluster in clusters:
        r = round(np.random.random(), 1)
        g = round(np.random.random(), 1)
        b = round(np.random.random(), 1)
        rgb = [r,g,b]
        for point in cluster:
            plt.plot(point['x_coord'], point['y_coord'], color=(rgb), marker='o')
        plt.plot(central_market['x_coord'], central_market['y_coord'], color=([0.0, 0.0, 0.0]), marker='o', markersize=14)

    for route in routes:
        route_x = []
        route_y = []
        for node in route:
            route_x.append(node['x_coord'])
            route_y.append(node['y_coord'])
        plt.plot(route_x, route_y)
    
    if config.PLOT_SOLUTION:
        if config.SAVEFIG:
            plt.savefig(fig_name)
        else:
            plt.show()  # in this way the execution ends only when the plot window is closed

    

    

    

    

