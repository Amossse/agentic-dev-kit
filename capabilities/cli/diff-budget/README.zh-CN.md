# Diff Budget

在 coding-agent 分支变成评审负担之前拦截超大改动。

## 问题

路径白名单能发现越界文件，但 agent 仍可能在允许目录内重写数千行。Diff Budget
从分支 merge-base 统计改动文件与文本行数，并应用显式 review 预算。

规模只是评审成本的代理指标：小改动也可能危险，大型机械修改也可能安全。这个
工具让团队策略可见、可执行，不声称存在通用正确阈值。

[English](README.md) · [工具集首页](../../../README.zh-CN.md)

## 五分钟开始

需要 Python 3.11+ 与 Git：

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.4.0
diff-budget . --base origin/main --head HEAD --max-files 10 --max-lines 400
```

退出码：`0` 非空且在预算内；`1` 至少一个预算超限；`2` 输入、历史或 Git
错误；`3` 没有改动。stdout 输出 JSON，stderr 仅输出计数摘要。

运行临时仓库 before/after 演示：

```bash
python3.11 examples/diff_budget_demo.py --installed
```

预期及实际输出：

```jsonl
{"changed_lines": 0, "exit": 3, "files": 0, "rejected_reasons": [], "state": "empty"}
{"changed_lines": 8, "exit": 1, "files": 2, "rejected_reasons": ["file_limit", "line_limit"], "state": "rejected"}
{"changed_lines": 2, "exit": 0, "files": 1, "rejected_reasons": [], "state": "approved"}
```

拒绝分支包含两行 payment 修复和六行意外生成文件；通过分支只保留 payment 修改。
固定结果见 [`examples/diff_budget_expected.json`](../../../examples/diff_budget_expected.json)。

## 配置与 CI

```text
diff-budget [REPOSITORY] --base REV [--head REV]
  --max-files N --max-lines N [--max-file-lines N] [--allow-binary]
```

- `--max-files` 限制全部路径数。关闭重命名识别，因此 rename 按删除和新增计两项。
- `--max-lines` 限制所有文本文件的新增行加删除行。
- `--max-file-lines` 可选，限制单个文本文件的新增行加删除行。
- 默认拒绝二进制文件，因为 Git 没有有意义的行数。`--allow-binary` 放行后仍计
  文件数，但按零行计算。
- 阈值范围为 `0` 到 `1,000,000,000`；`--head` 默认 `HEAD`。revision 采用
  Range Scope 相同的安全单 commit 规则。

GitHub PR 示例：

```yaml
- uses: actions/checkout@v5
  with:
    fetch-depth: 0
    ref: ${{ github.event.pull_request.head.sha }}
- run: pip install git+https://github.com/Amossse/agentic-dev-kit.git@v0.4.0
- run: diff-budget . --base ${{ github.event.pull_request.base.sha }} --head HEAD --max-files 20 --max-lines 600 --max-file-lines 300
```

阈值应来自仓库历史和实际评审习惯，不要直接复制示例。例外应在 workflow 或评审
策略中显式声明，不能藏进生成代码。

## 架构与实现

标准库实现解析 base/head commit，计算 merge-base，再执行固定的 `git diff
--numstat -z --no-renames`。NUL parser 保留路径原始字节的 base64，校验 framing
和行数，并识别 Git 的 `-/-` 二进制记录。JSON 返回预算、实测总量、每个路径和
稳定的拒绝原因。

Git 使用参数数组且 `shell=False`，清除继承的 `GIT_*` 覆盖，禁用全局/系统配置、
fsmonitor、external diff、textconv 和 rename detection，并设置 10 秒、10 MiB
边界。不 fetch、checkout、commit，不运行 hook、模型、API 或仓库代码。

## 安全、隐私与限制

- 输出包含改动路径和 commit ID，公开前必须审阅 JSON。
- 只对可信 Git 和仓库使用；它是只读门禁，不是恶意 Git 对象或配置的沙箱。
- 缺失、浅克隆、不相关或异常历史会显式失败；命令不 fetch，也不接收仓库凭据。
- 忽略工作树未提交和仅暂存改动；提交前使用 Staged Scope，路径归属使用 Range Scope。
- 改动行数只是 Git numstat 的新增加删除，不代表复杂度、语义风险、生成代码、
  覆盖率或真实评审成本。
- 二进制文件没有行数；放行后二进制会让行数预算不完整。
- rename 两端都计数，机械移动也可能超限。
- 工具不会拆分分支、批准 PR 或判断例外是否合理；通过只证明数字未超配置阈值。
- 上限为 10,000 条记录、10 MiB Git 输出、单次 Git 命令 10 秒。演示为合成数据。

## 贡献与搜索入口

[贡献指南](../../../CONTRIBUTING.md) · [MIT](../../../LICENSE) ·
[CHANGELOG](../../../CHANGELOG.md) · [趋势研究](../../../docs/research-2026-09-22.md)
· [验证记录](../../../docs/validation-2026-09-22.md) ·
[待发布推广文案](../../../PROMOTION.md)。

搜索词：AI PR 大小门禁、coding agent diff 预算、改动行数 CI、可评审 PR 自动化、
Git numstat 检查、Claude Code 交付。
