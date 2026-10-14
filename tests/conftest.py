import shutil

import pytest

from tests.pdf_helpers import make_pdf


def pytest_configure(config):
    config.addinivalue_line("markers", "needs_qpdf: requires the qpdf command-line tool")


def pytest_collection_modifyitems(config, items):
    if shutil.which("qpdf") or __import__("os").environ.get("AI_PDF_QPDF"):
        return
    skip = pytest.mark.skip(reason="qpdf is not installed")
    for item in items:
        if "needs_qpdf" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def three_page_pdf(tmp_path):
    path = tmp_path / "three.pdf"
    make_pdf(path, [
        ["Page one has enough text to be read as a real text layer"],
        ["Page two is different text, also long enough for the check"],
        ["Page three closes the sample document with its own words"],
    ])
    return path
