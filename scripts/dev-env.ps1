# Cereqon Android — local dev environment bootstrap (Windows)
# Usage: . .\scripts\dev-env.ps1

$ErrorActionPreference = "Stop"

$JdkHome = "C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot"
$AndroidSdk = "$env:LOCALAPPDATA\Android\Sdk"

if (Test-Path $JdkHome) {
    $env:JAVA_HOME = $JdkHome
    $env:Path = "$JdkHome\bin;$env:Path"
} else {
    Write-Warning "JDK 17 not found at $JdkHome — set JAVA_HOME manually."
}

$PlatformTools = Join-Path $AndroidSdk "platform-tools"
if (Test-Path $PlatformTools) {
    $env:Path = "$PlatformTools;$env:Path"
    $env:ANDROID_HOME = $AndroidSdk
    $env:ANDROID_SDK_ROOT = $AndroidSdk
} else {
    Write-Warning "Android SDK not found at $AndroidSdk — install via Android Studio."
}

Write-Host "JAVA_HOME=$env:JAVA_HOME"
Write-Host "ANDROID_SDK_ROOT=$env:ANDROID_SDK_ROOT"
if (Get-Command java -ErrorAction SilentlyContinue) { java -version 2>&1 | Select-Object -First 1 }
if (Get-Command adb -ErrorAction SilentlyContinue) { adb version 2>&1 | Select-Object -First 1 }
