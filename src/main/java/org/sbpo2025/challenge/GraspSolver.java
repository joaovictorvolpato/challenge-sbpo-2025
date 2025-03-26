package org.sbpo2025.challenge;

import java.util.*;
import java.util.stream.Collectors;

public class GraspSolver {
    private final List<Map<Integer, Integer>> orders;
    private final List<Map<Integer, Integer>> aisles;
    private final int nItems;
    private final int waveSizeLB;
    private final int waveSizeUB;
    private final Random random = new Random();

    public GraspSolver(List<Map<Integer, Integer>> orders, List<Map<Integer, Integer>> aisles,
                       int nItems, int waveSizeLB, int waveSizeUB) {
        this.orders = orders;
        this.aisles = aisles;
        this.nItems = nItems;
        this.waveSizeLB = waveSizeLB;
        this.waveSizeUB = waveSizeUB;
    }

    public ChallengeSolution solve() {
        int iterations = 50;
        int maxAislesToVisit = 10;
        int topKAisles = 10;
        ChallengeSolution bestSolution = null;
        double bestEfficiency = 0;

        Map<Integer, Integer> aisleTotalStock = new HashMap<>();
        Set<Integer> allAisles = new HashSet<>();

        for (int item = 0; item < nItems; item++) {
            for (Map.Entry<Integer, Integer> entry : getAislesWithItem(item).entrySet()) {
                aisleTotalStock.put(entry.getKey(), aisleTotalStock.getOrDefault(entry.getKey(), 0) + entry.getValue());
                allAisles.add(entry.getKey());
            }
        }

        List<Integer> sortedAisles = aisleTotalStock.entrySet().stream()
                .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
                .map(Map.Entry::getKey)
                .collect(Collectors.toList());

        for (int it = 0; it < iterations; it++) {
            int numAislesToPick = 1 + random.nextInt(maxAislesToVisit);
            int rclSize = Math.min(topKAisles, sortedAisles.size());
            List<Integer> candidateAisles = sortedAisles.subList(0, rclSize);
            Set<Integer> selectedAisles = new HashSet<>(candidateAisles.subList(0, Math.min(numAislesToPick, candidateAisles.size())));

            ChallengeSolution candidate = buildBatchFromAisles(selectedAisles);
            if (candidate == null) continue;

            ChallengeSolution improved = localSearch(selectedAisles, candidate, allAisles);
            double eff = computeObjectiveFunction(improved);

            if (eff > bestEfficiency) {
                bestEfficiency = eff;
                bestSolution = improved;
            }
        }

        return bestSolution;
    }

    private ChallengeSolution buildBatchFromAisles(Set<Integer> selectedAisles) {
        Map<Integer, Integer> aisleItemStock = new HashMap<>();
        for (int item = 0; item < nItems; item++) {
            int total = 0;
            for (int aisle : selectedAisles) {
                total += getStock(item, aisle);
            }
            aisleItemStock.put(item, total);
        }

        Set<Integer> batchOrders = new HashSet<>();
        Map<Integer, Integer> batchItems = new HashMap<>();

        for (int orderIdx = 0; orderIdx < orders.size(); orderIdx++) {
            Map<Integer, Integer> order = orders.get(orderIdx);
            boolean feasible = true;

            for (Map.Entry<Integer, Integer> e : order.entrySet()) {
                if (aisleItemStock.getOrDefault(e.getKey(), 0) < e.getValue()) {
                    feasible = false;
                    break;
                }
            }

            if (feasible) {
                batchOrders.add(orderIdx);
                for (Map.Entry<Integer, Integer> e : order.entrySet()) {
                    batchItems.put(e.getKey(), batchItems.getOrDefault(e.getKey(), 0) + e.getValue());
                    aisleItemStock.put(e.getKey(), aisleItemStock.get(e.getKey()) - e.getValue());
                }
            }
        }

        int totalItems = batchItems.values().stream().mapToInt(Integer::intValue).sum();
        if (totalItems < waveSizeLB || totalItems > waveSizeUB) return null;

        Set<Integer> aislesVisited = assignAisles(batchItems);
        if (aislesVisited == null) return null;

        return new ChallengeSolution(batchOrders, aislesVisited);
    }

    private ChallengeSolution localSearch(Set<Integer> selectedAisles, ChallengeSolution base, Set<Integer> allAisles) {
        ChallengeSolution best = base;
        double bestEff = computeObjectiveFunction(best);
        boolean improved = true;

        while (improved) {
            improved = false;
            List<Set<Integer>> neighbors = new ArrayList<>();

            for (int aisle : allAisles) {
                if (!selectedAisles.contains(aisle)) {
                    Set<Integer> added = new HashSet<>(selectedAisles);
                    added.add(aisle);
                    neighbors.add(added);
                }
            }

            if (selectedAisles.size() > 1) {
                for (int aisle : selectedAisles) {
                    Set<Integer> removed = new HashSet<>(selectedAisles);
                    removed.remove(aisle);
                    neighbors.add(removed);
                }
            }

            for (Set<Integer> neighbor : neighbors) {
                ChallengeSolution candidate = buildBatchFromAisles(neighbor);
                if (candidate == null) continue;

                double eff = computeObjectiveFunction(candidate);
                if (eff > bestEff) {
                    best = candidate;
                    bestEff = eff;
                    selectedAisles = new HashSet<>(neighbor);
                    improved = true;
                    break;
                }
            }
        }

        return best;
    }

    private Set<Integer> assignAisles(Map<Integer, Integer> batchItems) {
        Set<Integer> visited = new HashSet<>();

        for (Map.Entry<Integer, Integer> entry : batchItems.entrySet()) {
            int item = entry.getKey();
            int needed = entry.getValue();
            int remaining = needed;

            List<Map.Entry<Integer, Integer>> aislesWithItem = getAislesWithItem(item).entrySet().stream()
                    .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
                    .collect(Collectors.toList());

            for (Map.Entry<Integer, Integer> e : aislesWithItem) {
                int aisle = e.getKey();
                int available = e.getValue();

                if (remaining <= 0) break;
                visited.add(aisle);
                remaining -= available;
            }

            if (remaining > 0) return null;
        }

        return visited;
    }

    private Map<Integer, Integer> getAislesWithItem(int item) {
        Map<Integer, Integer> aislesWithStock = new HashMap<>();
        for (int a = 0; a < aisles.size(); a++) {
            if (aisles.get(a).containsKey(item)) {
                aislesWithStock.put(a, aisles.get(a).get(item));
            }
        }
        return aislesWithStock;
    }

    private int getStock(int item, int aisle) {
        if (aisle >= aisles.size()) return 0;
        return aisles.get(aisle).getOrDefault(item, 0);
    }

    private double computeObjectiveFunction(ChallengeSolution solution) {
        int total = solution.orders().stream()
                .mapToInt(o -> orders.get(o).values().stream().mapToInt(Integer::intValue).sum())
                .sum();
        int aislesCount = solution.aisles().size();
        return aislesCount == 0 ? 0 : (double) total / aislesCount;
    }
}
