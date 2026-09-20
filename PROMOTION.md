# Prepared launch copy — not posted

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

Description: `Local evidence gates for coding-agent changes: staged Git scope, literal paths, reproducible handoffs`

Suggested topics: `claude-code`, `ai-agents`, `developer-tools`, `git`, `code-review`,
`python-cli`, `agentic-workflows`.

Queries: Claude Code workflow, staged commit scope, coding agent handoff, monorepo
change gate, agentic developer toolkit. Main README → capability page → pinned
install → before/after example → issues/PRs. Copy is for manual publication only.
