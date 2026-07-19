# The State of Agent Benchmarking

## Everyone measures the model. Almost nobody measures the engine you ship.

**Mac Anderson (Oxagen) · July 2026 · v1.0**

*Conflict of interest, stated up front: the author builds Arena, an open-source agent-engine benchmark harness, and the Oxagen and Stella agents that appear in its examples. This paper argues a position. Every load-bearing claim carries a citation, and the gap analysis in Section 6 names the systems that already do parts of what Arena does.*

---

## Abstract

Teams that ship AI agents change their engine every week: prompts, tools, planning loops, context strategies, and orchestration. The model changes a few times a year. Yet nearly every public benchmark ranks models with the harness held fixed, which is the exact inverse of the question a working team needs answered: did my last change make my agent better or worse, on the model I already run? Recent controlled evidence says this inversion is not cosmetic. In a 3x3 factorial study on SWE-bench Verified, harness-induced variance exceeded model-induced variance by 7.8x, and model rankings reversed in six of nine harness pairings [3]. Two 2026 surveys independently name model-vs-harness conflation as an open methodological gap [1, 2]. This paper surveys the benchmark landscape as of July 2026 through that lens: what each system actually measures, whether it can isolate the engine from the model, whether it grades efficiency, whether it can run in CI as a regression gate, and whether its tasks stay fresh. We find that no existing system combines matched-model engine isolation, efficiency grading (diff size, tokens, wall clock, cost), statistically honest CI gating, and live task sourcing with verified fixes as reference traces. We close by describing that missing system and an interchange standard, the Agent Benchmark Protocol, that would let any harness provide it.

## 1. The question benchmarks answer, and the question teams ask

A model leaderboard answers: given a fixed scaffold, which model scores highest? That is the right question for a lab choosing a base model, and the wrong question for everyone downstream. Downstream, the model is a config value. The product is the engine: the system prompt, the tool set, the retrieval and context policy, the planning loop, the subagent topology, and the guardrails. One survey puts the distinction plainly: evaluating the LLM alone is like examining an engine on a stand, while agent evaluation must assess the whole car under driving conditions [2].

The scale of what the scaffold contributes has been measured repeatedly. SWE-agent showed in 2024 that the agent-computer interface alone moves resolve rates at a fixed model [24]. Agentless showed the same year that a deliberately non-agentic pipeline could outperform elaborate agents at a fraction of the cost [25]. And in 2026 a controlled factorial study quantified it: across three models and three harness configurations on a 100-task SWE-bench Verified subset, the harness contributed 18.48 pp² of score variance against the model's 2.37 pp², a ratio of 7.8x, with six model-ranking reversals across nine harness pairings [3]. The authors' conclusion is the thesis of this paper: the execution harness, the infrastructure layer that governs context construction, tool interaction, orchestration, and verification, is often a stronger determinant of agent performance than the model it wraps [3].

The benchmark ecosystem has not caught up. The most comprehensive survey of agent evaluation to date lists "Decoupling LLM & Harness Evaluation" as future work: most current benchmarks conflate the two targets, and no established benchmark provides controlled protocols that vary each factor independently [1]. The same survey finds cost and efficiency metrics broadly neglected, echoing the argument of "AI Agents That Matter" that accuracy-only leaderboards drive needlessly costly agents [1, 23].

## 2. Survey: coding-agent benchmarks

**SWE-bench** (Princeton/Stanford, 2023) established the template: 2,294 real GitHub issues from 12 Python repos, graded by the repo's own FAIL_TO_PASS and PASS_TO_PASS tests [4]. **SWE-bench Verified** (OpenAI, 2024) human-filtered 500 instances to remove impossible or underspecified tasks [5]. **SWE-bench Multimodal** adds visual, JavaScript-centric issues; **SWE-bench Pro** (Scale AI, 2025) raises difficulty with long-horizon, enterprise-style tasks and a held-out commercial subset [6]. **SWE-bench Live** (Microsoft Research and community, 2025) attacks contamination directly with a monthly-refreshed feed of new issues [7]. All of these grade one thing: did the repo's tests pass. None grades diff size, token spend, or wall clock as a ranked metric, and their leaderboards mix (model, scaffold) pairs, so a score is attributable to neither alone. They are, however, the raw material engine benchmarking needs: real repos, real issues, executable verification.

