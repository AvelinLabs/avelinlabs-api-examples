. "$PSScriptRoot/common.ps1"
Invoke-AvelinApi -Method GET -Path "/health/ready" -AuthRequired $false | ConvertTo-Json -Depth 20
