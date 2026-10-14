"""Run the qpdf command-line tool.

qpdf is found through the AI_PDF_QPDF environment variable, then on PATH.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

from ai_pdf.errors import PdfError

# qpdf exit codes: 0 success, 2 error, 3 success with warnings
OK_CODES = (0, 3)
_PAGES = re.compile(r"^\d+(-\d+)?(,\d+(-\d+)?)*$")


def qpdf_path() -> str:
    configured = os.environ.get("AI_PDF_QPDF")
    if configured:
        return configured
    found = shutil.which("qpdf")
    if found:
        return found
    raise PdfError("qpdf is not installed. On Ubuntu: sudo apt install qpdf (or set AI_PDF_QPDF to its path)")


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([qpdf_path(), *args], capture_output=True, text=True)


def run_checked(args: list[str]) -> subprocess.CompletedProcess:
    result = run(args)
    if result.returncode not in OK_CODES:
        message = (result.stderr.strip().splitlines() or ["qpdf failed"])[-1]
        raise PdfError(message if message.startswith("qpdf") else f"qpdf: {message}")
    return result


def valid_pages(spec: str) -> str:
    """Check a page selection such as '1-3,7,9-12'. Returns it unchanged if valid."""
    if not _PAGES.match(spec):
        raise PdfError(f"invalid page selection {spec!r}; use numbers and ranges, for example 1-3,7")
    return spec


def existing(path: Path) -> Path:
    if not path.is_file():
        raise PdfError(f"no such file: {path}")
    return path
