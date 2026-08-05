. "$PSScriptRoot/common.ps1"

$email = if ($env:AVELIN_EMAIL) { $env:AVELIN_EMAIL } else { Read-Host "Email" }
$securePassword = Read-Host "Password" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential($email, $securePassword)
$password = $credential.GetNetworkCredential().Password
$managementToken = $null

try {
    $register = Read-Host "Register this account now? [Y/n]"
    if ($register -notin @("n", "N", "no", "No")) {
        $fullName = if ($env:AVELIN_FULL_NAME) { $env:AVELIN_FULL_NAME } else { Read-Host "Full name" }
        $companyName = if ($env:AVELIN_COMPANY_NAME) { $env:AVELIN_COMPANY_NAME } else { Read-Host "Company name" }
        $registered = Invoke-AvelinApi -Method POST -Path "/api/v1/platform/register" -AuthRequired $false -Body @{
            email = $email
            password = $password
            full_name = $fullName
            company_name = $companyName
        }
        Write-Host ($registered.message | Out-String)
    }

    $verificationToken = Read-Host "Paste verification token, or press Enter if already verified"
    if ($verificationToken) {
        $escapedToken = [System.Uri]::EscapeDataString($verificationToken)
        $verified = Invoke-AvelinApi -Method GET -Path "/api/v1/platform/verify-email?token=$escapedToken" -AuthRequired $false
        Write-Host ($verified.message | Out-String)
    }

    $login = Invoke-AvelinApi -Method POST -Path "/api/v1/platform/login" -AuthRequired $false -Body @{
        email = $email
        password = $password
    }
    $managementToken = $login.access_token
    $keyName = if ($env:AVELIN_KEY_NAME) { $env:AVELIN_KEY_NAME } else { "local-development" }
    $created = Invoke-AvelinApi -Method POST -Path "/api/v1/platform/api-keys/create" -BearerToken $managementToken -Body @{
        name = $keyName
    }

    Write-Host ""
    Write-Host "Runtime API Key (shown once; store it securely):"
    Write-Host $created.raw_api_key
    Write-Host "Do not commit this value or use the management token on Runtime endpoints."
}
finally {
    $password = $null
    $managementToken = $null
}
