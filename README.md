# ai-pdf

One tool for PDFs that an AI agent can use. Every command prints JSON, refuses to overwrite its input, and fails with a plain message on stderr.

```bash
ai-pdf info report.pdf                              # pages, encryption
ai-pdf check report.pdf                             # ok, warnings, or errors
ai-pdf repair damaged.pdf -o fixed.pdf              # rewrite a damaged file so it opens
ai-pdf decrypt locked.pdf -o open.pdf               # only when no password is needed
ai-pdf merge a.pdf b.pdf -o both.pdf
ai-pdf extract report.pdf --pages 5-7 -o part.pdf
ai-pdf rotate report.pdf --pages 2 --degrees 90 -o turned.pdf
ai-pdf split report.pdf parts/                      # one file per page
ai-pdf to-markdown report.pdf -o report.md          # headings, tables, and pictures
ai-pdf to-markdown report.pdf --pages 5-7 -o part.md
```

## How it works

- **PDF structure** (info, check, repair, decrypt, merge, extract, rotate, split) uses **qpdf**, a mature command-line tool for PDFs. Page selections use qpdf's syntax: `1-3,7,9-`.
- **Markdown** (to-markdown) uses **Docling**. Before conversion, damaged files are repaired and encrypted files without a password are decrypted, both with qpdf. A page selection is extracted first, so only those pages are read.
- Scanned pages are read with OCR. `--ocr auto` (the default) runs OCR only on pages that have no text layer.
- Pictures are saved to `<name>-media/` and linked from the Markdown. Repeated running headers and footers are removed, and a note lists what was removed. `--keep-repeated-headers` turns this off.

## Requirements

- **qpdf** (for the structure commands and for to-markdown's preparation step): `sudo apt install qpdf`. Set `AI_PDF_QPDF` to use a specific binary.
- **Docling** for to-markdown only: `pip install -e ".[docling]"`. It installs PyTorch, so it is large.
- Python 3.10 or newer.

## Output

Each command prints a JSON object, for example:

```json
{"output": "part.pdf", "pages": 3, "selection": "5-7"}
```

Errors go to stderr as `error: ...` with exit code 1.

## Install

```bash
pip install -e .                  # qpdf commands
pip install -e ".[docling]"       # adds to-markdown
```

## Limits

- Password-protected files cannot be opened. `info` reports them, and the other commands refuse them.
- Markdown heading levels come from Docling, which reports every heading at the same level. The first heading becomes level 1 when a document has none, and the rest are level 2.
- Maths is written as LaTeX inside `$...$`.
- `check` reports warnings that many working files contain, so `warnings` does not mean the file is broken. Use `repair` only when `check` reports errors.

## Development

```bash
python3 -m venv ~/.venvs/ai-pdf-dev
~/.venvs/ai-pdf-dev/bin/pip install -e ".[dev]"
~/.venvs/ai-pdf-dev/bin/python -m pytest -q
```

## Licence

MIT. See [LICENSE](LICENSE). qpdf is Apache-2.0 and Docling is MIT; neither is bundled with this project.
