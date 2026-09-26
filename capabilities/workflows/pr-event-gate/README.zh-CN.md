# PR Event Gate

将 coding agent 的 PR 检查绑定到 GitHub `pull_request` 事件中的提交，再应用
base commit 原有的仓库策略。

[English](README.md) · [工具集首页](../../../README.zh-CN.md)

## 问题与五分钟开始

直接运行 `policy-gate --base origin/main --head HEAD` 时，CI 可能误用旧 base、
提交者指定的 ref，或 GitHub 默认 checkout 的合并提交。PR Event Gate 从事件
文件读取 base/head SHA，要求工作区 HEAD 与事件 head 完全一致，再执行既有
Policy Gate。这是可运行的 CLI 加可复用 workflow，不只是提示词或配置示意。

1. 在受保护 base 分支提交 [Policy Gate 的六字段策略](../../cli/policy-gate/README.zh-CN.md)
   `.agentic-dev-kit/policy.json`。
2. 将 [`caller.yml`](caller.yml) 复制到你的仓库
   `.github/workflows/agent-pr-policy.yml`。
3. 开 PR，确认结果后将页面显示的实际检查名称设为 required check。

设置后可用 [Required Check Audit](../../cli/required-check-audit/README.zh-CN.md)
核对该检查是否真的被要求通过。

Caller 调用本仓库的版本化
[`pr-event-gate.yml`](../../../.github/workflows/pr-event-gate.yml)：安装已发布
CLI、按事件 head SHA checkout 完整历史、不保留凭据，然后运行 `pr-event-gate .`。
权限仅 `contents: read`。不要改为 `pull_request_target`、转发 secrets 或在该
job 中运行候选代码。可按供应链要求进一步将标签及 Actions 固定到 commit SHA。

本地安装与可复现演示：

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.7.0
git clone --branch v0.7.0 --depth 1 https://github.com/Amossse/agentic-dev-kit.git
cd agentic-dev-kit
python3.11 examples/pr_event_gate_demo.py --installed
```

预期与实际输出见 `examples/pr_event_gate_expected.json`：

```jsonl
{"exit": 0, "rejected_reasons": [], "state": "approved", "step": "small_fix"}
{"exit": 2, "rejected_reasons": [], "state": "error", "step": "wrong_checkout"}
{"exit": 1, "rejected_reasons": ["outside_scope"], "state": "rejected", "step": "outside_scope"}
```

本地排障可指定 `pr-event-gate . --event ./event.json --event-name pull_request`；
在 Actions 中默认读 `GITHUB_EVENT_PATH` 和 `GITHUB_EVENT_NAME`。退出码 0
为非空通过、1 为策略拒绝、2 为事件/输入/Git 错误、3 为空 diff。stdout 是
Policy Gate JSON，stderr 是简短状态或错误。

## 架构、配置与限制

CLI 仅接受 `pull_request`，事件 JSON 最大 1 MiB，拒绝重复键，base/head
须为小写 40/64 位十六进制 SHA。校验当前 HEAD 后复用 Policy Gate，从 base
commit 读取策略，并按 merge-base 到 head 的 diff 检查路径和规模。无需新增
策略格式或 API。配置项是 base 策略、required check 与仓库保护规则。

- 本地 `--event` 可伪造；CI 的信任来自 GitHub 事件文件、可信 workflow、
  指定 toolkit 版本和受保护 base。CLI 自身不能认证 GitHub 身份。
- 不运行项目测试或候选代码；读取 Git 历史。请使用隔离 runner，审阅依赖与
  Actions 后才考虑授予其他权限，且不要向本 job 提供 secrets。
- 不支持用 `pull_request_target` 加不可信 checkout 获得提权。需由仓库设置
  required check、CODEOWNERS 和策略更新例外；本 CLI 不会设置这些权限。
- 缺少 base 对象、浅克隆、JSON 格式错误或 checkout 不匹配时显式失败。
  Fork PR 是否能获取事件 SHA 与历史，取决于实际 checkout 配置。
- 输出包含路径和 commit ID，分享前请审阅；策略与 fixture 不要包含密钥或
  个人信息。演示只创建临时合成 Git 仓库。

运行时仅依赖 Python 3.11+ 标准库及 Git。复用 workflow 需 runner 能安装
指定版本；本地合成演示不等于已在其他仓库验证 required check 或 fork PR。

## 贡献与搜索入口

MIT 许可；参见[贡献指南](../../../CONTRIBUTING.md)、[更新记录](../../../CHANGELOG.md)、
[趋势研究](../../../docs/research-2026-09-25.md)、[验证记录](../../../docs/validation-2026-09-25.md)
和[未代发文案](../../../PROMOTION.md)。修改事件信任或 checkout 语义时，请提供
合成事件和 Git 历史回归用例。

建议 topics：`github-actions`、`pull-request-security`、`coding-agents`、
`agent-policy`、`code-review-automation`。搜索词：PR 可信 base SHA、
coding-agent CI 门禁、GitHub PR 策略检查。
