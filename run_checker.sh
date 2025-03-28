#!/bin/bash

INPUT_DIR="./datasets/a"
OUTPUT_DIR="./outputs"

mkdir -p "$OUTPUT_DIR"


for i in {0001..0020}; do
    output_file="$OUTPUT_DIR/out_$i.txt"
    input_file="$INPUT_DIR/instance_$i.txt"
    if [[ -f "$output_file" ]]; then
        echo "Processing $output_file"
        python3 checker.py "$input_file" "$output_file"
    else
        echo "File $output_file not found"
    fi
done