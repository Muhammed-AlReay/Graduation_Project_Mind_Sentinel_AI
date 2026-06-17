#!/usr/bin/env python3
"""Test /crisis-detection via FastAPI TestClient (no server required)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv()

TEST_TEXT = "I feel hopeless and I don't want to continue living"
API_KEY = os.getenv("PROJECT12_API_KEY", "test-key-12345678")


def main() -> int:
  from fastapi.testclient import TestClient
  from service.app import app
  from service.loader import state

  state.initialize()
  client = TestClient(app)

  r = client.post(
    "/crisis-detection",
    json={"text": TEST_TEXT},
    headers={"Authorization": f"Bearer {API_KEY}"},
  )

  print(f"HTTP {r.status_code}")
  import json
  print(json.dumps(r.json(), ensure_ascii=True, indent=2))

  if r.status_code != 200:
    return 1
  data = r.json()
  if data.get("category") not in ("SUICIDE_RISK", "SELF_HARM", "CRISIS_DISTRESS", "SAFE"):
    print("FAIL: invalid category")
    return 1
  if data.get("category") == "SAFE":
    print("WARN: expected non-SAFE for crisis test text")
  else:
    print(f"PASS: category={data['category']}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
