# Daily job: fetch new jobs, then email the digest.
# Runs at most once a day: if a run already finished today, it skips.
# Starts Docker Desktop if it isn't running, and quits it again at the end
# only if this script started it. Writes one log file per day to logs\.
# Written for Windows PowerShell 5.1, which Task Scheduler uses.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$ProjectDir = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$LogDir = Join-Path $ProjectDir "logs"
$LogFile = Join-Path $LogDir ("daily-{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))
$MarkerFile = Join-Path $LogDir "last-success.txt"
$Today = Get-Date -Format "yyyy-MM-dd"
$LogKeepDays = 30
$DockerWaitSeconds = 300
$DatabaseWaitSeconds = 120

$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $ProjectDir

function Write-Log([string]$Message) {
    "$(Get-Date -Format o) $Message" | Out-File -FilePath $LogFile -Append -Encoding utf8
}

function Invoke-Step([string]$Name, [scriptblock]$Command) {
    Write-Log "step started: $Name"
    & $Command 2>&1 | ForEach-Object { "$_" } | Out-File -FilePath $LogFile -Append -Encoding utf8
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Log "step failed: $Name (exit code $code)"
        return $false
    }
    Write-Log "step finished: $Name"
    return $true
}

function Test-DockerReady {
    docker info *> $null
    return $LASTEXITCODE -eq 0
}

if ((Test-Path $MarkerFile) -and ((Get-Content $MarkerFile -Raw).Trim() -eq $Today)) {
    Write-Log "already ran today, skipping"
    exit 0
}

$Failed = $false
$StartedDocker = $false
Write-Log "daily run started"

try {
    if (-not (Test-DockerReady)) {
        Write-Log "Docker is not running, starting Docker Desktop"
        docker desktop start --detach *> $null
        $StartedDocker = $true

        $deadline = (Get-Date).AddSeconds($DockerWaitSeconds)
        while (-not (Test-DockerReady)) {
            if ((Get-Date) -gt $deadline) {
                throw "Docker was not ready after $DockerWaitSeconds seconds"
            }
            Start-Sleep -Seconds 5
        }
        Write-Log "Docker is ready"
    }

    $dbReady = Invoke-Step "start database" {
        docker compose up -d --wait --wait-timeout $DatabaseWaitSeconds
    }
    if (-not $dbReady) {
        throw "the database did not start"
    }

    if (-not (Invoke-Step "fetch_jobs" { & $Python manage.py fetch_jobs })) {
        $Failed = $true
    }
    if (-not (Invoke-Step "send_digest" { & $Python manage.py send_digest })) {
        $Failed = $true
    }
}
catch {
    $Failed = $true
    Write-Log "daily run stopped: $_"
}
finally {
    if ($StartedDocker) {
        Write-Log "quitting Docker Desktop, because this script started it"
        docker desktop stop *> $null
    }

    Get-ChildItem -Path $LogDir -Filter "daily-*.log" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$LogKeepDays) } |
        Remove-Item -Force

    if ($Failed) {
        Write-Log "daily run finished with errors"
    }
    else {
        Set-Content -Path $MarkerFile -Value $Today -Encoding ascii
        Write-Log "daily run finished"
    }
}

if ($Failed) {
    exit 1
}
exit 0