"""Write small, valid PDFs with text on each page, for tests."""

from pathlib import Path


def make_pdf(path: Path, pages: list[list[str]]) -> None:
    """One page per entry in ``pages``; each entry is a list of ASCII text lines for that page."""
    count = len(pages)
    font_obj = 3 + 2 * count
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{' '.join(f'{3 + 2 * i} 0 R' for i in range(count))}] /Count {count} >>",
    ]
    for i, lines in enumerate(pages):
        body = " ".join(f"BT /F1 12 Tf 72 {700 - 20 * j} Td ({line}) Tj ET" for j, line in enumerate(lines))
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {4 + 2 * i} 0 R "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> >>"
        )
        objects.append(f"<< /Length {len(body)} >>\nstream\n{body}\nendstream")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = "%PDF-1.4\n"
    offsets = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(out.encode("latin-1")))
        out += f"{number} 0 obj\n{obj}\nendobj\n"
    xref = len(out.encode("latin-1"))
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n"
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    path.write_bytes(out.encode("latin-1"))
