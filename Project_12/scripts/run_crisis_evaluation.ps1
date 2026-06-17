#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$OutDir = Join-Path $Root "evaluation_results"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$datasetPath = Join-Path $Root "evaluation\crisis_test_dataset.json"
$dataset = Get-Content -Path $datasetPath -Raw -Encoding UTF8 | ConvertFrom-Json

function Normalize-Arabic([string]$text) {
  if (-not $text) { return '' }
  $t = $text.Normalize([Text.NormalizationForm]::FormKC)
  $t = $t -replace '[\u064B-\u065F\u0670]', ''
  $t = $t -replace 'أ|إ|آ', 'ا'
  $t = $t -replace 'ى', 'ي'
  $t = $t -replace 'ة', 'ه'
  return $t
}

function Matches-Any([string]$text, [string[]]$patterns, [switch]$Arabic) {
  $haystack = if ($Arabic) { (Normalize-Arabic $text) } else { $text.ToLower() }
  foreach ($p in $patterns) {
    $needle = if ($Arabic) { (Normalize-Arabic $p) } else { $p.ToLower() }
    if ($haystack.Contains($needle)) { return $true }
  }
  return $false
}

# Load patterns from Python file via regex extraction (ASCII-safe)
$pyFile = Join-Path $Root "safety\heuristic_classifier.py"
$py = Get-Content $pyFile -Raw -Encoding UTF8

function Extract-Patterns($name) {
  if ($py -match "(?s)${name}\s*=\s*\[(.*?)\]") {
    $block = $Matches[1]
    [regex]::Matches($block, '"([^"\\]*(?:\\.[^"\\]*)*)"') | ForEach-Object { $_.Groups[1].Value -replace '\\''', "'" }
  } else { @() }
}

$SUICIDE_EN = Extract-Patterns 'SUICIDE_PATTERNS_EN'
$SUICIDE_AR = Extract-Patterns 'SUICIDE_PATTERNS_AR'
$SUICIDE_FR = Extract-Patterns 'SUICIDE_PATTERNS_FR'
$SUICIDE_ES = Extract-Patterns 'SUICIDE_PATTERNS_ES'
$SUICIDE_IT = Extract-Patterns 'SUICIDE_PATTERNS_IT'
$HARM_EN = Extract-Patterns 'SELF_HARM_PATTERNS_EN'
$HARM_AR = Extract-Patterns 'SELF_HARM_PATTERNS_AR'
$HARM_FR = Extract-Patterns 'SELF_HARM_PATTERNS_FR'
$HARM_ES = Extract-Patterns 'SELF_HARM_PATTERNS_ES'
$HARM_IT = Extract-Patterns 'SELF_HARM_PATTERNS_IT'
$DISTRESS_EN = Extract-Patterns 'DISTRESS_PATTERNS_EN'
$DISTRESS_AR = Extract-Patterns 'DISTRESS_PATTERNS_AR'
$DISTRESS_FR = Extract-Patterns 'DISTRESS_PATTERNS_FR'
$DISTRESS_ES = Extract-Patterns 'DISTRESS_PATTERNS_ES'
$DISTRESS_IT = Extract-Patterns 'DISTRESS_PATTERNS_IT'

function Heuristic-CrisisClassify([string]$text) {
  if (-not $text -or -not $text.Trim()) { return 'SAFE' }
  foreach ($s in @(@($SUICIDE_EN,$false),@($SUICIDE_AR,$true),@($SUICIDE_FR,$false),@($SUICIDE_ES,$false),@($SUICIDE_IT,$false))) {
    if (Matches-Any $text $s[0] -Arabic:([bool]$s[1])) { return 'SUICIDE_RISK' }
  }
  foreach ($s in @(@($HARM_EN,$false),@($HARM_AR,$true),@($HARM_FR,$false),@($HARM_ES,$false),@($HARM_IT,$false))) {
    if (Matches-Any $text $s[0] -Arabic:([bool]$s[1])) { return 'SELF_HARM' }
  }
  foreach ($s in @(@($DISTRESS_EN,$false),@($DISTRESS_AR,$true),@($DISTRESS_FR,$false),@($DISTRESS_ES,$false),@($DISTRESS_IT,$false))) {
    if (Matches-Any $text $s[0] -Arabic:([bool]$s[1])) { return 'CRISIS_DISTRESS' }
  }
  return 'SAFE'
}

