# Agent Benchmark Protocol (ABP)

**Draft 0.1 · July 2026 · Oxagen**

An open standard for benchmarking agent engines: the harness, prompts, tools, and loop an agent ships with, measured separately from the model it happens to run on.

Status: draft for public comment. The reference implementation is [Arena](https://github.com/macanderson/arena). Nothing here is final, including the name.

---

## 1. The problem this standard exists to solve

Teams that ship agents change their engine every week: a new system prompt, a new tool, a reworked planning loop, a different context strategy. None of those changes show up on a model leaderboard, because model leaderboards hold the harness fixed and vary the model. The people who build agent engines have the opposite need: hold the model fixed and vary the engine.

Today that comparison is nearly impossible to run honestly:

1. Every harness invokes agents differently, so "same task" rarely means same prompt, same budget, same timeout, or same autonomy level.
2. Every harness logs differently, so traces cannot be compared across engines.
3. Every harness grades differently, and most let the agent's own output influence the grade.
4. Almost no benchmark measures efficiency. Two agents that both fix a bug are scored as equals even when one shipped a 4-line patch in 90 seconds and the other shipped a 400-line rewrite in 20 minutes.
5. Almost no benchmark runs in CI. A benchmark you run once for a launch tweet cannot catch the Tuesday your agent quietly got worse.

ABP standardizes the four interfaces that make honest engine comparison possible: how a task is packaged, how a run is configured, how a trace is recorded, and how a verdict is reported. Any engine that speaks these formats can be benchmarked by any conforming harness, and any harness can be audited by anyone.

## 2. Why "protocol"

We considered "standard", "format", "spec", and "benchmark". Protocol is the right word for the same reason it was right for the Model Context Protocol: the deliverable is a set of interchange contracts between independent parties (task authors, engines, harnesses, graders, and auditors), not a single dataset or a single leaderboard. Datasets and leaderboards are built on top of ABP; they are products, and ABP is the plumbing. It also keeps the family resemblance with the Open Context Protocol, which Oxagen authored and built [Stella](https://github.com/macanderson/stella) on.

One naming caution, stated openly: "protocol" sets an expectation of wire-level rigor. This draft earns that word only in Sections 5 through 8, where the schemas live. If the community reads those sections and concludes the word oversells, the fallback name is the Agent Benchmark Format (ABF). The acronym to protect is ABP, one syllable per letter, easy to say in CI logs: `abp gate failed`.

## 3. Design principles

These are inherited from Arena's methodology and are non-negotiable for conformance:

1. **The engine is the unit under test.** The model, provider, budget, and timeout are pinned inputs. Runs that vary the model are stamped as such and cannot back engine-vs-engine claims.
2. **The agent never grades itself.** Verification material must be absent from the workspace while the agent runs, injected only after it exits, and immune to anything the agent planted.
3. **Every number carries its uncertainty.** Success rates get Wilson intervals. Paired comparisons get exact McNemar. Continuous metrics get seeded bootstrap CIs. No blended scores, ever.
4. **Harness failures are not agent failures.** An engine that could not be invoked is excluded from comparison, not counted as a loss.
5. **Receipts or it did not happen.** A conforming result ships its manifest, transcripts, diffs, and a one-line reproduce command.
6. **Efficiency is a first-class metric.** Resolution alone is a tie. Diff size, tokens, wall clock, and cost break it.

## 4. The live task pipeline

This is the part of ABP that no existing benchmark provides end to end.

### 4.1 Sourcing

A curated registry of the top 500 open-source repositories on GitHub, filtered for: OSI license, active maintainership (merged PR in the last 30 days), a runnable test suite, and issue hygiene (reproducible reports, labeled backlog). The registry is versioned and published; entries rotate quarterly so the pool tracks the real ecosystem.

From the registry, tasks are drawn by seeded random selection: pick a repo, pick an open issue from its backlog that passes eligibility (reproducible, in-scope for a code change, not a question or a feature debate). The seed is published with every draw, so the selection itself is auditable.

### 4.2 Solving and promotion

A frontier engine (or a human, or both) builds a fix for the issue against the repo's contribution rules and submits it upstream. The fix is **verified** when the project's own CI passes and a maintainer merges it into the production branch. Maintainer merge is the ground truth no synthetic benchmark has: a real reviewer accepted this change into a real codebase.

Two artifacts fall out of every verified fix:

- **Training data.** The (issue, repo state, verified diff) triple.
- **A golden trace.** The full ABP trace (Section 6) the solving engine printed along the way: every tool call, every file read, every edit, every token count, timestamped.

### 4.3 Replay and grading

Once a task is verified, it freezes: repo pinned at the pre-fix commit, issue text captured, and a verification bundle built from the repo's own test suite plus the tests the verified fix added (the FAIL_TO_PASS set). Other engines then attempt the same frozen task under matched config. They are graded on:

1. **Resolution.** The held-out verification bundle passes.
2. **Efficiency, in strict order:** smaller normalized git diff wins, then fewer tokens, then less wall clock, then lower cost.

The golden trace is published as evidence and as a study aid, not as the rubric. Version 1 deliberately does not grade trace similarity: an engine that reaches a passing, smaller fix by a different route beats the golden trace's author. Judging architectural quality and trajectory quality is a stated version 2 direction, and it needs its own adversarial review before it can be a metric.

### 4.4 Contamination control

Live sourcing is also the contamination story. Issues are selected from the current backlog, after every candidate model's training cutoff, and each task carries a `sourcedAt` timestamp plus the model cutoffs it was verified against. Tasks age out of the scored set once their fix has been public for 180 days; they remain available as a practice set. Frozen-set benchmarks decay into training data. A pipeline that keeps drawing from the living backlog does not.

### 4.5 Known objections, answered in the design

- **"Smallest diff is gameable."** Diff size is measured on a normalized form: formatting-only changes are canonicalized before counting, generated files and lockfiles are excluded, and test files are counted separately (deleting or weakening tests disqualifies the run, it does not shrink the diff). Resolution is still the gate; diff size only ranks engines that already passed. And the metric is honest about what it is: a proxy for surgical precision, not for design quality. Arena publishes the raw diffs, so anyone can audit whether small meant surgical or small meant degenerate.
- **"Maintainers did not consent to being a benchmark."** Sourcing follows each repo's contribution guidelines, fixes are submitted as normal PRs with disclosure, registry entries can opt out, and replay runs happen on frozen clones, never against the live repo.
- **"Issue selection will favor easy tasks."** Selection is seeded-random within eligibility, the seed is published, and difficulty is stratified in reporting (task metadata records diff size and files touched of the verified fix).

## 5. Task manifest (`abp-task/v1`)

```jsonc
{
  "schema": "abp-task/v1",
  "id": "gh-vercel-next.js-81234",
  "source": {
    "kind": "github-issue",              // or "fixture" for synthetic tasks
    "repo": "vercel/next.js",
    "issue": 81234,
    "baseCommit": "9f2c41d…",            // repo frozen here (pre-fix)
    "sourcedAt": "2026-07-02T14:11:09Z",
    "registryVersion": "abp-registry/2026Q3",
    "drawSeed": 424242
  },
  "prompt": "…full task statement given to every engine…",
  "environment": {
    "image": "ghcr.io/macanderson/abp-node:22",   // container digest-pinned
    "setup": ["pnpm install --frozen-lockfile"]
  },
  "verification": {
    "kind": "commands",
    "failToPass": ["pnpm test -- test/router/edge-case.test.ts"],
    "passToPass": ["pnpm test -- test/router/"],
    "timeoutSeconds": 900,
    "heldOut": true                       // must not be on disk during the run
  },
  "golden": {
    "diffBytesNormalized": 1843,
    "filesTouched": 2,
    "trace": "traces/gh-vercel-next.js-81234.abp-trace.jsonl",
    "mergedPr": "https://github.com/vercel/next.js/pull/81301"
  },
  "cutoffsVerified": ["claude-sonnet-5:2026-01", "gpt-5.2:2026-03"]
}
```

Synthetic fixtures (like Arena's built-in tasks) use the same schema with `source.kind: "fixture"` and no `golden` block. A harness must treat both identically at run time.

## 6. Trace format (`abp-trace/v1`)

One JSONL file per (task, engine, trial). Every line is an event:

```jsonc
{"t":"2026-07-02T14:12:01.402Z","seq":1,"kind":"run.start","engine":"oxagen/1.4.2","model":"anthropic/claude-sonnet-5","task":"gh-vercel-next.js-81234","config":{"budgetUsd":5,"timeoutSeconds":1200}}
{"t":"…","seq":2,"kind":"model.call","tokens":{"input":1204,"output":388,"cacheRead":9120,"cacheWrite":0}}
{"t":"…","seq":3,"kind":"tool.call","tool":"read_file","args":{"path":"src/router/match.ts"},"durationMs":12}
{"t":"…","seq":4,"kind":"tool.call","tool":"edit_file","args":{"path":"src/router/match.ts"},"diffBytes":412}
{"t":"…","seq":5,"kind":"subagent.start","id":"sa-1","purpose":"run tests"}
{"t":"…","seq":6,"kind":"run.end","outcome":"resolved","wallClockMs":184201,"tokens":{"input":48210,"output":9114,"cacheRead":301200,"cacheWrite":8100},"diffBytesNormalized":1610,"filesTouched":2}
```

Rules:

- `seq` is a strictly increasing integer; `t` is RFC 3339 UTC. Together they make traces diffable and mergeable.
- `tool.call` events record the tool name and a redacted argument summary, never raw secrets. A published redaction list is part of conformance.
- Multi-agent engines emit `subagent.start` / `subagent.end` with nested attribution, so a fan-out engine's token bill is visible per branch. Multi-model engines record `model` per `model.call`. This is how ABP stays meaningful for orchestrators, not just single-loop CLIs.
- Token counts follow Arena's normalization: `input` never includes cache reads; cache reads and writes are tracked separately.
- An engine that cannot emit ABP traces natively can ship a sidecar translator; the harness records which path produced the trace.

## 7. Run configuration (`abp-run/v1`)

The manifest a harness must write before the first trial:

```jsonc
{
  "schema": "abp-run/v1",
  "engines": [{"name": "oxagen", "version": "1.4.2"}, {"name": "claude-code", "version": "2.1.0"}],
  "model": "anthropic/claude-sonnet-5",
  "matchedModels": true,
  "budgetUsd": 5,
  "timeoutSeconds": 1200,
  "trials": 3,
  "ordering": "abba",
  "seed": 20260718,
  "tasks": ["gh-vercel-next.js-81234", "…"],
  "host": {"os": "linux", "arch": "arm64", "containerized": true},
  "reproduce": "abp run --config run.json"
}
```

`matchedModels: false` runs are legal (you may want to test your engine across models) but a conforming report must lead with the warning and must not present engine-vs-engine conclusions from them.

## 8. Verdict format (`abp-verdict/v1`)

```jsonc
{
  "schema": "abp-verdict/v1",
  "run": "run-20260718-a41c",
  "perEngine": [{
    "engine": "oxagen",
    "scoredTrials": 72,
    "excludedEngineErrors": 1,
    "resolveRate": {"point": 0.84, "wilson95": [0.71, 0.92]},
    "medianDiffBytesNormalized": 1650,
    "medianTokensTotal": 361000,
    "medianWallClockMs": 190334,
    "medianComputedUsd": 1.42
  }],
  "pairwise": [{
    "a": "oxagen", "b": "claude-code",
    "mcnemar": {"discordant": [14, 5], "pExact": 0.041},
    "diffDelta": {"relMedian": -0.22, "bootstrap95": [-0.31, -0.09], "seed": 20260718}
  }],
  "receipts": {"trials": "trials/", "transcripts": "transcripts/", "diffs": "diffs/", "traces": "traces/"}
}
```

## 9. Conformance levels

- **ABP-core.** The harness consumes `abp-task/v1`, enforces held-out verification and matched config, and emits `abp-run/v1` + `abp-verdict/v1` with the required statistics. Arena today is one file-format migration away from ABP-core.
- **ABP-traces.** Everything in core, plus `abp-trace/v1` emission for every trial, with subagent and multi-model attribution.
- **ABP-live.** Everything in traces, plus participation in the live task pipeline: consuming registry draws, contributing verified fixes, and publishing golden traces.

Conformance is claimed by shipping a passing run of the public conformance suite (a set of adversarial fixtures: a task that tries to plant verification files, an envelope that lies about tokens, a trial that must be scored engine-error) and linking the receipts.

## 10. CI integration

The reason ABP should win: it is the only benchmark designed to be run on every pull request, not once per launch.

```yaml
# .github/workflows/agent-quality.yml
- run: abp run --config abp-run.json -o results
- run: abp gate results/run-latest --baseline abp-baseline.json --require-significant
```

The gate semantics are Arena's, generalized: fail on a statistically significant resolve-rate drop, or on median token, cost, diff-size, or wall-clock growth past committed thresholds; refuse to compare across mismatched task sets. The baseline is a committed JSON artifact, so the PR that degrades the agent goes red the same day, with receipts attached.

## 11. Roadmap

| Phase | Deliverable | Exit criterion |
|---|---|---|
| 0 (now) | Arena as reference harness; this draft public at arena.oxagen.sh | Draft survives public review |
| 1 | Schemas frozen at v1; Arena emits and consumes all four formats; conformance suite published | Two non-Oxagen engines emit valid traces |
| 2 | Live pipeline pilot: 25-repo registry subset, 100 verified tasks, golden traces published | External team reproduces a published verdict from receipts alone |
| 3 | Registry at 500 repos; hosted leaderboard with matched-model brackets; GitHub Action in the marketplace | ABP gate running in 100 external repos' CI |
| 4 | Version 2 exploration: trajectory quality, architectural review, multi-agent orchestration scoring | Community RFC process |

## 12. Open questions

1. Trace redaction: how much tool-argument detail can be published from runs on private code without leaking it? Current answer: conformance requires the redaction list, and private runs may withhold traces while still claiming ABP-core.
2. Who signs verified tasks? A task's freeze bundle should be content-addressed and signed by the registry, or a poisoned mirror can grade dishonestly.
3. Diff normalization is specified per-language (formatter canonicalization). The v1 scope is the languages with deterministic formatters; the escape hatch is byte counts on `git diff --numstat` with published exclusions.
4. Should golden traces ever become the rubric? Version 1 says no. If v2 explores it, trace-similarity grading must never punish a better route to a passing fix.

---

*Feedback: open an issue at [github.com/macanderson/arena](https://github.com/macanderson/arena/issues) with the `abp` label.*
