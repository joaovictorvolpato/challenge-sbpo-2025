import random
import numpy as np
import explorer
from collections import defaultdict
import pulp

# Data

orders, warehouse, lb, ub = explorer.parse()

M = 10
min_items = lb
max_items = ub

O = list(range(len(orders)))
I = list(set(i for order in orders for i in order))
A = list(set(a for aisles in warehouse.values() for a in aisles))

model = pulp.LpProblem("Order_Batching_Aisle_Assignment", pulp.LpMaximize)

x = pulp.LpVariable.dicts("SelectOrder", O, cat="Binary") # X_o = 1 if the order o is selected 0 otherwise           
y = pulp.LpVariable.dicts("VisitAisle", A, cat="Binary")  # Y_a = 1 if the aisle a is visited 0 otherwise   
z = pulp.LpVariable.dicts("PickItemFromAisle", [(i, a) for i in I for a in A], cat="Binary") #Z_ia = 1 if the item i was picked from aisle a


total_items_picked = pulp.lpSum(
    orders[o].get(i, 0) * x[o] for o in O for i in I
)
total_aisles_visited = pulp.lpSum(
    y[a] for a in A
)

model += total_items_picked - M * total_aisles_visited

for i in I:
    demand = pulp.lpSum(orders[o].get(i, 0) * x[o] for o in O) # how many items of the item i we have on the order
    supply = pulp.lpSum(warehouse[i].get(a, 0) * z[(i, a)] for a in A) #how many units of the item i we have on the ailse a * if you picked that item from that isle
    model += demand <= supply #number of picked items must be equal or less the number of items in the aisle

# If you didnt visited the aisle you cannot retreive items from there
for i in I:
    for a in A:
        model += z[(i, a)] <= y[a]

# If there is no item in the aisle we cannot retrieve that item from that aisle (optimazation)
for i in I:
    for a in A:
        if warehouse[i].get(a, 0) == 0:
            model += z[(i, a)] == 0

model += total_items_picked >= min_items
model += total_items_picked <= max_items

# Solve the model with CBC solver
solver = pulp.PULP_CBC_CMD(msg=True)
solver.timeLimit = 60
model.solve(solver)

selected_orders = []
for o in O:
    if x[o].varValue > 0.5:
        print(f"Order {o}: {orders[o]}")
        selected_orders.append(o)

visited_aisles = []
for a in A:
    if y[a].varValue > 0.5:
        print(f"Aisle: {a}")
        visited_aisles.append(a)

def write_solution_to_file(selected_orders, visited_aisles, filename="best_solution_lp.txt"):
    """
    Writes the IP/LP best solution to a file in the following format:
    - number of orders selected
    - list of selected orders
    - number of aisles visited
    - list of visited aisles
    """

    with open(filename, "w") as file:
        # Number of orders selected
        file.write(f"{len(selected_orders)}\n")

        # List selected orders (could be indices or IDs, depending on your orders structure)
        for order_idx in selected_orders:
            file.write(f"{order_idx}\n")

        # Number of aisles visited
        file.write(f"{len(visited_aisles)}\n")

        # List each visited aisle
        for aisle in visited_aisles:
            file.write(f"{aisle}\n")

write_solution_to_file(selected_orders, visited_aisles)

