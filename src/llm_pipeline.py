"""LLM orchestration helpers for bounded Hybrid mode runs."""

from __future__ import annotations

import json
import re
from typing import Protocol

from pydantic import TypeAdapter

from src.prompts import load_prompt
from src.schemas import (
    AgentReaction,
    EchoItem,
    HybridArtifacts,
    LLMCostEstimate,
    LLMGenerationError,
    LLMProvider,
    MediaActor,
    NewsEvent,
    NewsFrame,
    RepresentativeComment,
    SocialBubble,
)


class HybridLLMClient(Protocol):
    def generate_framings_json(self, prompt: str) -> list[NewsFrame]:
        ...

    def generate_echo_items_json(self, prompt: str) -> list[EchoItem]:
        ...

    def generate_representative_comments_json(
        self, prompt: str
    ) -> list[RepresentativeComment]:
        ...


_FRAMES_ADAPTER = TypeAdapter(list[NewsFrame])
_ECHO_ITEMS_ADAPTER = TypeAdapter(list[EchoItem])
_COMMENTS_ADAPTER = TypeAdapter(list[RepresentativeComment])


def estimate_llm_cost(
    run_mode: str,
    provider: LLMProvider,
    population_size: int,
    frame_count: int,
    echo_enabled: bool,
) -> LLMCostEstimate:
    normalized_mode = run_mode.strip().lower()
    if normalized_mode == "mock":
        return LLMCostEstimate(
            run_mode=normalized_mode,
            provider=provider,
            estimated_calls=0,
            estimated_input_tokens=0,
            estimated_output_tokens=0,
            estimated_usd_low=0,
            estimated_usd_high=0,
            notes="Mock mode uses deterministic local generation and makes no LLM calls.",
        )

    calls = 1
    if echo_enabled:
        calls += 1
    calls += 1

    sampled_reactions = min(population_size * max(frame_count, 1), 24)
    input_tokens = 850 + frame_count * 220 + sampled_reactions * 95
    if echo_enabled:
        input_tokens += 1700
    output_tokens = frame_count * 180 + 900 + (900 if echo_enabled else 0)

    low_rate, high_rate = _rough_price_band(provider)
    total_tokens_m = (input_tokens + output_tokens) / 1_000_000

    return LLMCostEstimate(
        run_mode=normalized_mode,
        provider=provider,
        estimated_calls=calls,
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        estimated_usd_low=round(total_tokens_m * low_rate, 4),
        estimated_usd_high=round(total_tokens_m * high_rate, 4),
        notes="No per-agent LLM calls; Hybrid mode samples reactions for artifact generation.",
    )


def generate_hybrid_artifacts(
    client: HybridLLMClient,
    event: NewsEvent,
    fallback_frames: list[NewsFrame],
    initial_reactions: list[AgentReaction],
    media_actors: list[MediaActor],
    bubbles: list[SocialBubble],
    frame_count: int,
    fallback_echo_items: list[EchoItem] | None = None,
    reaction_sample_limit: int = 24,
    representative_comment_limit: int = 8,
) -> HybridArtifacts:
    frames, errors = generate_hybrid_frames(
        client=client,
        event=event,
        fallback_frames=fallback_frames,
        frame_count=frame_count,
    )
    artifacts = generate_hybrid_response_artifacts(
        client=client,
        event=event,
        frames=frames,
        initial_reactions=initial_reactions,
        media_actors=media_actors,
        bubbles=bubbles,
        fallback_echo_items=fallback_echo_items,
        reaction_sample_limit=reaction_sample_limit,
        representative_comment_limit=representative_comment_limit,
    )
    return artifacts.model_copy(update={"frames": frames, "errors": errors + artifacts.errors})


def generate_hybrid_frames(
    client: HybridLLMClient,
    event: NewsEvent,
    fallback_frames: list[NewsFrame],
    frame_count: int,
) -> tuple[list[NewsFrame], list[LLMGenerationError]]:
    errors: list[LLMGenerationError] = []
    frames = fallback_frames[:frame_count]
    try:
        generated_frames = client.generate_framings_json(
            build_framing_prompt(event, frame_count)
        )
        frames = _normalize_frames(generated_frames, frame_count) or frames
    except Exception as exc:
        errors.append(_llm_error("framings", exc))
    return frames, errors


def generate_hybrid_response_artifacts(
    client: HybridLLMClient,
    event: NewsEvent,
    frames: list[NewsFrame],
    initial_reactions: list[AgentReaction],
    media_actors: list[MediaActor],
    bubbles: list[SocialBubble],
    fallback_echo_items: list[EchoItem] | None = None,
    reaction_sample_limit: int = 24,
    representative_comment_limit: int = 8,
    echo_enabled: bool = True,
) -> HybridArtifacts:
    errors: list[LLMGenerationError] = []
    echo_items = fallback_echo_items or []
    if echo_enabled:
        try:
            generated_echo_items = client.generate_echo_items_json(
                build_echo_items_prompt(
                    event=event,
                    frames=frames,
                    reactions=initial_reactions,
                    media_actors=media_actors,
                    bubbles=bubbles,
                    sample_limit=reaction_sample_limit,
                )
            )
            echo_items = _ECHO_ITEMS_ADAPTER.validate_python(generated_echo_items)
        except Exception as exc:
            errors.append(_llm_error("echo_items", exc))

    representative_comments: list[RepresentativeComment] = []
    try:
        generated_comments = client.generate_representative_comments_json(
            build_representative_comments_prompt(
                event=event,
                frames=frames,
                reactions=initial_reactions,
                bubbles=bubbles,
                sample_limit=reaction_sample_limit,
                comment_limit=representative_comment_limit,
            )
        )
        representative_comments = _COMMENTS_ADAPTER.validate_python(generated_comments)
    except Exception as exc:
        errors.append(_llm_error("representative_comments", exc))

    return HybridArtifacts(
        frames=frames,
        echo_items=echo_items,
        representative_comments=representative_comments,
        errors=errors,
    )


