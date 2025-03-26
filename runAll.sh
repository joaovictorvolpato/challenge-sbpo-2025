#!/bin/bash

jarPath="target/ChallengeSBPO2025-1.0.jar"
inputDir="datasets/a"
outputDir="outputs"

# Create output directory if it doesn't exist
mkdir -p "$outputDir"

# Loop through instances
for i in $(seq -f "%04g" 1 20); do
    inputFile="$inputDir/instance_$i.txt"
    outputFile="$outputDir/out_$i.txt"
    echo "Executando para $inputFile..."
    
    java -jar "$jarPath" "$inputFile" "$outputFile"
done

echo "✅ Execução finalizada para todas as instâncias."
