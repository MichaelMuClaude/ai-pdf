---
name: ai-pdf
description: Work with PDF files: inspect them, check and repair them, decrypt them when no password is needed, merge, split, extract pages, rotate pages, and convert them to Markdown. Use for any PDF task that the agent needs to read or change.
---

# ai-pdf

## Commands

```bash
ai-pdf info FILE                                  # pages and encryption
ai-pdf check FILE                                 # ok | warnings | errors
ai-pdf repair FILE -o OUT                         # rewrite a damaged file
ai-pdf decrypt FILE -o OUT                        # no password only
ai-pdf merge FILE1 FILE2 ... -o OUT
ai-pdf extract FILE --pages 5-7 -o OUT            # page selection: 1-3,7,9-
ai-pdf rotate FILE --pages 2 --degrees 90 -o OUT  # 90, 180, or 270
ai-pdf split FILE OUT_FOLDER                      # one file per page
ai-pdf split FILE OUT_FOLDER --every 5            # five pages per file
ai-pdf to-markdown FILE -o OUT.md                 # add --pages to convert part of it
```

## Reading the output

- Every command prints a JSON object on success.
- On failure it prints `error: ...` on stderr and exits with code 1.
- `info` reports `password_required: true` for files that cannot be opened. Ask the user for the password, or say it cannot be read.
- `check` reporting `warnings` is common and usually harmless. Only `errors` means the file may not open properly. Run `repair` in that case.

## Rules

- The input file is never overwritten. Always give a new output name.
- Use `--force` only when the user has agreed to replace an existing file.
- `split` needs an empty folder, or a folder with no existing parts of that name.
- Reading a PDF into Markdown: start with `to-markdown --pages` for long documents, so only the pages needed are converted.

## Limits

- Password-protected files cannot be opened.
- Markdown heading levels come from the source. Check the outline before relying on it.
- Scanned pages are slow because they are read with OCR.
