. "$PSScriptRoot/common.ps1"
Invoke-AvelinApi -Method GET -Path "/api/v1/market/technologies/trending?limit=20" | ConvertTo-Json -Depth 20
