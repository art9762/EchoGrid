"""SQLite persistence for EchoGrid simulation runs."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.schemas import (
    AgentProfile,
    AgentReaction,
    EchoSimulationResult,
    MediaActor,
    NewsEvent,
    NewsFrame,
    SocialBubble,
)
from src.utils import stable_seed


TABLE_DEFINITIONS = [
    """
    create table if not exists simulations (
        simulation_id text primary key,
        created_at text not null,
        payload_json text not null
    )
    """,
    """
    create table if not exists events (
        simulation_id text primary key,
        payload_json text not null,
        foreign key(simulation_id) references simulations(simulation_id)
    )
    """,
    """
    create table if not exists agents (
        simulation_id text not null,
        agent_id text not null,
        payload_json text not null,
        primary key(simulation_id, agent_id)
    )
    """,
    """
    create table if not exists frames (
        simulation_id text not null,
        frame_id text not null,
        payload_json text not null,
        primary key(simulation_id, frame_id)
    )
    """,
    """
    create table if not exists reactions (
        simulation_id text not null,
        agent_id text not null,
        frame_id text not null,
        payload_json text not null
    )
    """,
    """
    create table if not exists media_actors (
        simulation_id text not null,
        actor_id text not null,
        payload_json text not null,
        primary key(simulation_id, actor_id)
    )
    """,
    """
    create table if not exists social_bubbles (
        simulation_id text not null,
        bubble_id text not null,
        payload_json text not null,
        primary key(simulation_id, bubble_id)
    )
    """,
    """
    create table if not exists echo_items (
        simulation_id text not null,
        echo_item_id text not null,
        payload_json text not null,
        primary key(simulation_id, echo_item_id)
    )
    """,
    """
    create table if not exists echo_reactions (
        simulation_id text not null,
        agent_id text not null,
        echo_item_id text not null,
        payload_json text not null
    )
    """,
    """
    create table if not exists echo_round_summaries (
        simulation_id text not null,
        round_number integer not null,
        payload_json text not null
    )
    """,
]


CHILD_TABLES = [
    "events",
    "agents",
    "frames",
    "reactions",
    "media_actors",
    "social_bubbles",
    "echo_items",
    "echo_reactions",
    "echo_round_summaries",
]


def init_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        for statement in TABLE_DEFINITIONS:
            connection.execute(statement)


def save_simulation(
    db_path: str | Path,
    event: NewsEvent,
    agents: list[AgentProfile],
    frames: list[NewsFrame],
    reactions: list[AgentReaction],
    media_actors: list[MediaActor],
    bubbles: list[SocialBubble],
    bubble_assignments: dict[str, list[str]],
    echo_result: EchoSimulationResult | None = None,
) -> str:
    init_database(db_path)
    simulation_id = (
        echo_result.simulation_id
        if echo_result
        else f"sim-{stable_seed(event.title, len(agents), len(frames)) % 1_000_000:06d}"
    )
    created_at = datetime.now(UTC).isoformat()
    payload = {
        "simulation_id": simulation_id,
        "event_title": event.title,
        "agent_count": len(agents),
        "frame_count": len(frames),
        "reaction_count": len(reactions),
        "echo_item_count": len(echo_result.echo_items) if echo_result else 0,
        "bubble_assignments": bubble_assignments,
    }

    with sqlite3.connect(db_path) as connection:
        for table in CHILD_TABLES:
            connection.execute(f"delete from {table} where simulation_id = ?", (simulation_id,))
        connection.execute(
            """
            insert or replace into simulations (simulation_id, created_at, payload_json)
            values (?, ?, ?)
            """,
            (simulation_id, created_at, json.dumps(payload)),
        )
        connection.execute(
            "insert or replace into events (simulation_id, payload_json) values (?, ?)",
            (simulation_id, _json(event)),
        )
        connection.executemany(
            "insert into agents (simulation_id, agent_id, payload_json) values (?, ?, ?)",
            [(simulation_id, agent.id, _json(agent)) for agent in agents],
        )
        connection.executemany(
            "insert into frames (simulation_id, frame_id, payload_json) values (?, ?, ?)",
            [(simulation_id, frame.frame_id, _json(frame)) for frame in frames],
        )
        connection.executemany(
            "insert into reactions (simulation_id, agent_id, frame_id, payload_json) values (?, ?, ?, ?)",
            [
                (simulation_id, reaction.agent_id, reaction.frame_id, _json(reaction))
                for reaction in reactions
            ],
        )
        connection.executemany(
            "insert into media_actors (simulation_id, actor_id, payload_json) values (?, ?, ?)",
            [(simulation_id, actor.id, _json(actor)) for actor in media_actors],
        )
        connection.executemany(
            "insert into social_bubbles (simulation_id, bubble_id, payload_json) values (?, ?, ?)",
            [(simulation_id, bubble.id, _json(bubble)) for bubble in bubbles],
        )
        if echo_result:
            connection.executemany(
                "insert into echo_items (simulation_id, echo_item_id, payload_json) values (?, ?, ?)",
                [
                    (simulation_id, item.id, _json(item))
                    for item in echo_result.echo_items
                ],
            )
            connection.executemany(
                "insert into echo_reactions (simulation_id, agent_id, echo_item_id, payload_json) values (?, ?, ?, ?)",
                [
                    (
                        simulation_id,
                        reaction.agent_id,
                        reaction.echo_item_id,
                        _json(reaction),
                    )
                    for reaction in echo_result.echo_reactions
                ],
            )
            connection.executemany(
                "insert into echo_round_summaries (simulation_id, round_number, payload_json) values (?, ?, ?)",
                [
                    (
                        simulation_id,
                        summary.round_number,
                        _json(summary),
                    )
                    for summary in echo_result.round_summaries
                ],
            )
    return simulation_id


def _json(model: Any) -> str:
    return json.dumps(model.model_dump(mode="json"))
