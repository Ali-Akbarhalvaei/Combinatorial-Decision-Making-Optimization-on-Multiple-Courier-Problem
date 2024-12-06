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
    

def process_mip_input(instance_input):
    """
    Process input specifically for MIP solver.
    Returns formatted string in the form of "lower,upper,solver_type"
    """
    if instance_input == 'ALL':
        return "1,21,ALL"
    
    elif ':' in instance_input:
        parts = instance_input.split(':')
        if len(parts) == 3:  # format: start:end:solver_type
            start, end, mip_solver = parts
            return f"{start},{end},{mip_solver}"
        elif len(parts) == 2:  # format: start:end
            start, mip_solver = parts
            return f"{start},{start},{mip_solver}"
        else:
            raise ValueError("Invalid MIP input format. Use 'start:end:solver' or 'start:end'")
    
    else:
        # Single instance case
        if ':' in instance_input:  # format: number:solver
            number, mip_solver = instance_input.split(':')
            return f"{number},{number},{mip_solver}"
        return f"{instance_input},{instance_input},ALL"

def process_input_for_all_solvers(instance_input):
    parts = instance_input.split(':')
    if len(parts) == 4:  # format: "1:5:cbc:model_01" (range with solver and model)
        MIP_input = ':'.join(parts[:-1])  # "1:5:cbc"
        MZN_input = ':'.join(parts[:-2] + [parts[-1]])  # "1:5:model_01"
        SMT_input = ':'.join(parts[:-2])  # "1:5"
    elif len(parts) == 3:  # format: "2:cbc:model_02" (single instance with solver and model)
        MIP_input = f"{parts[0]}:{parts[1]}"  # "2:cbc"
        MZN_input = f"{parts[0]}:{parts[2]}"  # "2:model_02"
        SMT_input = parts[0]  # "2"
    else:
        raise ValueError("Invalid input format for all solvers")
        
    return MIP_input, MZN_input, SMT_input




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
        mip_args = process_mip_input(instance_input)
        mip_main(mip_args)
    
    elif solver == "SMT":
        smt_main(instance_input)
    
    elif solver == "MZN":
        # Convert the input format for MZN if needed
        if instance_input and instance_input != 'ALL':
            # Process the input string to match MZN format
            mzn_input = process_mzn_input(instance_input)
            #print(f"Converting MZN input: {instance_input} -> {mzn_input}")
            mzn_main(mzn_input)
        else:
            # Handle 'ALL' case or no input
            mzn_main(instance_input)

    elif solver == 'all_solvers':
        MIP_input, MZN_input, SMT_input = process_input_for_all_solvers(instance_input)
        
        mzn_args = process_mzn_input(MZN_input)
        mzn_main(mzn_args)
        
        mip_args = process_mip_input(MIP_input)
        mip_main(mip_args)
        
        smt_main(SMT_input)


def main():
    parser = argparse.ArgumentParser(description='Multi-Courier Problem Solver')
    parser.add_argument('solver', choices=['MIP', 'SMT', 'MZN', 'all_solvers'], 
                      help='Solver to use (MIP, SMT, MZN, or all_solvers)')
    parser.add_argument('instance', nargs='?', default='ALL',
                      help='Instance number, range (e.g., 2:5), or ALL. '
                           'For MZN: accepts format like "3:5:model_2" or "4:model_1". '
                           'For all_solvers: use format "start:end:solver:model" (e.g., "1:5:cbc:model_01") '
                           'or "instance:solver:model" (e.g., "2:cbc:model_02")')   
    args = parser.parse_args()
    
    try:
        # Skip validation for MZN and all_solvers as they have different input formats
        if args.solver not in ['MZN', 'all_solvers']:
            instance_input = validate_instance_input(args.instance)
        else:
            instance_input = args.instance

        print(f"Running {args.solver} solver...")
        run_solver(args.solver, instance_input)

    except ValueError as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())