def build_framing_prompt(event: NewsEvent, frame_count: int) -> str:
    prompt = load_prompt("framing")
    event_json = json.dumps(event.model_dump(mode="json"), sort_keys=True)
    return (
        f"{prompt}\n\n"
        f"Generate exactly {frame_count} NewsFrame objects as a JSON array.\n\n"
        "Event JSON:\n"
        f"{event_json}"
    )


def build_echo_items_prompt(
    event: NewsEvent,
    frames: list[NewsFrame],
    reactions: list[AgentReaction],
    media_actors: list[MediaActor],
    bubbles: list[SocialBubble],
    sample_limit: int = 24,
) -> str:
    prompt = load_prompt("echo_generation")
    context = {
        "event": event.model_dump(mode="json"),
        "frames": [frame.model_dump(mode="json") for frame in frames],
        "reaction_samples": _reaction_samples(reactions, sample_limit),
        "media_actors": [actor.model_dump(mode="json") for actor in media_actors],
        "social_bubbles": [bubble.model_dump(mode="json") for bubble in bubbles],
    }
    return (
        f"{prompt}\n\n"
        "Generate a JSON array of EchoItem objects. Do not include wrapper keys.\n\n"
        "Context JSON:\n"
        f"{json.dumps(context, sort_keys=True)}"
    )


def build_representative_comments_prompt(
    event: NewsEvent,
    frames: list[NewsFrame],
    reactions: list[AgentReaction],
    bubbles: list[SocialBubble],
    sample_limit: int = 24,
    comment_limit: int = 8,
) -> str:
    prompt = load_prompt("representative_comments")
    context = {
        "event": event.model_dump(mode="json"),
        "frames": [frame.model_dump(mode="json") for frame in frames],
        "reaction_samples": _reaction_samples(reactions, sample_limit),
        "social_bubbles": [bubble.model_dump(mode="json") for bubble in bubbles],
        "max_comments": comment_limit,
    }
    return (
        f"{prompt}\n\n"
        f"Generate up to {comment_limit} RepresentativeComment objects as a JSON array.\n\n"
        "Context JSON:\n"
        f"{json.dumps(context, sort_keys=True)}"
    )


def _normalize_frames(frames: list[NewsFrame], frame_count: int) -> list[NewsFrame]:
    validated = _FRAMES_ADAPTER.validate_python(frames)
    normalized: list[NewsFrame] = []
    seen_ids: set[str] = set()
    for index, frame in enumerate(validated[:frame_count], start=1):
        base_id = _slug(frame.frame_id or frame.label) or f"llm_frame_{index}"
        frame_id = base_id
        suffix = 2
        while frame_id in seen_ids:
            frame_id = f"{base_id}_{suffix}"
            suffix += 1
        seen_ids.add(frame_id)
        normalized.append(frame.model_copy(update={"frame_id": frame_id}))
    return normalized


def _reaction_samples(reactions: list[AgentReaction], limit: int) -> list[dict[str, object]]:
    ranked = sorted(
        reactions,
        key=lambda reaction: (
            reaction.emotional_intensity + reaction.share_likelihood,
            reaction.agent_id,
            reaction.frame_id,
        ),
        reverse=True,
    )
    samples: list[dict[str, object]] = []
    for reaction in ranked[:limit]:
        samples.append(
            {
                "reaction_id": f"{reaction.agent_id}:{reaction.frame_id}",
                "agent_id": reaction.agent_id,
                "frame_id": reaction.frame_id,
                "stance": reaction.stance.value,
                "stance_strength": reaction.stance_strength,
                "emotions": reaction.emotions.model_dump(mode="json"),
                "trust_in_source": reaction.trust_in_source,
                "share_likelihood": reaction.share_likelihood,
                "comment_likelihood": reaction.comment_likelihood,
                "main_reason": reaction.main_reason,
                "likely_comment": reaction.likely_comment,
            }
        )
    return samples


def _llm_error(step: str, exc: Exception) -> LLMGenerationError:
    return LLMGenerationError(step=step, message=f"{type(exc).__name__}: {exc}")


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9_-]+", "_", value.lower()).strip("_-")
    return slug[:48]


def _rough_price_band(provider: LLMProvider) -> tuple[float, float]:
    if provider == LLMProvider.MOCK:
        return 0, 0
    if provider == LLMProvider.GEMINI:
        return 0.05, 3.5
    return 0.1, 15.0
