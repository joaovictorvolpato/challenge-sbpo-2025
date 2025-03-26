import os
import multiprocessing

from graspV2 import run_grasp_algorithm
from integer_programming import run_ip_algorithm
from psoV3 import run_pso_algorithm


def run_algorithm_with_timeout(algorithm, instance_path):
    with multiprocessing.Pool(1) as pool: # It's possible to change the number of processes
        result = pool.apply_async(algorithm, (instance_path,))
        try:
            return result.get(TIMEOUT)  # Wait TIMEOUT seconds for the result
        except multiprocessing.TimeoutError:
            return "Timeout"
        except Exception as e:
            return f"Error: {e}"

if __name__ == "__main__":
    INPUT_PATH = "datasets/a"
    OUTPUT_PATH = "outputs"
    TIMEOUT = 600 # seconds

    instances = sorted([f for f in os.listdir(INPUT_PATH) if f.endswith(".txt")])
    algorithms = [run_grasp_algorithm, run_pso_algorithm, run_ip_algorithm]

    for i, instance in enumerate(instances, start=16):
        instance_path = os.path.join(INPUT_PATH, instance)

        for j, algorithm in enumerate(algorithms, start=1):
            output_path = os.path.join(OUTPUT_PATH, f"final_algorithm_{j}_instance_{i}.txt")

            result = run_algorithm_with_timeout(algorithm, instance_path)

            with open(output_path, "w") as out_file:
                out_file.write(str(result))

            print(f"Execution completed: Algorithm {j}, Instance {i} -> {output_path}")
