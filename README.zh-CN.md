# Agentic Dev Kit

面向 coding agent 改动交付的本地证据工具集：检查**改了什么**、是否仍可评审，
当前状态是否仍是**测试通过时的状态**，并将这些证据收束为可复验交接。

小修复可能夹带 CI、配置或无关模块改动。工具分别检查 Git index、提交范围、
测试凭证与仓库策略，给出可用于门禁的证据和退出码，适用于 Claude Code、Codex
和其他 CLI agent。

## 能力矩阵

| 能力 | 类型 | 输入 → 输出 | 状态 |
| --- | --- | --- | --- |
| [Staged Scope](capabilities/cli/staged-scope/README.zh-CN.md) | 开发者自动化 CLI | Git index + 字面路径白名单 → JSON 判定、退出码 | v0.1.0 已实现 |
| [Range Scope](capabilities/cli/range-scope/README.zh-CN.md) | CI / PR CLI | base + head → merge-base 路径判定、退出码 | v0.2.0 已实现 |
| [Test Proof](capabilities/cli/test-proof/README.zh-CN.md) | 测试证据 CLI | 测试命令 + Git 状态 → 可复验凭证、过期门禁 | v0.3.0 已实现 |
| [Diff Budget](capabilities/cli/diff-budget/README.zh-CN.md) | 评审规模 CLI | merge-base diff + 数字预算 → 逐文件证据、退出码 | v0.4.0 已实现 |
| [Handoff Proof](capabilities/cli/handoff-proof/README.zh-CN.md) | 交接证据 CLI | 任务策略 + 三项 gate → 状态绑定清单 | v0.5.0 已实现 |
| [Policy Gate](capabilities/cli/policy-gate/README.zh-CN.md) | PR 策略 CLI | base commit 策略 + 分支 diff → 路径与规模判定 | v0.6.0 已实现 |
| [PR Event Gate](capabilities/workflows/pr-event-gate/README.zh-CN.md) | GitHub PR 工作流 + CLI | PR 事件 SHA + checkout HEAD + base 策略 → CI 判定 | v0.7.0 已实现 |

该仓库作为后续能力的统一安装、贡献和发布入口。新增能力须有真实工程用途和
可运行检查；现有独立项目不在本次迁移范围内。

## 安装与五分钟开始

需要 Python 3.11+、PATH 中的 Git，无运行时 Python 依赖、无需 API key。

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.7.0
git status --short
git diff --cached
staged-scope . --allow src/payments/ --allow tests/test_payments.py
```

`--allow` 是相对于仓库根目录的字面路径；结尾 `/` 表示目录内的所有后代文件，
否则只匹配一个文件，不支持 glob。嵌套目录运行也检查整个仓库 index。

stdout 输出 JSON，stderr 只输出状态和数量。退出码 `0`：非空且全部通过；
`1`：越界或未解决冲突；`2`：输入/Git 错误；`3`：没有暂存改动。

完整可复现演示：

```bash
git clone https://github.com/Amossse/agentic-dev-kit.git
cd agentic-dev-kit
python3.11 examples/staged_scope_demo.py --installed
python3.11 examples/range_scope_demo.py --installed
```

演示在临时 Git 仓库内生成 payment 修复和额外 CI 文件，依次验证空 index、
越界拒绝、撤去 CI 暂存后的通过。不会改动当前仓库；临时示例在退出时清理。
也可在克隆根目录用 `python3.11 -m agentic_devkit.staged_scope` 运行源码。

已提交分支或 PR 使用：

```bash
range-scope . --base origin/main --head HEAD --allow src/payments/ --allow tests/
```

它按 merge-base 到候选 head 检查，不把 base 后续新增的改动算进候选分支。

把真实测试结果绑定到当前 Git 状态：

```bash
test-proof run . -- python -m unittest
test-proof verify .
```

凭证默认位于 Git 元数据目录。之后出现已跟踪改动、commit 或未跟踪文件时，
验证会失败。输入输出和 before/after 演示见 [Test Proof](capabilities/cli/test-proof/README.zh-CN.md)。

按仓库策略拒绝过大的 agent 分支：

```bash
diff-budget . --base origin/main --head HEAD --max-files 10 --max-lines 400
```

fixture、二进制策略和 CI 示例见 [Diff Budget](capabilities/cli/diff-budget/README.zh-CN.md)。

把路径范围、评审预算和当前 Test Proof 收束成一份可重跑交接清单：

```bash
handoff-proof create . --task "Fix payment rounding" --base origin/main \
  --allow src/payments/ --allow tests/ --max-files 10 --max-lines 400
handoff-proof verify .
```

拒绝、通过和过期演示见 [Handoff Proof](capabilities/cli/handoff-proof/README.zh-CN.md)。

用 base 分支既有策略检查待合并 PR：

```bash
policy-gate . --base origin/main --head HEAD
```

先把 `.agentic-dev-kit/policy.json` 提交到 base 分支；schema、CI 示例与演示见
[Policy Gate](capabilities/cli/policy-gate/README.zh-CN.md)。

将 GitHub PR 事件 SHA 与 checkout HEAD 绑定，并复用 base 策略时，使用
[PR Event Gate](capabilities/workflows/pr-event-gate/README.zh-CN.md) 的
caller workflow；确认结果后可将其设为 required check。

## 实现、安全与限制

通过固定 Git 命令读取 HEAD 与 index 的 NUL 分隔路径状态，关闭重命名合并，
因此移动文件的删除端和新增端都要通过。保留原始路径字节的 base64 表示，避免
特殊文件名和显示转义造成歧义。

CLI 只读、离线，不运行 hook、外部 diff/textconv、模型或用户代码。输出文件名
和范围可能包含敏感信息，请审阅后再分享。使用可信 Git 和工作树；此工具不提供
恶意仓库沙箱。示例脚本会在临时仓库写入合成文件。

只检查暂存路径，不覆盖未暂存/未跟踪改动、语义正确性和编辑归属。已有暂存内容
需要先审阅；检查后 index 仍可能变化，应重新检查再提交。普通 CI checkout
没有暂存改动，需由任务明确构造 index 后才适用。详细规则见模块文档。

Test Proof 只执行 `--` 后的显式参数数组，但命令会继承用户环境且不受沙箱保护。
凭证只证明退出码和所表示 Git 状态一致，不证明测试质量或外部服务稳定。命令
参数会进入凭证，禁止把密钥放在命令行中。

Diff Budget 把规模当成策略信号，不当成质量分。rename 两端都计数，二进制默认
拒绝；是否允许例外仍由团队和仓库策略决定。

Handoff Proof 只记录并重跑这些本地策略，不签名、不批准策略严格性、
不校验人工 task 文本，也不替代 SLSA、in-toto、GitHub attestation 或 Owner 评审。

Policy Gate 从调用者指定的 base commit 读取策略。要形成 Owner 控制的合并门禁，
CI 需使用可信 base SHA，并设置 required check 和 CODEOWNERS 或等效审阅。

PR Event Gate 校验事件字段与 checkout 一致性，但无法认证本地提供的事件文件，
也无法配置 GitHub 分支保护。复用 workflow 只用 `pull_request` 和只读权限，
不运行候选代码或索取 secrets；使用前仍需审阅版本化依赖。

MIT；[贡献指南](CONTRIBUTING.md)、[CHANGELOG](CHANGELOG.md)、
[最新趋势与竞品](docs/research-2026-09-25.md)、[最新验证记录](docs/validation-2026-09-25.md)、
[中英文推广文案](PROMOTION.md)。
