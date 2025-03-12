import random
import numpy as np
import explorer

# ----------------------
# Problem Data
# ----------------------

orders, warehouse, lb, ub = explorer.parse()

items = list(warehouse.keys())
NUM_ITEMS = len(items)
NUM_ORDERS = len(orders)

MAX_CAPACITY = ub   
MIN_CAPACITY = lb   

# ----------------------
# PSO Parameters
# ----------------------

NUM_PARTICLES = 500
MAX_ITERATIONS = 200
C1 = 2    
C2 = 2    
W = 1   


def calculate_fitness(particle):
    corridors_visited = set()
    total_quantity = 0

    #print(particle)
    for order_idx, selected in enumerate(particle):
        if selected == 1:  # Order selected
            order = orders[order_idx]
            for item, qty in order.items():
                if item in warehouse:
                    for aisle, aisle_qty in warehouse[item].items():
                        #print("aisle: ", aisle)
                        #print("quantity: ", aisle_qty)
                        if qty <= aisle_qty: 
                            corridors_visited.add(aisle)
                            total_quantity += qty
                            break
                        else:
                            qty =- aisle_qty
                            continue

    num_corridors = len(corridors_visited)

    if total_quantity > MAX_CAPACITY or total_quantity < MIN_CAPACITY:
        return 1e6  

    if num_corridors == 0 or total_quantity == 0:
        efficiency = 0
    else:
        efficiency = total_quantity / num_corridors

    penalty = 0
    if total_quantity > MAX_CAPACITY:
        penalty += (total_quantity - MAX_CAPACITY) * 10
        efficiency = 0
    elif total_quantity < MIN_CAPACITY:
        penalty += (MIN_CAPACITY - total_quantity) * 10
        efficiency = 0

    fitness = -efficiency + penalty
    return fitness

def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# PSO Core 

particles = [np.random.randint(2, size=NUM_ORDERS) for _ in range(0,NUM_PARTICLES)]
velocities = [np.random.uniform(-1, 1, NUM_ORDERS) for _ in range(NUM_PARTICLES)]

pbest_positions = [particle.copy() for particle in particles]
pbest_scores = [calculate_fitness(p) for p in particles]

gbest_index = np.argmin(pbest_scores)
gbest_position = pbest_positions[gbest_index].copy()
gbest_score = pbest_scores[gbest_index]

for iteration in range(MAX_ITERATIONS):
    for i in range(NUM_PARTICLES):
        r1, r2 = random.random(), random.random()
        velocities[i] = (
            W * velocities[i]
            + C1 * r1 * (pbest_positions[i] - particles[i])
            + C2 * r2 * (gbest_position - particles[i])
        )

        prob = sigmoid(velocities[i])
        particles[i] = np.array([1 if random.random() < prob[j] else 0 for j in range(NUM_ORDERS)])

        fitness = calculate_fitness(particles[i])

        if fitness < pbest_scores[i]:
            pbest_scores[i] = fitness
            pbest_positions[i] = particles[i].copy()

        if fitness < gbest_score:
            gbest_score = fitness
            gbest_position = particles[i].copy()

    print(f"Iteration {iteration + 1}/{MAX_ITERATIONS}: Best Fitness = {gbest_score:.4f}")
    print("BEST POSITION FOUND:", gbest_position)



selected_orders = [i for i in range(NUM_ORDERS) if gbest_position[i] == 1]
total_quantity = sum([sum(order.values()) for i, order in enumerate(orders) if gbest_position[i] == 1])

corridors_visites = set()
for order_idx, selected in enumerate(gbest_position):
    if selected == 1:  # Order selected
        order = orders[order_idx]
        for item, qty in order.items():
            if item in warehouse:
                for aisle, aisle_qty in warehouse[item].items():
                    #print("aisle: ", aisle)
                    #print("quantity: ", aisle_qty)
                    if qty <= aisle_qty:
                        corridors_visites.add(aisle)
                        total_quantity += qty
                        break
                    else:
                        qty =- aisle_qty
                        continue

num_corridors = len(corridors_visites)

efficiency = total_quantity / num_corridors if num_corridors != 0 else 0

#print(f"Selected Orders (indexes): {selected_orders}")
#print(f"Total Quantity Picked: {total_quantity}")
#print(f"Corridors Visited (indexes): {sorted(corridors_visites)}")
#print(f"Number of Corridors Visited: {num_corridors}")
#print(f"Efficiency (items per corridor): {efficiency:.4f}")
