import json
import subprocess
import sys

import pytest

from ai_pdf import markdown
from ai_pdf.errors import PdfError
from tests.pdf_helpers import make_pdf

pytestmark = pytest.mark.needs_qpdf


def test_text_pdf_has_no_text_layer_gap(three_page_pdf):
    assert markdown.pdf_needs_ocr(three_page_pdf) is False


def test_blank_pdf_needs_ocr(tmp_path):
    path = tmp_path / "blank.pdf"
    make_pdf(path, [[]])
    assert markdown.pdf_needs_ocr(path) is True


def test_unreadable_pdf_defaults_to_ocr(tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"not a pdf")
    assert markdown.pdf_needs_ocr(path) is True


def test_invalid_ocr_mode_is_rejected(three_page_pdf, tmp_path):
    with pytest.raises(ValueError):
        markdown.convert(three_page_pdf, tmp_path / "x.md", ocr="sometimes")


def test_password_protected_pdf_is_refused_before_docling(three_page_pdf, tmp_path):
    import subprocess as sp
    from ai_pdf.qpdf import qpdf_path

    locked = tmp_path / "locked.pdf"
    sp.run([qpdf_path(), "--encrypt", "owner", "user", "256", "--", str(three_page_pdf), str(locked)], check=True)
    with pytest.raises(PdfError, match="password-protected"):
        markdown.convert(locked, tmp_path / "x.md")


def test_missing_docling_gives_a_clear_message(three_page_pdf, tmp_path, monkeypatch):
    for name in list(sys.modules):
        if name == "docling" or name.startswith("docling."):
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.setitem(sys.modules, "docling", None)
    with pytest.raises(PdfError, match=r"ai-pdf\[docling\]"):
        markdown.convert(three_page_pdf, tmp_path / "x.md")


def test_page_selection_is_checked_before_conversion(three_page_pdf, tmp_path):
    with pytest.raises(PdfError, match="invalid page selection"):
        markdown.convert(three_page_pdf, tmp_path / "x.md", pages="1-x")


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("docling") is None, reason="needs the docling extra"
)
def test_text_pdf_converts_to_markdown_and_page_selection_limits_output(three_page_pdf, tmp_path):
    out = tmp_path / "all.md"
    markdown.convert(three_page_pdf, out, ocr="off")
    assert "Page one" in out.read_text(encoding="utf-8")

    picked = tmp_path / "page3.md"
    markdown.convert(three_page_pdf, picked, ocr="off", pages="3")
    text = picked.read_text(encoding="utf-8")
    assert "Page three" in text
    assert "Page one" not in text
    assert "<!-- image -->" not in text
    assert not (tmp_path / "all-media").exists()
