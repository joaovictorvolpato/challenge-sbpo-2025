package org.sbpo2025.challenge;

import org.apache.commons.lang3.time.StopWatch;

import java.util.*;

public class PsoSolver {
    private final int NUM_PARTICLES = 200;
    private final int NUM_ITERATIONS = 40;
    private final double MUTATION_RATE = 0.6;
    private final Random random = new Random();

    private final List<Map<Integer, Integer>> orders;
    private final List<Map<Integer, Integer>> aisles;
    private final int nItems;
    private final int waveSizeLB;
    private final int waveSizeUB;

    public PsoSolver(List<Map<Integer, Integer>> orders, List<Map<Integer, Integer>> aisles,
                     int nItems, int waveSizeLB, int waveSizeUB) {
        this.orders = orders;
        this.aisles = aisles;
        this.nItems = nItems;
        this.waveSizeLB = waveSizeLB;
        this.waveSizeUB = waveSizeUB;
    }

    public ChallengeSolution solve(StopWatch stopWatch) {
        Set<Integer> bestOrderSelection = null;
        Set<Integer> bestAislesVisited = null;
        double bestFitness = Double.NEGATIVE_INFINITY;

        List<Particle> swarm = new ArrayList<>();
        Set<Integer> tabu = new HashSet<>();

        for (int i = 0; i < NUM_PARTICLES; i++) {
            Particle p = initializeParticle();
            if (p != null && tabu.add(p.hashCode())) {
                p.fitness = computeObjectiveFunction(p.orderSelection, p.aislesVisited);
                p.bestFitness = p.fitness;
                p.bestOrderSelection = new HashSet<>(p.orderSelection);
                p.bestAislesVisited = new HashSet<>(p.aislesVisited);
                swarm.add(p);

                if (p.fitness > bestFitness) {
                    bestFitness = p.fitness;
                    bestOrderSelection = p.orderSelection;
                    bestAislesVisited = p.aislesVisited;
                }
            }
        }

        for (int iter = 0; iter < NUM_ITERATIONS; iter++) {
            for (Particle p : swarm) {
                Set<Integer> mutatedOrders = mutateOrderSelection(p.orderSelection);
                Set<Integer> aislesVisited = assignAisles(mutatedOrders);
                if (aislesVisited == null) continue;

                if (!isSolutionFeasible(mutatedOrders, aislesVisited)) continue;

                double fitness = computeObjectiveFunction(mutatedOrders, aislesVisited);
                if (fitness > p.bestFitness) {
                    p.bestFitness = fitness;
                    p.bestOrderSelection = mutatedOrders;
                    p.bestAislesVisited = aislesVisited;
                }
                if (fitness > bestFitness) {
                    bestFitness = fitness;
                    bestOrderSelection = mutatedOrders;
                    bestAislesVisited = aislesVisited;
                }
                p.orderSelection = mutatedOrders;
                p.aislesVisited = aislesVisited;
                p.fitness = fitness;
            }
        }

        return new ChallengeSolution(bestOrderSelection, bestAislesVisited);
    }

    private Particle initializeParticle() {
        Set<Integer> selectedOrders = new HashSet<>();
        List<Integer> indices = new ArrayList<>();
        for (int i = 0; i < orders.size(); i++) indices.add(i);
        Collections.shuffle(indices);
        int totalItems = 0;

        for (int idx : indices) {
            int orderItems = orders.get(idx).values().stream().mapToInt(Integer::intValue).sum();
            if (totalItems + orderItems > waveSizeUB) continue;
            selectedOrders.add(idx);
            totalItems += orderItems;
            if (totalItems >= waveSizeLB) break;
        }

        if (totalItems < waveSizeLB || totalItems > waveSizeUB) return null;
        Set<Integer> aislesVisited = assignAisles(selectedOrders);
        if (aislesVisited == null) return null;

        return new Particle(selectedOrders, aislesVisited);
    }

    private Set<Integer> mutateOrderSelection(Set<Integer> current) {
        Set<Integer> result = new HashSet<>(current);
        for (int i = 0; i < orders.size(); i++) {
            if (random.nextDouble() < MUTATION_RATE) {
                if (result.contains(i)) result.remove(i);
                else result.add(i);
            }
        }
        int total = result.stream().mapToInt(o -> orders.get(o).values().stream().mapToInt(Integer::intValue).sum()).sum();
        if (total < waveSizeLB || total > waveSizeUB) return current;
        return result;
    }

    private Set<Integer> assignAisles(Set<Integer> selectedOrders) {
        int[] itemDemand = new int[nItems];
        for (int order : selectedOrders) {
            for (Map.Entry<Integer, Integer> e : orders.get(order).entrySet()) {
                itemDemand[e.getKey()] += e.getValue();
            }
        }
        int[] itemAvailable = new int[nItems];
        Set<Integer> aislesVisited = new HashSet<>();

        for (int a = 0; a < aisles.size(); a++) {
            for (Map.Entry<Integer, Integer> e : aisles.get(a).entrySet()) {
                itemAvailable[e.getKey()] += e.getValue();
            }
        }

        for (int i = 0; i < nItems; i++) {
            if (itemDemand[i] > itemAvailable[i]) return null;
        }

        for (int i = 0; i < nItems; i++) {
            int needed = itemDemand[i];
            if (needed == 0) continue;
            for (int a = 0; a < aisles.size(); a++) {
                int available = aisles.get(a).getOrDefault(i, 0);
                if (available > 0) {
                    aislesVisited.add(a);
                    needed -= available;
                    if (needed <= 0) break;
                }
            }
        }

        return aislesVisited;
    }

    private boolean isSolutionFeasible(Set<Integer> selectedOrders, Set<Integer> visitedAisles) {
        if (selectedOrders.isEmpty() || visitedAisles.isEmpty()) return false;

        int[] totalPicked = new int[nItems];
        int[] totalAvailable = new int[nItems];

        for (int o : selectedOrders) {
            for (Map.Entry<Integer, Integer> e : orders.get(o).entrySet()) {
                totalPicked[e.getKey()] += e.getValue();
            }
        }

        for (int a : visitedAisles) {
            for (Map.Entry<Integer, Integer> e : aisles.get(a).entrySet()) {
                totalAvailable[e.getKey()] += e.getValue();
            }
        }

        int total = Arrays.stream(totalPicked).sum();
        if (total < waveSizeLB || total > waveSizeUB) return false;

        for (int i = 0; i < nItems; i++) {
            if (totalPicked[i] > totalAvailable[i]) return false;
        }

        return true;
    }

    private double computeObjectiveFunction(Set<Integer> selectedOrders, Set<Integer> visitedAisles) {
        if (selectedOrders.isEmpty() || visitedAisles.isEmpty()) return 0.0;

        int totalItems = 0;
        for (int order : selectedOrders) {
            totalItems += orders.get(order).values().stream().mapToInt(Integer::intValue).sum();
        }

        return (double) totalItems / visitedAisles.size();
    }

    private static class Particle {
        Set<Integer> orderSelection;
        Set<Integer> aislesVisited;
        double fitness;
        Set<Integer> bestOrderSelection;
        Set<Integer> bestAislesVisited;
        double bestFitness;

        public Particle(Set<Integer> orderSelection, Set<Integer> aislesVisited) {
            this.orderSelection = orderSelection;
            this.aislesVisited = aislesVisited;
        }

        @Override
        public int hashCode() {
            return Objects.hash(orderSelection, aislesVisited);
        }
    }
}
