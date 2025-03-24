import os
from graspV2 import run_grasp_algorithm
from integer_programming import run_ip_algorithm
from psoV3 import run_pso_algorithm

input_folder = "datasets/a"
output_folder = "outputs"

instances = sorted([f for f in os.listdir(input_folder) if f.endswith(".txt")])

algorithms = [run_grasp_algorithm, run_ip_algorithm, run_pso_algorithm]

for i, instance in enumerate(instances, start=1):
    instance_path = os.path.join(input_folder, instance)

    for j, algorithm in enumerate(algorithms, start=1):
        output_path = os.path.join(output_folder, f"algorithm_{j}_instance_{i}.txt")
        try:
            result = algorithm(instance_path)
        except Exception as e:
            result = f"Error: {e}"
        
        with open(output_path, "w") as out_file:
            out_file.write(str(result))

        print(f"Execution completed: Algorithm {j}, Instance {i} -> {output_path}")
