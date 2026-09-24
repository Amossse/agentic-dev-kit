# Prepared launch copy — not posted

## v0.6.0 English

**Agentic Dev Kit v0.6.0 adds Policy Gate for coding-agent PRs.**

A change author can choose permissive `--allow` paths and budgets. Policy Gate
reads `.agentic-dev-kit/policy.json` from the selected base commit, checks the
candidate branch against it, and rejects a policy edit in the same PR. It reuses
the toolkit's Range Scope and Diff Budget checks.

```bash
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.6.0 policy-gate . --base origin/main --head HEAD
```

Python stdlib + Git, offline and read-only. Use a trusted PR base SHA, a required
CI check, and owner review for the policy and workflow. The CLI does not verify
GitHub identities or set branch protection.

Repository: https://github.com/Amossse/agentic-dev-kit
Release: https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.6.0

## v0.6.0 中文

**Agentic Dev Kit v0.6.0 新增 coding-agent PR 仓库策略门禁 Policy Gate。**

改动提交者可以把 `--allow` 路径和规模阈值设得很宽。Policy Gate 从指定 base
commit 读取 `.agentic-dev-kit/policy.json`，按 base 原有策略检查候选分支，
并拒绝在同一 PR 中改策略。路径与规模检查复用 Range Scope 和 Diff Budget。

```bash
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.6.0 policy-gate . --base origin/main --head HEAD
```

Python 标准库 + Git，离线只读。CI 应使用可信 PR base SHA、required check，
并由 Owner 审阅策略和 workflow。CLI 不认证 GitHub 身份，也不设置分支保护。

仓库：https://github.com/Amossse/agentic-dev-kit
版本：https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.6.0

---

## v0.5.0 English

**Agentic Dev Kit v0.5.0 adds Handoff Proof for state-bound agent delivery.**

"Changed only the intended files, stayed reviewable, tests passed" is three
claims that can drift independently. Handoff Proof runs the toolkit's Range
Scope, Diff Budget and Test Proof together, records the exact policy and evidence,
then re-runs it when a reviewer or successor agent verifies the handoff.

```bash
test-proof run . -- python -m unittest
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.5.0 handoff-proof create . --task "Fix payment rounding" --base origin/main --allow src/ --allow tests/ --max-files 10 --max-lines 400
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.5.0 handoff-proof verify .
```

Python stdlib + Git, local and provider-neutral. It does not collect transcripts,
call a model, or claim signed provenance. The task text and policy are creator
assertions; use SLSA, in-toto or GitHub attestations when adversarial trust matters.

Repository: https://github.com/Amossse/agentic-dev-kit
Release: https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.5.0

## v0.5.0 中文

**Agentic Dev Kit v0.5.0 新增状态绑定的 agent 交接门禁 Handoff Proof。**

“只改了预期文件、规模可评审、测试通过”是三个可独立过期的声明。
Handoff Proof 联合执行 Range Scope、Diff Budget 和 Test Proof，记录原始
策略与证据；评审者或后续 agent 可按同一策略复验。

```bash
test-proof run . -- python -m unittest
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.5.0 handoff-proof create . --task "Fix payment rounding" --base origin/main --allow src/ --allow tests/ --max-files 10 --max-lines 400
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.5.0 handoff-proof verify .
```

Python 标准库 + Git，本地运行且与 agent 平台无关。不收集会话、不请求模型、
不冒充签名凭证。task 与策略由创建者声明；对抗性信任请使用 SLSA、
in-toto 或 GitHub attestation。

仓库：https://github.com/Amossse/agentic-dev-kit
版本：https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.5.0

---

## v0.4.0 English

**Agentic Dev Kit v0.4.0 adds Diff Budget for reviewable agent PRs.**

Path scope is not enough: an agent can rewrite 5,000 lines inside an allowed
directory. Diff Budget compares merge-base to branch head, counts files and text
lines, and fails explicit total/per-file budgets with deterministic JSON.

```bash
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.4.0 diff-budget . --base origin/main --head HEAD --max-files 10 --max-lines 400 --max-file-lines 200
```

Python stdlib + Git, offline, read-only, no model or API key. Renames count both
endpoints and binaries fail unless explicitly allowed. Size is a review-cost proxy,
not a code-quality score; choose limits from your repository's history and policy.

Repository: https://github.com/Amossse/agentic-dev-kit
Release: https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.4.0

## v0.4.0 中文

**Agentic Dev Kit v0.4.0 新增 agent PR 评审规模门禁 Diff Budget。**

路径范围通过不代表改动仍可评审：agent 可能在允许目录内重写 5,000 行。Diff
Budget 从 merge-base 检查到 branch head，统计文件数和文本变更行数，用稳定 JSON
和退出码执行总量、单文件及二进制策略。

```bash
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.4.0 diff-budget . --base origin/main --head HEAD --max-files 10 --max-lines 400 --max-file-lines 200
```

Python 标准库 + Git，离线只读，无模型/API key。rename 两端都计数，二进制默认
拒绝。规模只是评审成本代理，不是代码质量分；阈值应来自仓库历史和团队策略。

仓库：https://github.com/Amossse/agentic-dev-kit
版本：https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.4.0

---

## v0.3.0 English

**Agentic Dev Kit v0.3.0 adds Test Proof for coding-agent handoffs.**

Your agent says tests passed, then edits the branch. Test Proof runs your real test
command, fingerprints Git HEAD plus the tracked diff before and after, and writes a
receipt. Verify it later: any tracked edit, commit, or untracked file makes it stale.

