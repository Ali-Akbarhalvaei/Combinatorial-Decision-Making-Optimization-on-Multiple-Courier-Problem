# Multi-Courier Problem Solver Docker Environment

This Docker environment provides a standardized setup for solving the Multi-Courier Problem (MCP) using three different approaches: MiniZinc (Constraint Programming), SMT (Z3), and MIP (Mixed Integer Programming).

## Prerequisites

- Docker installed on your system

## Quick Start

To get to know the project files, you can see the project structure here:

```
/app
├── Main.py
├── instances/
│   ├── dat_instances/ # Data instances for SMT and MIP
│   └── dzn_instances/ # Data instances for MiniZinc
├── MZN/ # MiniZinc models and implementation
├── SMT/ # SMT (Z3) implementation
├── MIP/ # Mixed Integer Programming implementation
└── res/ # Results directory
 ├── MiniZinc/ # MiniZinc solution files
 ├── SMT/ # SMT solution files
 └── MIP/ # MIP solution files
```

### 1. Install Docker

#### For macOS:

1. Visit [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
2. Click "Download for Mac"
3. Choose the appropriate version:
   - For Apple Silicon (M1/M2) Macs: Download "Apple Chip" version
   - For Intel Macs: Download "Intel Chip" version
4. Follow the installation instructions
5. Verify installation by running:
   ```bash
   docker --version
   ```

#### For Windows:

1. Visit [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Click "Download for Windows"
3. Requirements:
   - WSL 2 backend and Windows 10 64-bit: Build 19041 or later
   - Enable WSL 2 feature on Windows
4. Run the installer
5. Verify installation by running:
   ```bash
   docker --version
   ```

### 2. Build the Docker image:

Make sure Docker Desktop is running before executing following commands.

#### For macOS:

1. Open Terminal
2. Navigate to the project directory:
   ```bash
   cd path/to/project/folder
   ```
   For example, if your project is in Downloads:
   ```bash
   cd ~/Downloads/multi-courier-solver
   ```
3. Build the Docker image:

   ```bash
   docker build -t multi-courier-solver .
   ```

   multi-courier-solver is an example for the name of the image file.

#### For Windows:

1. Open Command Prompt or PowerShell
2. Navigate to the project directory:
   ```bash
   cd path\to\project\folder
   ```
   For example, if your project is in Downloads:
   ```bash
   cd C:\Users\YourUsername\Downloads\multi-courier-solver
   ```
3. Build the Docker image:
   ```bash
   docker build -t multi-courier-solver .
   ```


## Usage

### Running Individual Solvers

As we want out output in the JSON format, we have to mount volume while we want to run the project 3. Run the solver with volume mapping:

2. **MiniZinc**:
   We have 12 models in Minizinc all of which are executable through different input from user. Below, you can find some example about how we can run each solver on different instances:

   ```shell
   docker run -v "$(pwd)/res":/app/res multi-courier-solver MZN 5:model_01
   ```

   The above command, solve instance number 5 using model number 1. However, if you want to run a model on a range of different instances, you can use the following commands:

   ```shell
   docker run -v "$(pwd)/res":/app/res multi-courier-solver MZN 5:9:model_02


   docker run -v "$(pwd)/res":/app/res multi-courier-solver MZN 1:21:model_02 #solve all instances
   ```

   before going to SMT and MIP, there is a brief description about different models of the Minizinc:

   #model_01:
   #model_02:
   ....
   ` To be COMPLETED`

3. **SMT Solver**:

   ```shell
   docker run -v "$(pwd)/res":/app/res multi-courier-solver SMT 5
   ```

   The code above run the SMT solver on instance number 5. So, the general format is as below:

   ```shell
   docker run -v "$(pwd)/res":/app/res multi-courier-solver [Solver-Name] [instances]
   ```

   In solver-name you can write: SMT, MIP, MZN, all_solvers. in this way you indicate which solver you want to use or all of them

   In instances part you can write:

   - specific number such as `5` indicating instance number 5 should be solved
   - range of instances such as `2:6` indicating that instances from 2 to 6 should be solved
   - `ALL` indicating that all instances should be solved

   ```shell
   docker run -v "$(pwd)/res":/app/res multi-courier-solver SMT 9

   docker run -v "$(pwd)/res":/app/res multi-courier-solver SMT 5:7

   docker run -v "$(pwd)/res":/app/res multi-courier-solver SMT ALL
   ```

4. **MIP Solver**:
   Runing MIP solver is almost similar to SMT but with the small difference that you can choose what method the solver choose among: CBC, HIGHS. Below you can see an example of how you can run MIP solver.

   ```shell
   docker run -v "$(pwd)/res":/app/res multi-courier-solver MIP 3:7:cbc

   docker run -v "$(pwd)/res":/app/res multi-courier-solver MIP 3:7:highs

   docker run -v "$(pwd)/res":/app/res multi-courier-solver MIP ALL:cbc

   docker run -v "$(pwd)/res":/app/res multi-courier-solver MIP 2:highs

   ```

5. **Run all solvers**:
   To run all 3 solvers on specific instances you can simply use the following commands:

   ```shell
   docker run -v "$(pwd)/res":/app/res multi-courier-solver all_solvers 9:cbc:model_01

   docker run -v "$(pwd)/res":/app/res multi-courier-solver all_solvers 3:5:highs:model_04

   docker run -v "$(pwd)/res":/app/res multi-courier-solver all_solvers 1:21:highs:model_04
   ```

   The first command is for running only one instance using all different solvers. Furthermore, you can give the range of instances so it can be solved with different solvers

### Solution Output

All solvers generate JSON output files in their respective results directories with the following format:

```
json
{
"time": Integer(rounded), // Solution time in seconds
"optimal": boolean, // Whether the solution is optimal
"obj": integer, // Objective value (null if no solution)
"sol": array // Solution paths for each courier
}
```
