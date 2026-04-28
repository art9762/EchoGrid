import importlib
from pathlib import Path


CORE_MODULES = [
    "src.analytics",
    "src.echo_engine",
    "src.framing",
    "src.guardrails",
    "src.llm_client",
    "src.media_ecosystem",
    "src.population",
    "src.reaction_engine",
    "src.report",
    "src.social_bubbles",
    "src.storage",
    "src.utils",
]


PROMPT_FILES = [
    "framing_prompt.txt",
    "reaction_prompt.txt",
    "echo_generation_prompt.txt",
    "echo_reaction_prompt.txt",
]


def test_core_modules_are_importable() -> None:
    for module_name in CORE_MODULES:
        importlib.import_module(module_name)


def test_prompt_templates_exist_and_request_json() -> None:
    prompt_dir = Path("src/prompts")
    for filename in PROMPT_FILES:
        content = (prompt_dir / filename).read_text(encoding="utf-8")
        assert "Return JSON only" in content


def test_project_entrypoint_and_env_example_exist() -> None:
    assert Path("app.py").is_file()
    env_example = Path(".env.example").read_text(encoding="utf-8")
    assert "ANTHROPIC_API_KEY" in env_example
    assert "GEMINI_API_KEY" in env_example


def test_public_repository_metadata_exists() -> None:
    license_text = Path("LICENSE").read_text(encoding="utf-8")
    readme_text = Path("README.md").read_text(encoding="utf-8")

    assert license_text.startswith("MIT License")
    assert "## License" in readme_text
    assert "LICENSE" in readme_text
