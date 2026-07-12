"""Built-in agent specs for agents Harbor does not ship itself.

Harbor 0.6+ already bundles Claude Code, Gemini CLI, Codex, Cursor, Copilot,
Aider, and more — run those with ``--agent claude-code`` etc. These specs cover
the gaps (oxagen, stella) and double as worked examples of the spec format.

Harbor-free.
"""

from __future__ import annotations

from .spec import AgentSpec, InstallSpec, MetricsSpec

# Provider API keys worth forwarding for most agents.
_COMMON_KEYS = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "ZAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "OPENROUTER_API_KEY",
    "AI_GATEWAY_API_KEY",
]


#: Oxagen — a Node CLI (``#!/bin/sh`` launcher), so it needs a *script* install.
#: The install command is intentionally left to the operator via
#: ``ARENA_OXAGEN_INSTALL`` (e.g. ``npm i -g @oxagen/cli@X`` or a tarball URL)
#: rather than hard-coding a package name we can't verify.
OXAGEN_SPEC = AgentSpec(
    name="oxagen",
    binary="oxagen",
    run_template=(
        "{bin} --local --output-format json --model {model} "
        "--budget {budget} -- {instruction}"
    ),
    install=InstallSpec(
        kind="script",
        script_env="ARENA_OXAGEN_INSTALL",
        script=(
            'echo "Set ARENA_OXAGEN_INSTALL to the shell command that installs '
            'oxagen in the container (e.g. an npm i -g or a tarball fetch)." >&2; '
            "exit 1"
        ),
        system_packages=["nodejs", "npm"],
    ),
    version_command="oxagen --version",
    env_keys=[*_COMMON_KEYS, "OXAGEN_MODEL_SLUG", "OXAGEN_BUDGET"],
    default_model="anthropic/claude-sonnet-5",
    default_budget="5",
    metrics=MetricsSpec(
        kind="json_tail",
        input_path="usage.inputTokens",
        output_path="usage.outputTokens",
        cache_read_path="usage.cachedInputTokens",
        input_includes_cache=True,  # oxagen's inputTokens includes cache reads
    ),
)


#: Stella — a single native binary, so it can be *uploaded* from the host. The
#: host binary must match the container's OS/arch (Linux x86-64 for stock SWE-
#: bench images): build with ``cargo build --release --target x86_64-unknown-
#: linux-gnu`` and point ``ARENA_STELLA_BIN`` at it, or switch to a script
#: install that fetches a Linux release.
STELLA_SPEC = AgentSpec(
    name="stella",
    binary="stella",
    run_template="{bin} --model {model} --output-format json --budget {budget} run {instruction}",
    install=InstallSpec(kind="binary", binary_env="ARENA_STELLA_BIN"),
    version_command="stella --version",
    version_regex=r"(\d+\.\d+\.\d+)",
    env_keys=[*_COMMON_KEYS, "STELLA_MODEL", "STELLA_BASE_URL", "STELLA_BUDGET"],
    default_model="zai/glm-5.2",
    default_budget="5",
    metrics=MetricsSpec(
        kind="json_tail",
        input_path="usage.inputTokens",
        output_path="usage.outputTokens",
        cache_read_path="usage.cachedInputTokens",
        cost_path="costUsd",
        input_includes_cache=True,
    ),
)

BUILTIN_SPECS = {spec.name: spec for spec in (OXAGEN_SPEC, STELLA_SPEC)}
