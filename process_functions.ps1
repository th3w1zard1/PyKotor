# Parse the function list and generate comment batches
$filePath = "c:\Users\boden\OneDrive\Documents\swkotor2.exe.re.txt"
$content = Get-Content $filePath

$functions = @()
foreach ($line in $content) {
    if ($line -match '^([^\t]+)\t([0-9a-fA-F]+)\t(.+?)\t\d+$') {
        $name = $matches[1]
        $address = "0x$($matches[2])"
        $signature = $matches[3]
        $functions += @{
            Name = $name
            Address = $address
            Signature = $signature
        }
    }
}

Write-Host "Parsed $($functions.Count) functions"

# Group into batches of 20
$batchSize = 20
$batches = @()
for ($i = 0; $i -lt $functions.Count; $i += $batchSize) {
    $batch = $functions[$i..([Math]::Min($i + $batchSize - 1, $functions.Count - 1))]
    $batches += ,$batch
}

Write-Host "Created $($batches.Count) batches"

# Generate JSON for each batch (starting from batch 3, since we've done 0-2)
for ($batchIdx = 2; $batchIdx -lt $batches.Count; $batchIdx++) {
    $batch = $batches[$batchIdx]
    $comments = @()
    foreach ($func in $batch) {
        $comments += @{
            address = $func.Address
            comment = "Function signature: $($func.Signature)"
            comment_type = "eol"
        }
    }
    
    $json = $comments | ConvertTo-Json -Depth 10
    $json | Out-File "batch_$batchIdx.json" -Encoding UTF8
    Write-Host "Generated batch_$batchIdx.json with $($batch.Count) functions"
}

Write-Host "Done generating batch files"
