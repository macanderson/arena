# Arena architecture

Two subsystems share one repo: a TypeScript CLI harness (`src/`) and a Python Harbor adapter (`harbor/`). They share no code, only a token-normalization convention: `input` never includes cache reads.

```mermaid
graph TD
  subgraph CLI["TypeScript harness"]
    cli["cli.ts (entry / dispatch)"]
    cli --> c_run["run"] & c_verify["verify"] & c_gate["gate / baseline"] & c_report["report"] & c_list["list / doctor"]

    subgraph CORE["core pipeline"]
      orch["orchestrator.ts executeRun/runOne"]
      ws["workspace.ts seed/diff/verify"]
      adp["adapters/ claude-code · gemini · oxagen · stella · mock"]
      parse["parse.ts envelope/diff parsing"]
      pricing["pricing.ts + pricing.json"]
    end

    stats["stats.ts wilson/mcnemar/bootstrap"]
    summary["summary.ts perAgentSummary"]
    report["report.ts"]
    baseline["baseline.ts gate/baseline"]
    tasksdir["tasks/<id>/ task.json + workspace + verify + solution"]

    c_run --> orch
    c_verify --> ws
    c_report --> report
    c_gate --> baseline
    orch --> ws & adp & parse & pricing
    ws --> tasksdir
    report --> stats & summary
    baseline --> summary
    summary --> stats
  end

  subgraph HARBOR["harbor/ Python adapter (separate process)"]
    h_agents["agents.py Byo/Oxagen/StellaAgent"]
    h_base["base.py ArenaInstalledAgent"]
    h_spec["spec.py AgentSpec (TOML/JSON)"]
    h_cmd["command.py build_command"]
    h_metrics["metrics.py extract_metrics"]
    HarborFW["Harbor framework (Docker verifier)"]
    h_agents --> h_base --> h_cmd & h_metrics & h_spec
    h_base --> HarborFW
  end

  CLI -. "token normalization convention only" .- HARBOR
```

## One trial, end to end

1. `cli.ts:cmdRun` parses argv into a `RunConfig`, loads tasks.
2. `orchestrator.ts:executeRun` creates the run dir, checks each adapter's availability, writes `manifest.json`, then loops trials × tasks × agents with ABBA order flipping.
3. `runOne`: `seedWorkspace` copies the fixture into a temp dir and git-commits the seed → `adapter.execute` spawns the CLI (own process group, SIGKILL tree on timeout) → `collectDiff` captures exactly what the agent changed → `parseEnvelope` normalizes tokens → held-out `runVerification` (wipe `.arena-verify/`, copy tests in, `node --test`, wipe again) → `TrialResult` written; `results.json` rewritten every trial.
4. `report.ts` renders per-agent summaries (via `summary.ts`, the same aggregation the gate uses), pairwise McNemar and bootstrap deltas, the per-task matrix, and receipts.
5. `baseline.ts` snapshots a run (`baseline save`) and gates later runs (`gate`), refusing task-set mismatches and, with `--require-significant`, only failing accuracy drops that clear the 95% CIs.

## Contracts

- **Adapter** (`src/adapters/base.ts`): implement `name`, `defaultBinary`, `buildArgs(args)` (argv array, never shell), and `parseEnvelope(stdout)` returning normalized tokens (`input` excludes cache reads; use `totalize`/`emptyEnvelope`). Optional overrides: `resolveModel`, `env`, `execute`, `isAvailable`/`version`. Register in `src/adapters/index.ts`.
- **Task fixture** (`tasks/<id>/`): `task.json` (`id` must equal the dir name), `workspace/` (what the agent sees), `verify/` (held-out `node:test` suite, never on disk during the run), `solution/` (reference proving solvability). `arena verify` enforces: pristine fails, solution passes.
- **Harbor spec** (`harbor/arena_harbor/spec.py`): a TOML/JSON file with `name`, `binary`, `run_template` (`{bin} {model} {budget} {timeout} {instruction}` placeholders; instruction shell-quoted for you), plus install and metrics blocks. Point `ARENA_AGENT_SPEC` at it; no Python needed.
