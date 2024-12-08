from z3 import *
import os
import time
import json
import math

def create_mcp_solver(m, n, l, s, D):
    solver = Optimize()
    
    # Decision variables
    x = [[[Bool(f"x_{i}_{j}_{k}") 
           for k in range(n+1)]  
           for j in range(n+1)]  
           for i in range(m)]
    
    # MTZ variables
    u = [[Int(f"u_{i}_{j}") for j in range(n+1)] for i in range(m)]
    
    # Variable for maximum route length (objective)
    max_route_length = Int('max_route_length')
    
    # Route length for each courier
    for i in range(m):
        route_length = Sum([If(x[i][j][k], D[j][k], 0)
                          for j in range(n+1) 
                          for k in range(n+1) if j != k])
        solver.add(route_length <= max_route_length)
    
    # Route length bounds
    min_possible_route = max(D[n][j] + D[j][n] for j in range(n))
    max_distance = max(D[j][k] for j in range(n+1) for k in range(n+1) if j != k)
    points_per_courier = ((n + m - 1) // m)
    max_possible_route = (points_per_courier + 1) * max_distance

    solver.add(max_route_length >= min_possible_route)
    solver.add(max_route_length <= max_possible_route)

    # Customer visit constraints
    for j in range(n):
        solver.add(Sum([Or([x[i][j][k] for k in range(n+1) if k != j]) for i in range(m)]) == 1)
        solver.add(Sum([If(Or([x[i][j][k] for k in range(n+1) if k != j]), 1, 0) for i in range(m)]) == 1)
    
    # Flow conservation
    for i in range(m):
        for k in range(n+1):
            sum_in = Sum([x[i][j][k] for j in range(n+1) if j != k])
            sum_out = Sum([x[i][k][j] for j in range(n+1) if j != k])
            solver.add(sum_in == sum_out)
            solver.add(Or(And(sum_in == 0, sum_out == 0), And(sum_in == 1, sum_out == 1)))
    
    # Depot constraints
    for i in range(m):
        solver.add(Sum([x[i][n][j] for j in range(n)]) == 1)
        solver.add(Sum([x[i][j][n] for j in range(n)]) == 1)
    
    # MTZ constraints
    for i in range(m):
        for j in range(n+1):
            solver.add(u[i][j] >= 0)
            solver.add(u[i][j] <= n)
        
        for j in range(n):
            for k in range(n):
                if j != k:
                    solver.add(Implies(x[i][j][k], u[i][k] >= u[i][j] + 1))
    
    # Capacity constraints
    for i in range(m):
        solver.add(Sum([If(Or([x[i][j][k] for k in range(n+1) if k != j]), s[j], 0) 
                       for j in range(n)]) <= l[i])
    
    solver.minimize(max_route_length)
    return solver, x, u, max_route_length

def solve_mcp(m, n, l, s, D, json_filename, results_path):
    print("\nSolving MCP instance...")
    
    timeout = 300  # 5 minutes timeout
    start_time = time.time()
    
    # Track the best solution found
    best_solution = None
    best_max_route = None
    
    solver, x, u, max_route_length = create_mcp_solver(m, n, l, s, D)
    solver.set("timeout", timeout * 1000)
    solver.set("maxsat_engine", "maxres")
    
    # Callback to track solutions as they're found
    def on_model(m):
        nonlocal best_solution, best_max_route
        current_route = m.eval(max_route_length).as_long()
        print(f"Found solution with max route length: {current_route}")
        best_solution = m
        best_max_route = current_route
    
    solver.set_on_model(on_model)
    
    result = solver.check()
    solve_time = time.time() - start_time
    
    print(f"Solution time: {solve_time:.2f} seconds")
    
    json_time = min(math.floor(solve_time), 300)

    json_output = {
        "time": json_time,
        "optimal": solve_time < timeout,
        "obj": None,
        "sol": []
    }
    
    if best_solution is not None:
        model = best_solution
        max_route = best_max_route
        
        if solve_time >= timeout:
            print("WARNING: Solution is not optimal (timeout reached)")
        print(f"\nBest maximum route length found: {max_route}")
        
        json_output["obj"] = max_route
        courier_paths = []
        
        for i in range(m):
            tour = []
            current = n
            total_load = 0
            path = []
            
            while True:
                next_point = None
                for k in range(n+1):
                    if k != current and model.evaluate(x[i][current][k]):
                        next_point = k
                        if k != n:
                            total_load += s[k]
                            path.append(k + 1)
                        break
                
                if next_point == n:
                    break
                elif next_point is not None:
                    tour.append(str(next_point + 1))
                    current = next_point
                else:
                    break
            
            if tour:
                print(f"Courier {i+1}: o -> {' -> '.join(tour)} -> o")
                print(f"Total load: {total_load}/{l[i]}")
                courier_paths.append(path)
        
        json_output["sol"] = courier_paths
    
    elif result == unknown:
        print(f"Solver timed out after {timeout} seconds without finding a solution")
    else:
        print("No solution exists")
    
    # Save JSON output
    output_filename = os.path.join(results_path, json_filename)
    with open(output_filename, 'w') as f:
        json.dump(json_output, f, indent=4)
    
    print(f"\nJSON output saved to {output_filename}")
    return json_output

def read_instance(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith(('#', '%', '//'))]
            
            m = int(lines[0])
            n = int(lines[1])
            l = list(map(int, lines[2].split()))
            s = list(map(int, lines[3].split()))
            D = [list(map(int, line.split())) for line in lines[4:4+n+1]]
            
            return m, n, l, s, D
            
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        raise

def main(input_choice):
    # Set specific paths
    instances_path = "/app/instances/dat_instances"
    results_path = "/app/res/SMT"
    
    # Ensure the solutions directory exists
    os.makedirs(results_path, exist_ok=True)
    
    # Determine which instances to process
    if input_choice.upper() == 'ALL':
        instance_numbers = range(1, 22)  # Assuming 21 instances
    elif ':' in input_choice:
        start, end = map(int, input_choice.split(':'))
        instance_numbers = range(start, end + 1)
    else:
        instance_numbers = [int(input_choice)]
    
    
    for instance_num in instance_numbers:
        filename = f"inst{instance_num:02d}.dat"
        file_path = os.path.join(instances_path, filename)
        
        if os.path.exists(file_path):
            try:
                m, n, l, s, D = read_instance(file_path)
                json_filename = f"{instance_num:02d}.json"
                solve_mcp(m, n, l, s, D, json_filename, results_path)
            except Exception as e:
                print(f"Failed to process instance {filename}: {str(e)}")
        else:
            print(f"Error: Instance file {filename} not found")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
    else:
        user_input = "1"
    main(user_input)