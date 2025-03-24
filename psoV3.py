import random
import numpy as np
import explorer
from collections import defaultdict

# Data
#orders, warehouse, lb, ub = explorer.parse()

# GLOBAL VARIABLES (Bro, please don't use global variables again)
num_particles = 200
num_iterations = 40
mutation_rate = 0.6

fitness_cache = {}  
tabu_list = set()  


def get_particle_hash(order_selection, aisle_assignment):
    orders_hash = tuple(order_selection.tolist())
    aisles_hash = tuple(sorted(aisle_assignment.items()))
    return hash((orders_hash, aisles_hash))


def calculate_fitness(orders, warehouse, order_selection, aisle_assignment):
    total_items = 0
    visited_aisles = set()

    batch_items = defaultdict(int)
    for order_idx in order_selection:
        for item, qty in orders[order_idx].items():
            batch_items[item] += qty

    for item, qty in batch_items.items():
        if item not in aisle_assignment:
            return 0 

        aisle = aisle_assignment[item]
        available_qty = warehouse.get(item, {}).get(aisle, 0)

        if available_qty < qty:
            return 0 

        visited_aisles.add(aisle)
        total_items += qty

    if len(visited_aisles) == 0:
        return 0

    efficiency = total_items / len(visited_aisles)

    return efficiency


def calculate_fitness_with_cache(orders, warehouse, order_selection, aisle_assignment):
    state_hash = get_particle_hash(order_selection, aisle_assignment)

    if state_hash in fitness_cache:
        return fitness_cache[state_hash]

    fitness = calculate_fitness(orders, warehouse, order_selection, aisle_assignment)
    fitness_cache[state_hash] = fitness

    return fitness


def initialize_particle(orders, warehouse, NUM_ORDERS, MIN_CAPACITY, MAX_CAPACITY):
    valid = False
    while not valid:
        # Generate a binary mask and use it to select order indices
        mask = np.random.rand(NUM_ORDERS) < 0.5
        order_selection = np.nonzero(mask)[0]

        total_items = sum(
            sum(orders[idx].values()) for idx in order_selection
        )

        if MIN_CAPACITY <= total_items <= MAX_CAPACITY:
            valid = True

    aisle_assignment = {}
    for order_idx in order_selection:
        for item in orders[order_idx]:
            if item not in aisle_assignment:
                aisles = np.array(list(warehouse.get(item, {}).keys()))
                if len(aisles) > 0:
                    aisle_assignment[item] = np.random.choice(aisles)

    return order_selection, aisle_assignment


def mutate_aisle_assignment(warehouse, aisle_assignment, mutation_rate=0.1):
    new_assignment = aisle_assignment.copy()
    already_selected_aisles = set(new_assignment.values())

    for item in aisle_assignment.keys():
        if np.random.rand() < mutation_rate:
            possible_aisles = np.array(list(warehouse.get(item, {}).keys()))

            # Prefer aisles already being visited
            preferred_aisles = possible_aisles[np.isin(possible_aisles, list(already_selected_aisles))]

            if len(preferred_aisles) > 0:
                new_assignment[item] = np.random.choice(preferred_aisles)
            elif len(possible_aisles) > 0:
                new_assignment[item] = np.random.choice(possible_aisles)

    return new_assignment


def mutate_order_selection(orders, NUM_ORDERS, MIN_CAPACITY, MAX_CAPACITY, order_selection, mutation_rate=0.1):
    current_selection = order_selection.copy()
    new_selection = current_selection.tolist()

    for idx in range(NUM_ORDERS):
        if np.random.rand() < mutation_rate:
            if idx in new_selection:
                new_selection.remove(idx)
            else:
                new_selection.append(idx)

    new_selection = np.array(sorted(set(new_selection)))

    total_items = sum(
        sum(orders[idx].values()) for idx in new_selection
    )

    if total_items < MIN_CAPACITY or total_items > MAX_CAPACITY:
        return current_selection

    return new_selection


def pso(orders, warehouse, lb, ub):
    swarm = []
    global_best_position = None
    global_best_fitness = float('-inf')
    items = np.array(list(warehouse.keys()))
    NUM_ITEMS = len(items)
    NUM_ORDERS = len(orders)

    MAX_CAPACITY = ub
    MIN_CAPACITY = lb

    for _ in range(num_particles):
        order_selection, aisle_assignment = initialize_particle(orders, warehouse, NUM_ORDERS, MIN_CAPACITY, MAX_CAPACITY)

        particle_hash = get_particle_hash(order_selection, aisle_assignment)

        if particle_hash in tabu_list:
            continue

        tabu_list.add(particle_hash)
        fitness = calculate_fitness_with_cache(orders, warehouse, order_selection, aisle_assignment)

        swarm.append({
            'order_selection': order_selection,
            'aisle_assignment': aisle_assignment,
            'fitness': fitness,
            'best_order_selection': order_selection,
            'best_aisle_assignment': aisle_assignment,
            'best_fitness': fitness
        })

        if fitness > global_best_fitness:
            global_best_fitness = fitness
            global_best_position = (order_selection, aisle_assignment)

    for iteration in range(num_iterations):
        #print(f"Iteration {iteration + 1}/{num_iterations}")

        for particle in swarm:
            order_selection = particle['order_selection']
            aisle_assignment = particle['aisle_assignment']

            new_order_selection = mutate_order_selection(orders, NUM_ORDERS, MIN_CAPACITY, MAX_CAPACITY, order_selection, mutation_rate)
            new_aisle_assignment = mutate_aisle_assignment(warehouse, aisle_assignment, mutation_rate)

            particle_hash = get_particle_hash(new_order_selection, new_aisle_assignment)

            if particle_hash in tabu_list:
                continue

            tabu_list.add(particle_hash)

            fitness = calculate_fitness_with_cache(orders, warehouse, new_order_selection, new_aisle_assignment)

            if fitness > particle['best_fitness']:
                particle['best_fitness'] = fitness
                particle['best_order_selection'] = new_order_selection
                particle['best_aisle_assignment'] = new_aisle_assignment

            if fitness > global_best_fitness:
                global_best_fitness = fitness
                global_best_position = (new_order_selection, new_aisle_assignment)

            particle['order_selection'] = new_order_selection
            particle['aisle_assignment'] = new_aisle_assignment
            particle['fitness'] = fitness

        #print(f"Best fitness so far: {global_best_fitness}")

    return global_best_position, global_best_fitness


def write_solution_to_file(orders, best_solution, filename="best_solution.txt"):
    visited_aisles = set()
    order_selection = best_solution[0]
    aisle_assignment = best_solution[1]

    batch_items = defaultdict(int)
    for order_idx in order_selection:
        for item, qty in orders[order_idx].items():
            batch_items[item] += qty

    for item in batch_items.keys():
        aisle = aisle_assignment[item]
        visited_aisles.add(aisle)

    with open(filename, "w") as file:
        file.write(f"{len(order_selection)}\n")
        for order_idx in order_selection:
            file.write(f"{order_idx}\n")

        file.write(f"{len(visited_aisles)}\n")
        for aisle in visited_aisles:
            file.write(f"{aisle}\n")

def run_pso_algorithm(instance_path: str):    
    orders, warehouse, lb, ub = explorer.parse(instance_path)
    best_solution, best_fitness = pso(orders, warehouse, lb, ub)
    solution_dict = {
        "best_solution": best_solution,
        "best_fitness": best_fitness
    }

    return solution_dict

#write_solution_to_file(best_solution)

if __name__ == "__main__":
    solution = run_pso_algorithm("datasets/a/instance_0020.txt")
    print(solution)
