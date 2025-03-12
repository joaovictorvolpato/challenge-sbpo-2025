import numpy as np
import math
import seaborn
import pandas as pd
import copy
import bisect
import random
import matplotlib.pyplot as plt
from collections import defaultdict
from itertools import combinations

path = "/home/joaovolp/challenge-sbpo-2025/datasets/a"


def parse():
    with open(f"{path}/instance_0001.txt","r") as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines if line.strip()]
        first_line = lines[0].split()
        orders = int(first_line[0])
        items = int(first_line[1])
        aisle = int(first_line[2])

        orders_list = []
        #aisle_list = []

        for line in lines[1:orders+1]:
            line = line.split()
            size = int(line[0])
            i = 1
            orders_book = {}
            while i <= size * 2:
                item = int(line[i])
                quantity = int(line[i+1])
                orders_book[item] = quantity
                i += 2
            orders_list.append(copy.deepcopy(orders_book))

        aisle_book = {}
        aisle_num = 0
        for line in lines[1 + orders: - 1]:            
            line = line.split()
            size = int(line[0])
            i = 1
            while i <= size * 2:
                item_num = int(line[i])
                quantity = int(line[i+1])
                if item_num not in aisle_book.keys():
                    aisle_book[item_num] = {aisle_num : quantity}
                else:
                    aisle_book[item_num].update({aisle_num : quantity})
                i += 2
            aisle_num += 1

        list = lines[-1].split()
        lower_b = list[0]
        upper_b = list[1]

        #print(orders_list)

        return orders_list, aisle_book, int(lower_b), int(upper_b)


def find_cost_for_wave(wave, orders_list, aisle_book):
    wave_cost = 0
    total_order = {}
    for x in wave:
        for key, value in orders_list[x].items():
            if key in total_order.keys():
                total_order[key] += value
            else:
                total_order[key] = value
        
    #print(total_order)
    #print(aisle_book)
    cost = find_aisles_and_items(total_order,aisle_book)
    wave_cost += cost

    return wave_cost

def generate_wave(orders_list, lower_b, upper_b):

    size_of_orders_list = len(orders_list)
    qnty_orders_on_wave = random.randint(1,size_of_orders_list)
    wave = random.sample(range(0, size_of_orders_list), qnty_orders_on_wave)
    check, items = validate_wave(wave,orders_list,lower_b,upper_b)
    #print(wave)
    #print(items)
    if(check):
        return wave, items
    else:
        return False, False

def validate_wave(wave,orders_list, lower_b, upper_b):
    total_items_in_wave = 0
    for x in wave:
        order = orders_list[x]
        #print(order)
        for _, value in order.items():
            total_items_in_wave += value

    if(lower_b < total_items_in_wave < upper_b ):
        return True, total_items_in_wave
    else:
        return False, _
    
def is_valid_combination(selected_corridors, order, warehouse):
    items_picked = defaultdict(int)
    for corridor in selected_corridors:
        for item in warehouse:
            if corridor in warehouse[item]:
                items_picked[item] += warehouse[item][corridor]
    
    return all(items_picked[item] >= order[item] for item in order)

def find_aisles_and_items(order,aisle_book):
    corridors_visited = set()
    items_to_pick = order.copy()
    retrieval_plan = defaultdict(int)

    corridor_scores = defaultdict(int)
    for item, corridors in aisle_book.items():
        if item in items_to_pick:
            for corridor, available in corridors.items():
                corridor_scores[corridor] += min(items_to_pick[item], available)

    sorted_corridors = sorted(corridor_scores.items(), key=lambda x: x[1], reverse=True)

    for corridor, _ in sorted_corridors:
        for item in aisle_book:
            if item in items_to_pick and items_to_pick[item] > 0 and corridor in aisle_book[item]:
                take = min(items_to_pick[item], aisle_book[item][corridor])
                retrieval_plan[(item, corridor)] += take
                corridors_visited.add(corridor)
                items_to_pick[item] -= take

    if any(amount > 0 for amount in items_to_pick.values()):
        return 1000

    return len(corridors_visited)

def find_aisles_and_items_exaustive(order, aisle_book):
    all_corridors = set()
    for corridors in aisle_book.values():
        all_corridors.update(corridors.keys())
    
    # Try from the smallest number of corridors upwards
    for r in range(1, len(all_corridors) + 1):
        for selected_corridors in combinations(all_corridors, r):
            if is_valid_combination(selected_corridors, order, aisle_book):
                retrieval_plan = defaultdict(int)
                remaining_order = order.copy()
                for corridor in selected_corridors:
                    for item in aisle_book:
                        if item in remaining_order and remaining_order[item] > 0 and corridor in aisle_book[item]:
                            take = min(remaining_order[item], aisle_book[item][corridor])
                            retrieval_plan[(item, corridor)] += take
                            remaining_order[item] -= take
                
                return len(selected_corridors)

def aisles_for_order_cost(item : int, qnty : int, aisle_book : dict):
    visited_aisle = []
    availabe = aisle_book.get(item)[::-1]
    x = 0
    total = sum(availabe)
    if qnty > total:
        return 10000 
    while x < len(availabe):
        if availabe[x] >= qnty:
            return x + 1, visited_aisle
        else:
            qnty = qnty - availabe[x]
            x +=1

            
if __name__ == '__main__':
    o_list, a_book, lb, ub = parse()
    number_of_waves = 100
    x = 0
    res = {"cost": [], "items": [] }
    df = pd.DataFrame(data=res)
    while x < number_of_waves:
        wave, items = generate_wave(orders_list=o_list, lower_b=lb, upper_b=ub)
        if wave == False or items == False:
            continue
        cost = find_cost_for_wave(wave, o_list, a_book)
        df = pd.concat([df, pd.DataFrame({"cost":[cost],"items":[items]})], ignore_index=True)
        x += 1

    df['objective'] = df['items']/df['cost']
    print(df)
    
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    ax.scatter(df['cost'], df['items'], df['objective'])

    ax.set_xlabel('Corredores')
    ax.set_ylabel('Items')
    ax.set_zlabel('Função Objetivo')

    ax.set_xlim(0,60)

    #plt.show()

    



