Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-AvelinBaseUrl {
    if ($env:BASE_URL) { return $env:BASE_URL.TrimEnd("/") }
    return "https://api.avelinlabs.com"
}

function Get-AvelinTimeoutSeconds {
    if (-not $env:AVELIN_TIMEOUT_SECONDS) { return 60 }

    try {
        $value = [int]$env:AVELIN_TIMEOUT_SECONDS
    }
    catch {
        throw "AVELIN_TIMEOUT_SECONDS must be a positive integer."
    }

    if ($value -lt 1) { throw "AVELIN_TIMEOUT_SECONDS must be a positive integer." }
    return $value
}

function Invoke-AvelinApi {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Path,
        [object]$Body = $null,
        [bool]$AuthRequired = $true,
        [string]$BearerToken = ""
    )

    $headers = @{ Accept = "application/json" }
    if ($AuthRequired) {
        $token = if ($BearerToken) { $BearerToken } else { $env:AVELIN_API_KEY }
        if (-not $token) { throw "Set AVELIN_API_KEY before running this example." }
        $headers.Authorization = "Bearer $token"
    }

    $parameters = @{
        Method = $Method
        Uri = "$(Get-AvelinBaseUrl)$Path"
        Headers = $headers
        TimeoutSec = Get-AvelinTimeoutSeconds
    }
    if ($null -ne $Body) {
        $parameters.ContentType = "application/json"
        $parameters.Body = ($Body | ConvertTo-Json -Depth 20)
    }

    try {
        Invoke-RestMethod @parameters
    }
    catch {
        if ($_.ErrorDetails.Message) {
            Write-Error $_.ErrorDetails.Message
        }
        throw
    }
}
