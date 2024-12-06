# using PuLP library to generate code that can be solved by different solvers
from pulp import *
import numpy as np
import pandas as pd
import math
# Use relative import
from .utils import print_route, print_terminal


def mip_problem(n_couriers, n_items, capacities, item_size, D, verbose=False):
    '''
    Problem constraints modelling:_____________________________________________________________________________________________________
    0. Ensure that capacity constraints are satisfied
    1. Ensure that exactly m salesman depart from node n+1 (depot)
    2. Ensure that exactly m salesman return to node n+1 (depot)
    3. Ensure that each city is visited
    4. Flow conservation constraint - once a salesman enters a city, he must leave the same city
    5. Subtour elimination constraints
    6. Avoid backtracking of courier - if one arch is used, the opposite arch is not used'''
    
    MTSP = LpProblem("Multiple_TSP", LpMinimize)    # minimize the total distance traveled by all couriers
    n_cities = D.shape[0]-1                         # n_citites excludes the depot
    depot_idx = n_cities+1                          # depot_idx is the last city
    
    if verbose:
        print_terminal(D, n_couriers, n_items, capacities, item_size)
    
    
    # Objective function bounds_______________________________________________________________________________________________________
    
    #upper_bound = sum(D.flatten())//2
    #maximum_dist_two_cities = max([D[i][j] for i in range(depot_idx) for j in range(depot_idx)])
    #div = math.ceil(n_items//n_couriers)
    #upper_bound = maximum_dist_two_cities * div + min_round_trip
    
    # Summing consecutive cities distances - upper bound for the objective function of a TSP problem
    #upper_bound = D[depot_idx-1][0] + sum([ (D[i][i+1]) for i in range(depot_idx-1) ])
    #upper_bound = max([D[depot_idx-1][i] for i in range(n_cities)]) + sum([ (D[i][i+1]) for i in range(depot_idx-1) ])             # istance 7 way faster compared to the previous line 
    
    lower_bound = max([ (D[depot_idx-1][i] + D[i][depot_idx-1]) for i in range(0,n_cities) ])                                       # longest round-trip
    
    consec = sum([ (D[i][i+1]) for i in range(n_cities-1) ])                                    # summing consecutive cities distance
    upper_bound = math.ceil(consec/n_couriers) + lower_bound                                   # dividing distance by number of couriers
    
    
    print('Upper bound:', upper_bound)
    

    
    
    # Variables definition______________________________________________________________________________________________________________
    # Variables route[i][j][k] means that courier k has used arch (i,j) to leave city i and reach city j
    route = LpVariable.dicts("route", (range(depot_idx), range(depot_idx), range(n_couriers)), cat="Binary")
    min_round_trip = min( [ (D[depot_idx-1][i] + D[i][depot_idx-1]) for i in range(0,n_cities)] )                                   # minimum distance a courier can travel
    cour_dist = [LpVariable("Courier_Distance_%d" % k, lowBound=min_round_trip, upBound=upper_bound) for k in range(n_couriers)]    #unbounding this variables from integer type makes istances faster
    
    # value constrained by upBound
    bag_weight = [LpVariable("Courier_Capacity_%d" % k, lowBound=0, upBound=capacities[k]) for k in range(n_couriers)]
    
    # Equality constraints to set variable values involve a binary variable multiplied by a costant: linear
    for k in range(n_couriers):
        MTSP += cour_dist[k] == lpSum( route[i][j][k] * D[i][j] for i in range(0,depot_idx) for j in range(0,depot_idx) )
        MTSP += bag_weight[k] == lpSum( route[i][j][k] * item_size[j] for i in range(0,depot_idx) for j in range(0,n_cities) )      # depot_idx excluded for arrival cities 
        
        #cour_dist[k] = sum( route[i][j][k] * D[i][j] for i in range(0,depot_idx) for j in range(0,depot_idx) )
        #bag_weight[k] = sum( route[i][j][k] * item_size[j] for i in range(0,depot_idx) for j in range(0,n_cities) )                 # depot_idx excluded for arrival cities
        
        #0. Ensure that capacity constraints are satisfied_____________________________________________________________________________
        # Already constrained with variable upBound, adding it makes the istance slower
        #MTSP += bag_weight[k] <= capacities[k]  # capacity constraint

    
    
    # __ SETTING MINMAX PROBLEM: minimize each cour dist separately for fairness  _____________________________________________________
    #To achieve a fair division among drivers, the objective is to minimize the maximum distance travelled by any courier.
    
    # constraining max distance for each courier with upBound and lowBound
    max_allowed_distance = LpVariable("Objective_Function", lowBound=lower_bound, upBound=upper_bound)
    for k in range(n_couriers):                                        
        MTSP += cour_dist[k] <= max_allowed_distance    # each courier distance must be less than the objective function
    
    MTSP += max_allowed_distance    # assigning the objective function to minimize
    
    # Constraints to model the problem____________________________________________________________________________________________________
    
    #1.2. Depot constraints_______________________________________________________________________________________________________________
    for k in range(n_couriers):
        #1. Ensure that exactly m salesman depart from node n+1 (depot) exactly once. Ensure that variable will be 1______________________
        # the sum of route[depot_idx][j][k] for all j must be equal to 1 for same courier k
        MTSP += lpSum( route[depot_idx-1][j][k] for j in range(0,n_cities) ) == 1
        #2. Ensure that exactly m salesman return to node n+1 (depot_idx)_________________________________________________________________
        # the sum of route[i][depot_idx][k] for all i must be equal to 1 for same courier k (one and only one return to depot)
        MTSP += lpSum( route[i][depot_idx-1][k] for i in range(0,n_cities) ) == 1
        
        '''
        # additional equality constraint for the depot -> redundant, makes the istance slower
        MTSP += lpSum(route[depot_idx-1][j][k] for j in range(n_cities)) == lpSum(route[j][depot_idx-1][k] for j in range(n_cities))'''
    
    
    #3. Ensure that each city is visited. Each city must be served_______________________________________________________________________
    for j in range(0,n_cities): # arrival at all cities excluding depot_idx, but including for departure
        MTSP += lpSum( route[i][j][k] for i in range(0,depot_idx) for k in range(n_couriers) ) == 1
        
    
    #4. Flow conservation constraint - once a salesman enters a city, he must leave the same city - not includig depot___________________
    # for each city i, the sum of all the variables that represent arrival at city j must be equal to the sum of all the variables that represent departure from city i
    for j in range(0,n_cities): # only cities excluding depot_idx for arrival cities, but considering also depot_idx for departure
        for k in range(n_couriers):
            MTSP += lpSum( route[i][j][k] for i in range(0,depot_idx) ) == lpSum( route[j][z][k] for z in range(0,depot_idx) )
            
    
    # 5. Subtour elimination constraint (Miller-Tucker-Zemlin formulation)_______________________________________________________________
    # the MTZ constraints force the u variables to represent a valid ordering of the cities if the corresponding x variables indicate that those cities are visited by a courier
    # assigned logically within the optimization model itself to ensure that the selected routes form valid, complete tours without subtours
    u = LpVariable.dicts("u", (range(n_cities), range(n_couriers)), 0, n_cities, cat='Integer')  
    for k in range(n_couriers):
        for i in range(n_cities):
            for j in range(0,n_cities):
                if i != j:
                    # if edge used, then u[i] <= u[j]-1
                    MTSP += u[i][k] - u[j][k] + (n_cities) * route[i][j][k] <= n_cities - 1
                    
    
                    
    
    # additional implied constraints_____________________________________________________________________________________________________
    # 6. ensure that if one arch is used, the opposite arch is not used (couriers cannot go back to the city where they are coming from).
    # Not inclding depot_idx to include case where courier could have only one city to visit.
    for i in range(0,n_cities):
        for j in range(0,n_cities):
            for k in range(n_couriers):
                MTSP += route[i][j][k] + route[j][i][k] <= 1

    
    # Test constraints_____________________________________________________________________________________________________________________
    
    '''
    # Simmetry breaking constraints for couriers with the same capacity
    for k1 in range(n_couriers):
        for k2 in range(k1 + 1, n_couriers):  # Only compare each pair once
            if capacities[k1] == capacities[k2]:
                for i in range(n_cities):
                    for j in range(n_cities):
                        if i == j:
                            continue  # Skip invalid arcs
                        MTSP += route[i][j][k1] <= route[i][j][k2]'''
                        
    
    '''
    # don't allow to go from a city to itself
    for k in range(n_couriers):
        for i in range(0,n_cities):
            MTSP += route[i][i][k] == 0'''
    
    '''
    # Each courier should visit at least one city -> redundant
    for k in range(n_couriers):
        MTSP += lpSum( route[i][j][k] for i in range(0,depot_idx) for j in range(0,depot_idx) ) >= 1'''
                            
    return MTSP, route, max_allowed_distance, cour_dist