**Terminal-Bench** (Stanford and the Laude Institute, 2025) measures terminal-native task completion in containers; its 2.0 release ships on **Harbor** [8, 9]. Harbor deserves its own entry: it is a meta-harness from the Terminal-Bench creators for "evaluating and optimizing agents and language models", wrapping third-party benchmarks (Terminal-Bench 2.0, SWE-bench, Aider Polyglot) behind one containerized runner, with the agent scaffold (Claude Code, OpenHands, Codex CLI, and more) selected independently of the `--model` flag [9]. That structure enables matched-model harness comparison, and a 2026 survey names Harbor (with Exgentic) as the first frameworks pushing a unified protocol for general agent assessment [1]. What Harbor does not do: rank efficiency, gate CI on regressions with statistics, or source fresh tasks with reference traces. **Harness-Bench** (2026) is the academic complement: a 6-harness by 8-model factorial over 106 sandboxed tasks (5,194 trajectories) that fixes task, sandbox, budget, timeout, and evaluator while letting each harness keep its native behavior [10]. It is a study rather than an ongoing service, but it is the cleanest matched-model prior art to date, and this paper leans on its design.

**Aider Polyglot** (225 hard Exercism exercises) is honest about being a model benchmark: one fixed harness (Aider), many models, with cost per run displayed [11]. **Commit0** (build a library from scratch against a spec and tests) and **RepoBench** (repo-level completion) sit closer to the model end. **SWE-Gym** and **R2E** are environment generators, aimed at training rather than refereeing [12].

## 3. Survey: general agent benchmarks

**AgentBench** (2023) spans eight environments from OS shells to web shopping [13]. **GAIA** (Meta/HF, 2023) asks 466 tool-requiring questions with unambiguous answers [14]. **WebArena** and **VisualWebArena** grade functional task completion on self-hosted websites [15]; **OSWorld** does the same for 369 tasks on real desktop operating systems [16]. **tau-bench** and **tau2-bench** (Sierra) simulate customer-service conversations with an LLM user and domain policies, and contribute the ecosystem's best reliability statistic: pass^k, the probability that an agent succeeds on all k independent attempts, which exposes flakiness that a single-run pass rate hides [17]. **TheAgentCompany** (CMU, 2024) drops agents into a simulated software company (GitLab, RocketChat, ownCloud) and grades checkpointed long-horizon work with partial credit [18]. **BFCL** (Berkeley) is the standard for function-call correctness, including multi-turn tool use [19]; **ToolBench** covers 16,000+ real APIs [20]. **MLE-bench** (OpenAI) uses 75 Kaggle competitions; **CORE-bench** (Princeton) tests computational reproducibility of real papers [21].

Two observations. First, nearly all of these publish leaderboards keyed by model, with the benchmark's own reference scaffold underneath: they are model benchmarks with agentic tasks. Second, the exceptions prove the demand: **HAL**, the Holistic Agent Leaderboard (Princeton), re-runs (model, scaffold) pairs across many of the benchmarks above and plots accuracy against cost, an explicit two-axis Pareto view [22]. HAL is the closest thing to a public engine-aware leaderboard. It still is not a tool a team can point at its own agent in its own CI, and cost is its only efficiency axis.

## 4. Survey: trace-based evaluation and eval platforms

Trajectory grading has real prior art. **AgentBoard**'s progress rate compares an agent's actual trajectory against an expected one for per-step progress [2, 26]. **T-Eval** decomposes tool use into step-wise next-call alignment [26]. LLM-as-judge trajectory scoring is now a stock feature of eval platforms. What does not exist is what we will call a golden-trace corpus: reference traces from verified, production-merged fixes, published as auditable evidence alongside outcome grades.

The observability and eval platforms are where CI actually happens today. **LangSmith** (LangChain), **Langfuse** (open source), **Braintrust**, **Arize Phoenix** (open source, OpenTelemetry-based), and **W&B Weave** all offer tracing plus dataset-driven evals, and most can fail a CI job on a metric drop [27]. **DeepEval** runs evals as pytest tests; **promptfoo** runs config-driven evals and red-team suites in CI; **OpenAI Evals** seeded the genre [27]. On standards: OpenTelemetry's GenAI semantic conventions are emerging as the de facto wire format for agent traces (spans for model calls and tool executions), and the Model Context Protocol showed that a small interchange spec can reorganize an ecosystem within a year [28]. There is no equivalent interchange standard for benchmark tasks, runs, or verdicts. A 2026 factorial study proposes "Harness Cards", a structured disclosure taxonomy (execution, tool, context, scheduling, observability, verification, governance) for exactly this reason [3].

