from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_demo_mode_renders_dashboard_without_widget_collisions(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("ECHOGRID_DATABASE_PATH", str(tmp_path / "ui.sqlite3"))
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py")

    app.run(timeout=15)
    app.button[0].click().run(timeout=20)

    assert len(app.exception) == 0
    html_exports = [
        button
        for button in app.get("download_button")
        if button.proto.label == "Export HTML report"
    ]
    assert len(html_exports) == 1
    assert html_exports[0].proto.url
    pdf_exports = [
        button for button in app.get("download_button") if button.proto.label == "Export PDF report"
    ]
    assert len(pdf_exports) == 1
    assert pdf_exports[0].proto.url
    assert [tab.label for tab in app.tabs] == [
        "Overview",
        "Narrative",
        "Population",
        "Media",
        "Bubbles",
        "Initial Reaction",
        "Echo Timeline",
        "Echo Items",
        "Amplification",
        "Bubble Impact",
        "Frame Comparison",
        "Segment Explorer",
        "Comments",
        "Export",
    ]
