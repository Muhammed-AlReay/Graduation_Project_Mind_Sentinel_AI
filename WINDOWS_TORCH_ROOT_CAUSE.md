# Windows Torch Root Cause Analysis — Project_12

**Date:** 2026-06-08  
**Scope:** Investigate `WinError 1114` preventing full Project_12 FastAPI startup on Windows  
**Mind-Sanctuary:** Not modified

---

## 1. Symptom

Starting Project_12 via:

```powershell
python -m uvicorn service.app:app --host 127.0.0.1 --port 8100
```

Fails during import chain:

```
service.app → chat_service → loader → reranker → sentence_transformers → torch
```

**Error:**

```
OSError: [WinError 1114] A dynamic link library (DLL) initialization routine failed.
Error loading "...torch\lib\c10.dll" or one of its dependencies.
```

---

## 2. Environment Snapshot

| Property | Value |
|----------|-------|
| OS | Windows 10.0.26100 (64-bit) |
| Python (working) | 3.10.11 x64 (`C:\Users\Dell\AppData\Local\Programs\Python\Python310\`) |
| PyTorch installed | `2.12.0+cpu` (system site-packages, not isolated venv) |
| Project_12 venv | `.venv` — **broken** (`pyvenv.cfg` pointed to missing Python 3.10.0; `Scripts\python.exe` invalid) |
| Docker | Not installed on validation host |
| WSL | Not installed |

---

## 3. Diagnostic Results

### 3.1 MSVC runtime — NOT the root cause

| DLL | Load test |
|-----|-----------|
| `vcruntime140.dll` | ✅ OK |
| `vcruntime140_1.dll` | ✅ OK |
| `msvcp140.dll` | ✅ OK |

Microsoft Visual C++ Redistributable is present.

### 3.2 Intel OpenMP — NOT missing (when PATH set correctly)

With `os.add_dll_directory(torch\lib)`:

| DLL | Load test |
|-----|-----------|
| `libiomp5md.dll` | ✅ OK |
| `libiompstubs5md.dll` | ✅ OK |

Initial failure to load `libiomp5md.dll` without `add_dll_directory` is a **PATH/DLL search order** issue, not absence of the file.

### 3.3 Failing DLLs — initialization failure (not "file not found")

Per-DLL `ctypes.WinDLL` tests with `add_dll_directory(torch\lib)`:

| DLL | Result |
|-----|--------|
| `c10.dll` | ❌ **WinError 1114** |
| `shm.dll` | ❌ **WinError 1114** |
| `torch_cpu.dll` | ❌ **WinError 1114** |
| `torch_python.dll` | ❌ **WinError 1114** |
| `torch.dll` | ✅ OK |
| `uv.dll` | ✅ OK |

**Conclusion:** Core PyTorch native libraries (`c10`, `torch_cpu`) fail during **DllMain initialization**, not because a dependency file is missing from disk.

### 3.4 GPU vs CPU

| Check | Result |
|-------|--------|
| Installed wheel | `torch-2.12.0+cpu` (CPU-only) |
| CUDA required? | No |
| GPU driver issue? | **No** — not a GPU dependency problem |

---

## 4. Root Cause Determination

### Primary root cause: **PyTorch native library initialization failure on this Windows host**

`WinError 1114` on `c10.dll` / `torch_cpu.dll` indicates the DLL **loaded but its initialization routine failed**. On PyTorch Windows CPU builds this is most commonly caused by:

1. **CPU instruction-set / wheel mismatch** — PyTorch 2.x CPU wheels are built assuming modern x86-64 features (AVX2+). If the CPU or hypervisor exposes an incompatible subset, `DllMain` can abort with 1114 rather than a clean "missing DLL" error.
2. **PyTorch version skew** — `sentence-transformers==3.0.0` (pinned in `requirements.txt`) was released against PyTorch **2.3.x** era. A manual upgrade to **torch 2.12.0+cpu** on this host introduces an untested native binary combination.
3. **Broken / mixed Python environment** — Project_12 `.venv` is non-functional; packages resolve from **system** Python 3.10 site-packages while `PYTHONPATH` hacks point at `.venv\Lib\site-packages`. This is an **environment mismatch**, not a clean reproducible install.

### Contributing factors

| Factor | Severity | Detail |
|--------|----------|--------|
| Broken `.venv` | **High** | Cannot `pip install -r requirements.txt` into isolated env as documented |
| Unpinned `torch` in requirements | **Medium** | `requirements.txt` pins `sentence-transformers==3.0.0` but not `torch`; pip may pull incompatible latest |
| Windows not a supported dev path for this stack | **Medium** | Deployment guide recommends Docker; Windows native is best-effort |
| Antivirus / endpoint security | **Low** (unverified) | Can cause 1114 on DLL init — not observed directly |

### Ruled out

| Hypothesis | Verdict |
|------------|---------|
| Missing MSVC redistributable | ❌ Ruled out — VC++ DLLs load |
| Missing `libiomp5md.dll` on disk | ❌ Ruled out — present in `torch\lib`, loads with correct directory |
| GPU/CUDA dependency | ❌ Ruled out — CPU wheel |
| Missing `fbgemm.dll` / `asmjit.dll` | ❌ Not present in 2.12 layout; not the failing load target |

---

## 5. Exact Failing Dependency Chain

```
uvicorn
  → service.app
    → service.loader
      → retrieval.reranker.Reranker
        → sentence_transformers.CrossEncoder
          → torch (import)
            → _load_dll_libraries()
              → LoadLibrary(c10.dll)  ← FAIL WinError 1114
```

Secondary failure path (same root):

```
langchain_huggingface.HuggingFaceEmbeddings  →  torch  →  c10.dll
```

Both **retrieval** and **reranker** stacks require a working `torch` import.

---

## 6. Recommended Remediation (Windows)

| Priority | Action |
|----------|--------|
| P0 | **Use Docker/Linux for Project_12** — do not block staging on Windows native torch |
| P1 | Delete broken `.venv`; recreate: `py -3.10 -m venv .venv` → `pip install -r requirements.txt` |
| P1 | **Pin torch** in `requirements.txt` to a version tested with `sentence-transformers==3.0.0` (e.g. `torch==2.3.1+cpu` from PyTorch index) |
| P2 | If native Windows required: install [VC++ 2015–2022 x64](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) (already present here, but verify on other machines) |
| P2 | Verify CPU supports AVX2 (`wmic cpu get Name`) — if not, use older torch wheel or Docker |
| P3 | Add `os.add_dll_directory(torch/lib)` bootstrap only as last resort — does not fix 1114 on `c10.dll` on this host |

---

## 7. Impact on Staging Blockers

| Blocker | Status after analysis |
|---------|----------------------|
| Full Project_12 on Windows | **BLOCKED** until clean venv + compatible torch wheel or Docker |
| B.3 edge integration code | **Unblocked** — does not require local torch |
| Staging E2E with real P12 | **Requires Linux/Docker host** |

---

## 8. Verdict

| Question | Answer |
|----------|--------|
| Exact failing dependency | **`c10.dll` → `torch_cpu.dll` native init** (PyTorch CPU core) |
| CPU vs GPU issue? | **CPU wheel** — not GPU |
| Missing runtime? | **No** — MSVC + OpenMP present |
| PyTorch version issue? | **Likely yes** — 2.12.0+cpu on mixed/broken env |
| Environment mismatch? | **Yes** — broken venv + system site-packages |

**Do not attempt further Windows native fixes as a staging gate. Use Docker/Linux deployment path documented in `LINUX_DEPLOYMENT_VALIDATION.md`.**
