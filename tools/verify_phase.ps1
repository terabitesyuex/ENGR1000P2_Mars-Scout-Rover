[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Phase,

    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"
$script:HadFailure = $false
$script:HadWarning = $false
$script:LogPath = $null

function Write-LogLine {
    param([string]$Message)
    if ($script:LogPath) {
        Add-Content -LiteralPath $script:LogPath -Value $Message -Encoding UTF8
    }
}

function Write-Compact {
    param(
        [string]$Label,
        [ValidateSet("PASS", "FAIL", "WARN", "INFO")]
        [string]$Status,
        [string]$Detail = ""
    )
    if ($Status -eq "FAIL") {
        $script:HadFailure = $true
    }
    if ($Status -eq "WARN") {
        $script:HadWarning = $true
    }
    $line = if ($Detail) {
        "{0,-34} {1} {2}" -f $Label, $Status, $Detail
    } else {
        "{0,-34} {1}" -f $Label, $Status
    }
    Write-Host $line
    Write-LogLine $line
}

function Invoke-CommandCapture {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @()
    )
    Write-LogLine ""
    Write-LogLine ("> {0} {1}" -f $FilePath, ($Arguments -join " "))
    try {
        $output = & $FilePath @Arguments 2>&1
        $exitCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } elseif ($?) { 0 } else { 1 }
    } catch {
        $output = @($_.Exception.Message)
        $exitCode = 127
    }
    foreach ($line in $output) {
        Write-LogLine ([string]$line)
    }
    Write-LogLine ("ExitCode: {0}" -f $exitCode)
    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = @($output | ForEach-Object { [string]$_ })
    }
}

function Show-FailureOutput {
    param(
        [string]$Title,
        [string[]]$Output
    )
    Write-Host ""
    Write-Host $Title
    $tail = @($Output | Select-Object -Last 80)
    foreach ($line in $tail) {
        Write-Host $line
    }
}

function Get-GitPorcelainSummary {
    param([string[]]$Lines)
    $staged = 0
    $tracked = 0
    $untracked = 0
    foreach ($line in $Lines) {
        if ($line.StartsWith("??")) {
            $untracked++
            continue
        }
        if ($line.Length -ge 2) {
            if ($line[0] -ne " ") { $staged++ }
            if ($line[1] -ne " ") { $tracked++ }
        }
    }
    return "tracked={0}, staged={1}, untracked={2}" -f $tracked, $staged, $untracked
}

function Select-Python {
    param([string]$RepoRoot)
    $localPython = Join-Path $RepoRoot "pc\.venv\Scripts\python.exe"
    $candidates = @()
    if (Test-Path -LiteralPath $localPython) {
        $candidates += $localPython
    }
    $candidates += "py"
    $candidates += "python"

    foreach ($candidate in $candidates) {
        $result = Invoke-CommandCapture -FilePath $candidate -Arguments @("--version")
        if ($result.ExitCode -eq 0) {
            return [pscustomobject]@{
                Command = $candidate
                VersionOutput = (($result.Output -join " ").Trim())
            }
        }
    }
    return $null
}

function Invoke-PytestSet {
    param(
        [string]$PythonCommand,
        [string]$Label,
        [string[]]$TestPaths
    )
    $arguments = @("-m", "pytest") + $TestPaths + @("-v")
    $result = Invoke-CommandCapture -FilePath $PythonCommand -Arguments $arguments
    if ($result.ExitCode -eq 0) {
        Write-Compact $Label "PASS"
    } else {
        Write-Compact $Label "FAIL" ("exit {0}" -f $result.ExitCode)
        Show-FailureOutput -Title "$Label output:" -Output $result.Output
    }
}

