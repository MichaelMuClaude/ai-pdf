"""PDF operations that do not need a converter: information, checks, and page editing.

Every function takes paths and returns plain data, so the CLI can print it as JSON.
"""

import re
from pathlib import Path

from ai_pdf import qpdf
from ai_pdf.errors import PdfError

ROTATIONS = (90, 180, 270)


def _output(path: Path, source: Path, force: bool) -> Path:
    if path.resolve() == source.resolve():
        raise PdfError("the output must be a different file; the input is never overwritten")
    if path.exists() and not force:
        raise PdfError(f"{path} already exists (use --force to replace it)")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def page_count(source: Path) -> int:
    result = qpdf.run_checked(["--show-npages", str(source)])
    return int(result.stdout.strip())


def info(source: Path) -> dict:
    qpdf.existing(source)
    encrypted = qpdf.run(["--is-encrypted", str(source)]).returncode == 0
    needs_password = encrypted and qpdf.run(["--requires-password", str(source)]).returncode == 0
    return {
        "file": source.name,
        "pages": None if needs_password else page_count(source),
        "encrypted": encrypted,
        "password_required": needs_password,
    }


def check(source: Path) -> dict:
    qpdf.existing(source)
    result = qpdf.run(["--check", str(source)])
    if result.returncode == 0:
        status = "ok"
    elif result.returncode == 3:
        status = "warnings"
    else:
        status = "errors"
    messages = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()]
    return {"file": source.name, "status": status, "messages": messages[-10:]}


def repair(source: Path, output: Path, force: bool = False) -> dict:
    qpdf.existing(source)
    output = _output(output, source, force)
    result = qpdf.run(["--warning-exit-0", str(source), str(output)])
    if result.returncode not in qpdf.OK_CODES:
        raise PdfError(f"could not repair {source.name}: {(result.stderr.strip().splitlines() or [''])[-1]}")
    return {"output": output.name, "pages": page_count(output)}


def decrypt(source: Path, output: Path, force: bool = False) -> dict:
    qpdf.existing(source)
    output = _output(output, source, force)
    result = qpdf.run(["--decrypt", str(source), str(output)])
    if result.returncode not in qpdf.OK_CODES:
        message = (result.stderr.strip().splitlines() or [""])[-1]
        raise PdfError(f"could not decrypt {source.name} (a password may be required): {message}")
    return {"output": output.name, "pages": page_count(output)}


def merge(sources: list[Path], output: Path, force: bool = False) -> dict:
    if len(sources) < 2:
        raise PdfError("merge needs at least two input files")
    for source in sources:
        qpdf.existing(source)
    output = _output(output, sources[0], force)
    if any(output.resolve() == s.resolve() for s in sources):
        raise PdfError("the output must be a different file from every input")
    qpdf.run_checked(["--empty", "--pages", *[str(s) for s in sources], "--", str(output)])
    return {"output": output.name, "pages": page_count(output), "inputs": [s.name for s in sources]}


def extract(source: Path, output: Path, pages: str, force: bool = False) -> dict:
    qpdf.existing(source)
    qpdf.valid_pages(pages)
    output = _output(output, source, force)
    qpdf.run_checked([str(source), "--pages", ".", pages, "--", str(output)])
    return {"output": output.name, "pages": page_count(output), "selection": pages}


def rotate(source: Path, output: Path, pages: str, degrees: int, force: bool = False) -> dict:
    qpdf.existing(source)
    qpdf.valid_pages(pages)
    if degrees not in ROTATIONS:
        raise PdfError(f"degrees must be one of {', '.join(map(str, ROTATIONS))}")
    output = _output(output, source, force)
    qpdf.run_checked([str(source), f"--rotate=+{degrees}:{pages}", str(output)])
    return {"output": output.name, "pages": page_count(output), "rotated": pages, "degrees": degrees}


def split(source: Path, out_dir: Path, every: int = 1) -> dict:
    qpdf.existing(source)
    if every < 1:
        raise PdfError("--every must be 1 or more")
    out_dir.mkdir(parents=True, exist_ok=True)
    if any(out_dir.glob(f"{source.stem}-*.pdf")):
        raise PdfError(f"{out_dir} already contains {source.stem}-*.pdf files; use an empty folder")
    qpdf.run_checked([f"--split-pages={every}", str(source), str(out_dir / f"{source.stem}-%d.pdf")])
    files = sorted(out_dir.glob(f"{source.stem}-*.pdf"), key=lambda p: int(re.search(r"-(\d+)\.pdf$", p.name).group(1)))
    return {"output_folder": out_dir.name, "files": [f.name for f in files], "every": every}
