#!/bin/bash

INPUT_DIR="./datasets/a"
OUTPUT_DIR="./outputs/checker_input"
ALGORITHM_NAME="pso"

mkdir -p "$OUTPUT_DIR"

for input_file in "$INPUT_DIR"/instance_00*.txt; do
    base_name=$(basename "$input_file" .txt)
    output_file="$OUTPUT_DIR/${ALGORITHM_NAME}_partial_solution_${base_name#instance_00}.txt"

    python3 checker.py "$input_file" "$output_file"

    echo "Processado: $input_file -> $output_file"
done
