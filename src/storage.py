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
    EchoItem,
    EchoReaction,
    MediaActor,
    NewsEvent,
    NewsFrame,
    RoundSummary,
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
    seed: int | None = None,
    provider: str = "mock",
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
        "created_at": created_at,
        "event_title": event.title,
        "country": event.country,
        "topic": event.topic,
        "source_type": event.source_type,
        "population_size": len(agents),
        "seed": seed,
        "provider": provider,
        "agent_count": len(agents),
        "frame_count": len(frames),
        "reaction_count": len(reactions),
        "echo_item_count": len(echo_result.echo_items) if echo_result else 0,
        "bubble_assignments": bubble_assignments,
        "amplification_metrics": echo_result.amplification_metrics if echo_result else {},
        "final_reaction_state_by_agent": (
            {
                agent_id: state.model_dump(mode="json")
                for agent_id, state in echo_result.final_reaction_state_by_agent.items()
            }
            if echo_result
            else {}
        ),
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


def list_simulations(db_path: str | Path, limit: int = 25) -> list[dict[str, Any]]:
    path = Path(db_path)
    if not path.exists():
        return []

    init_database(path)
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            """
            select simulation_id, created_at, payload_json
            from simulations
            order by created_at desc
            limit ?
            """,
            (limit,),
        ).fetchall()

    summaries: list[dict[str, Any]] = []
    for simulation_id, created_at, payload_json in rows:
        payload = json.loads(payload_json)
        summaries.append(
            {
                "simulation_id": simulation_id,
                "created_at": payload.get("created_at", created_at),
                "event_title": payload.get("event_title", "Untitled event"),
                "country": payload.get("country", ""),
                "topic": payload.get("topic", ""),
                "source_type": payload.get("source_type", ""),
                "population_size": payload.get(
                    "population_size", payload.get("agent_count", 0)
                ),
                "seed": payload.get("seed"),
                "provider": payload.get("provider", "mock"),
                "frame_count": payload.get("frame_count", 0),
                "reaction_count": payload.get("reaction_count", 0),
                "echo_item_count": payload.get("echo_item_count", 0),
            }
        )
    return summaries


def delete_simulation(db_path: str | Path, simulation_id: str) -> bool:
    path = Path(db_path)
    if not path.exists():
        return False

    with sqlite3.connect(path) as connection:
        for table in CHILD_TABLES:
            connection.execute(
                f"delete from {table} where simulation_id = ?", (simulation_id,)
            )
        cursor = connection.execute(
            "delete from simulations where simulation_id = ?", (simulation_id,)
        )
    return cursor.rowcount > 0


def load_simulation(db_path: str | Path, simulation_id: str) -> dict[str, Any]:
    with sqlite3.connect(db_path) as connection:
        simulation_row = connection.execute(
            "select payload_json from simulations where simulation_id = ?",
            (simulation_id,),
        ).fetchone()
        if simulation_row is None:
            raise KeyError(f"Simulation not found: {simulation_id}")
        metadata = json.loads(simulation_row[0])

        event = _load_one(connection, "events", simulation_id, NewsEvent)
        agents = _load_many(connection, "agents", simulation_id, AgentProfile)
        frames = _load_many(connection, "frames", simulation_id, NewsFrame)
        reactions = _load_many(connection, "reactions", simulation_id, AgentReaction)
        media_actors = _load_many(connection, "media_actors", simulation_id, MediaActor)
        bubbles = _load_many(connection, "social_bubbles", simulation_id, SocialBubble)
        echo_items = _load_many(connection, "echo_items", simulation_id, EchoItem)
        echo_reactions = _load_many(
            connection, "echo_reactions", simulation_id, EchoReaction
        )
        round_summaries = _load_many(
            connection, "echo_round_summaries", simulation_id, RoundSummary
        )

    echo_result = None
    if echo_items or echo_reactions or round_summaries:
        echo_result = EchoSimulationResult(
            simulation_id=simulation_id,
            echo_items=echo_items,
            echo_reactions=echo_reactions,
            round_summaries=round_summaries,
            final_reaction_state_by_agent=metadata.get(
                "final_reaction_state_by_agent", {}
            ),
            amplification_metrics=metadata.get("amplification_metrics", {}),
        )

    return {
        "simulation_id": simulation_id,
        "event": event,
        "agents": agents,
        "frames": frames,
        "reactions": reactions,
        "initial_reactions": reactions,
        "media_actors": media_actors,
        "bubbles": bubbles,
        "bubble_assignments": metadata.get("bubble_assignments", {}),
        "echo_result": echo_result,
    }


def _load_one(
    connection: sqlite3.Connection,
    table: str,
    simulation_id: str,
    model_type: type[Any],
) -> Any:
    row = connection.execute(
        f"select payload_json from {table} where simulation_id = ?",
        (simulation_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"Missing {table} row for simulation: {simulation_id}")
    return model_type.model_validate_json(row[0])


def _load_many(
    connection: sqlite3.Connection,
    table: str,
    simulation_id: str,
    model_type: type[Any],
) -> list[Any]:
    rows = connection.execute(
        f"select payload_json from {table} where simulation_id = ? order by rowid",
        (simulation_id,),
    ).fetchall()
    return [model_type.model_validate_json(row[0]) for row in rows]


def _json(model: Any) -> str:
    return json.dumps(model.model_dump(mode="json"))
