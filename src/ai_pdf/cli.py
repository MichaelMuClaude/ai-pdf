import argparse
import json
import sys
from pathlib import Path

from ai_pdf import __version__, operations
from ai_pdf.errors import PdfError


def _emit(data: dict) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _info(args):
    _emit(operations.info(Path(args.file)))


def _check(args):
    _emit(operations.check(Path(args.file)))


def _repair(args):
    _emit(operations.repair(Path(args.file), Path(args.output), args.force))


def _decrypt(args):
    _emit(operations.decrypt(Path(args.file), Path(args.output), args.force))


def _merge(args):
    _emit(operations.merge([Path(f) for f in args.files], Path(args.output), args.force))


def _extract(args):
    _emit(operations.extract(Path(args.file), Path(args.output), args.pages, args.force))


def _rotate(args):
    _emit(operations.rotate(Path(args.file), Path(args.output), args.pages, args.degrees, args.force))


def _split(args):
    _emit(operations.split(Path(args.file), Path(args.out_dir), args.every))


def _to_markdown(args):
    from ai_pdf import markdown

    source = Path(args.file)
    output = Path(args.output) if args.output else source.with_suffix(".md")
    if output.exists() and not args.force:
        raise PdfError(f"{output} already exists (use --force to replace it)")
    note = markdown.convert(
        source,
        output,
        device=args.device,
        keep_repeated_headers=args.keep_repeated_headers,
        ocr=args.ocr,
        pages=args.pages,
    )
    _emit({
        "output": output.name,
        "pages": args.pages or "all",
        "header_filter_note": note or None,
    })


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-pdf",
        description="One tool for PDFs: inspect, check, repair, decrypt, merge, split, extract, rotate, and convert to Markdown",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, help_text, func):
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(func=func)
        return p

    p = add("info", "Pages and encryption status, as JSON", _info)
    p.add_argument("file")

    p = add("check", "Check a PDF for structural problems (ok, warnings, or errors)", _check)
    p.add_argument("file")

    p = add("repair", "Rewrite a damaged PDF so it opens cleanly", _repair)
    p.add_argument("file")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--force", action="store_true")

    p = add("decrypt", "Remove encryption when no password is needed", _decrypt)
    p.add_argument("file")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--force", action="store_true")

    p = add("merge", "Join several PDFs, in the order given", _merge)
    p.add_argument("files", nargs="+")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--force", action="store_true")

    p = add("extract", "Keep only some pages, for example 1-3,7", _extract)
    p.add_argument("file")
    p.add_argument("--pages", required=True, help="Page selection, for example 5-7 or 1,3,9-")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--force", action="store_true")

    p = add("rotate", "Rotate some pages clockwise by 90, 180, or 270 degrees", _rotate)
    p.add_argument("file")
    p.add_argument("--pages", required=True)
    p.add_argument("--degrees", type=int, required=True, choices=[90, 180, 270])
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--force", action="store_true")

    p = add("split", "Write each page (or each group of pages) to its own file", _split)
    p.add_argument("file")
    p.add_argument("out_dir")
    p.add_argument("--every", type=int, default=1, help="Pages per output file (default 1)")

    p = add("to-markdown", "Convert a PDF to Markdown (needs the docling extra)", _to_markdown)
    p.add_argument("file")
    p.add_argument("-o", "--output", help="Output .md path (default: same name, .md)")
    p.add_argument("--pages", help="Only convert these pages, for example 5-7")
    p.add_argument("--ocr", choices=["auto", "on", "off"], default="auto",
                   help="auto runs OCR only on pages with no text layer (default)")
    p.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cpu")
    p.add_argument("--keep-repeated-headers", action="store_true")
    p.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except PdfError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
