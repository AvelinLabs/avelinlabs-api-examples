. "$PSScriptRoot/common.ps1"

$payloadPath = Join-Path (Split-Path $PSScriptRoot -Parent) "payloads/job-classify.json"
$payload = Get-Content -Raw -Path $payloadPath | ConvertFrom-Json
Invoke-AvelinApi -Method POST -Path "/api/v1/job/classify" -Body $payload | ConvertTo-Json -Depth 20