The platforms' limitation is the mirror image of the benchmarks'. They grade your agent on your dataset with judge-model rubrics: perfect for product regression, but with no held-out verification (the eval data lives in your repo, next to the agent that will be graded on it), no cross-engine comparability, and no shared task corpus, so a score means nothing outside your org.

## 5. Best practices: what a credible agent benchmark must do in 2026

The literature has converged on a checklist, even if no system implements all of it.

1. **Separate the engine from the model, by construction.** Hold one fixed while varying the other; stamp the run; refuse cross-attribution [1, 3, 10].
2. **Held-out verification.** The grader must be absent from the workspace while the agent runs, and immune to anything the agent planted. Benchmarks with repo-native tests (SWE-bench) get this half right; eval platforms mostly do not attempt it [4].
3. **Cost and efficiency as ranked metrics, not footnotes.** Accuracy-cost Pareto curves (AI Agents That Matter, HAL), plus tokens, wall clock, and, we argue, diff size: no surveyed system ranks the size of the change an agent makes, though every reviewer knows a 4-line fix and a 400-line rewrite are not equal [22, 23, 2].
4. **Statistics that respect small n.** Confidence intervals on rates; paired tests for head-to-heads; reliability metrics like pass^k; seeded, reproducible resampling [17, 23].
5. **Contamination control.** Frozen sets decay into training data; live sourcing (SWE-bench Live) with recorded cutoffs is the credible answer [7].
6. **Receipts.** Full transcripts, diffs, manifests, and a reproduce command; disclosure of the harness configuration (Harness Cards) [3].
7. **Run in CI.** A benchmark you run at launch is marketing; a benchmark that fails a pull request is engineering.

## 6. Gap analysis: the four capabilities, and who has them

**(a) Matched-model engine isolation.** Harbor enables it structurally; Harness-Bench and the factorial study execute it as research; HAL reports (model, scaffold) pairs [9, 10, 3, 22]. None operationalizes it as a stamped, enforced property of every published run.

**(b) Efficiency grading beyond cost.** HAL plots cost; Aider Polyglot displays it; tau-bench measures reliability [22, 11, 17]. No surveyed system ranks normalized git-diff size, and only ad hoc reporting covers tokens and wall clock together [2].

**(c) CI regression gating with statistics.** Eval platforms gate CI on judge-scored private datasets; no benchmark harness offers a significance-aware gate over held-out, executable verification [27].

**(d) Live tasks with verified fixes as golden traces.** SWE-bench Live sources fresh issues; nobody promotes fixes upstream, treats maintainer merge as ground truth, and publishes the solving trace as a reference artifact [7].

No system does all four. That is the hole in the landscape, stated with the evidence above.

## 7. Arena, and the Agent Benchmark Protocol

**Arena** (github.com/macanderson/arena, MIT) is our attempt at the first three capabilities, today: two or more coding agents on the same tasks, same model, same budget, same timeout; held-out verification injected only after the agent exits; Wilson intervals, exact McNemar on paired outcomes, and seeded paired-bootstrap CIs on wall-clock, token, and cost deltas; no blended score; full receipts with a one-line reproduce command; and a CI gate (`arena baseline save` / `arena gate --require-significant`) that fails a pull request only when a regression clears interval noise. A Harbor adapter scales the same discipline to SWE-bench Verified with the official containerized verifier [9].

The fourth capability needs a standard more than a product. The **Agent Benchmark Protocol** (draft spec published alongside this paper) defines four interchange schemas: a task manifest, a run configuration, a trace format with per-subagent and per-model attribution, and a verdict format with required statistics. On top of them it specifies a live pipeline: a versioned registry of the top 500 open-source GitHub repositories; seeded random draws of real backlog issues; fixes built and submitted upstream under each repo's contribution rules; maintainer merge as verification; and the solving engine's full trace published as a golden trace beside the frozen task. Replays are graded on resolution first, then efficiency in strict order: smaller normalized diff, then fewer tokens, then less wall clock, then lower cost. Golden traces are evidence and study material, deliberately not the rubric, because trajectory-similarity grading punishes better routes to a passing fix; AgentBoard-style progress metrics are a version 2 question [26]. Contamination is handled by construction: tasks are drawn after candidate model cutoffs, stamped, and retired from the scored set 180 days after their fix goes public.

