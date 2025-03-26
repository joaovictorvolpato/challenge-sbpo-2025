import random
from collections import defaultdict
from itertools import combinations
import explorer
import copy
import json

def grasp_aisle_based_batch(warehouse, orders, min_items, max_items, iterations=100, max_aisles_to_visit=10, top_k_aisles=10, instance_name=""):
    best_solution = None
    best_efficiency = 0

    all_aisles = set()
    aisle_total_stock = defaultdict(int)

    for item_data in warehouse.values():
        for aisle, qty in item_data.items():
            aisle_total_stock[aisle] += qty
            all_aisles.add(aisle)

    sorted_aisles = sorted(aisle_total_stock.items(), key=lambda x: -x[1])
    aisle_list = [a for a, _ in sorted_aisles]

    for it in range(iterations):
        num_aisles_to_pick = random.randint(1, max_aisles_to_visit)
        rcl_size = min(top_k_aisles, len(aisle_list))
        candidate_aisles = aisle_list[:rcl_size]

        selected_aisles = set(random.sample(candidate_aisles, num_aisles_to_pick))

        solution = build_batch_from_aisles(selected_aisles, warehouse, orders, min_items, max_items)

        if solution is None:
            continue

        batch_orders, batch_items, aisle_assignment, aisles_visited, efficiency = solution

        improved_solution = local_search_aisles(
            selected_aisles, warehouse, orders, min_items, max_items,
            batch_orders, batch_items, aisle_assignment, aisles_visited, efficiency,
            all_aisles
        )

        if improved_solution is not None:
            batch_orders, batch_items, aisle_assignment, aisles_visited, efficiency = improved_solution

        if efficiency > best_efficiency:
            best_efficiency = efficiency
            best_solution = (batch_orders, batch_items, aisle_assignment, aisles_visited, efficiency)
            write_solution_to_file(batch_orders, aisle_assignment, aisles_visited, instance_name)


    return best_solution

def build_batch_from_aisles(selected_aisles, warehouse, orders, min_items, max_items):
    aisle_item_stock = defaultdict(int)
    for item, aisle_data in warehouse.items():
        for aisle, qty in aisle_data.items():
            if aisle in selected_aisles:
                aisle_item_stock[item] += qty

    batch_orders = set()
    batch_items = defaultdict(int)

    for order_idx, order in enumerate(orders):
        feasible = True
        for item, qty in order.items():
            if aisle_item_stock[item] < qty:
                feasible = False
                break

        if feasible:
            batch_orders.add(order_idx)
            for item, qty in order.items():
                batch_items[item] += qty
                aisle_item_stock[item] -= qty

    total_items = sum(batch_items.values())

    if total_items < min_items or total_items > max_items:
        return None

    aisle_assignment, aisles_visited = assign_aisles_for_batch(batch_items, warehouse)
    if aisle_assignment is None:
        return None

    efficiency = total_items / len(aisles_visited) if aisles_visited else 0

    return batch_orders, batch_items, aisle_assignment, aisles_visited, efficiency

def assign_aisles_for_batch(batch_items, warehouse):
    aisle_assignment = {}
    visited_aisles = set()

    for item, required_qty in batch_items.items():
        remaining_qty = required_qty
        aisle_qty_list = []

        aisles_with_stock = sorted(
            warehouse[item].items(), key=lambda x: -x[1]
        )

        for aisle, available_qty in aisles_with_stock:
            if remaining_qty <= 0:
                break

            pick_qty = min(available_qty, remaining_qty)
            remaining_qty -= pick_qty
            aisle_qty_list.append((aisle, pick_qty))
            visited_aisles.add(aisle)

        if remaining_qty > 0:
            return None, None

        aisle_assignment[item] = aisle_qty_list

    return aisle_assignment, visited_aisles

def local_search_aisles(selected_aisles, warehouse, orders, min_items, max_items,
                        current_orders, current_items, current_assignment, current_visited, current_efficiency,
                        all_aisles):

    best_solution = (
        current_orders, current_items, current_assignment, current_visited, current_efficiency
    )

    improved = True
    while improved:
        improved = False
        neighbors = []

        for aisle in all_aisles - selected_aisles:
            new_aisles = selected_aisles | {aisle}
            neighbors.append(new_aisles)

        if len(selected_aisles) > 1:
            for aisle in selected_aisles:
                new_aisles = selected_aisles - {aisle}
                neighbors.append(new_aisles)

        for neighbor_aisles in neighbors:
            result = build_batch_from_aisles(neighbor_aisles, warehouse, orders, min_items, max_items)

            if result is None:
                continue

            batch_orders, batch_items, aisle_assignment, aisles_visited, efficiency = result

            if efficiency > best_solution[4]:  
                best_solution = (batch_orders, batch_items, aisle_assignment, aisles_visited, efficiency)
                selected_aisles = neighbor_aisles
                improved = True
                break 

    return best_solution if best_solution[4] > current_efficiency else None

def write_solution_to_file(batch_orders, aisle_assignment, aisles_visited, instance_name=""):
    filename = f"outputs/grasp_partial_solution_{instance_name}.txt"    
    with open(filename, "w") as file:
        file.write(f"{len(batch_orders)}\n")
        for order_idx in sorted(batch_orders):
            file.write(f"{order_idx}\n")

        file.write(f"{len(aisles_visited)}\n")
        for aisle in sorted(aisles_visited):
            file.write(f"{aisle}\n")

def run_grasp_algorithm(instance_path: str):
    orders, warehouse, min_items, max_items = explorer.parse(instance_path)
    solution = grasp_aisle_based_batch(warehouse, orders, min_items, max_items, instance_name=instance_path[-6:-4])

    if solution:
        batch_orders, batch_items, aisle_assignment, aisles_visited, efficiency = solution
        #print("Best efficiency:", efficiency)
        #print("Orders selected:", batch_orders)
        #print("Aisles visited:", aisles_visited)
        # write_solution_to_file(batch_orders, aisle_assignment, aisles_visited)
        solution_formatted = {
            "best_efficiency": efficiency,
            "batch_items": batch_items,
            "batch_orders": batch_orders,
            "aisle_assignment": aisle_assignment,
            "aisles_visited": aisles_visited
        }

        return solution_formatted

    return "No valid batch found."


if __name__ == "__main__":
    solution = run_grasp_algorithm("datasets/a/instance_0020.txt")
    print(solution)
