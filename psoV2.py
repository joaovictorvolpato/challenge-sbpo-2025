import random
import numpy as np
import explorer

# ----------------------
# Problem Data
# ----------------------

orders, warehouse, lb, ub = explorer.parse()

# List of items
items = list(warehouse.keys())
NUM_ITEMS = len(items)
NUM_ORDERS = len(orders)

# Capacity Constraints
MAX_CAPACITY = ub   # Maximum number of items per batch
MIN_CAPACITY = lb   # Minimum number of items per batch

NUM_PARTICLES = 20000
MAX_ITERATIONS = 30
C1, C2, W = 2, 2, 1

# ----------------------
# Helper Functions
# ----------------------

def calculate_batch_item_requirements(order_selection):
    """Sum required quantities for selected orders."""
    total_demand = {}
    for order_idx, selected in enumerate(order_selection):
        if selected == 1:
            order = orders[order_idx]
            for item, qty in order.items():
                total_demand[item] = total_demand.get(item, 0) + qty
    return total_demand

def calculate_fitness(order_selection, aisle_assignment):
    """Evaluate fitness based on batch efficiency and aisle assignment."""
    total_demand = calculate_batch_item_requirements(order_selection)

    # Capacity constraint check
    total_quantity = sum(total_demand.values())
    if total_quantity < MIN_CAPACITY or total_quantity > MAX_CAPACITY:
        return 1e6  # infeasible batch penalty

    aisles_visited = set()
    for item, required_qty in total_demand.items():
        if item not in aisle_assignment:
            return 1e6  # invalid aisle assignment penalty
        
        assigned_aisle = aisle_assignment[item]
        
        # Check if assigned aisle has enough stock
        available_qty = warehouse.get(item, {}).get(assigned_aisle, 0)
        if available_qty < required_qty:
            return 1e6  # not enough stock penalty
        
        aisles_visited.add(assigned_aisle)

    # Efficiency = items per aisle
    efficiency_score = total_quantity / len(aisles_visited) if aisles_visited else 0

    # Fitness = negative efficiency (since we minimize fitness)
    fitness = -efficiency_score
    return fitness

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def initialize_aisle_assignment(total_demand):
    """Randomly assign an aisle for each item in demand."""
    assignment = {}
    for item in total_demand.keys():
        possible_aisles = list(warehouse.get(item, {}).keys())
        if possible_aisles:
            assignment[item] = random.choice(possible_aisles)
    return assignment

def mutate_aisle_assignment(aisle_assignment, mutation_rate=0.1):
    """Mutate aisle assignments with preference for already visited aisles."""
    new_assignment = aisle_assignment.copy()
    
    # Get currently assigned aisles
    already_selected_aisles = set(new_assignment.values())

    for item in aisle_assignment.keys():
        if random.random() < mutation_rate:
            possible_aisles = list(warehouse.get(item, {}).keys())
            
            # Step 1: Filter for aisles already selected (reuse aisles)
            preferred_aisles = [a for a in possible_aisles if a in already_selected_aisles]
            
            if preferred_aisles:
                # Reuse existing aisle if possible
                new_assignment[item] = random.choice(preferred_aisles)
            else:
                # If no preferred aisles, pick any available aisle
                new_assignment[item] = random.choice(possible_aisles)

    return new_assignment

# ----------------------
# PSO Initialization
# ----------------------

particles = []
velocities = []

for _ in range(NUM_PARTICLES):
    order_selection = np.random.randint(2, size=NUM_ORDERS)
    total_demand = calculate_batch_item_requirements(order_selection)
    aisle_assignment = initialize_aisle_assignment(total_demand)
    
    particles.append({'order_selection': order_selection, 'aisle_assignment': aisle_assignment})
    velocities.append(np.random.uniform(-1, 1, NUM_ORDERS))

# Personal bests
pbest_positions = particles.copy()
pbest_scores = [
    calculate_fitness(p['order_selection'], p['aisle_assignment'])
    for p in particles
]

gbest_index = np.argmin(pbest_scores)
gbest_position = pbest_positions[gbest_index]
gbest_score = pbest_scores[gbest_index]

# ----------------------
# PSO Main Loop
# ----------------------

for iteration in range(MAX_ITERATIONS):
    for i in range(NUM_PARTICLES):
        particle = particles[i]
        order_selection = particle['order_selection']
        aisle_assignment = particle['aisle_assignment']

        # Update order selection velocity and position
        r1, r2 = random.random(), random.random()
        velocities[i] = (
            W * velocities[i]
            + C1 * r1 * (pbest_positions[i]['order_selection'] - order_selection)
            + C2 * r2 * (gbest_position['order_selection'] - order_selection)
        )
        prob = sigmoid(velocities[i])
        new_order_selection = np.array([
            1 if random.random() < prob[j] else 0
            for j in range(NUM_ORDERS)
        ])

        # Recalculate item demands for new order selection
        total_demand = calculate_batch_item_requirements(new_order_selection)

        # Mutate aisle assignment to explore alternatives
        new_aisle_assignment = mutate_aisle_assignment(aisle_assignment)

        # Ensure aisle assignment covers items in the new demand
        for item in total_demand.keys():
            if item not in new_aisle_assignment:
                possible_aisles = list(warehouse.get(item, {}).keys())
                if possible_aisles:
                    new_aisle_assignment[item] = random.choice(possible_aisles)

        # Evaluate fitness
        fitness = calculate_fitness(new_order_selection, new_aisle_assignment)

        # Update personal best
        if fitness < pbest_scores[i]:
            pbest_scores[i] = fitness
            pbest_positions[i] = {
                'order_selection': new_order_selection.copy(),
                'aisle_assignment': new_aisle_assignment.copy()
            }

        # Update global best
        if fitness < gbest_score:
            gbest_score = fitness
            gbest_position = {
                'order_selection': new_order_selection.copy(),
                'aisle_assignment': new_aisle_assignment.copy()
            }

        # Update particle
        particles[i] = {
            'order_selection': new_order_selection,
            'aisle_assignment': new_aisle_assignment
        }

    print(f"Iteration {iteration+1}/{MAX_ITERATIONS} - Best fitness: {gbest_score:.4f}")

# ----------------------
# Results
# ----------------------

best_orders = gbest_position['order_selection']
best_aisles = gbest_position['aisle_assignment']

print(best_orders)
print(best_aisles)

selected_orders = [idx for idx, selected in enumerate(best_orders) if selected == 1]
total_demand = calculate_batch_item_requirements(best_orders)
aisles_visited = set(best_aisles.values())
total_quantity = sum(total_demand.values())

print("\n✅ Best Batch Found:")
print(f"Selected Orders (indexes): {selected_orders}")
print(f"Total Quantity Picked: {total_quantity}")
print(f"Aisle Assignment: {best_aisles}")
print(f"Number of Corridors Visited: {len(aisles_visited)}")
print(f"Efficiency (items per corridor): {total_quantity / len(aisles_visited) if aisles_visited else 0:.4f}")
