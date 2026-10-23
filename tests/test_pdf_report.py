import json
import zipfile
from io import BytesIO

import pytest
from pypdf import PdfReader

from src.framing import generate_framings
from src.report import simulation_export_zip, simulation_report_pdf, simulation_summary_json
from src.schemas import NewsEvent, RepresentativeComment, Stance
from src.simulation import run_simulation
from src.storage import load_simulation, save_simulation


def saved_run(tmp_path, echo_enabled=True):
    event = NewsEvent(
        title="Городская среда и общественный транспорт",
        description="Обсуждение развития транспорта и прозрачных правил.",
        country="Russia",
        topic="transportation",
        source_type="public_announcement",
        original_text="Город предлагает обновить маршруты и улучшить доступность.",
    )

    def no_llm_calls(_settings):
        pytest.fail("PDF workflow must not create an LLM client")

    database = tmp_path / "report.sqlite3"
    simulation = run_simulation(
        event=event,
        frames=generate_framings(event, n=2),
        population_size=8,
        seed=73,
        echo_enabled=echo_enabled,
        echo_rounds=2 if echo_enabled else 0,
        db_path=database,
        llm_client_factory=no_llm_calls,
    )
    comment = RepresentativeComment(
        segment_id="neutral:transport",
        segment_label="Жители города",
        stance=Stance.NEUTRAL,
        comment="Нужны понятные правила и открытые данные.",
        source_reaction_ids=[simulation["initial_reactions"][0].agent_id],
    )
    simulation_id = save_simulation(
        db_path=database,
        event=event,
        agents=simulation["agents"],
        frames=simulation["frames"],
        reactions=simulation["initial_reactions"],
        media_actors=simulation["media_actors"],
        bubbles=simulation["bubbles"],
        bubble_assignments=simulation["bubble_assignments"],
        echo_result=simulation["echo_result"],
        seed=73,
        provider="mock",
        run_mode="mock",
        representative_comments=[comment],
    )
    return load_simulation(database, simulation_id)


def pdf_text(reader):
    # Page marks can interrupt a phrase at a page boundary in extracted text.
    # Remove only those marks before checking the complete body across pages.
    return " ".join(
        " ".join(
            page.extract_text()
            .replace("EchoGrid · Synthetic simulation — not a real poll", "")
            .replace(f"Page {number}", "")
            .split()
        )
        for number, page in enumerate(reader.pages, 1)
    )


@pytest.mark.parametrize("echo_enabled", [False, True])
def test_pdf_report_uses_saved_run_data_and_is_in_zip(tmp_path, echo_enabled):
    simulation = saved_run(tmp_path, echo_enabled)
    content = simulation_report_pdf(simulation)
    assert content.startswith(b"%PDF-")
    reader = PdfReader(BytesIO(content), strict=True)
    text = pdf_text(reader)
    summary = json.loads(
        simulation_summary_json(
            simulation["event"],
            simulation["frames"],
            simulation["initial_reactions"],
            echo_result=simulation["echo_result"],
            bubbles=simulation["bubbles"],
        )
    )
    assert simulation["event"].title in text
    assert "Нужны понятные правила и открытые данные." in text
    assert simulation["simulation_id"] in text
    assert "seed: 73" in text
    assert "provider: mock" in text
    assert "run mode: mock" in text
    assert f"trust average: {summary['initial_metrics']['trust_average']}" in text
    assert "not a real poll" in text
    assert "not be used as evidence of actual public opinion" in text
    assert "political targeting" in text
    assert reader.metadata.title == simulation["event"].title
    if echo_enabled:
        assert "Final state metrics" in text
        assert "Echo rounds" in text
        assert "Echo items" in text
    else:
        assert "No echo results were recorded for this run." in text
        assert "Final state metrics" not in text
    with zipfile.ZipFile(BytesIO(simulation_export_zip(simulation))) as archive:
        zipped = PdfReader(BytesIO(archive.read("report.pdf")), strict=True)
        assert pdf_text(zipped) == text
        assert "report.pdf" in archive.read("README.txt").decode()
        assert {"report.html", "summary.json", "agents.csv", "reactions.csv"} <= set(
            archive.namelist()
        )


def test_pdf_paginates_long_fields_without_losing_text_or_page_margins(tmp_path):
    simulation = saved_run(tmp_path, echo_enabled=False)
    paragraph = "Длинный русский текст о городской среде и прозрачных правилах. "
    simulation["event"].description = paragraph * 600 + "КОНЕЦ_ОПИСАНИЯ"
    simulation["representative_comments"][0].comment = (
        "НАЧАЛО_КОММЕНТАРИЯ " + "слово" * 900 + " КОНЕЦ_КОММЕНТАРИЯ"
    )
    reader = PdfReader(BytesIO(simulation_report_pdf(simulation)), strict=True)
    text = pdf_text(reader)
    assert len(reader.pages) >= 5
    assert text.count("Длинный русский текст") == 600
    for marker in ["КОНЕЦ_ОПИСАНИЯ", "НАЧАЛО_КОММЕНТАРИЯ", "КОНЕЦ_КОММЕНТАРИЯ"]:
        assert marker in text
    assert "слово" * 900 in "".join(text.split())
    for number, page in enumerate(reader.pages, 1):
        assert f"Page {number}" in page.extract_text()
        assert "Synthetic simulation" in page.extract_text()
        width, height = float(page.mediabox.width), float(page.mediabox.height)

        def check_position(text, cm, tm, _font, _size, width=width, height=height):
            if text.strip():
                x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
                y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
                assert 42 <= x <= width - 42
                assert 20 <= y <= height - 20

        page.extract_text(visitor_text=check_position)


def test_pdf_embeds_fonts_and_treats_markup_as_inert_text(tmp_path):
    simulation = saved_run(tmp_path, echo_enabled=False)
    hostile = '<img src="https://example.invalid/test"><link href="file:///etc/passwd">Текст & данные</link>'
    simulation["event"].original_text = hostile + " 🧪\x01"
    reader = PdfReader(BytesIO(simulation_report_pdf(simulation)), strict=True)
    text = pdf_text(reader)
    assert hostile in text
    assert "[U+1F9EA]" in text
    assert "[U+0001]" in text
    root = reader.trailer["/Root"]
    assert "/OpenAction" not in root
    assert "/Names" not in root
    embedded_fonts = set()
    for page in reader.pages:
        assert not page.get("/Annots")
        for reference in page["/Resources"]["/Font"].values():
            font = reference.get_object()
            if "NotoSans" in font.get("/BaseFont", ""):
                descriptor = font["/FontDescriptor"]
                assert "/FontFile2" in descriptor
                embedded_fonts.add(font["/BaseFont"])
    assert len(embedded_fonts) >= 2


def test_pdf_does_not_invent_missing_run_metadata(tmp_path):
    simulation = saved_run(tmp_path, echo_enabled=False)
    simulation.pop("metadata")
    text = pdf_text(PdfReader(BytesIO(simulation_report_pdf(simulation))))
    assert "created at: Not recorded" in text
    assert "seed: Not recorded" in text
