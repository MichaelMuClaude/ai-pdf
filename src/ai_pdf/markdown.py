"""Convert a PDF to Markdown with Docling: headings, tables, lists, and pictures.

Before conversion, the PDF is checked with qpdf. Damaged files are repaired, and
encrypted files without a password are decrypted. Page selections are extracted
with qpdf first, so Docling only reads the pages that were asked for.
"""

import os
import tempfile
from pathlib import Path

from ai_pdf import operations
from ai_pdf.errors import PdfError
from ai_pdf.postprocess import promote_title

OCR_MODES = ("auto", "on", "off")

# A page with fewer characters than this in its text layer is treated as a scan.
MIN_TEXT_CHARS_PER_PAGE = 20


def pdf_needs_ocr(path: Path) -> bool:
    """Return True if any page of the PDF has no usable text layer.

    If the file cannot be read, return True: OCR is the safe default.
    """
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return True
    try:
        pdf = pdfium.PdfDocument(str(path))
    except Exception:
        return True
    try:
        for index in range(len(pdf)):
            text = pdf[index].get_textpage().get_text_range().strip()
            if len(text) < MIN_TEXT_CHARS_PER_PAGE:
                return True
        return False
    finally:
        pdf.close()


def _prepare(source: Path, scratch: Path, pages: str | None) -> Path:
    """Return a PDF that Docling can read: decrypted, repaired, and limited to the pages asked for."""
    current = source
    info = operations.info(source)
    if info["password_required"]:
        raise PdfError(f"{source.name} is password-protected; remove the password before converting")
    if info["encrypted"]:
        current = scratch / "decrypted.pdf"
        operations.decrypt(source, current)
    if operations.check(current)["status"] == "errors":
        repaired = scratch / "repaired.pdf"
        operations.repair(current, repaired)
        current = repaired
    if pages:
        selected = scratch / "pages.pdf"
        operations.extract(current, selected, pages)
        current = selected
    return current


def convert(
    input_path: Path,
    output_path: Path,
    device: str = "cpu",
    keep_repeated_headers: bool = False,
    ocr: str = "auto",
    pages: str | None = None,
) -> str:
    """Write the Markdown file. Returns the note about removed headers and footers ('' if none)."""
    if ocr not in OCR_MODES:
        raise ValueError(f"ocr must be one of {OCR_MODES}, not {ocr!r}")
    if pages is not None:
        from ai_pdf import qpdf
        qpdf.valid_pages(pages)

    # Imported here so that qpdf-only operations never load PyTorch.
    try:
        from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling_core.types.doc import ImageRefMode
    except ImportError as exc:
        raise PdfError(
            "Docling is not installed. To convert PDFs to Markdown, run: pip install 'ai-pdf[docling]'"
        ) from exc

    from ai_pdf.furniture import filter_running_furniture, format_note

    accelerator = {
        "cpu": AcceleratorDevice.CPU,
        "cuda": AcceleratorDevice.CUDA,
        "auto": AcceleratorDevice.AUTO,
    }[device]

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ai-pdf-") as scratch_name:
        prepared = _prepare(input_path, Path(scratch_name), pages)

        do_ocr = ocr == "on" or (ocr == "auto" and pdf_needs_ocr(prepared))
        pipeline_options = PdfPipelineOptions(do_ocr=do_ocr, generate_picture_images=True)
        pipeline_options.accelerator_options = AcceleratorOptions(
            device=accelerator, num_threads=os.cpu_count() or 4
        )
        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )
        document = converter.convert(str(prepared)).document

        filtered = []
        if not keep_repeated_headers:
            filtered = filter_running_furniture(document)
        note = format_note(filtered) if filtered else ""

        # Docling writes picture files and links them. Use an absolute folder so the
        # links can be rewritten to paths relative to the Markdown file.
        media_name = f"{output_path.stem}-media"
        media_dir = output_path.parent / media_name
        document.save_as_markdown(
            output_path,
            artifacts_dir=media_dir,
            image_mode=ImageRefMode.REFERENCED,
            image_placeholder="",
        )
        markdown = output_path.read_text(encoding="utf-8")
        markdown = markdown.replace(str(media_dir) + "/", media_name + "/")
        if media_dir.is_dir() and not any(media_dir.iterdir()):
            media_dir.rmdir()
        markdown = promote_title(markdown)

        if note:
            markdown = note + "\n\n" + markdown

        output_path.write_text(markdown, encoding="utf-8")
        return note
