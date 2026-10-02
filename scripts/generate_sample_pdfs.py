"""
Code Bloom — Generate Sample Knowledge Base PDFs
------------------------------------------------
Renders the curated public-domain Thirukkural sample content
(data/sample/thirukkural_sample_content.py) into an actual PDF file
using PyMuPDF, so the demo knowledge base is ingested through the SAME
pipeline real user-uploaded PDFs go through — no shortcuts.

Mixed Tamil + English text needs care: PyMuPDF's HTML/Story renderer
mis-maps a couple of Tamil pre-base vowel signs (e.g. ி) in the
extracted text layer, and a single embedded Tamil font has no Latin
glyphs (so English words extract as NUL bytes). To get a clean,
correctly-extractable text layer for BOTH scripts we do a small manual
text layout: each line is split into same-script runs (Tamil vs
Latin/other), each run is drawn with the matching font via low-level
`page.insert_text`, word-wrapping and paginating as needed.

Run once during setup (also invoked automatically on first app launch
if no sample PDF is found):

    python scripts/generate_sample_pdfs.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fitz  # PyMuPDF

from data.sample.thirukkural_sample_content import PAGES
from src.config import SAMPLE_DIR
from src.language_detector import TAMIL_RANGE

OUTPUT_PATH = SAMPLE_DIR / "thirukkural_sample.pdf"

PAGE_WIDTH, PAGE_HEIGHT = 595, 842  # A4 in points
MARGIN = 50
BODY_SIZE = 11
HEADER_SIZE = 13
LINE_HEIGHT = 16
HEADER_LINE_HEIGHT = 19

_CANDIDATE_TAMIL_FONTS = [
    "/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSerifTamil-Regular.ttf",
    "/usr/share/fonts/truetype/lohit-tamil/Lohit-Tamil.ttf",
]

_RUN_SPLIT_RE = re.compile(r"[\u0B80-\u0BFF]+|[^\u0B80-\u0BFF]+")


def _find_tamil_font():
    for path in _CANDIDATE_TAMIL_FONTS:
        if Path(path).exists():
            return path
    return None


def _split_runs(line: str):
    """Split a line into (text, is_tamil) runs preserving order."""
    runs = []
    for match in _RUN_SPLIT_RE.finditer(line):
        chunk = match.group(0)
        is_tamil = bool(TAMIL_RANGE.match(chunk[0])) if chunk else False
        runs.append((chunk, is_tamil))
    return runs


class PageWriter:
    """Minimal manual text-layout engine supporting mixed Tamil/Latin
    runs on the same line, with word-wrap and automatic pagination."""

    def __init__(self, doc, tamil_font_path):
        self.doc = doc
        self.tamil_font_path = tamil_font_path
        self.font_en = fitz.Font("helv")
        self.font_ta = fitz.Font(fontfile=tamil_font_path) if tamil_font_path else self.font_en
        self.page = None
        self.x = MARGIN
        self.y = MARGIN
        self._new_page()

    def _new_page(self):
        self.page = self.doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        if self.tamil_font_path:
            self.page.insert_font(fontname="TamilFont", fontfile=self.tamil_font_path)
        self.x = MARGIN
        self.y = MARGIN + BODY_SIZE

    def _ensure_space(self, needed: float):
        if self.y + needed > PAGE_HEIGHT - MARGIN:
            self._new_page()

    def _draw_word(self, word: str, is_tamil: bool, size: float, line_h: float):
        font = self.font_ta if is_tamil else self.font_en
        fontname = "TamilFont" if (is_tamil and self.tamil_font_path) else "helv"
        width = font.text_length(word, fontsize=size)
        max_x = PAGE_WIDTH - MARGIN
        if self.x + width > max_x and self.x > MARGIN:
            self.x = MARGIN
            self.y += line_h
            self._ensure_space(line_h)
        self.page.insert_text((self.x, self.y), word, fontsize=size, fontname=fontname)
        self.x += width

    def write_line(self, line: str, size: float = BODY_SIZE, line_h: float = LINE_HEIGHT):
        self._ensure_space(line_h)
        if not line.strip():
            self.y += line_h
            self.x = MARGIN
            return
        for run_text, is_tamil in _split_runs(line):
            words = re.findall(r"\S+\s*|\s+", run_text)
            for w in words:
                # Draw every token — including whitespace-only ones — as a
                # real glyph via insert_text. This matters for correct
                # text-EXTRACTION later: a cursor-only advance (no glyph
                # drawn) is invisible to PyMuPDF's gap-based space
                # detection and silently drops the space when re-reading
                # the PDF (e.g. "அதிகாரம் 40" -> "அதிகாரம்40").
                self._draw_word(w, is_tamil, size, line_h)
        self.x = MARGIN
        self.y += line_h

    def write_paragraph(self, text: str, size: float = BODY_SIZE, line_h: float = LINE_HEIGHT):
        for line in text.split("\n"):
            self.write_line(line, size=size, line_h=line_h)

    def write_header(self, text: str):
        self.write_line(text, size=HEADER_SIZE, line_h=HEADER_LINE_HEIGHT)
        self.y += 4  # small gap after header


def build_pdf():
    doc = fitz.open()
    tamil_font_path = _find_tamil_font()
    writer = PageWriter(doc, tamil_font_path)

    for page_data in PAGES:
        chapter = page_data.get("chapter", "")
        body = page_data.get("text", "")

        if chapter:
            writer.write_header(chapter)

        for para in body.split("\n\n"):
            writer.write_paragraph(para)
            writer.y += 6  # paragraph spacing

        # Force a fresh PDF page per logical "page" entry so page_number
        # metadata used for citations lines up 1:1 with the source content.
        writer._new_page()

    # Drop the final blank page created by the loop's trailing _new_page()
    if doc.page_count > 1:
        doc.delete_page(doc.page_count - 1)

    doc.save(str(OUTPUT_PATH), garbage=4, deflate=True)
    doc.close()
    status = "with embedded Tamil font" if tamil_font_path else (
        "WITHOUT a Tamil font found on this system (install fonts-noto-core for correct rendering)"
    )
    print(f"Sample PDF written to: {OUTPUT_PATH} ({status})")


if __name__ == "__main__":
    build_pdf()
