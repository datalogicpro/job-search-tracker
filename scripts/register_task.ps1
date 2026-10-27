# Creates or updates the Windows scheduled task that runs run_daily.ps1.
# Triggers: every day at 6:00 AM, and 2 minutes after you sign in.
# run_daily.ps1 itself makes sure the job runs at most once a day.
# Run again after changing any setting here; -Force replaces the old task.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TaskName = "job-search-tracker daily"
$ProjectDir = Split-Path -Parent $PSScriptRoot
$Script = Join-Path $PSScriptRoot "run_daily.ps1"
$User = "$env:USERDOMAIN\$env:USERNAME"

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Script`"" `
    -WorkingDirectory $ProjectDir

$DailyTrigger = New-ScheduledTaskTrigger -Daily -At 6am
$LogOnTrigger = New-ScheduledTaskTrigger -AtLogOn -User $User
$LogOnTrigger.Delay = "PT2M"

$Settings = New-ScheduledTaskSettingsSet `
    -WakeToRun `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew

$Principal = New-ScheduledTaskPrincipal -UserId $User -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Description "Fetch new jobs and email the daily digest (job-search-tracker)." `
    -Action $Action `
    -Trigger @($DailyTrigger, $LogOnTrigger) `
    -Settings $Settings `
    -Principal $Principal `
    -Force | Out-Null

Write-Output "Scheduled task '$TaskName' is registered."