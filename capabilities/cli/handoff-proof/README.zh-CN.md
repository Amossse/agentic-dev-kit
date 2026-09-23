# Handoff Proof

把 coding agent 的“已完成”摘要转成一份绑定 Git 状态、可重新执行的交接清单。

## 问题

“只改了 `src/`、改动不大、测试通过”实际包含三个可独立过期的声明。
评审者往往需要重新寻找原始路径规则、规模预算、测试凭证与 Git 状态。

Handoff Proof 一次执行 Range Scope、Diff Budget 和 Test Proof，记录原始策略
及证据；复验时用原策略重跑三项检查。它不收集会话轨迹，不是 agent
memory，也不冒充签名供应链 attestation。

[English](README.md) · [工具集首页](../../../README.zh-CN.md)

## 五分钟开始

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.5.0
test-proof run . -- python -m unittest
handoff-proof create . \
  --task "Fix payment rounding" \
  --base origin/main \
  --allow src/payments/ --allow tests/ \
  --max-files 10 --max-lines 400
handoff-proof verify .
```

只有三项 gate 全部通过，`create` 才返回 `0` 并写清单。默认位置是
`.git/agentic-dev-kit/handoff-proof.json`，因此写入本身不会让 Test Proof 过期。
同一 JSON 也会输出到 stdout；需要显式便携文件时可用 `--output /tmp/handoff.json`，
并通过 `verify --manifest /tmp/handoff.json` 复验。

可复现演示：

```bash
python3.11 examples/handoff_proof_demo.py --installed
```

预期与实际输出：

```jsonl
{"exit": 1, "state": "rejected", "step": "wrong_scope"}
{"exit": 0, "state": "approved", "step": "create"}
{"exit": 0, "state": "valid", "step": "verify"}
{"exit": 1, "state": "stale", "step": "edit_then_verify"}
```

固定 fixture 见 [`examples/handoff_proof_expected.json`](../../../examples/handoff_proof_expected.json)。

## 命令与配置

```text
handoff-proof create [REPOSITORY] --task TEXT --base REV [--head REV]
  --allow PATH [--allow PATH ...] --max-files N --max-lines N
  [--max-file-lines N] [--allow-binary]
  [--test-receipt PATH] [--output PATH]

handoff-proof verify [REPOSITORY] [--manifest PATH]
```

- `--allow`、`--base`、`--head` 沿用 Range Scope 语义。
- 数字预算与二进制策略沿用 Diff Budget 语义。
- `--test-receipt` 选择 Test Proof 凭证；不传则使用 Git 元数据下的默认凭证。
- `--task` 必填，限 500 字符；它是交接上下文，不是从 diff 推导的事实。
- 自定义清单只能位于工作树外或 Git 元数据中，避免清单自己污染被验证状态。

退出码：`0` 通过；`1` 拒绝或过期；`2` 输入、JSON、I/O 或 Git 错误。
创建失败会输出三项证据，但不覆盖上一份已通过清单。

## 架构与实现

1. 校验 task、仓库、字面路径、revision 和预算。
2. 对 merge-base 到 head 运行 Range Scope。
3. 对同一范围运行 Diff Budget。
4. 将 Test Proof 凭证与当前 HEAD 和工作状态比较。
5. 仅在三项都返回零时，原子写入策略和完整报告。
6. `verify` 校验最大 2 MiB 的 JSON schema，重跑原策略，并要求当前报告与记录完全一致。

运行时仍只依赖 Python 标准库和 Git。不通过 shell 调用三个 CLI，而是复用
已校验实现，保留固定 Git 参数、NUL-safe 解析、资源上限与退出语义。

## 安全、隐私与限制

- 离线运行，不请求模型/API，不 fetch、checkout、commit 或 push。
- Handoff Proof 本身不执行测试；Test Proof 早先执行的命令不受沙箱保护。
- 清单包含 task、允许路径、commit ID、变更路径、规模数据和测试命令元数据。
  公开前必须审阅，不得放入密钥、个人信息和机密任务文本。
- 通过只证明三项本地检查仍产生记录结果，不证明正确性、任务完整性、归属、
  测试质量、覆盖率或可部署性。
- task 是创建者声明，工具不校验它是否与 diff 一致。
- JSON 未签名，可写者能伪造。对抗性信任应使用 GitHub artifact attestation、
  in-toto、SLSA 或签名。
- 复验沿用清单内策略，不证明该策略足够严格或已被仓库 Owner 批准。
- 忽略文件、外部服务、环境状态与测试质量不在证据内。

## 贡献与搜索入口

MIT 许可。参见 [贡献指南](../../../CONTRIBUTING.md)。请提供合成仓库、完整策略、
各组件预期结果和最终交接状态，不得附带私有代码、生产路径或凭据。

搜索词：coding agent 交接清单、agent 证据 manifest、Claude Code 工作流、
Git 状态凭证、AI PR 门禁、测试凭证、评审策略自动化。
