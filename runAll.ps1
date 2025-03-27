$jarPath = "target/ChallengeSBPO2025-1.0.jar"
$inputDir = "datasets/a"
$outputDir = "outputs"

if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir
}

For ($i = 1; $i -le 20; $i++) {
    $index = "{0:D4}" -f $i
    $inputFile = "$inputDir\instance_$index.txt"
    $outputFile = "$outputDir\out_$index.txt"
    java -jar $jarPath $inputFile $outputFile
}

Write-Host "✅ Execução finalizada para todas as instâncias."