```bash
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.3.0 test-proof run . -- python -m unittest
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.3.0 test-proof verify .
```

Python stdlib + Git, offline, provider-neutral, no model or API key. It uses no
shell string, but it does execute the command you provide and is not a sandbox.
The receipt proves an exit code against represented Git state—not test quality,
coverage or external-service reproducibility.

Repository: https://github.com/Amossse/agentic-dev-kit
Release: https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.3.0

## v0.3.0 中文

**Agentic Dev Kit v0.3.0 新增 coding-agent 测试凭证 Test Proof。**

Agent 说测试通过后又改了代码，原结论就已过期。Test Proof 执行真实测试命令，
在前后对 Git HEAD 和已跟踪 diff 做指纹并写入凭证；之后出现已跟踪修改、commit
或未跟踪文件时，复验会直接判定 stale。

```bash
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.3.0 test-proof run . -- python -m unittest
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.3.0 test-proof verify .
```

Python 标准库 + Git，离线、与平台无关，无模型/API key，不执行 shell 字符串。
但它会执行你显式提供的命令，并不是沙箱。凭证只证明退出码对应所表示 Git 状态，
不证明测试质量、覆盖率或外部服务可复现。

仓库：https://github.com/Amossse/agentic-dev-kit
版本：https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.3.0

---

## v0.2.0 English

**Agentic Dev Kit v0.2.0 adds Range Scope for coding-agent PRs.**

Your agent fixed `src/payment.py` and also committed a workflow edit. Range
Scope compares the branch's merge base to its head, checks every raw Git path
against literal file/directory rules, and exits nonzero with deterministic JSON.
Base-branch changes after divergence are excluded. Renames check both endpoints.

```bash
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.2.0 range-scope . --base origin/main --head HEAD --allow src/ --allow tests/
```

Python stdlib + Git, offline and read-only: no model, token, fetch, checkout or
automatic fix. It checks paths rather than correctness or authorship. Try the
three-outcome disposable demo and bring a reproducible CI boundary case.

Repository: https://github.com/Amossse/agentic-dev-kit
Release: https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.2.0

## v0.2.0 中文

**Agentic Dev Kit v0.2.0 新增 coding-agent PR 提交范围门禁。**

Agent 修了 `src/payment.py`，却同时提交了 workflow 文件。Range Scope 从分支
merge-base 检查到候选 head，用字面文件/目录规则判定每个 Git 路径，输出稳定
JSON 和非零退出码；base 分叉后的自身改动不会混入，移动文件两端都需通过。

```bash
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.2.0 range-scope . --base origin/main --head HEAD --allow src/ --allow tests/
```

Python 标准库 + Git，离线只读，无模型、token、fetch、checkout 或自动修复。
只证明路径范围，不判断正确性和编辑归属。欢迎运行三种结果的临时仓库演示，
并提交可复现的 CI 边界案例。

仓库：https://github.com/Amossse/agentic-dev-kit
版本：https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.2.0

---

## English

**Agentic Dev Kit: check the commit your coding agent is about to hand you.**

The first capability, Staged Scope, catches staged files outside an explicit task
scope. A payment rounding fix that also stages a CI edit returns a failing exit;
both sides of a moved file must be allowed. Literal path rules, NUL-safe Git
records, JSON evidence and a disposable three-outcome example. Python stdlib,
no model calls or API keys, no automatic staging or commits.

```bash
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.1.0 staged-scope . --allow src/payments/ --allow tests/test_payments.py
```

Repository: https://github.com/Amossse/agentic-dev-kit
Release: https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.1.0

Scope checks already exist; this is a focused Git-index gate inside a growing
developer toolkit. It checks paths, not correctness or session ownership. Review
existing staged changes first. Try the synthetic CI-edit example and contribute
a reproducible engineering case for the next capability.

## 中文

**Agentic Dev Kit：检查 coding agent 准备交付的暂存改动。**

首个能力 Staged Scope 将 Git index 中的文件逐个与任务允许路径比较。
payment 小修复夹带 CI 文件时直接返回失败；移动文件两端都需要放行。
字面路径、NUL 分隔记录、JSON 证据和三种结果的临时仓库演示，Python 标准库
实现，无需模型/API key，不自动暂存或提交。

```bash
uvx --from git+https://github.com/Amossse/agentic-dev-kit.git@v0.1.0 staged-scope . --allow src/payments/ --allow tests/test_payments.py
```

仓库：https://github.com/Amossse/agentic-dev-kit
版本：https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.1.0

同类范围检查已有方案；这里把 Git index 检查作为持续工具集的首个模块。
只检查路径，不判断代码正确性和编辑归属；已有暂存改动请先审阅。
欢迎跑一次 CI 越界演示，并提交能复现的真实工程需求。

## Metadata and search entry

Title: `Agentic Dev Kit — local evidence gates for coding-agent changes`

Description: `Local scope, review-size, test-evidence, handoff, and policy gates for coding agents`

Suggested topics: `claude-code`, `ai-agents`, `developer-tools`, `git`, `code-review`,
`python-cli`, `agentic-workflows`, `testing`, `test-automation`, `pull-request-size`,
`code-review-automation`, `agent-handoff`, `coding-agents`, `agent-policy`.

Queries: Claude Code workflow, staged commit scope, coding agent handoff, monorepo
change gate, test evidence receipt, stale test result, AI PR size gate, changed
lines budget, coding agent handoff manifest, state-bound agent evidence, agentic
developer toolkit, base-branch agent policy, policy as code for AI PRs.
Main README → capability page → pinned install → before/after example → issues/PRs.
Copy is for manual publication only.
