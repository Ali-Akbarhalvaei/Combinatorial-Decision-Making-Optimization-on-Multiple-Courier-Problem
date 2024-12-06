import signal
import numpy as np
import gurobipy as gp
import highspy as hp
from pulp import *
# Use relative imports
from .mip_problem import *
from .utils import *
import argparse
import multiprocessing
import time
import os

def solve(solver, instance, time_limit=300, verbose=False):
    n_couriers, n_items, load_i, obj_size_j, D = retrieve_istance(instance)
    MTSP, route, max_dist, distances = mip_problem(n_couriers, n_items, load_i, obj_size_j, D, verbose=verbose)
    depot_node = D.shape[0]  # depot is the last city n+1
   
    MTSP.solve(solver)
        
    # If solution found within time, process solution results
    status = LpStatus[MTSP.status]
    optimal = status == "Optimal"
        
    # Calculate distance metrics if solved
    '''tot_distance = sum(
        [ (route[i][j][k].varValue or 0) * D[i][j]
        for i in range(0, depot_node) for j in range(0, depot_node)
        for k in range(n_couriers)
        ]
    )'''
    obj = MTSP.objective.value()
    solution_time = MTSP.solutionTime
    
    # giving some margin to the time limit since timer is not precise but optimal solution can be still found in around 300 plus extra milliseconds (inst 13 is 300.12 w. cbc, 300.00 with highs)
    if solution_time > time_limit and solution_time < time_limit+5:
        solution_time = 300

    if verbose:
        print_route(route, depot_node, n_couriers)
    
    
    if solution_time > time_limit+5:
        print(f"Solution for instance {instance} timed out and no solution was available.")
        return [], depot_node, n_couriers, 300, False, -1, distances
    
    return route, depot_node, n_couriers, solution_time, optimal, obj, distances


def solver_process(solver,instance,queue):
        # Solve and store the result in a queue to retrieve outside of the process
        result = solve(solver, instance, verbose=False)
        queue.put(result)
        

# Wrapper to solve with timeout using multiprocessing
def solve_with_timeout(solver, instance, time_limit=305):

    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=solver_process, args=(solver,instance,queue))
    process.start()
    process.join(timeout=time_limit)

    if process.is_alive():
        print(f"Solver exceeded {time_limit} seconds; terminating the process.")
        process.terminate()  # Force stop the solver process
        process.join()       # Ensure process has fully terminated
        
        # Retrieve the partial solution (if available)
        if not queue.empty():
            partial_solution = queue.get()
            print("Returning partial solution due to timeout.")
            return partial_solution  # Return partial solution if available
        else:
            print("No solution found before timeout.")
            return None  # No solution, process was terminated before solving
    else:
        return queue.get()  # Retrieve the full solution if completed
    
    
# li, ui = istance range to be solved
def main(li_ui_solver):
    TIME_LIMIT = 300    #5mins
    solvers = {
        "cbc": PULP_CBC_CMD(timeLimit=TIME_LIMIT),                          
        "highs": getSolver('HiGHS', timeLimit=TIME_LIMIT, msg=False),       
        "gurobi": GUROBI_CMD(timeLimit=TIME_LIMIT)                          
    }
    li, ui, solver = li_ui_solver.split(",")
    li = int(li)
    ui = int(ui)
    
    json = {} # dictionary to store the results
    if solver == "ALL":
        print("Solving with all solvers...")
        for instance in range(li, ui+1):
            for solver_name, solver_object in solvers.items():
                
                result = solve(solver_object, instance, TIME_LIMIT)
                if result is None:
                    print(f"Solution for instance {instance} timed out and no solution was available.")
                    n_couriers, n_items, load_i, obj_size_j, D = retrieve_istance(instance)
                    depot_node = D.shape[0]  # depot is the last city n+1
                    route, time, optimal, obj  = [], 300, False, 'N/A'
                else:
                    route, depot_node, n_couriers, time, optimal, obj, distances = result
                
                json[solver_name] = convert_to_json(route,depot_node, n_couriers, time, optimal, obj)
            save_json(instance,json)
    else:
        print(f"Solving with {solver}...")
        for instance in range(li, ui+1):
            
            result = solve(solvers[solver], instance, TIME_LIMIT)
            if result is None:
                print(f"Solution for instance {instance} timed out and no solution was available.")
                n_couriers, n_items, load_i, obj_size_j, D = retrieve_istance(instance)
                depot_node = D.shape[0]  # depot is the last city n+1
                route, time, optimal, obj  = [], 300, False, 'N/A'
            else:
                route, depot_node, n_couriers, time, optimal, obj, distances = result
            
            json[solver] = convert_to_json(route, depot_node, n_couriers, time, optimal, obj)
            save_json(instance,json)
    
    
def validate_arguments(li_ui_solver):
    try:
        commas=0
        for char in li_ui_solver:
            if char == ',':
                commas+=1
        if commas != 2:
            raise ValueError("Lower Bound, Upper Bound and Solver Type must be in the format: li,ui,solver. \n \
                             Solver Options: cbc, highs, gurobi, ALL")
    except ValueError as e:
        print(e)
        return False
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Solve MTSP problem.')
    
    parser.add_argument('li_ui_solver', type=str, help='Lower, Upper Bound and Solver Type of the instance range. Format: li,ui,solver.\n \
                        Solver Options: cbc, highs, gurobi, ALL')
    args = parser.parse_args()
    
    valid = validate_arguments(args.li_ui_solver)
    if valid:
        main(args.li_ui_solver) # Call main with the arguments
    else:
        print("Invalid arguments. Exiting...")