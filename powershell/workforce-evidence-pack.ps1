Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $env:AVELIN_API_KEY) {
    throw "Set AVELIN_API_KEY to a Runtime API Key before running this example."
}

$baseUrl = if ($env:BASE_URL) { $env:BASE_URL.TrimEnd("/") } else { "https://api.avelinlabs.com" }
$headers = @{
    Authorization = "Bearer $($env:AVELIN_API_KEY)"
    Accept = "application/json"
}
$root = Split-Path $PSScriptRoot -Parent
$requestPath = Join-Path $root "workforce-evidence-pack\request.json"
$outputDir = if ($env:OUTPUT_DIR) { $env:OUTPUT_DIR } else { Join-Path $root "workforce-evidence-pack\output" }
$request = Get-Content -Raw -Path $requestPath | ConvertFrom-Json

$capabilities = Invoke-RestMethod `
    -Method Get `
    -Uri "$baseUrl/api/v1/workforce/capabilities?country_code=US" `
    -Headers $headers

if ($capabilities.features.evidence_pack_creation -ne "available") {
    throw "Evidence Pack creation is not enabled for US in this environment."
}

$occupationHelp = Invoke-RestMethod `
    -Method Get `
    -Uri "$baseUrl/api/v1/workforce/occupations?country_code=US&query=welder&limit=5" `
    -Headers $headers

if (@($occupationHelp.items.code) -notcontains "51-4121") {
    throw "The SOC help response did not contain 51-4121."
}

$detail = Invoke-RestMethod `
    -Method Get `
    -Uri "$baseUrl/api/v1/workforce/occupations/51-4121?country_code=US" `
    -Headers $headers

if ($detail.code -ne "51-4121") { throw "Unexpected SOC detail response." }

$body = $request | ConvertTo-Json -Depth 10
$first = Invoke-RestMethod `
    -Method Post `
    -Uri "$baseUrl/api/v1/workforce/evidence-packs" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $body

$reorderedIndustries = @($request.industries)
$reorderedOccupations = @($request.occupations)
[array]::Reverse($reorderedIndustries)
[array]::Reverse($reorderedOccupations)
$request.industries = $reorderedIndustries
$request.occupations = $reorderedOccupations
$reorderedBody = $request | ConvertTo-Json -Depth 10
$second = Invoke-RestMethod `
    -Method Post `
    -Uri "$baseUrl/api/v1/workforce/evidence-packs" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $reorderedBody

if ($second.evidence_pack_id -ne $first.evidence_pack_id -or $second.cache_status -ne "reused") {
    throw "Deterministic cache reuse check failed."
}

$packId = $first.evidence_pack_id
$document = Invoke-RestMethod `
    -Method Get `
    -Uri "$baseUrl/api/v1/workforce/evidence-packs/$packId" `
    -Headers $headers

New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
$jsonPath = Join-Path $outputDir "$packId.json"
$htmlPath = Join-Path $outputDir "$packId.html"
$document | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 -Path $jsonPath

Invoke-WebRequest `
    -UseBasicParsing `
    -Method Get `
    -Uri "$baseUrl/api/v1/workforce/evidence-packs/$packId/report?format=html" `
    -Headers $headers `
    -OutFile $htmlPath

[pscustomobject]@{
    status = "passed"
    evidence_pack_id = $packId
    first_cache_status = $first.cache_status
    cache_reused = $true
    occupations = @($document.evidence.occupations).Count
    industries = @($document.evidence.industries).Count
    json_path = $jsonPath
    html_path = $htmlPath
} | ConvertTo-Json -Depth 5
