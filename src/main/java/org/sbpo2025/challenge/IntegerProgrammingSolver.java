package org.sbpo2025.challenge;

import ilog.concert.*;
import ilog.cplex.IloCplex;

import java.util.*;

public class IntegerProgrammingSolver {
    private final List<Map<Integer, Integer>> orders;
    private final List<Map<Integer, Integer>> aisles;
    private final int nItems;
    private final int waveSizeLB;
    private final int waveSizeUB;

    public IntegerProgrammingSolver(List<Map<Integer, Integer>> orders, List<Map<Integer, Integer>> aisles,
                                    int nItems, int waveSizeLB, int waveSizeUB) {
        this.orders = orders;
        this.aisles = aisles;
        this.nItems = nItems;
        this.waveSizeLB = waveSizeLB;
        this.waveSizeUB = waveSizeUB;
    }

    public ChallengeSolution solve() {
        try {
            IloCplex cplex = new IloCplex();
            cplex.setParam(IloCplex.Param.TimeLimit, 550);

            int O = orders.size();
            int A = aisles.size();

            Set<Integer> itemSet = new HashSet<>();
            for (Map<Integer, Integer> order : orders) {
                itemSet.addAll(order.keySet());
            }

            IloNumVar[] x = cplex.boolVarArray(O); 
            IloNumVar[] y = cplex.boolVarArray(A); 

            Map<String, IloNumVar> z = new HashMap<>(); 
            for (int i : itemSet) {
                for (int a = 0; a < A; a++) {
                    z.put(i + "_" + a, cplex.boolVar("z_" + i + "_" + a));
                }
            }

            int M = 10;
            IloLinearNumExpr totalItems = cplex.linearNumExpr();
            for (int o = 0; o < O; o++) {
                for (Map.Entry<Integer, Integer> e : orders.get(o).entrySet()) {
                    totalItems.addTerm(e.getValue(), x[o]);
                }
            }

            IloLinearNumExpr totalAisles = cplex.linearNumExpr();
            for (int a = 0; a < A; a++) {
                totalAisles.addTerm(M, y[a]);
            }

            cplex.addMaximize(cplex.diff(totalItems, totalAisles));

            for (int i : itemSet) {
                IloLinearNumExpr demand = cplex.linearNumExpr();
                for (int o = 0; o < O; o++) {
                    demand.addTerm(orders.get(o).getOrDefault(i, 0), x[o]);
                }

                IloLinearNumExpr supply = cplex.linearNumExpr();
                for (int a = 0; a < A; a++) {
                    int available = aisles.get(a).getOrDefault(i, 0);
                    if (available > 0) {
                        supply.addTerm(available, z.get(i + "_" + a));
                    } else {
                        cplex.addEq(z.get(i + "_" + a), 0); 
                    }
                }

                cplex.addLe(demand, supply);
            }

            for (int i : itemSet) {
                for (int a = 0; a < A; a++) {
                    cplex.addLe(z.get(i + "_" + a), y[a]);
                }
            }

            IloLinearNumExpr total = cplex.linearNumExpr();
            for (int o = 0; o < O; o++) {
                for (Map.Entry<Integer, Integer> e : orders.get(o).entrySet()) {
                    total.addTerm(e.getValue(), x[o]);
                }
            }

            cplex.addGe(total, waveSizeLB);
            cplex.addLe(total, waveSizeUB);

            if (cplex.solve()) {
                Set<Integer> selectedOrders = new HashSet<>();
                Set<Integer> visitedAisles = new HashSet<>();

                for (int o = 0; o < O; o++) {
                    if (cplex.getValue(x[o]) > 0.5) {
                        selectedOrders.add(o);
                    }
                }

                for (int a = 0; a < A; a++) {
                    if (cplex.getValue(y[a]) > 0.5) {
                        visitedAisles.add(a);
                    }
                }

                return new ChallengeSolution(selectedOrders, visitedAisles);
            } else {
                System.out.println("CPLEX did not find a solution.");
            }

            cplex.end();
        } catch (IloException e) {
            e.printStackTrace();
        }

        return null;
    }
}
