#!/usr/bin/env pwsh
# RAG infrastructure verification (no Python required)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$OutDir = Join-Path $Root "evaluation_results"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$vectorDir = Join-Path $Root "vectorstore"
$dataDir = Join-Path $Root "data"

$report = @{
  timestamp = (Get-Date).ToString('o')
  chunk_size = 1200
  chunk_overlap = 200
  embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
  reranker_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"
  retrieval_top_k = 7
  retrieval_candidate_k = 20
  vectorstore_exists = (Test-Path $vectorDir)
  vectorstore_files = @()
  pdf_count = 0
  rag_status = "unknown"
  grounding_simulation = @()
}

if (Test-Path $vectorDir) {
  $report.vectorstore_files = @(Get-ChildItem $vectorDir -Recurse -File | Select-Object -ExpandProperty Name)
  $report.rag_status = "vectorstore_present"
}

if (Test-Path $dataDir) {
  $report.pdf_count = @(Get-ChildItem $dataDir -Filter "*.pdf" -Recurse -ErrorAction SilentlyContinue).Count
}

# Simulated grounding for test queries (term overlap heuristic - same as explainability.py)
$testQueries = @(
  "What is cognitive behavioral therapy?",
  "What are the symptoms of depression?",
  "How is anxiety treated?",
  "What is panic disorder?",
  "Tell me about PTSD treatment"
)

foreach ($q in $testQueries) {
  $report.grounding_simulation += @{
    query = $q
    note = "Full retrieval requires Python+FAISS. Run: cd Project_12 && python scripts/rag_verify.py"
    vectorstore_ready = $report.vectorstore_exists
  }
}

if (-not $report.vectorstore_exists) {
  $report.rag_status = "BLOCKED - vectorstore missing. Run: python ingest.py"
  $report.action_required = "Install Python, set OPENROUTER_API_KEY, run ingest.py then run_eval.py"
}

$out = Join-Path $OutDir "rag_verification_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$report | ConvertTo-Json -Depth 6 | Set-Content $out -Encoding UTF8
Write-Host "RAG Status: $($report.rag_status)" -ForegroundColor $(if ($report.vectorstore_exists) {'Green'} else {'Red'})
Write-Host "Vectorstore: $($report.vectorstore_exists) | PDFs: $($report.pdf_count) | Files: $($report.vectorstore_files.Count)"
Write-Host "Saved: $out"
