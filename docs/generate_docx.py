"""Сборка пояснительной записки EchoGrid в .docx по ГОСТ 7.32-2017.

Читает ``docs/zapiska.md`` (простой markdown) и собирает
``docs/Пояснительная_записка.docx`` с оформлением по ГОСТ:

- шрифт Times New Roman 14 пт, межстрочный интервал 1.5, выравнивание по ширине;
- поля: левое 30 мм, правое 10 мм, верхнее 20 мм, нижнее 20 мм;
- абзацный отступ первой строки 1.25 см;
- заголовки разделов первого уровня — полужирные, с новой страницы;
- титульный лист отдельной страницей по центру, без номера;
- нумерация страниц снизу по центру, начиная со 2-й.

Парсинг markdown намеренно простой (по строкам), без внешних md-парсеров:
только python-docx + стандартная библиотека.
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt

HERE = Path(__file__).resolve().parent
SRC_MD = HERE / "zapiska.md"
OUT_DOCX = HERE / "Пояснительная_записка.docx"

FONT_NAME = "Times New Roman"
FONT_SIZE = Pt(14)
LINE_SPACING = 1.5
FIRST_LINE_INDENT = Mm(12.5)  # 1.25 см


# --------------------------------------------------------------------------- #
# Низкоуровневые помощники oxml
# --------------------------------------------------------------------------- #
def _set_base_style(doc: Document) -> None:
    """Базовый стиль Normal: Times New Roman 14, интервал 1.5, по ширине."""
    style = doc.styles["Normal"]
    style.font.name = FONT_NAME
    style.font.size = FONT_SIZE
    # Корректное имя шрифта для кириллицы.
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), FONT_NAME)
    pf = style.paragraph_format
    pf.line_spacing = LINE_SPACING
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def _set_margins(section) -> None:
    section.left_margin = Mm(30)
    section.right_margin = Mm(10)
    section.top_margin = Mm(20)
    section.bottom_margin = Mm(20)


def _page_number_field(paragraph) -> None:
    """Вставить поле PAGE по центру нижнего колонтитула."""
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    run.font.name = FONT_NAME
    run.font.size = FONT_SIZE


def _style_run(run) -> None:
    run.font.name = FONT_NAME
    run.font.size = FONT_SIZE
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), FONT_NAME)


# --------------------------------------------------------------------------- #
# Параграфы
# --------------------------------------------------------------------------- #
def _add_paragraph(doc, text, *, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                   indent=True, center=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else align
    pf = p.paragraph_format
    pf.line_spacing = LINE_SPACING
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.first_line_indent = FIRST_LINE_INDENT if indent and not center else Mm(0)
    run = p.add_run(text)
    run.bold = bold
    _style_run(run)
    return p


def _add_heading(doc, text, level, *, page_break=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = LINE_SPACING
    pf.space_before = Pt(6 if not page_break else 0)
    pf.space_after = Pt(12)
    pf.first_line_indent = Mm(0)
    if page_break:
        p.paragraph_format.page_break_before = True
    # Разделы первого уровня без номера (РЕФЕРАТ/ВВЕДЕНИЕ/...) центрируем,
    # нумерованные — по левому краю; здесь определяем по началу строки.
    numbered = bool(re.match(r"^\d+\s", text))
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT if numbered else WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = True
    _style_run(run)
    return p


# --------------------------------------------------------------------------- #
# Титульный лист
# --------------------------------------------------------------------------- #
def _build_title_page(doc, lines):
    # lines — содержимое между @TITLE@ и @ENDTITLE@.
    for _ in range(3):
        _add_paragraph(doc, "", center=True, indent=False)
    big = {0, 1, 2}  # верхний блок — организация
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            _add_paragraph(doc, "", center=True, indent=False)
            continue
        is_theme = "EchoGrid" in line or "ОТЧЁТ" in line
        p = _add_paragraph(doc, line, center=True, indent=False,
                           bold=is_theme)
        if is_theme:
            for r in p.runs:
                r.font.size = Pt(16)
    # Низ страницы — город/год уже в lines последней строкой.


# --------------------------------------------------------------------------- #
# Основной разбор
# --------------------------------------------------------------------------- #
def build():
    raw = SRC_MD.read_text(encoding="utf-8")
    lines = raw.splitlines()

    doc = Document()
    _set_base_style(doc)
    _set_margins(doc.sections[0])

    # 1) Титульный лист (между @TITLE@ / @ENDTITLE@).
    title_lines = []
    body_start = 0
    if lines and lines[0].strip() == "@TITLE@":
        i = 1
        while i < len(lines) and lines[i].strip() != "@ENDTITLE@":
            title_lines.append(lines[i])
            i += 1
        body_start = i + 1
    _build_title_page(doc, title_lines)

    # 2) Новый раздел -> начинаем нумерацию страниц со 2-й, без номера на титуле.
    new_section = doc.add_section(WD_SECTION.NEW_PAGE)
    _set_margins(new_section)
    new_section.footer.is_linked_to_previous = False
    doc.sections[0].different_first_page_header_footer = False
    # На титульной секции футер пустой (номера нет).
    _page_number_field(new_section.footer.paragraphs[0])
    # Стартовый номер страницы основной части = 2.
    sectPr = new_section._sectPr
    pgNumType = OxmlElement("w:pgNumType")
    pgNumType.set(qn("w:start"), "2")
    sectPr.append(pgNumType)

    # 3) Тело: разбор markdown по строкам.
    list_re = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
    first_body_heading = True

    i = body_start
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("### "):
            _add_heading(doc, stripped[4:].strip(), 3)
        elif stripped.startswith("## "):
            _add_heading(doc, stripped[3:].strip(), 2)
        elif stripped.startswith("# "):
            text = stripped[2:].strip()
            # Раздел первого уровня — с новой страницы (кроме самого первого,
            # т.к. основная часть и так начинается с новой секции).
            page_break = not first_body_heading
            _add_heading(doc, text, 1, page_break=page_break)
            first_body_heading = False
        else:
            m = list_re.match(line)
            if m:
                marker = m.group(2)
                content = m.group(3).strip()
                bullet = "— " if marker in ("-", "*") else f"{marker} "
                p = _add_paragraph(doc, bullet + content, indent=True)
            else:
                _add_paragraph(doc, stripped, indent=True)
        i += 1

    doc.save(OUT_DOCX)
    return OUT_DOCX


if __name__ == "__main__":
    out = build()
    size = out.stat().st_size
    print(f"OK: {out} ({size} bytes)")
