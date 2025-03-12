import random
import numpy as np
import explorer
from collections import defaultdict

# Data

orders, warehouse, lb, ub = explorer.parse()

items = list(warehouse.keys())
NUM_ITEMS = len(items)
NUM_ORDERS = len(orders)

MAX_CAPACITY = ub  
MIN_CAPACITY = lb  

num_particles = 20000
num_iterations = 40
mutation_rate = 0.5

fitness_cache = {}  
tabu_list = set()  


def get_particle_hash(order_selection, aisle_assignment):
    orders_hash = tuple(order_selection)
    aisles_hash = tuple(sorted(aisle_assignment.items()))
    return hash((orders_hash, aisles_hash))


def calculate_fitness(order_selection, aisle_assignment):
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

    #print(visited_aisles)
    #print(len(visited_aisles))

    return efficiency


def calculate_fitness_with_cache(order_selection, aisle_assignment):
    state_hash = get_particle_hash(order_selection, aisle_assignment)

    if state_hash in fitness_cache:
        return fitness_cache[state_hash]

    fitness = calculate_fitness(order_selection, aisle_assignment)
    fitness_cache[state_hash] = fitness

    return fitness


def initialize_particle():
    valid = False
    while not valid:
        order_selection = [idx for idx in range(len(orders)) if random.random() < 0.5]

        total_items = sum(
            sum(orders[idx].values()) for idx in order_selection
        )

        if MIN_CAPACITY <= total_items <= MAX_CAPACITY:
            valid = True

    aisle_assignment = {}
    for order_idx in order_selection:
        for item in orders[order_idx]:
            if item not in aisle_assignment:
                aisles = list(warehouse.get(item, {}).keys())
                if aisles:
                    aisle_assignment[item] = random.choice(aisles)

    return order_selection, aisle_assignment


def mutate_aisle_assignment(aisle_assignment, mutation_rate=0.1):
    new_assignment = aisle_assignment.copy()
    already_selected_aisles = set(new_assignment.values())

    for item in aisle_assignment.keys():
        if random.random() < mutation_rate:
            possible_aisles = list(warehouse.get(item, {}).keys())

            # Prefer aisles already being visited
            preferred_aisles = [a for a in possible_aisles if a in already_selected_aisles]

            if preferred_aisles:
                new_assignment[item] = random.choice(preferred_aisles)
            else:
                new_assignment[item] = random.choice(possible_aisles)

    return new_assignment


def mutate_order_selection(order_selection, mutation_rate=0.1):
    new_selection = order_selection.copy()

    for idx in range(len(orders)):
        if random.random() < mutation_rate:
            if idx in new_selection:
                new_selection.remove(idx)
            else:
                new_selection.append(idx)

    new_selection = sorted(list(set(new_selection)))

    total_items = sum(
        sum(orders[idx].values()) for idx in new_selection
    )

    if total_items < MIN_CAPACITY or total_items > MAX_CAPACITY:
        return order_selection 

    return new_selection


def pso():
    # Initialize swarm
    swarm = []
    global_best_position = None
    global_best_fitness = float('-inf')

    for _ in range(num_particles):
        order_selection, aisle_assignment = initialize_particle()

        particle_hash = get_particle_hash(order_selection, aisle_assignment)

        if particle_hash in tabu_list:
            continue

        tabu_list.add(particle_hash)
        fitness = calculate_fitness_with_cache(order_selection, aisle_assignment)

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

    # Main PSO loop
    for iteration in range(num_iterations):
        print(f"Iteration {iteration + 1}/{num_iterations}")

        for particle in swarm:
            order_selection = particle['order_selection']
            aisle_assignment = particle['aisle_assignment']

            new_order_selection = mutate_order_selection(order_selection, mutation_rate)
            new_aisle_assignment = mutate_aisle_assignment(aisle_assignment, mutation_rate)

            particle_hash = get_particle_hash(new_order_selection, new_aisle_assignment)

            if particle_hash in tabu_list:
                continue

            tabu_list.add(particle_hash)

            fitness = calculate_fitness_with_cache(new_order_selection, new_aisle_assignment)

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

        print(f"Best fitness so far: {global_best_fitness}")

    return global_best_position, global_best_fitness

def write_solution_to_file(best_solution, filename="best_solution.txt"):
    #total_items = 0
    visited_aisles = set()
    order_selection = best_solution[0]
    aisle_assignment = best_solution[1]

    # Unique aisles visited in the assignment
    #aisles_visited = sorted(set(aisle_assignment.values()))

    batch_items = defaultdict(int)
    for order_idx in order_selection:
        for item, qty in orders[order_idx].items():
            batch_items[item] += qty

    for item, qty in batch_items.items():
        aisle = aisle_assignment[item]
        visited_aisles.add(aisle)

    with open(filename, "w") as file:
        file.write(f"{len(order_selection)}\n")
        for order_idx in order_selection:
            file.write(f"{order_idx}\n")

        file.write(f"{len(visited_aisles)}\n")
        for aisle in visited_aisles:
            file.write(f"{aisle}\n")


best_solution, best_fitness = pso()

write_solution_to_file(best_solution)

#print("\n✅ Final Best Solution ✅")
#print("Orders in batch:", best_solution[0])
#print("Aisle assignments:", best_solution[1])
#print("Batch efficiency (items / unique aisles):", best_fitness)
