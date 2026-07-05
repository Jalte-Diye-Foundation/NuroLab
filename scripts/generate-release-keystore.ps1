# Generates release-keystore.jks from keystore.properties (gitignored).
# Run from android/ root: .\scripts\generate-release-keystore.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$propsFile = Join-Path $root "keystore.properties"
if (-not (Test-Path $propsFile)) {
    Write-Error "Missing keystore.properties. Copy keystore.properties.example and fill in values."
}

$props = @{}
Get-Content $propsFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line -match "^([^=]+)=(.*)$") {
        $props[$Matches[1].Trim()] = $Matches[2].Trim()
    }
}

$required = @("storeFile", "storePassword", "keyAlias", "keyPassword")
foreach ($key in $required) {
    if (-not $props.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($props[$key])) {
        Write-Error "keystore.properties is missing required key: $key"
    }
    if ($props[$key] -match "YOUR_") {
        Write-Error "Replace placeholder values in keystore.properties before generating the keystore."
    }
}

$storePath = Join-Path $root $props["storeFile"]
if (Test-Path $storePath) {
    Write-Host "Keystore already exists: $($props['storeFile'])"
    exit 0
}

$javaHome = $env:JAVA_HOME
if (-not $javaHome) {
    Write-Error "Set JAVA_HOME to JDK 17 before running this script."
}
$keytool = Join-Path $javaHome "bin\keytool.exe"
if (-not (Test-Path $keytool)) {
    Write-Error "keytool not found at $keytool"
}

& $keytool -genkey -v `
    -keystore $storePath `
    -keyalg RSA `
    -keysize 2048 `
    -validity 10000 `
    -alias $props["keyAlias"] `
    -storepass $props["storePassword"] `
    -keypass $props["keyPassword"] `
    -dname "CN=Cereqon, OU=Engineering, O=Jalte Diye Foundation, C=US"

Write-Host "Created keystore: $($props['storeFile'])"
