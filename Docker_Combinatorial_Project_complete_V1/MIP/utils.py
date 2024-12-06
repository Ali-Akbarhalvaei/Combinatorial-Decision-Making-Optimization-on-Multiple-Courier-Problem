from pulp import value  # using the PuLP library in order to have a solver INDEPENDENT language.
import numpy as np
import pandas as pd
import json
import os
from IPython.display import display


def print_route(route, depot_index, n_couriers):
    for k in range(n_couriers):
        print(f"Courier {k+1} path:")
        for i in range(depot_index):
            print([route[i][j][k].varValue for j in range(depot_index)])
            
def print_terminal(D, n_couriers, n_items, capacities, item_size):
    print()
    print('Distance Matrix Dimensions:',D.shape)
    print()
    print('DMatrix first value:',D[0][0])
    print('Number of Couriers:',n_couriers)
    print('Number of Items:',n_items)
    print('Courier Capacities:',capacities)
    print('Item Sizes:',item_size)
    print()
        

def retrieve_istance(n):
    '''
    Istance .dat file format
    m - number of couriers
    n - number of items
    li - load size for courier i
    sj - size of object j
    D - Distance Matrix
    '''
    # change the working directory to the directory where the script is located
    dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(dir)                                                   # change current directory to path
    
    if n < 10:
        in_path = f"/app/instances/dat_instances/inst0{n}.dat"
    else:
        in_path = f"/app/instances/dat_instances/inst{n}.dat"

    f = open(in_path)
    lines = [line for line in f]
    f.close()
    
    n_couriers = int(lines[0].rstrip('\n'))                         # number of couriers is in line 1
    n_items = int(lines[1].rstrip('\n'))                            # number of items is in line 2
    
    load_i = list(map(int, lines[2].rstrip( '\n').split()))         # load size for courier i is in line 3
    obj_size_j = list(map(int, lines[3].rstrip('\n').split()))      # size of object j is in line 4
    
    for i in range(4, len(lines)):
        lines[i] = lines[i].rstrip('\n').split()

    D_j_i = np.array([[lines[j][i] for i in range(len(lines[j]))] for j in range(4, len(lines))])
    D_j_i = D_j_i.astype(int)
    
    print("\nIstance", n, "retrieved successfully.\n")
    
    return n_couriers, n_items, load_i, obj_size_j, D_j_i


def couriers_paths(x, depot_node, n_couriers):
    routes = [[] for _ in range(n_couriers)]  # Initialize list of routes for each courier
    
    for k in range(n_couriers):
        current_city = depot_node - 1       # Start at the depot
        routes[k].append(0)                # Route at index k starts at the depot, marked by number -1
    
        visited = []            # Keep track of visited cities for this courier
        
        while True:
            next_city = -1                  # Initialize next city to non existent city
            
            for j in range(depot_node):   # Iterate over all cities including the depot
                if value(x[current_city][j][k]) is not None and value(x[current_city][j][k]) > 0.9: # Check if the edge is used
                    next_city = j
                    break

            if next_city == -1: # Check for no next city.
                routes[k].append('No Outgoing Edges') 
                break  # Exit loop if no more outgoing edges
            
            if next_city in visited: # Check for subtour
                routes[k].append(next_city+1)
                routes[k].append('Subtour') # Mark that previous city has been already visited
                break                      #Exit loop if subtour is found

            if next_city == depot_node-1:
                routes[k].append(0) # Mark that the courier has returned to the depot
                break
            
            routes[k].append(next_city+1)   # Append the next city to the route, summing 1 to remove 0-indexing
            visited.append(next_city)
            current_city = next_city

        
        # if at the end of the loop the next city is not the depot, mark an incomplete path
        if next_city != depot_node-1 and next_city != -1: # handle subtours + incomplete paths
            routes[k].append('Incomplete') # Mark an incomplete path ending in not the depot

    return routes


def convert_to_json(x,n_cities,n_couriers,time,optimal,obj):
    if obj < 0: # if obj. function is negative return N/A
        return {"time": time, "optimal": optimal, "obj": "N/A", "sol": []}
    else:
        c_paths = couriers_paths(x,n_cities, n_couriers)
        return {"time": time, "optimal": optimal, "obj": round(obj), "sol": c_paths}


def save_json(instance, json_dict):
    # Get the directory of the current script
    # Define the results directory using the mounted volume path
    results_path = f"/app/res/MIP/{instance}.json"
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w') as file:
        json.dump(json_dict, file, indent=3)