Why a protocol rather than another leaderboard: the measurement problem is an interoperability problem. Tasks, runs, traces, and verdicts need to move between task authors, engines, harnesses, and auditors, exactly as context moves between hosts and tools under MCP [28]. Arena is the reference implementation, not the standard; the standard is the four schemas and the conformance suite.

## 8. Limitations

This survey characterizes fast-moving systems from their public documentation as of July 2026; version specifics will drift. The 7.8x variance ratio comes from one study on one benchmark family and one task size; it needs replication, though its direction agrees with SWE-agent, Agentless, and Harness-Bench [3, 24, 25, 10]. Diff-size ranking is a proxy for surgical precision, not design quality, and is honest only with the normalization and disqualification rules the spec defines. And the author's conflict of interest is real: the reader should treat Section 7 as a proposal to be attacked, with the receipts to attack it.

## References

1. Yehudai et al., *Survey on Evaluation of LLM-based Agents*, v2 (2026). arxiv.org/abs/2503.16416
2. *A Survey of AI Agent Evaluation* (2025). arxiv.org/abs/2507.21504
3. *Harness variance factorial study: Harness Cards and ETCSOVG taxonomy* (2026). arxiv.org/abs/2605.23950
4. Jimenez et al., *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* (2023). arxiv.org/abs/2310.06770
5. OpenAI, *Introducing SWE-bench Verified* (2024). openai.com/index/introducing-swe-bench-verified
6. Scale AI, *SWE-bench Pro* (2025). github.com/scaleapi/SWE-bench_Pro-os
7. *SWE-bench Live* (2025). swe-bench-live.github.io
8. Terminal-Bench (2025). tbench.ai
9. Harbor Framework (2026). github.com/harbor-framework/harbor
10. *Harness-Bench* (2026). arxiv.org/abs/2605.27922
11. Aider Polyglot leaderboard. aider.chat/docs/leaderboards
12. SWE-Gym: github.com/SWE-Gym · R2E: r2e.dev · Commit0: github.com/commit-0/commit0 · RepoBench (2023)
13. Liu et al., *AgentBench* (2023). arxiv.org/abs/2308.03688
14. Mialon et al., *GAIA* (2023). arxiv.org/abs/2311.12983
15. Zhou et al., *WebArena* (2023). arxiv.org/abs/2307.13854
16. Xie et al., *OSWorld* (2024). arxiv.org/abs/2404.07972
17. Yao et al., *tau-bench* (2024). arxiv.org/abs/2406.12045 · tau2-bench: github.com/sierra-research/tau2-bench
18. Xu et al., *TheAgentCompany* (2024). arxiv.org/abs/2412.14161
19. Berkeley Function-Calling Leaderboard. gorilla.cs.berkeley.edu/leaderboard.html
20. Qin et al., *ToolLLM/ToolBench* (2023). arxiv.org/abs/2307.16789
21. OpenAI, *MLE-bench* (2024). arxiv.org/abs/2410.07095 · CORE-bench (Princeton, 2024)
22. HAL: Holistic Agent Leaderboard (Princeton). hal.cs.princeton.edu
23. Kapoor et al., *AI Agents That Matter* (2024). arxiv.org/abs/2407.01502
24. Yang et al., *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering* (2024). arxiv.org/abs/2405.15793
25. Xia et al., *Agentless* (2024). arxiv.org/abs/2407.01489
26. Ma et al., *AgentBoard* (2024). arxiv.org/abs/2401.13178 · T-Eval (2023). arxiv.org/abs/2312.14033
27. LangSmith: smith.langchain.com · Langfuse: langfuse.com · Braintrust: braintrust.dev · Arize Phoenix: phoenix.arize.com · W&B Weave: wandb.ai · DeepEval: github.com/confident-ai/deepeval · promptfoo: promptfoo.dev · OpenAI Evals: github.com/openai/evals
28. Model Context Protocol. modelcontextprotocol.io · OpenTelemetry GenAI semantic conventions. opentelemetry.io

---

*Companion documents: the [Agent Benchmark Protocol draft spec](agent-benchmark-protocol.md) and [Arena's methodology](../METHODOLOGY.md). Corrections: open an issue with the `paper` label.*
