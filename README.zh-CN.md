# Agentic Dev Kit

面向 coding agent 改动交付的本地证据工具集。首个能力 **Staged Scope**
检查下一次提交的暂存文件是否落在任务允许的范围内。

小修复可能夹带 CI、配置或无关模块改动。这里直接读取 Git index，给出每个
路径的判定和可用于门禁的退出码，适用于 Claude Code、Codex 和其他 CLI agent。

## 能力矩阵

| 能力 | 类型 | 输入 → 输出 | 状态 |
| --- | --- | --- | --- |
| [Staged Scope](capabilities/cli/staged-scope/README.zh-CN.md) | 开发者自动化 CLI | Git index + 字面路径白名单 → JSON 判定、退出码 | v0.1.0 已实现 |

该仓库作为后续能力的统一安装、贡献和发布入口。新增能力须有真实工程用途和
可运行检查；现有独立项目不在本次迁移范围内。

## 安装与五分钟开始

需要 Python 3.11+、PATH 中的 Git，无运行时 Python 依赖、无需 API key。

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.1.0
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
```

演示在临时 Git 仓库内生成 payment 修复和额外 CI 文件，依次验证空 index、
越界拒绝、撤去 CI 暂存后的通过。不会改动当前仓库；临时示例在退出时清理。
也可在克隆根目录用 `python3.11 -m agentic_devkit.staged_scope` 运行源码。

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

MIT；[贡献指南](CONTRIBUTING.md)、[CHANGELOG](CHANGELOG.md)、
[趋势与竞品](docs/research-2026-09-16.md)、[验证记录](docs/validation-2026-09-16.md)、
[中英文推广文案](PROMOTION.md)。
