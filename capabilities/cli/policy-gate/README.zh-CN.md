# Policy Gate

用 base commit 已存在的仓库策略检查 coding agent 提交的分支。

## 问题

Handoff Proof 的创建者可以自行填写允许路径和规模阈值。PR 场景中，同一位改动
提交者不应单独决定检查自己的规则。Policy Gate 从指定 base commit 读取
`.agentic-dev-kit/policy.json`，检查 merge-base 到 head 的 diff，并拒绝同一
分支修改策略文件。

[English](README.md) · [工具集首页](../../../README.zh-CN.md)

## 五分钟开始

需要 Python 3.11+ 和 Git。安装固定版本：

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.6.0
```

先在受保护的 base 分支提交 `.agentic-dev-kit/policy.json`：

```json
{
  "schema_version": 1,
  "allow": ["src/", "tests/"],
  "max_files": 10,
  "max_lines": 400,
  "max_file_lines": 200,
  "allow_binary": false
}
```

再检查待合并分支：

```bash
policy-gate . --base origin/main --head HEAD
```

退出码 `0`：非空且通过；`1`：拒绝；`2`：策略、输入或 Git 错误；`3`：空 diff。
缺失或格式错误的 base 策略会显式返回 `2`。stdout 是稳定 JSON，stderr 是状态摘要。

可复现演示：

```bash
python3.11 examples/policy_gate_demo.py --installed
```

预期与实际输出：

```jsonl
{"exit": 0, "rejected_reasons": [], "state": "approved", "step": "small_fix"}
{"exit": 1, "rejected_reasons": ["budget_exceeded"], "state": "rejected", "step": "oversized"}
{"exit": 1, "rejected_reasons": ["policy_changed", "outside_scope", "budget_exceeded"], "state": "rejected", "step": "policy_edit"}
```

结果 fixture 见 [`examples/policy_gate_expected.json`](../../../examples/policy_gate_expected.json)。

## 配置与 CI

JSON 恰好包含上述六个字段。`allow` 是 1–100 条相对仓库根目录的字面文件路径
或以 `/` 结尾的目录路径，不支持 glob。整数阈值范围为 0–1,000,000,000；
`max_file_lines` 可为 `null`。二进制默认拒绝，放行后仍计文件数；rename 两端
都计数。请按仓库历史和评审习惯确定阈值。

策略位置固定。`--head` 默认 `HEAD`；`--base` 必须来自可信 CI 事件：

```yaml
- uses: actions/checkout@v5
  with:
    fetch-depth: 0
    ref: ${{ github.event.pull_request.head.sha }}
- run: pip install git+https://github.com/Amossse/agentic-dev-kit.git@v0.6.0
- run: policy-gate . --base ${{ github.event.pull_request.base.sha }} --head HEAD
```

把 CI 检查设为 required，并用 CODEOWNERS 审阅策略文件与 workflow 修改。有意更新
策略时需要管理员控制的例外或独立可信更新流程，因为普通候选 PR 修改策略文件必被
此检查拒绝。本 CLI 不修改 GitHub 权限。

## 架构与实现

1. 把 base/head 解析成不可变 commit ID。
2. 从 base commit 读取固定路径的策略 blob，最多 64 KiB；严格校验 JSON
   字段，并对原始 blob 做 SHA-256 供审计。
3. 复用 Range Scope 和 Diff Budget，对相同的 merge-base 到 head 范围检查
   路径与规模。
4. 只要本次 diff 包含策略文件，就拒绝，即使父目录被允许。

运行时只依赖 Python 标准库和 Git；使用固定的只读 Git 命令，不 fetch、checkout、
运行 hook、请求模型或网络，也不运行用户代码。

## 安全、隐私与限制

- 调用者可以指定不真实的 `--base`。本地结果仅供参考；CI 应从可信事件取 base
  commit，并要求该检查通过才能合并。
- 工具不认证谁创建或批准了 base 策略。此信任边界由分支保护、required checks
  和 CODEOWNERS 提供。
- 策略更新需要管理员控制的例外或可信更新流程；普通 PR 修改策略文件必定失败。
- 输出含路径、commit ID 和策略 hash，分享前审阅；策略中不要放密钥或个人信息。
- 只检查已提交的分支改动，不包含未暂存或已暂存的本地改动，也不证明正确性、
  测试覆盖率或语义安全。
- 浅克隆缺少历史会显式失败，工具不会 fetch。请使用可信 Git 和仓库；不提供沙箱。

## 贡献与搜索入口

MIT 许可。参见[贡献指南](../../../CONTRIBUTING.md)、[更新记录](../../../CHANGELOG.md)、
[趋势研究](../../../docs/research-2026-09-24.md)、[验证记录](../../../docs/validation-2026-09-24.md)
和[待发布文案](../../../PROMOTION.md)。修改解析或门禁语义时，请附合成 Git 历史
与完整策略，不要提交私有仓库路径和凭据。

建议 topics：`agent-policy`、`coding-agents`、`claude-code`、
`code-review-automation`、`git`、`developer-tools`。搜索词：base 分支策略、
AI PR 路径门禁、coding agent policy as code、代码改动行数预算。
