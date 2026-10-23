"""Offline PDF rendering for the shared recorded/computed report content."""

from __future__ import annotations

from html import escape
from io import BytesIO
from pathlib import Path
from threading import Lock
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from src.config import ETHICAL_USE_DISCLAIMER, SYNTHETIC_SIMULATION_DISCLAIMER

_FONT_DIR = Path(__file__).parent / "assets" / "fonts"
_FONT_LOCK = Lock()
_REGULAR, _BOLD = "EchoGridNotoSans", "EchoGridNotoSansBold"


def _register_fonts() -> frozenset[int]:
    # Streamlit can render reports in concurrent sessions. Register each shared font once.
    with _FONT_LOCK:
        if _REGULAR not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(_REGULAR, str(_FONT_DIR / "NotoSans-Regular.ttf")))
            pdfmetrics.registerFont(TTFont(_BOLD, str(_FONT_DIR / "NotoSans-Bold.ttf")))
            pdfmetrics.registerFontFamily(
                _REGULAR, normal=_REGULAR, bold=_BOLD, italic=_REGULAR, boldItalic=_BOLD
            )
        return frozenset(pdfmetrics.getFont(_REGULAR).face.charToGlyph)


def render_pdf_report(title: str, sections: list[tuple[str, Any]]) -> bytes:
    """Produce a portable PDF; long paragraphs split naturally across A4 pages.

    Values are plain text, never ReportLab markup, images, links or file paths.
    Unsupported font glyphs are shown as explicit code points instead of silently
    disappearing. No browser, system fonts, network renderer or LLM is involved.
    """
    coverage = _register_fonts()
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=48,
        rightMargin=48,
        topMargin=54,
        bottomMargin=48,
        pageCompression=1,
        title=_plain_text(title, coverage),
        author="EchoGrid",
        subject="Synthetic simulation report; not evidence of actual public opinion",
    )
    body_style = ParagraphStyle(
        "ReportBody",
        fontName=_REGULAR,
        fontSize=9,
        leading=13,
        spaceAfter=5,
        splitLongWords=True,
        allowWidows=1,
        allowOrphans=1,
    )
    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=body_style,
        fontName=_BOLD,
        fontSize=13,
        leading=17,
        spaceBefore=14,
        spaceAfter=7,
        keepWithNext=True,
    )
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=body_style,
        fontName=_BOLD,
        fontSize=18,
        leading=24,
        spaceAfter=12,
    )
    note_style = ParagraphStyle(
        "ReportNote",
        parent=body_style,
        fontSize=7,
        leading=10,
        textColor=colors.HexColor("#536477"),
        spaceAfter=8,
    )
    story: list[Any] = []

    def paragraph(value: Any, style: ParagraphStyle = body_style, prefix: str = "") -> None:
        content = escape(_plain_text(value, coverage)).replace("\n", "<br/>")
        story.append(Paragraph(prefix + content, style))

    def value_rows(value: Any, depth: int = 0) -> None:
        style = ParagraphStyle(
            f"FieldDepth{depth}",
            parent=body_style,
            leftIndent=min(depth, 6) * 10,
        )
        if isinstance(value, dict):
            if not value:
                paragraph("No values recorded.", style)
            for key, item in value.items():
                label = escape(_plain_text(str(key).replace("_", " "), coverage))
                if isinstance(item, (dict, list)) and item:
                    story.append(Paragraph(f"<b>{label}</b>", style))
                    value_rows(item, depth + 1)
                else:
                    paragraph(
                        item if not isinstance(item, (dict, list)) else "No entries recorded.",
                        style,
                        prefix=f"<b>{label}:</b> ",
                    )
        elif isinstance(value, list):
            if not value:
                paragraph("No entries recorded.", style)
            for index, item in enumerate(value, 1):
                if isinstance(item, dict):
                    paragraph(f"Entry {index}", style)
                    value_rows(item, depth + 1)
                    story.append(Spacer(1, 5))
                else:
                    paragraph(item, style, prefix="• ")
        else:
            paragraph(value, style)

    paragraph("EchoGrid · Synthetic simulation report", heading_style)
    paragraph(title, title_style)
    paragraph("Synthetic simulation — not a real poll", heading_style)
    paragraph(SYNTHETIC_SIMULATION_DISCLAIMER)
    paragraph(ETHICAL_USE_DISCLAIMER)
    paragraph(
        "Report content uses recorded run data and EchoGrid's existing analytics. "
        "Missing metadata is shown as Not recorded. Raw agent/reaction rows remain in the CSV exports. "
        "Characters outside the bundled font coverage are written as [U+XXXX] code points.",
        note_style,
    )
    for heading, content in sections:
        paragraph(heading, heading_style)
        value_rows(content)

    def page_marks(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#365f91"))
        canvas.setFont(_REGULAR, 8)
        canvas.drawString(48, A4[1] - 28, "EchoGrid · Synthetic simulation — not a real poll")
        canvas.drawRightString(A4[0] - 48, 25, f"Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=page_marks, onLaterPages=page_marks)
    return buffer.getvalue()


def _plain_text(value: Any, coverage: frozenset[int]) -> str:
    text = "Not recorded" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
    return "".join(
        char if char == "\n" or ord(char) in coverage else f"[U+{ord(char):04X}]" for char in text
    )
