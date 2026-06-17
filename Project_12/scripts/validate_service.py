#!/usr/bin/env python3
"""Quick validation script for Project_12 production service."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
  errors = []

  print("=== Project_12 Service Validation ===\n")

  # 1. Config paths
  from config import API_KEY, AUTH_ENABLED, BASE_DIR, DATA_DIR, MEMORY_DATA_DIR, PROFILE_FILE, VECTORSTORE_DIR

  print(f"BASE_DIR:          {BASE_DIR}")
  print(f"DATA_DIR:          {DATA_DIR} (exists={DATA_DIR.exists()})")
  print(f"VECTORSTORE_DIR:   {VECTORSTORE_DIR} (exists={VECTORSTORE_DIR.exists()})")
  print(f"MEMORY_DATA_DIR:   {MEMORY_DATA_DIR}")
  print(f"PROFILE_FILE:      {PROFILE_FILE}")
  print(f"AUTH_ENABLED:      {AUTH_ENABLED}")
  print(f"API_KEY set:       {bool(API_KEY) and len(API_KEY) >= 16}")

  if AUTH_ENABLED and (not API_KEY or len(API_KEY) < 16):
    errors.append("PROJECT12_API_KEY not set or too short (min 16 chars)")

  if not (VECTORSTORE_DIR / "index.faiss").exists():
    errors.append("FAISS index.faiss missing — run: python ingest.py")

  # 2. Startup validation
  from service.startup import run_startup_validation

  report = run_startup_validation()
  for check in report.checks:
    status = "OK" if check.ok else "FAIL"
    print(f"  [{status}] {check.name}: {check.detail}")
    if not check.ok:
      errors.append(f"{check.name}: {check.detail}")

  # 3. Import service
  try:
    from service.app import app
    routes = [r.path for r in app.routes if hasattr(r, "methods")]
    print(f"\nRegistered routes: {routes}")
  except Exception as exc:
    errors.append(f"Failed to import service.app: {exc}")

  print()
  if errors:
    print(f"VALIDATION FAILED ({len(errors)} issue(s)):")
    for e in errors:
      print(f"  - {e}")
    return 1

  print("VALIDATION PASSED")
  return 0


if __name__ == "__main__":
  sys.exit(main())
