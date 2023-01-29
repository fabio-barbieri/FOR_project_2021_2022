from amplpy import AMPL, Environment
import utils
import math
import numpy as np
import config
from copy import deepcopy
import time

min_minimart = -1
max_minimart = -1

start = time.time()

# MINIMART INSTALLATION
for index_dat in range(len(config.DATFILES)):
    for indx in range(config.NUMBER_OF_ITERATIONS):

        tot_installation_cost = 0

        ampl = AMPL(Environment(config.PATH_TO_AMPL_EXECUTABLE))
        ampl.reset()

        dat_file = config.DATFILES[index_dat]
        if(min_minimart==-1):
            mod_file = 'minimart_minimum.mod'
        else:
            mod_file = 'minimart_atleast.mod'
            min_minimart = min_minimart + 1
            if min_minimart > (config.FRACTIONS_OF_MINIMART) * (max_minimart - 1):
                # this is done to interrupt the cycle when trying the solution with max usable market
                break
            utils.add_max_minimart_param(dat_file,min_minimart)

        ampl.read(mod_file)
        ampl.read_data(dat_file)

        ampl.solve()

        # Getting the data (parameters and variables) from AMPL solver
        parameters_df = utils.get_market_data(ampl)
        Vc = utils.get_cost_per_kilometer(ampl)
        Fc = utils.get_driver_cost(ampl)
        capacity = utils.get_capacity(ampl)

        if (min_minimart == -1): #set minimum
            min_minimart = len(parameters_df)
            max_minimart = utils.get_number_of_usable_markets(ampl)
        
        # VEHICLE ROUTING PROBLEM
        # Creating array containing all the markets built in the AMPL solution
        markets = []
        for idx, row in parameters_df.iterrows():
            market_dict = {}
            market_dict['idx'] = idx + 1
            market_dict['x_coord'] = row['x_coord']
            market_dict['y_coord'] = row['y_coord']
            market_dict['distance'] = 0
            tot_installation_cost += row['Dc']
            markets.append(market_dict)

        # Getting some parameters
        # number_of_trucks == number of routes that should be planned
        min_number_of_trucks = math.ceil((len(markets) - 1) / capacity)
        # number of nodes that will be contained in each cluster
        cluster_cardinality = 2 * min_number_of_trucks

        # Dividing all nodes into different clusters
        # 1. first cluster contains the first N nodes with minimum distance from the central node
        # 2. the second cluster contains the first N nodes with minimum distance from the centroid of the first cluster
        # 3. the third cluster contains the first N nodes with minimum distance from the centroid of the second cluster
        # 4. and so on.1.
        clusters = []  # list containing the clusters
        clusters = utils.populate_node_clusters(markets, clusters, cluster_cardinality)
        safe_clusters = deepcopy(clusters)
        config.CLUSTERS = deepcopy(clusters)

        # COMPUTING THE ROUTES
        best_routes = []
        min_cost = (np.inf, 0, 0)

        for _ in range(config.NUM_ITERATIONS_VRP):
            routes = []
            routes_indices = []
            clusters = deepcopy(safe_clusters)
            i = 0
            for _ in range(min_number_of_trucks):
                routes.append([markets[0]])
                routes_indices.append(i)
                i += 1

            for cl_idx in range(len(clusters)):
                tmp_indices = deepcopy(routes_indices)
                while len(tmp_indices) > 0:
                    del_from_tmp_indices = np.random.randint(0, len(tmp_indices))
                    curr_idx = tmp_indices[del_from_tmp_indices]
                    route = routes[curr_idx]
                    if len(clusters[cl_idx]) != 0:
                        nearest_idx, nearest_node = utils.compute_nearest_node(route[-1], clusters[cl_idx])
                        route.append(nearest_node)
                        del clusters[cl_idx][nearest_idx]
                    del tmp_indices[del_from_tmp_indices]
            
            while cl_idx >= -1:
                tmp_indices = deepcopy(routes_indices)
                while len(tmp_indices) > 0:
                    del_from_tmp_indices = np.random.randint(0, len(tmp_indices))
                    curr_idx = tmp_indices[del_from_tmp_indices]
                    route = routes[curr_idx]
                    if cl_idx == -1:
                        route.append(markets[0])
                        del tmp_indices[del_from_tmp_indices]
                    else:
                        if len(clusters[cl_idx]) != 0:
                            nearest_idx, nearest_node = utils.compute_nearest_node(route[-1], clusters[cl_idx])
                            route.append(nearest_node)
                            del clusters[cl_idx][nearest_idx]
                        del tmp_indices[del_from_tmp_indices]
                cl_idx -= 1

            tmp_cost = utils.compute_costs(tot_installation_cost=tot_installation_cost ,n_track_used=min_number_of_trucks, driver_cost=Fc, routes=routes, cost_per_kilometer=Vc)

            if tmp_cost[0] < min_cost[0]:
                best_routes = deepcopy(routes)
                min_cost = tmp_cost

        if(len(config.SOLUTIONS_COSTS)==index_dat):
            config.SOLUTIONS_COSTS.append(min_cost)
            config.SOLUTIONS_ROUTES.append(best_routes)
            config.SOLUTION_CLUSTERS.append(config.CLUSTERS)
        else:
            if(config.SOLUTIONS_COSTS[index_dat][0] > min_cost[0]):
                config.SOLUTIONS_COSTS[index_dat] = min_cost
                config.SOLUTIONS_ROUTES[index_dat] = best_routes
                config.SOLUTION_CLUSTERS[index_dat] = config.CLUSTERS
    
    utils.restore_file(config.DATFILES[index_dat])
    min_minimart = -1
    max_minimart = -1

    # PLOT THE BEST SOLUTION  
    utils.plot_solution(config.DATFILES[index_dat], markets[0], config.SOLUTION_CLUSTERS[index_dat], config.SOLUTIONS_ROUTES[index_dat])

utils.write_solution_file()

print('COMPUTATION ENDED')
print('Elpsed time (s): ')
print(str(time.time() - start))







