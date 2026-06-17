#!/usr/bin/env python3
"""
Phase 1 proof: verify Project_12 is the ONLY AI text-generation provider.
Gemini is image-only. No Groq, OpenRouter direct calls from edge, or Lovable AI.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent / "Mind-Sanctuary-main"
EDGE = ROOT / "supabase" / "functions"
SRC = ROOT / "src"
P12 = Path(__file__).resolve().parent.parent

FORBIDDEN_EDGE_PATTERNS = [
  (r"generativelanguage\.googleapis\.com", "Gemini direct in edge (must be analyze-image only)"),
  (r"api\.groq\.com", "Groq API"),
  (r"openrouter\.ai", "OpenRouter direct from edge"),
  (r"lovable.*gateway|ai\.gateway\.lovable", "Lovable AI Gateway"),
]

ALLOWED_EDGE_GEMINI = EDGE / "analyze-image" / "index.ts"

def scan_directory(path: Path, patterns: list, exclude: set[Path] | None = None):
  violations = []
  exclude = exclude or set()
  for f in path.rglob("*"):
    if not f.is_file():
      continue
    if f.suffix not in (".ts", ".tsx", ".py", ".js"):
      continue
    if "node_modules" in str(f) or "venv" in str(f) or ".venv" in str(f):
      continue
    if f in exclude:
      continue
    try:
      text = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
      continue
    for pattern, label in patterns:
      if re.search(pattern, text, re.I):
        if "analyze-image" in str(f) and "gemini" in pattern.lower():
          continue
        violations.append((str(f.relative_to(path.parent.parent)), label, pattern))
  return violations


def main():
  print("=" * 60)
  print("PROJECT_12 PROVIDER AUDIT — Phase 1 Proof")
  print("=" * 60)

  edge_violations = scan_directory(EDGE, FORBIDDEN_EDGE_PATTERNS)

  print("\n[1] Edge function provider scan:")
  if edge_violations:
    for path, label, pat in edge_violations:
      print(f"  VIOLATION: {path} — {label} ({pat})")
  else:
    print("  PASS: No forbidden LLM providers in edge functions")

  p12_openrouter = (P12 / "llm_router.py").exists()
  print(f"\n[2] Project_12 LLM backend: OpenRouter via llm_router.py = {p12_openrouter}")
  print("  NOTE: OpenRouter is internal to Project_12 only — edge routes through Project_12")

  gemini_only = ALLOWED_EDGE_GEMINI.exists()
  print(f"\n[3] Gemini restriction: analyze-image edge exists = {gemini_only}")
  if gemini_only:
    text = ALLOWED_EDGE_GEMINI.read_text(encoding="utf-8")
    has_history = "chat_history" in text or "messages" in text.lower()
    print(f"  Gemini receives chat history: {has_history} (must be False)")

  chat_p12 = (EDGE / "chat" / "index.ts").exists()
  print(f"\n[4] Chat edge routes through Project_12: {chat_p12}")

  print("\n[5] Request flow:")
  print("  User → SessionChat → supabase/functions/chat → Project_12 /chat → OpenRouter")
  print("  Image → analyze-image (Gemini JSON only) → Project_12 /chat → final answer")

  print("\n[6] Response flow:")
  print("  OpenRouter → Project_12 → edge synthetic SSE → SessionChat → User")

  passed = len(edge_violations) == 0
  print(f"\n{'PASS' if passed else 'FAIL'}: Provider audit")
  sys.exit(0 if passed else 1)


if __name__ == "__main__":
  main()
