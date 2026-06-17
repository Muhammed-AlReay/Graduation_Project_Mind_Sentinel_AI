"""Startup validation and dependency checks for Project_12 service."""
import logging
from dataclasses import dataclass, field

from config import (
  API_KEY,
  AUTH_ENABLED,
  AUTO_INGEST,
  DATA_DIR,
  OPENROUTER_API_KEY,
  VECTORSTORE_DIR,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
  name: str
  ok: bool
  detail: str = ""


@dataclass
class StartupReport:
  checks: list[ValidationResult] = field(default_factory=list)

  @property
  def ready(self) -> bool:
    return all(c.ok for c in self.checks)


def validate_data_directory() -> ValidationResult:
  if not DATA_DIR.exists():
    return ValidationResult("data_directory", False, f"Missing: {DATA_DIR}")
  pdfs = list(DATA_DIR.glob("*.pdf"))
  if not pdfs:
    return ValidationResult("data_directory", False, f"No PDF files in {DATA_DIR}")
  return ValidationResult("data_directory", True, f"{len(pdfs)} PDF(s) found")


def validate_vectorstore_files() -> ValidationResult:
  index_faiss = VECTORSTORE_DIR / "index.faiss"
  index_pkl = VECTORSTORE_DIR / "index.pkl"
  if index_faiss.exists() and index_pkl.exists():
    return ValidationResult("vectorstore_files", True, str(VECTORSTORE_DIR))
  return ValidationResult(
    "vectorstore_files",
    False,
    f"Missing FAISS index in {VECTORSTORE_DIR}",
  )


def ensure_vectorstore() -> ValidationResult:
  files_check = validate_vectorstore_files()
  if files_check.ok:
    return files_check

  if not AUTO_INGEST:
    return ValidationResult(
      "vectorstore_build",
      False,
      "Vectorstore missing. Set PROJECT12_AUTO_INGEST=true or run: python ingest.py",
    )

  logger.info("Vectorstore missing — running auto-ingest")
  try:
    from ingest import ingest_data

    if ingest_data():
      return ValidationResult("vectorstore_build", True, "Auto-ingest completed")
    return ValidationResult("vectorstore_build", False, "Auto-ingest found no PDFs")
  except Exception as exc:
    logger.exception("Auto-ingest failed")
    return ValidationResult("vectorstore_build", False, str(exc))


def validate_openrouter_key() -> ValidationResult:
  if OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_agentrouter_api_key_here":
    return ValidationResult("openrouter_api_key", True, "Configured")
  return ValidationResult(
    "openrouter_api_key",
    False,
    "OPENROUTER_API_KEY not set — /chat and /crisis-detection will fail",
  )


def validate_api_key() -> ValidationResult:
  if not AUTH_ENABLED:
    return ValidationResult("api_key", True, "Auth disabled (PROJECT12_AUTH_ENABLED=false)")
  if API_KEY and len(API_KEY) >= 16:
    return ValidationResult("api_key", True, "Configured")
  return ValidationResult(
    "api_key",
    False,
    "PROJECT12_API_KEY not set or too short (minimum 16 characters)",
  )


def run_startup_validation() -> StartupReport:
  report = StartupReport()
  report.checks.append(validate_data_directory())
  report.checks.append(ensure_vectorstore())
  report.checks.append(validate_openrouter_key())
  report.checks.append(validate_api_key())
  return report
