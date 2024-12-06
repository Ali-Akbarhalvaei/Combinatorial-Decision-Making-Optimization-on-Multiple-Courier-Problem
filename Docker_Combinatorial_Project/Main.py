import argparse
from MIP.main import main as mip_main
from SMT.SMT import main as smt_main
from MZN.Main_MZN import main as mzn_main

def process_mzn_input(input_str):
    """
    Process MiniZinc input string to convert it to the required format.
    
    Examples:
    "3:5:model_2" -> "3:5-02"
    "4:model_1" -> "4-01"
    """
    parts = input_str.split(':')
    
    # Handle case with three parts (e.g., "3:5:model_2")
    if len(parts) == 3:
        start, end, model = parts
        # Extract number from model_n format
        model_num = model.split('_')[1]
        # Convert to two-digit format
        model_num = f"{int(model_num):02d}"
        return f"{start}:{end}-{model_num}"
    
    # Handle case with two parts (e.g., "4:model_1")
    elif len(parts) == 2:
        number, model = parts
        # Extract number from model_n format
        model_num = model.split('_')[1]
        # Convert to two-digit format
        model_num = f"{int(model_num):02d}"
        return f"{number}-{model_num}"
    
    # Handle single instance or 'ALL' case
    else:
        return input_str

def validate_instance_input(instance_input):
    """Validate and parse instance input format."""
    if instance_input.upper() == 'ALL':
        return 'ALL'
    elif ':' in instance_input:
        try:
            parts = instance_input.split(':')
            if len(parts) == 3:  # format: start:end:solver
                start, end, solver = parts
                start, end = int(start), int(end)
                if start > end:
                    raise ValueError("Start instance cannot be greater than end instance")
                return f"{start}:{end}:{solver}"
            elif len(parts) == 2:  # format: start:end or number:solver
                try:
                    start, end = map(int, parts)
                    if start > end:
                        raise ValueError("Start instance cannot be greater than end instance")
                    return f"{start}:{end}"
                except ValueError:
                    # This might be a single instance with solver (e.g., "3:cbc")
                    number, solver = parts
                    return f"{number}:{solver}"
        except ValueError as e:
            if "Start instance cannot be greater than end instance" in str(e):
                raise
            raise ValueError("Range must be in format 'start:end' or 'start:end:solver' with valid integers")
    else:
        try:
            instance_num = int(instance_input)
            return str(instance_num)
        except ValueError:
            raise ValueError("Instance must be a number, range (start:end), or 'ALL'")

def run_solver(solver, instance_input):
    """Run the specified solver with given instance input."""
    if solver == "MIP":
        # Convert instance input to MIP format (li,ui,solver)
        if instance_input == 'ALL':
            mip_args = "1,21,ALL"
        elif ':' in instance_input:
            parts = instance_input.split(':')
            if len(parts) == 3:  # format: start:end:solver_type
                start, end, mip_solver = parts
                mip_args = f"{start},{end},{mip_solver}"
            elif len(parts) == 2:  # format: start:end
                start, end = parts
                mip_args = f"{start},{end},ALL"
            else:
                raise ValueError("Invalid MIP input format. Use 'start:end:solver' or 'start:end'")
        else:
            # Single instance case
            if ':' in instance_input:  # format: number:solver
                number, mip_solver = instance_input.split(':')
                mip_args = f"{number},{number},{mip_solver}"
            else:
                mip_args = f"{instance_input},{instance_input},ALL"
        mip_main(mip_args)
    
    elif solver == "SMT":
        smt_main(instance_input)
    
    elif solver == "MZN":
        # Convert the input format for MZN if needed
        if instance_input and instance_input != 'ALL':
            # Process the input string to match MZN format
            mzn_input = process_mzn_input(instance_input)
            print(f"Converting MZN input: {instance_input} -> {mzn_input}")
            mzn_main(mzn_input)
        else:
            # Handle 'ALL' case or no input
            mzn_main(instance_input)

def main():
    parser = argparse.ArgumentParser(description='Multi-Courier Problem Solver')
    parser.add_argument('solver', choices=['MIP', 'SMT', 'MZN', 'ALL'], 
                      help='Solver to use (MIP, SMT, MZN, or ALL)')
    parser.add_argument('instance', nargs='?', default='ALL',
                      help='Instance number, range (e.g., 2:5), or ALL. For MZN: also accepts format like "3:5:model_2" or "4:model_1"')

    args = parser.parse_args()

    try:
        # Validate instance input only if it's not None and solver is not MZN
        if args.solver != 'MZN' and args.instance is not None:
            instance_input = validate_instance_input(args.instance)
        else:
            instance_input = args.instance

        # Run solver(s)
        if args.solver == 'ALL':
            print("Running all solvers...")
            for solver in ['MIP', 'SMT', 'MZN']:
                print(f"\nRunning {solver} solver...")
                run_solver(solver, instance_input)
        else:
            print(f"Running {args.solver} solver...")
            run_solver(args.solver, instance_input)

    except ValueError as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())