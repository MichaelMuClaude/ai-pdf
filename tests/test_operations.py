import json
import subprocess
import sys

import pytest

from ai_pdf import operations
from ai_pdf.errors import PdfError
from ai_pdf.qpdf import valid_pages
from tests.pdf_helpers import make_pdf

pytestmark = pytest.mark.needs_qpdf


def texts(path):
    from pypdf import PdfReader  # noqa: F401  (installed in the dev environment for checks)
    return [p.extract_text() for p in PdfReader(str(path)).pages]


def test_info_reports_pages_and_encryption(three_page_pdf):
    data = operations.info(three_page_pdf)
    assert data == {"file": "three.pdf", "pages": 3, "encrypted": False, "password_required": False}


def test_check_reports_a_clean_file_as_ok(three_page_pdf):
    assert operations.check(three_page_pdf)["status"] in ("ok", "warnings")


def test_extract_keeps_the_selected_pages(three_page_pdf, tmp_path):
    out = tmp_path / "two.pdf"
    data = operations.extract(three_page_pdf, out, "2-3")
    assert data["pages"] == 2
    assert operations.page_count(out) == 2


def test_merge_joins_files_in_order(three_page_pdf, tmp_path):
    other = tmp_path / "other.pdf"
    make_pdf(other, [["Another document with its own single page of text"]])
    out = tmp_path / "joined.pdf"
    data = operations.merge([three_page_pdf, other], out)
    assert data["pages"] == 4


def test_merge_needs_two_inputs(three_page_pdf, tmp_path):
    with pytest.raises(PdfError, match="at least two"):
        operations.merge([three_page_pdf], tmp_path / "x.pdf")


def test_rotate_sets_the_rotation_on_the_chosen_page(three_page_pdf, tmp_path):
    from pypdf import PdfReader

    out = tmp_path / "rotated.pdf"
    operations.rotate(three_page_pdf, out, "2", 90)
    pages = PdfReader(str(out)).pages
    assert pages[1].get("/Rotate") == 90
    assert pages[0].get("/Rotate") in (None, 0)


def test_split_writes_one_file_per_page(three_page_pdf, tmp_path):
    folder = tmp_path / "parts"
    data = operations.split(three_page_pdf, folder)
    assert len(data["files"]) == 3
    assert all(operations.page_count(folder / name) == 1 for name in data["files"])


def test_split_refuses_a_folder_that_already_has_parts(three_page_pdf, tmp_path):
    folder = tmp_path / "parts"
    operations.split(three_page_pdf, folder)
    with pytest.raises(PdfError, match="already contains"):
        operations.split(three_page_pdf, folder)


def test_input_is_never_overwritten(three_page_pdf):
    with pytest.raises(PdfError, match="never overwritten"):
        operations.extract(three_page_pdf, three_page_pdf, "1", force=True)


def test_existing_output_needs_force(three_page_pdf, tmp_path):
    out = tmp_path / "out.pdf"
    out.write_bytes(b"x")
    with pytest.raises(PdfError, match="--force"):
        operations.extract(three_page_pdf, out, "1")


@pytest.mark.parametrize("spec", ["1-x", "3..4", "", "1;2"])
def test_bad_page_selections_are_refused(spec):
    with pytest.raises(PdfError, match="invalid page selection"):
        valid_pages(spec)


def test_bad_rotation_is_refused(three_page_pdf, tmp_path):
    with pytest.raises(PdfError, match="degrees"):
        operations.rotate(three_page_pdf, tmp_path / "x.pdf", "1", 45)


def test_missing_file_is_refused(tmp_path):
    with pytest.raises(PdfError, match="no such file"):
        operations.info(tmp_path / "nope.pdf")


def test_damaged_file_is_repaired(three_page_pdf, tmp_path):
    damaged = tmp_path / "damaged.pdf"
    data = three_page_pdf.read_bytes()
    position = data.rfind(b"startxref")
    damaged.write_bytes(data[:position] + b"startxref\n0\n%%EOF\n")
    out = tmp_path / "repaired.pdf"
    result = operations.repair(damaged, out)
    assert result["pages"] == 3


def test_encrypted_without_password_is_decrypted(three_page_pdf, tmp_path):
    import subprocess as sp
    from ai_pdf.qpdf import qpdf_path

    locked = tmp_path / "locked.pdf"
    sp.run([qpdf_path(), "--encrypt", "", "", "256", "--", str(three_page_pdf), str(locked)], check=True)
    assert operations.info(locked)["encrypted"] is True
    assert operations.info(locked)["password_required"] is False
    out = tmp_path / "open.pdf"
    operations.decrypt(locked, out)
    assert operations.info(out)["encrypted"] is False


def test_password_protected_file_is_not_decrypted(three_page_pdf, tmp_path):
    import subprocess as sp
    from ai_pdf.qpdf import qpdf_path

    locked = tmp_path / "secret.pdf"
    sp.run([qpdf_path(), "--encrypt", "owner", "user", "256", "--", str(three_page_pdf), str(locked)], check=True)
    assert operations.info(locked)["password_required"] is True
    with pytest.raises(PdfError, match="password"):
        operations.decrypt(locked, tmp_path / "x.pdf")


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "ai_pdf.cli", *args], capture_output=True, text=True)


def test_cli_prints_json_and_exits_zero(three_page_pdf, tmp_path):
    result = run_cli("extract", str(three_page_pdf), "--pages", "1", "-o", str(tmp_path / "one.pdf"))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["pages"] == 1


def test_cli_errors_go_to_stderr_with_exit_one(tmp_path):
    result = run_cli("info", str(tmp_path / "missing.pdf"))
    assert result.returncode == 1
    assert "error: no such file" in result.stderr
