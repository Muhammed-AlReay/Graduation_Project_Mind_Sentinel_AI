#!/usr/bin/env python3
"""Diagnose crisis-detection / SafetyGuard failures."""
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv()

TEST_TEXT = "I feel hopeless and I don't want to continue living"


def main() -> int:
    print("=== Crisis Detection Diagnostic ===\n")
    print(f"OPENROUTER_API_KEY set: {bool(os.getenv('OPENROUTER_API_KEY'))}")
    print(f"MODEL: {os.getenv('PROJECT12_LLM_MODEL', 'openrouter/free')}")

    try:
        from llm_router import get_llm
        from safety.safety_guard import SafetyGuard

        llm = get_llm()
        print("LLM initialized OK")

        sg = SafetyGuard(llm)
        print("SafetyGuard initialized OK")

        try:
            raw = sg.chain.invoke({"input": TEST_TEXT})
            print(f"Raw LLM content: {repr(getattr(raw, 'content', None))[:300]}")
        except Exception as llm_err:
            print(f"Raw LLM call failed (expected for crisis text on free tier): {type(llm_err).__name__}")

        category = sg.classify(TEST_TEXT)
        print(f"\nCLASSIFY_OK: {category}")
        return 0
    except Exception as e:
        print(f"\nCLASSIFY_FAIL: {type(e).__name__}: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
