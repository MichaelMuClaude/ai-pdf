"""Clean-up applied to Markdown produced by the engines."""

import re

# [text](../Text/page_1.xhtml#id) -> text
# EPUB-internal targets do not exist in the Markdown output, so keep only the text.
# The link text may contain escaped brackets such as \[9\].
_INTERNAL_LINK = re.compile(r"\[((?:\\.|[^\]\\])*)\]\([^)]*\.xhtml[^)]*\)")


def unwrap_internal_links(markdown: str) -> str:
    return _INTERNAL_LINK.sub(r"\1", markdown)


def promote_title(markdown: str) -> str:
    """Make the first level-2 heading the title, if the document has no level-1 heading.

    Docling reports every heading as the same level, so a PDF's title comes out as a
    level-2 heading. This is a heuristic: when the first heading of a document is a
    chapter rather than the title, that chapter becomes level 1.
    """
    if re.search(r"^# ", markdown, re.M):
        return markdown
    match = re.search(r"^## ", markdown, re.M)
    if match is None:
        return markdown
    return markdown[: match.start()] + "# " + markdown[match.start() + 3 :]
