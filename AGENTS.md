# AGENTS.md — guide for AI agents contributing to ai-pdf

This file is for AI coding agents that read, test, or change this project. The human-facing rules are in [CONTRIBUTING.md](CONTRIBUTING.md).

## What this project is

`ai-pdf` is the single PDF tool for AI agents. Structure commands use the qpdf command-line tool. `to-markdown` uses Docling and is an optional install.

## Promises to keep

1. **The input is never overwritten.** Every command that writes a file must refuse an output that is the input (`_output` in `operations.py`).
2. **Existing outputs need `--force`.** Never replace a file silently.
3. **JSON on success, `error:` on stderr on failure.** Keep the output stable.
4. **Validate before running qpdf.** Page selections go through `qpdf.valid_pages`. Degrees must be 90, 180, or 270.
5. **Encrypted files are not cracked.** Decrypt only files that need no password. Never add password guessing.
6. **Docling is imported only inside `markdown.convert`.** The qpdf commands must work without it.

## Layout

```
src/ai_pdf/
  cli.py          commands and JSON output
  qpdf.py         finds and runs qpdf; page-selection check
  operations.py   info, check, repair, decrypt, merge, extract, rotate, split
  markdown.py     to-markdown: prepares the PDF with qpdf, then runs Docling
  furniture.py    removes repeated running headers and footers (Docling items)
  postprocess.py  makes the first heading the title
  errors.py       PdfError, the user-facing error
tests/
  pdf_helpers.py  writes small valid PDFs with text
  test_operations.py, test_markdown.py, test_furniture.py
```

## Setup and checks

```bash
sudo apt install qpdf
python3 -m venv ~/.venvs/ai-pdf-dev
~/.venvs/ai-pdf-dev/bin/pip install -e ".[dev]"
~/.venvs/ai-pdf-dev/bin/python -m pytest -q
```

Tests build their own PDFs. Do not commit real documents. Tests that need qpdf are skipped when it is missing.

## Rules for changes

- One change per pull request, with tests for each behaviour change.
- Keep the Python floor at 3.10.
- Do not add a runtime dependency. qpdf is used as a program; Docling is optional.

## Security

Do not report vulnerabilities in a public issue. Use a private security advisory on GitHub.
