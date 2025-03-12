import numpy as np
import math
import seaborn
import pandas as pd
import copy
import bisect
import random
import matplotlib.pyplot as plt
import itertools
import explorer

orders, warehouse, lb, ub = explorer.parse()

def analyze_batch(order_indices, warehouse):
    #print("\n🔍 Batch Analysis 🔍")
    batch_orders = [orders[i] for i in order_indices]
    
    # Aggregate items and quantities
    total_items_needed = {}
    for order in batch_orders:
        for item, qty in order.items():
            total_items_needed[item] = total_items_needed.get(item, 0) + qty
    
    #print(f"\nSelected Orders: {order_indices}")
    #print(f"Total Items Needed: {total_items_needed}")

    # Aisle assignment decision (basic: pick aisle with max stock)
    aisle_assignment = {}
    for item, qty in total_items_needed.items():
        best_aisle = max(warehouse[item], key=lambda aisle: warehouse[item][aisle])
        aisle_assignment[item] = best_aisle
    
    aisles_visited = set(aisle_assignment.values())
    
    #print(f"\nAisle Assignments:")
    #for item, aisle in aisle_assignment.items():
        #print(f"  Pick {item} from {aisle}")

    # Efficiency
    total_items = sum(total_items_needed.values())
    efficiency = total_items / len(aisles_visited) if aisles_visited else 0
    
    #print(f"\n✅ Batch Stats ✅")
    #print(f"Total items picked: {total_items}")
    #print(f"Aisles visited ({len(aisles_visited)}): {aisles_visited}")
    #print(f"Batch efficiency (items / aisles): {efficiency:.2f}")

    return {
        "total_items": total_items,
        "aisles_visited": aisles_visited,
        "efficiency": efficiency
    }

# Function to plot batch efficiency by different order combinations
def plot_search_space(orders, warehouse, max_combination_size=5):
    combinations = []
    efficiencies = []
    
    for r in range(1, max_combination_size + 1):
        for order_indices in itertools.combinations(range(len(orders)), r):
            stats = analyze_batch(order_indices, warehouse)
            combinations.append(order_indices)
            efficiencies.append(stats['efficiency'])
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.scatter(range(len(efficiencies)), efficiencies, color='blue')
    plt.title('Batch Efficiencies Across Order Combinations')
    plt.xlabel('Combination Index')
    plt.ylabel('Efficiency (items / aisles)')
    plt.grid(True)
    plt.show()

plot_search_space(orders, warehouse)