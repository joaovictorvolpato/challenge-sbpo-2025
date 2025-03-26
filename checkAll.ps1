$inputDir = "datasets/a"
$outputDir = "outputs"
$checker = "checker.py"  # Caminho para o script checker

For ($i = 1; $i -le 20; $i++) {
    $index = "{0:D4}" -f $i
    $inputFile = "$inputDir\instance_$index.txt"
    $outputFile = "$outputDir\out_$index.txt"

    if (Test-Path $outputFile) {
        Write-Host "`n🔍 Verificando $outputFile..."
        python $checker $inputFile $outputFile
    } else {
        Write-Host "⚠️ Arquivo não encontrado: $outputFile"
    }
}
