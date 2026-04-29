from streamlit.testing.v1 import AppTest


def test_streamlit_demo_mode_renders_dashboard_without_widget_collisions() -> None:
    app = AppTest.from_file("app.py")

    app.run(timeout=15)
    app.button[0].click().run(timeout=20)

    assert len(app.exception) == 0
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