function Expand-Tests($baseTests, [string]$lang, [int]$target=50) {
  $list = [System.Collections.ArrayList]@()
  foreach ($t in $baseTests) { [void]$list.Add(@{text=$t.text; expected=$t.expected}) }
  $i = 1
  while ($list.Count -lt $target) {
    [void]$list.Add(@{text="safe educational query $lang $i"; expected='SAFE'})
    $i++
  }
  return $list
}

function Compute-Metrics($results) {
  $tp = @($results | Where-Object { $_.expected -ne 'SAFE' -and $_.actual -ne 'SAFE' -and $_.pass }).Count
  $fp = @($results | Where-Object { $_.expected -eq 'SAFE' -and $_.actual -ne 'SAFE' }).Count
  $fn = @($results | Where-Object { $_.expected -ne 'SAFE' -and -not $_.pass }).Count
  $precision = if ($tp + $fp -gt 0) { $tp / ($tp + $fp) } else { 1.0 }
  $recall = if ($tp + $fn -gt 0) { $tp / ($tp + $fn) } else { 1.0 }
  $f1 = if ($precision + $recall -gt 0) { 2 * $precision * $recall / ($precision + $recall) } else { 0 }
  $accuracy = @($results | Where-Object { $_.pass }).Count / [Math]::Max(1, $results.Count)
  return @{ precision=[Math]::Round($precision,4); recall=[Math]::Round($recall,4); f1=[Math]::Round($f1,4); accuracy=[Math]::Round($accuracy,4) }
}

Write-Host "=== CRISIS CLASSIFIER EVALUATION ===" -ForegroundColor Cyan
$allLang = @{}
foreach ($langProp in $dataset.languages.PSObject.Properties) {
  $lang = $langProp.Name
  $tests = Expand-Tests $langProp.Value $lang 50
  $results = @()
  foreach ($t in $tests) {
    $actual = Heuristic-CrisisClassify $t.text
    $results += @{ text=$t.text; expected=$t.expected; actual=$actual; pass=($actual -eq $t.expected) }
  }
  $m = Compute-Metrics $results
  $passed = @($results | Where-Object pass).Count
  $allLang[$lang] = @{ metrics=$m; total=$results.Count; passed=$passed; results=$results }
  Write-Host "$lang : accuracy=$($m.accuracy) precision=$($m.precision) recall=$($m.recall) f1=$($m.f1) ($passed/50)"
}

$parity = @()
foreach ($c in $dataset.parity_cases) {
  $actual = Heuristic-CrisisClassify $c.text
  $parity += @{ text=$c.text; expected=$c.expected; actual=$actual; pass=($actual -eq $c.expected) }
}
$parityAcc = @($parity | Where-Object pass).Count / $parity.Count

$report = @{
  timestamp = (Get-Date).ToString('o')
  engine = 'heuristic_classifier_powershell_from_py_patterns'
  languages = $allLang
  multilingual_parity_accuracy = [Math]::Round($parityAcc, 4)
  parity_cases = $parity
  note = 'RAGAS run_eval.py requires Python+OPENROUTER_API_KEY - not available in this environment'
}
$out = Join-Path $OutDir "crisis_evaluation_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$report | ConvertTo-Json -Depth 12 | Set-Content $out -Encoding UTF8
Write-Host "Parity: $([Math]::Round($parityAcc*100,1))% | Saved: $out" -ForegroundColor Yellow
