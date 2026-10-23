"""Export and report helpers for simulation results."""

from __future__ import annotations

import json
import zipfile
from html import escape
from io import BytesIO
from typing import Any

import pandas as pd

from src.analytics import (
    age_group,
    echo_amplification_breakdown,
    emotion_averages,
    final_state_metrics,
    institutional_trust_bucket,
    narrative_risk_summary,
    share_likelihood_distribution,
    stance_distribution,
    trust_average,
)
from src.config import ETHICAL_USE_DISCLAIMER, SYNTHETIC_SIMULATION_DISCLAIMER
from src.schemas import (
    AgentProfile,
    AgentReaction,
    EchoItem,
    EchoReaction,
    EchoSimulationResult,
    LLMGenerationError,
    LLMProvider,
    NewsEvent,
    NewsFrame,
    RepresentativeComment,
    SocialBubble,
)


def agents_to_dataframe(agents: list[AgentProfile]) -> pd.DataFrame:
    rows = []
    for agent in agents:
        row = agent.model_dump(mode="json")
        row["age_group"] = age_group(agent.age)
        row["institutional_trust_bucket"] = institutional_trust_bucket(agent.institutional_trust)
        rows.append(row)
    return pd.DataFrame(rows)


def reactions_to_dataframe(
    reactions: list[AgentReaction],
    bubble_assignments: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    bubble_by_agent = _bubble_by_agent(bubble_assignments or {})
    rows = []
    for reaction in reactions:
        row = reaction.model_dump(mode="json")
        emotions = row.pop("emotions")
        row.update({f"emotion_{key}": value for key, value in emotions.items()})
        row["emotional_intensity"] = reaction.emotional_intensity
        if bubble_assignments is not None:
            row["social_bubble"] = bubble_by_agent.get(reaction.agent_id)
        rows.append(row)
    return pd.DataFrame(rows)


def echo_items_to_dataframe(echo_items: list[EchoItem]) -> pd.DataFrame:
    return pd.DataFrame([item.model_dump(mode="json") for item in echo_items])


def echo_reactions_to_dataframe(echo_reactions: list[EchoReaction]) -> pd.DataFrame:
    rows = []
    for reaction in echo_reactions:
        row = reaction.model_dump(mode="json")
        shifts = row.pop("emotion_shift")
        row.update({f"{key}_shift": value for key, value in shifts.items()})
        rows.append(row)
    return pd.DataFrame(rows)


def simulation_summary_json(
    event: NewsEvent,
    frames: list[NewsFrame],
    reactions: list[AgentReaction],
    echo_result: EchoSimulationResult | None = None,
    run_mode: str = "mock",
    provider: LLMProvider | str | None = None,
    representative_comments: list[RepresentativeComment] | None = None,
    llm_errors: list[LLMGenerationError] | None = None,
    bubbles: list[SocialBubble] | None = None,
) -> str:
    payload = {
        "export_metadata": export_metadata("summary"),
        "run_mode": run_mode,
        "provider": provider.value if isinstance(provider, LLMProvider) else provider,
        "event": event.model_dump(mode="json"),
        "frames": [frame.model_dump(mode="json") for frame in frames],
        "initial_metrics": {
            "stance_distribution": stance_distribution(reactions),
            "emotion_averages": emotion_averages(reactions),
            "trust_average": trust_average(reactions),
            "share_likelihood_distribution": share_likelihood_distribution(reactions),
        },
        "amplification_metrics": (echo_result.amplification_metrics if echo_result else {}),
        "amplification_breakdown": (
            echo_amplification_breakdown(
                reactions, echo_result.echo_reactions, echo_result.echo_items
            )
            if echo_result
            else {}
        ),
        "final_state_metrics": (
            final_state_metrics(
                echo_result.final_reaction_state_by_agent,
                echo_result.echo_reactions,
            )
            if echo_result
            else {}
        ),
        "narrative_risk_summary": (
            narrative_risk_summary(
                echo_result.echo_items, echo_result.echo_reactions, bubbles or []
            )
            if echo_result
            else {}
        ),
        "echo_item_count": len(echo_result.echo_items) if echo_result else 0,
        "echo_reaction_count": len(echo_result.echo_reactions) if echo_result else 0,
        "representative_comments": [
            comment.model_dump(mode="json") for comment in representative_comments or []
        ],
        "llm_errors": [error.model_dump(mode="json") for error in llm_errors or []],
    }
    return json.dumps(payload, indent=2)


def dataframe_to_csv_export(frame: pd.DataFrame, export_name: str) -> str:
    metadata = export_metadata(export_name)
    header = "\n".join(
        [
            f"# EchoGrid export: {metadata['export_name']}",
            f"# {metadata['synthetic_simulation_disclaimer']}",
            f"# {metadata['ethical_use_disclaimer']}",
        ]
    )
    return f"{header}\n{frame.to_csv(index=False)}"


def simulation_report_html(simulation: dict[str, Any]) -> str:
    """Render a self-contained report from a current or rehydrated simulation.

    All run content is escaped as text; no scripts or external resources are used.
    Metrics share the JSON summary's existing analytics rather than a new model.
    """
    echo_result = simulation.get("echo_result")
    summary = json.loads(
        simulation_summary_json(
            event=simulation["event"],
            frames=simulation["frames"],
            reactions=simulation["initial_reactions"],
            echo_result=echo_result,
            run_mode=simulation.get("run_mode", "mock"),
            provider=simulation.get("provider"),
            representative_comments=simulation.get("representative_comments"),
            llm_errors=simulation.get("llm_errors"),
            bubbles=simulation.get("bubbles", []),
        )
    )
    metadata = simulation.get("metadata") or {}
    event = summary["event"]
    identity = {
        "simulation_id": simulation.get("simulation_id", metadata.get("simulation_id")),
        "created_at": metadata.get("created_at"),
        "seed": metadata.get("seed"),
        "run_mode": summary["run_mode"],
        "provider": summary["provider"],
        "synthetic_agents": len(simulation["agents"]),
        "frames": len(summary["frames"]),
        "initial_reactions": len(simulation["initial_reactions"]),
        "echo_items": summary["echo_item_count"],
        "echo_reactions": summary["echo_reaction_count"],
    }
    sections = [
        ("Run details", _html_value(identity)),
        ("Event", _html_value(event)),
        ("Media framings", _html_table(summary["frames"])),
        (
            "Initial reaction metrics",
            "<p>Stance shares are percentages of initial agent/frame reactions, "
            "not population survey estimates. Emotion, trust and sharing scores use "
            "the simulator's 0–100 scale.</p>" + _html_value(summary["initial_metrics"]),
        ),
    ]
    if echo_result is not None:
        sections.extend(
            [
                ("Final state metrics", _html_value(summary["final_state_metrics"])),
                ("Amplification metrics", _html_value(summary["amplification_metrics"])),
                ("Amplification breakdown", _html_value(summary["amplification_breakdown"])),
                ("Narrative risk summary", _html_value(summary["narrative_risk_summary"])),
                (
                    "Echo rounds",
                    _html_table(
                        [row.model_dump(mode="json") for row in echo_result.round_summaries]
                    ),
                ),
                (
                    "Echo items",
                    _html_table([item.model_dump(mode="json") for item in echo_result.echo_items]),
                ),
            ]
        )
    else:
        sections.append(("Echo phase", "<p>No echo results were recorded for this run.</p>"))
    sections.extend(
        [
            ("Representative synthetic comments", _html_table(summary["representative_comments"])),
            ("Generation diagnostics", _html_table(summary["llm_errors"])),
        ]
    )
    body = "\n".join(
        f"<section><h2>{escape(title)}</h2>{content}</section>" for title, content in sections
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>EchoGrid synthetic simulation — {escape(event["title"])}</title>
<style>
body {{ margin: 0 auto; padding: 2rem; max-width: 76rem; color: #172437;
       background: #fff; font: 16px/1.5 system-ui, sans-serif; }}
h1, h2 {{ line-height: 1.2; }} h2 {{ margin-top: 2rem; }}
.notice {{ padding: 1rem; background: #eef3fa; border-left: 4px solid #365f91; }}
dt {{ font-weight: 600; }} dd {{ margin: 0 0 .6rem 1rem; }}
td, dd, p {{ overflow-wrap: anywhere; white-space: pre-wrap; }}
.table-wrap {{ overflow-x: auto; }} table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #cbd3dc; padding: .5rem; text-align: left; vertical-align: top; }}
th {{ background: #f0f3f7; }} ul {{ padding-left: 1.3rem; }} footer {{ margin-top: 2rem; }}
@media print {{ body {{ padding: 0; font-size: 10pt; }}
  .table-wrap {{ overflow: visible; }} tr {{ break-inside: avoid; }}
  h2 {{ break-after: avoid; }} thead {{ display: table-header-group; }} }}
</style>
</head>
<body>
<header><p>EchoGrid · Synthetic simulation report</p><h1>{escape(event["title"])}</h1></header>
<aside class="notice"><strong>Synthetic simulation — not a real poll</strong>
<p>{escape(SYNTHETIC_SIMULATION_DISCLAIMER)}</p>
<p>{escape(ETHICAL_USE_DISCLAIMER)}</p></aside>
{body}
<footer><p>This report uses the recorded run and EchoGrid's existing analytics.
No external data or report-generation LLM calls were used. Missing metadata is
shown as “Not recorded”. Raw agent and reaction rows remain available in the CSV exports.</p></footer>
</body>
</html>
"""


def _html_value(value: Any) -> str:
    if isinstance(value, dict):
        if not value:
            return "<p>No values recorded.</p>"
        return (
            "<dl>"
            + "".join(
                f"<dt>{escape(str(key).replace('_', ' '))}</dt><dd>{_html_value(item)}</dd>"
                for key, item in value.items()
            )
            + "</dl>"
        )
    if isinstance(value, list):
        return "<ul>" + "".join(f"<li>{_html_value(item)}</li>" for item in value) + "</ul>"
    return escape("Not recorded" if value is None else str(value))


def _html_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p>No entries recorded.</p>"
    columns = list(dict.fromkeys(key for row in rows for key in row))
    header = "".join(f'<th scope="col">{escape(key.replace("_", " "))}</th>' for key in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{_html_value(row.get(key))}</td>" for key in columns) + "</tr>"
        for row in rows
    )
    return f'<div class="table-wrap"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>'


def simulation_export_zip(simulation: dict[str, Any]) -> bytes:
    echo_result = simulation.get("echo_result")
    bubble_assignments = simulation.get("bubble_assignments") or simulation.get("assignments") or {}
    files = {
        "README.txt": _archive_readme(),
        "report.html": simulation_report_html(simulation),
        "summary.json": simulation_summary_json(
            event=simulation["event"],
            frames=simulation["frames"],
            reactions=simulation["initial_reactions"],
            echo_result=echo_result,
            run_mode=simulation.get("run_mode", "mock"),
            provider=simulation.get("provider"),
            representative_comments=simulation.get("representative_comments"),
            llm_errors=simulation.get("llm_errors"),
            bubbles=simulation["bubbles"],
        ),
        "agents.csv": dataframe_to_csv_export(agents_to_dataframe(simulation["agents"]), "agents"),
        "reactions.csv": dataframe_to_csv_export(
            reactions_to_dataframe(
                simulation["initial_reactions"],
                bubble_assignments=bubble_assignments,
            ),
            "reactions",
        ),
        "media_actors.csv": dataframe_to_csv_export(
            pd.DataFrame([actor.model_dump(mode="json") for actor in simulation["media_actors"]]),
            "media_actors",
        ),
        "social_bubbles.csv": dataframe_to_csv_export(
            pd.DataFrame([bubble.model_dump(mode="json") for bubble in simulation["bubbles"]]),
            "social_bubbles",
        ),
    }
    if echo_result:
        files["echo_items.csv"] = dataframe_to_csv_export(
            echo_items_to_dataframe(echo_result.echo_items), "echo_items"
        )
        files["echo_reactions.csv"] = dataframe_to_csv_export(
            echo_reactions_to_dataframe(echo_result.echo_reactions), "echo_reactions"
        )

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, content in files.items():
            archive.writestr(filename, content)
    return buffer.getvalue()


def export_metadata(export_name: str) -> dict[str, str]:
    return {
        "export_name": export_name,
        "synthetic_simulation_disclaimer": SYNTHETIC_SIMULATION_DISCLAIMER,
        "ethical_use_disclaimer": ETHICAL_USE_DISCLAIMER,
    }


def _archive_readme() -> str:
    return "\n".join(
        [
            "EchoGrid export bundle",
            "",
            SYNTHETIC_SIMULATION_DISCLAIMER,
            ETHICAL_USE_DISCLAIMER,
            "",
            "Files:",
            "- report.html: standalone synthetic simulation report; open locally in a browser.",
            "- summary.json: event, frames, initial metrics, and echo metrics.",
            "- agents.csv: synthetic agent profiles.",
            "- reactions.csv: initial synthetic reactions.",
            "- media_actors.csv: media ecosystem actors used in the run.",
            "- social_bubbles.csv: social bubble definitions used in the run.",
            "- echo_items.csv: generated echo items, when echo simulation was enabled.",
            "- echo_reactions.csv: second-round synthetic reactions, when enabled.",
        ]
    )


def _bubble_by_agent(assignments: dict[str, list[str]]) -> dict[str, str]:
    return {
        agent_id: bubble_id
        for bubble_id, agent_ids in assignments.items()
        for agent_id in agent_ids
    }
