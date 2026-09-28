# Workflow Run Audit

核对一条 GitHub Actions 运行记录，确认它在指定提交上、由指定 workflow 和事件触发，并且已经成功结束。

[English](README.md) · [工具包](../../../README.zh-CN.md)

## 解决的问题

看到一条绿色 CI 记录，还不能确定它跑的是准备交付的那个提交。这个命令按运行 ID 查询记录，逐项核对提交 SHA、workflow 文件、事件和运行结果。

## 五分钟上手

安装 Python 3.11+ 和 GitHub CLI，运行 `gh auth login` 登录。工具包没有运行时 Python 依赖：

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.10.0
workflow-run-audit OWNER/REPO --run 123456789 --sha FULL_COMMIT_SHA \
  --workflow .github/workflows/ci.yml --event push
```

运行 ID 可从 Actions 页面地址获取，完整提交 SHA 可用 `git rev-parse HEAD` 获取。退出 `0` 表示全部匹配且运行成功；`1` 表示记录不匹配、仍在运行或运行失败；`2` 表示输入、API 或响应有问题。命令将 JSON 写到标准输出。

## 可复现示例

本仓库 v0.9.0 的公开 CI 记录可直接核对：

```bash
workflow-run-audit Amossse/agentic-dev-kit --run 36281705940 \
  --sha 034d46bf8d4e4aaa0dd35e433df4e1a55c7d55b0 \
  --workflow .github/workflows/ci.yml --event push
```

预期与实测均为退出 `0`、`"state": "matched"`。把 SHA 换成另一个完整 SHA，会退出 `1` 并显示 `"state": "rejected"`。没有 GitHub 连接时，可在仓库根目录使用离线样例：

```bash
python3.11 -m agentic_devkit.workflow_run_audit Amossse/agentic-dev-kit \
  --run 36281705940 --sha 034d46bf8d4e4aaa0dd35e433df4e1a55c7d55b0 \
  --workflow .github/workflows/ci.yml --event push \
  --snapshot examples/workflow_run_success.json
```

离线样例只复现判定，不证明当前 GitHub 状态。详见[验证记录](../../../docs/validation-2026-09-28.md)。

## 实现、配置与限制

命令使用固定参数调用 `gh api repos/OWNER/REPO/actions/runs/RUN_ID`，不经过 shell。它限制响应大小、拒绝重复 JSON 键，再核对运行 ID、提交 SHA、workflow 路径、事件、状态和结论。`--snapshot` 用于离线测试。认证交由 `gh` 管理，工具包不保存令牌。

成功运行不证明具体执行了哪些测试、workflow 定义是否安全、检查是否被设为必需，也不证明发布附件就是被测试的文件。后两项可分别使用 Required Check Audit 和 Release Asset Audit。GitHub 可能按保留策略清除旧记录。

## 安全与隐私

全程只读，不触发重跑、不检出仓库或执行用户代码。离线快照可以伪造；发布核查应查询实时 API。输出会包含提交 SHA、workflow 路径和运行地址，分享私有仓库结果前请检查。API 错误正文和凭据不会打印。

采用 [MIT 许可](../../../LICENSE)。欢迎按[贡献指南](../../../CONTRIBUTING.md)提交脱敏边界案例；另见[更新记录](../../../CHANGELOG.md)与[未代发推广文案](../../../PROMOTION.md)。建议 topics：`github-actions`、`ci-evidence`、`coding-agents`、`release-engineering`。搜索词：指定提交 CI 核对、GitHub Actions 运行 SHA 审计。
