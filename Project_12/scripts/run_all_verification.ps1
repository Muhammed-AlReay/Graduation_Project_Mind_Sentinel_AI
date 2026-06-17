#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Master verification script — run after installing Python 3.12 + Node.js LTS
#>
$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$P12 = Join-Path $Root "Project_12"
$Front = Join-Path (Split-Path -Parent $Root) "Mind-Sanctuary-main"

Write-Host "`n========== MIND SANCTUARY PRODUCTION VERIFICATION ==========" -ForegroundColor Cyan

# 1. Crisis evaluation (works without Python)
Write-Host "`n[1/6] Crisis Classifier (250 tests)..." -ForegroundColor Yellow
& "$P12\scripts\run_crisis_evaluation.ps1"

# 2. RAG infra check
Write-Host "`n[2/6] RAG Infrastructure..." -ForegroundColor Yellow
& "$P12\scripts\run_rag_verification.ps1"

# 3. Python RAG verify (if python available)
Write-Host "`n[3/6] RAG Retrieval + Grounding (requires Python)..." -ForegroundColor Yellow
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
  Push-Location $P12
  python scripts/rag_verify.py
  Pop-Location
} else {
  Write-Host "  SKIP: Python not found" -ForegroundColor Red
}

# 4. RAGAS eval (if python + API key)
Write-Host "`n[4/6] RAGAS Evaluation (requires Python + OPENROUTER_API_KEY)..." -ForegroundColor Yellow
if ($py -and $env:OPENROUTER_API_KEY) {
  Push-Location $P12
  python run_eval.py
  Pop-Location
} else {
  Write-Host "  SKIP: Python or OPENROUTER_API_KEY missing" -ForegroundColor Red
}

# 5. Frontend tests
Write-Host "`n[5/6] Frontend Tests (requires npm)..." -ForegroundColor Yellow
$npm = Get-Command npm -ErrorAction SilentlyContinue
if ($npm -and (Test-Path (Join-Path $Front "package.json"))) {
  Push-Location $Front
  npm run test
  npm run typecheck
  npm run build
  Pop-Location
} else {
  Write-Host "  SKIP: npm not found or frontend path missing" -ForegroundColor Red
}

# 6. Provider audit
Write-Host "`n[6/6] Provider Audit..." -ForegroundColor Yellow
if ($py) {
  Push-Location $P12
  python scripts/provider_audit.py
  Pop-Location
} else {
  Write-Host "  SKIP: Python not found" -ForegroundColor Red
}

Write-Host "`n========== VERIFICATION COMPLETE ==========" -ForegroundColor Green
Write-Host "Reports in: $P12\evaluation_results\" -ForegroundColor Cyan
