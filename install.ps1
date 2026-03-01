[CmdletBinding()]
param(
    [switch]$AddPath
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

function Get-PythonCommand {
    if ($env:PYTHON_BIN) {
        return $env:PYTHON_BIN
    }

    $venvPython = Join-Path $scriptDir '.venv\Scripts\python.exe'
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return 'py'
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return 'python'
    }

    throw 'Python not found. Install Python or set PYTHON_BIN before running this script.'
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonCommand,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    if ($PythonCommand -eq 'py') {
        & py -3 @Arguments
    }
    else {
        & $PythonCommand @Arguments
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

Write-Host '[BUILD] Building and installing export-code...'
$pythonCommand = Get-PythonCommand
Write-Host "Using Python: $pythonCommand"

Invoke-Python -PythonCommand $pythonCommand -Arguments @('-m', 'pip', 'install', '--disable-pip-version-check', '-q', 'pyinstaller')

Invoke-Python -PythonCommand $pythonCommand -Arguments @(
    '-m', 'PyInstaller',
    '--clean',
    '--noconfirm',
    '--onefile',
    '--name', 'export-code',
    'main.py',
    '--add-data', 'config.json;.',
    '--add-data', 'locales;locales'
)

$exePath = Join-Path $scriptDir 'dist\export-code.exe'
if (-not (Test-Path $exePath)) {
    throw "Build finished but EXE not found: $exePath"
}

if ($AddPath) {
    Write-Host '[PATH] Adding dist folder to User PATH...'
    $distPath = Join-Path $scriptDir 'dist'
    $currentUserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $pathParts = @()

    if (-not [string]::IsNullOrWhiteSpace($currentUserPath)) {
        $pathParts = $currentUserPath.Split(';') | Where-Object { $_ -and $_.Trim() -ne '' }
    }

    if ($pathParts -notcontains $distPath) {
        $newPath = (($pathParts + $distPath) | Select-Object -Unique) -join ';'
        [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
        Write-Host '[OK] Added dist to User PATH'
    }
    else {
        Write-Host '[INFO] dist already exists in User PATH'
    }
}

Write-Host "[OK] Successfully built to: $exePath"
Write-Host "Run immediately with full path: $exePath --help"

if ($AddPath) {
    Write-Host 'Open a new terminal, then run: export-code --help'
}
else {
    Write-Host 'To update PATH via script, run: .\install.ps1 -AddPath'
}