try {
    $scriptDir = Split-Path -Parent $PSCommandPath
    $repoRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
    $manifestPath = Join-Path $scriptDir "verification\phase_manifest.json"
    $logRoot = Join-Path $repoRoot ".verification"
    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $safePhase = $Phase -replace "[^A-Za-z0-9_.-]", "_"
    $script:LogPath = Join-Path $logRoot ("verify_{0}_{1}.log" -f $safePhase, $timestamp)
    $latestLog = Join-Path $logRoot "latest.log"

    "Phase verification log" | Set-Content -LiteralPath $script:LogPath -Encoding UTF8
    Write-LogLine ("Timestamp: {0}" -f (Get-Date -Format "o"))
    Write-LogLine ("Requested phase: {0}" -f $Phase)
    Write-LogLine ("Repository root: {0}" -f $repoRoot)
    Write-LogLine ("AllowDirty: {0}" -f [bool]$AllowDirty)

    Write-Compact "Repository root" "PASS" $repoRoot

    $expectedFiles = @(
        "README.md",
        "CHANGELOG.md",
        "pc\pyproject.toml",
        "pc\tests",
        "tools\verify_phase.ps1",
        "tools\verification\phase_manifest.json"
    )
    foreach ($relative in $expectedFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $relative))) {
            Write-Compact "Expected files" "FAIL" ("missing {0}" -f $relative)
        }
    }
    if (-not $script:HadFailure) {
        Write-Compact "Expected files" "PASS"
    }

    if (-not (Test-Path -LiteralPath $manifestPath)) {
        Write-Compact "Manifest" "FAIL" "missing"
        throw "Manifest missing"
    }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $supported = @($manifest.supported_phases)
    if ($supported -notcontains $Phase) {
        Write-Compact "Phase supported" "FAIL" ("supported: {0}" -f ($supported -join ", "))
        throw "Unsupported phase: $Phase"
    }
    Write-Compact "Phase supported" "PASS" $Phase
    $phaseConfig = $manifest.phases.PSObject.Properties[$Phase].Value

    Push-Location $repoRoot
    try {
        $gitVersion = Invoke-CommandCapture -FilePath "git" -Arguments @("--version")
        if ($gitVersion.ExitCode -eq 0) {
            Write-Compact "Git available" "PASS" (($gitVersion.Output -join " ").Trim())
        } else {
            Write-Compact "Git available" "FAIL" "git --version failed"
            throw "Git unavailable"
        }

        $branch = Invoke-CommandCapture -FilePath "git" -Arguments @("rev-parse", "--abbrev-ref", "HEAD")
        $commit = Invoke-CommandCapture -FilePath "git" -Arguments @("rev-parse", "HEAD")
        if ($branch.ExitCode -eq 0) {
            Write-Compact ("Branch: {0}" -f (($branch.Output -join "").Trim())) "PASS"
        } else {
            Write-Compact "Branch" "FAIL"
        }
        if ($commit.ExitCode -eq 0) {
            $commitHash = (($commit.Output -join "").Trim())
            Write-Compact ("Commit: {0}" -f $commitHash.Substring(0, [Math]::Min(12, $commitHash.Length))) "PASS"
        } else {
            Write-Compact "Commit" "FAIL"
        }

        $upstream = Invoke-CommandCapture -FilePath "git" -Arguments @("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        if ($upstream.ExitCode -eq 0) {
            $upstreamName = (($upstream.Output -join "").Trim())
            Write-Compact "Upstream configured" "PASS" $upstreamName
            $upstreamCommit = Invoke-CommandCapture -FilePath "git" -Arguments @("rev-parse", "@{u}")
            if ($upstreamCommit.ExitCode -eq 0 -and (($upstreamCommit.Output -join "").Trim()) -eq $commitHash) {
                Write-Compact "Upstream synchronized" "PASS"
            } else {
                Write-Compact "Upstream synchronized" "FAIL"
            }
        } else {
            Write-Compact "Upstream configured" "WARN" "none"
        }

        $statusBefore = Invoke-CommandCapture -FilePath "git" -Arguments @("status", "--porcelain=v1")
        $statusBeforeLines = @($statusBefore.Output)
        if ($statusBeforeLines.Count -eq 0) {
            Write-Compact "Working tree clean" "PASS"
        } else {
            $summary = Get-GitPorcelainSummary -Lines $statusBeforeLines
            if ($AllowDirty) {
                Write-Compact "Working tree clean" "WARN" ("AllowDirty: {0}" -f $summary)
            } else {
                Write-Compact "Working tree clean" "FAIL" $summary
            }
        }

        $latestFiles = Invoke-CommandCapture -FilePath "git" -Arguments @("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")
        if ($latestFiles.ExitCode -eq 0) {
            Write-LogLine ""
            Write-LogLine "Latest commit changed files:"
            foreach ($file in $latestFiles.Output) {
                Write-LogLine ("- {0}" -f $file)
            }
            $suspicious = @($latestFiles.Output | Where-Object {
                $_ -match "^(firmware/|firmware\\)" -or
                $_ -match "(STM32|stm32|motor|encoder)"
            })
            if ($suspicious.Count -gt 0 -and $Phase -match "^phase2\.") {
                Write-Compact "Scope heuristic" "WARN" ("review {0} file(s)" -f $suspicious.Count)
            } else {
                Write-Compact "Scope heuristic" "PASS"
            }
        }

        if ($script:HadFailure) {
            throw "Pre-test checks failed"
        }

        $python = Select-Python -RepoRoot $repoRoot
        if ($null -eq $python) {
            Write-Compact "Python interpreter" "FAIL" "no usable candidate"
            throw "Python unavailable"
        }
        Write-Compact "Python interpreter" "PASS" $python.Command
        Write-Compact "Python version" "PASS" $python.VersionOutput

        $pytestImport = Invoke-CommandCapture -FilePath $python.Command -Arguments @("-c", "import pytest; print(pytest.__version__)")
        if ($pytestImport.ExitCode -eq 0) {
            Write-Compact "pytest import" "PASS" (($pytestImport.Output -join " ").Trim())
        } else {
            Write-Compact "pytest import" "FAIL"
            Show-FailureOutput -Title "pytest import output:" -Output $pytestImport.Output
            throw "pytest import failed"
        }

        if ($phaseConfig.targeted) {
            Invoke-PytestSet -PythonCommand $python.Command -Label ("{0} targeted tests" -f $phaseConfig.display_name) -TestPaths @($phaseConfig.targeted)
        }
        if ($phaseConfig.regression) {
            Invoke-PytestSet -PythonCommand $python.Command -Label ("{0} regression tests" -f $phaseConfig.display_name) -TestPaths @($phaseConfig.regression)
        }
        if ($phaseConfig.full) {
            Invoke-PytestSet -PythonCommand $python.Command -Label "Complete PC test suite" -TestPaths @($phaseConfig.full)
        }

        $statusAfter = Invoke-CommandCapture -FilePath "git" -Arguments @("status", "--porcelain=v1")
        $beforeText = ($statusBefore.Output -join "`n")
        $afterText = ($statusAfter.Output -join "`n")
        if ($beforeText -eq $afterText) {
            Write-Compact "Tracked files unchanged" "PASS"
        } else {
            Write-Compact "Tracked files unchanged" "FAIL"
            Write-LogLine "Before status:"
            foreach ($line in $statusBefore.Output) { Write-LogLine $line }
            Write-LogLine "After status:"
            foreach ($line in $statusAfter.Output) { Write-LogLine $line }
        }
    } finally {
        Pop-Location
    }

    if ($script:HadFailure) {
        Write-Host ""
        Write-Host ("{0} VERIFICATION: FAIL" -f $Phase.ToUpperInvariant())
        Write-LogLine ("{0} VERIFICATION: FAIL" -f $Phase.ToUpperInvariant())
        Copy-Item -LiteralPath $script:LogPath -Destination $latestLog -Force
        exit 1
    }

    Write-Host ""
    Write-Host ("{0} VERIFICATION: PASS" -f $Phase.ToUpperInvariant())
    if ($script:HadWarning) {
        Write-Host "Warnings were reported; review the log for details."
    }
    Write-LogLine ("{0} VERIFICATION: PASS" -f $Phase.ToUpperInvariant())
    Copy-Item -LiteralPath $script:LogPath -Destination $latestLog -Force
    exit 0
} catch {
    Write-LogLine ("ERROR: {0}" -f $_.Exception.Message)
    if (-not $script:HadFailure) {
        Write-Compact "Verification" "FAIL" $_.Exception.Message
    }
    if ($script:LogPath) {
        Copy-Item -LiteralPath $script:LogPath -Destination (Join-Path (Split-Path -Parent $script:LogPath) "latest.log") -Force
    }
    Write-Host ""
    Write-Host ("{0} VERIFICATION: FAIL" -f $Phase.ToUpperInvariant())
    exit 1
}
