. "$PSScriptRoot/common.ps1"
Invoke-AvelinApi -Method GET -Path "/api/v1/market/remote-rate" | ConvertTo-Json -Depth 20
