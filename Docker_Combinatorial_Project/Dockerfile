# Use MiniZinc base image
FROM minizinc/minizinc:2.8.7-jammy

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Python
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    wget \
    gcc \
    g++ \
    curl \
    libc6 \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create licenses directory and copy Gurobi license
RUN mkdir -p /app/licenses
COPY licenses/gurobi.lic /app/licenses/gurobi.lic

# Copy requirements file first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV GRB_LICENSE_FILE=/app/licenses/gurobi.lic

# Copy all project files
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/res/MIP \
    /app/res/SMT \
    /app/res/MiniZinc

# Make sure all scripts are executable
RUN chmod +x /app/Main.py

# Set environment variables
ENV PYTHONPATH=/app

# Verify installations
RUN echo "=== Python Version ===" && \
    python3 --version && \
    echo "\n=== MiniZinc Version ===" && \
    minizinc --version && \
    echo "\n=== Available Solvers ===" && \
    minizinc --solvers

# Default command
ENTRYPOINT ["python3", "/app/Main.py"]