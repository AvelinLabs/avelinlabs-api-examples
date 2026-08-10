. "$PSScriptRoot/common.ps1"
Invoke-AvelinApi -Method GET -Path "/health/live" -AuthRequired $false | ConvertTo-Json -Depth 20
