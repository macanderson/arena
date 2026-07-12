# Arena Harbor Adapter

Run **your** coding agent through [Harbor](https://www.harborframework.com/)'s
official, containerized verifier — head-to-head against Claude Code, Gemini,
Codex, Cursor, Aider, and the rest — on SWE-bench Verified and Terminal-Bench.

## The idea

Harbor already ships adapters for the industry-leading agents
(`--agent claude-code`, `codex`, `gemini-cli`, `cursor-cli`, `aider`, …) and
scores every trial with the **same** repo-native test suite (FAIL_TO_PASS /
PASS_TO_PASS) inside a container. The agent never sees the verifier.

This package adds the two things Harbor doesn't give you:

1. **`ByoAgent`** — wire up your own agent from a small spec file. No Python.
2. Specs for agents Harbor lacks — **oxagen**, **stella** — that double as
   worked examples.

Your agent then competes against the built-ins under one scorer, so the
resolve-rate comparison is fair by construction.

## Install

```bash
pip install -e .        # from this directory (arena/harbor)
# Harbor itself needs Docker running to execute tasks.
```

## Wire up your agent (the main path)

1. Copy [`specs/byo.example.toml`](specs/byo.example.toml) and edit it for your
   CLI — how to install it in the container, how to invoke it one-shot, which
   env vars to forward. The placeholders (`{model}`, `{budget}`, `{instruction}`,
   …) are documented in the file.

2. Point Harbor at it. `--agent-import-path` loads any `module:Class`:

```bash
export ARENA_AGENT_SPEC=$PWD/my-agent.toml
export ARENA_AGENT_NAME=my-agent          # how results are labelled
export MY_AGENT_API_KEY=...               # forwarded per your spec's env_keys

harbor run \
  --agent-import-path arena_harbor:ByoAgent \
  --dataset swe-bench/swe-bench-verified \
  -m anthropic/claude-sonnet-5 \
  -n 4 -k 1 \
  -o results/my-agent
```

3. Run a built-in competitor on the **same** dataset and model, then compare
   resolved counts:

```bash
harbor run --agent claude-code -m anthropic/claude-sonnet-5 \
  --dataset swe-bench/swe-bench-verified -n 4 -o results/claude-code
```

Same model, same dataset, same verifier — the difference is the harness.

## Built-in Arena agents

```bash
# Stella — a single native binary, uploaded from the host.
# Build for the CONTAINER's arch (Linux x86-64), not your laptop:
#   cargo build --release --target x86_64-unknown-linux-gnu -p stella-cli
export ARENA_STELLA_BIN=/path/to/linux/stella
harbor run --agent-import-path arena_harbor:StellaAgent \
  -m zai/glm-5.2 --dataset swe-bench/swe-bench-verified -n 4

# Oxagen — a Node CLI, so you supply its install command (no package name is
# hard-coded):
export ARENA_OXAGEN_INSTALL="npm install -g @your-scope/oxagen@X"
export AI_GATEWAY_API_KEY=...
harbor run --agent-import-path arena_harbor:OxagenAgent \
  -m anthropic/claude-sonnet-5 --dataset swe-bench/swe-bench-verified -n 4
```

`run.sh` wraps this flow with sensible defaults — `AGENT=stella ./run.sh`.

## How a run works

For each task Harbor builds a container, then this adapter:

1. **installs** your agent (`install.kind = "binary"` uploads a host executable;
   `"script"` runs your shell snippet as root — npm/pip/curl/tarball);
2. **runs** it one-shot in the task repo with your `run_template`, forwarding the
   host env vars your spec declares (plus every `ARENA_*`);
3. lets Harbor's **verifier** decide pass/fail from the repo's own tests — a
   non-zero exit from your CLI never aborts scoring;
4. best-effort **parses** token/cost numbers from stdout for the trial metadata
   (these annotate; they never score).

Token normalization matches Arena's TS adapters: set `metrics.input_includes_cache`
when your reported input count already includes cache reads, so cross-agent
token totals stay comparable.

## Configuration knobs

| Env var | Purpose |
|---|---|
| `ARENA_AGENT_SPEC` | Path to your `ByoAgent` spec (`.toml`/`.json`). |
| `ARENA_AGENT_NAME` | Result label for `ByoAgent` (default `arena-byo`). |
| `ARENA_BUDGET` | Per-task USD cap (fills `{budget}`). |
| `ARENA_TIMEOUT` | Per-task seconds (fills `{timeout}`; default 1800). |
| `ARENA_STELLA_BIN` | Host path to the stella binary (StellaAgent). |
| `ARENA_OXAGEN_INSTALL` | Shell command that installs oxagen (OxagenAgent). |

Provider keys (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `ZAI_API_KEY`,
`AI_GATEWAY_API_KEY`, …) are forwarded when named in the spec's `env_keys`.

## Development

```bash
pip install -e '.[dev]'
pytest -q          # spec/metrics/command tests need no Harbor; agent tests use it
```

The pure logic (`spec.py`, `metrics.py`, `command.py`) imports nothing from
Harbor and is tested in isolation; `test_agents.py` exercises the real
`BaseInstalledAgent` subclasses and `importorskip`s when Harbor is absent.

MIT © Oxagen
