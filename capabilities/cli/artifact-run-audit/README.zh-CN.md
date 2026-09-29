# Artifact Run Audit

核对一份 GitHub Actions 附件是否来自指定提交上的指定运行记录。

[English](README.md) · [工具包](../../../README.zh-CN.md)

## 解决的问题

CI 成功、附件名称也对，仍需确认附件与那条运行记录确有关联。这个命令读取附件和运行记录两份元数据，核对运行 ID、提交 SHA、workflow 文件、触发事件及结果。

## 五分钟上手

需要 Python 3.11+ 和已登录的 GitHub CLI（先运行 `gh auth login`）。工具包没有运行时 Python 依赖：

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.11.0
gh api repos/OWNER/REPO/actions/runs/RUN_ID/artifacts --jq '.artifacts[] | {id,name}'
artifact-run-audit OWNER/REPO --artifact ARTIFACT_ID --run RUN_ID \
  --sha FULL_COMMIT_SHA --workflow .github/workflows/ci.yml --event push
```

退出 `0` 表示两份记录的运行 ID 和提交 SHA 一致、运行成功、附件未过期；`1` 表示关联不符、运行未成功或附件已过期；`2` 表示输入、元数据或 API 查询失败。输出包含 GitHub 报告的附件压缩包 SHA-256 摘要，但命令不下载压缩包，也不自行计算摘要。

## 离线示例

在仓库根目录运行：

```bash
python3.11 -m agentic_devkit.artifact_run_audit Amossse/agentic-dev-kit \
  --artifact 12345 --run 36281705940 \
  --sha 034d46bf8d4e4aaa0dd35e433df4e1a55c7d55b0 \
  --workflow .github/workflows/ci.yml --event push \
  --artifact-snapshot examples/artifact_run_matched.json \
  --run-snapshot examples/workflow_run_success.json
```

预期与实测均为退出 `0`、`"state": "matched"`。把附件关联的运行 ID 改掉会退出 `1`，显示 `"state": "rejected"`。附件快照是合成数据，并非 run 36281705940 实际上传。两项快照参数必须同时传入；真实调用见[验证记录](../../../docs/validation-2026-09-30.md)。

## 实现与配置

命令以固定参数调用两次只读 `gh api`，分别读取指定附件和运行记录。它限制 JSON 大小、拒绝重复键，复用 Workflow Run Audit 的提交、workflow、事件和成功判定，再核对附件的运行关联、过期状态与摘要格式。配置仅为 `OWNER/REPO` 和命令行参数。认证由 `gh` 管理。

## 安全、隐私与限制

- 不执行仓库代码，不下载附件、不保存令牌，也不修改 GitHub。API 错误正文不会打印；请使用可信的 `gh`。
- 摘要对应 Actions 附件压缩包，不是包内每个文件。本命令只核对元数据，不能独立验证文件字节，也不证明文件已被测试或等同于 Release 附件。
- 运行成功不证明所有相关 job 都执行过，也不证明检查是必过项。离线快照可以伪造。旧附件可能因保留策略过期或被清除。
- 输出包含附件名称、提交 SHA、摘要和运行地址。分享私有仓库结果前请检查。

采用 [MIT 许可](../../../LICENSE)。欢迎按[贡献指南](../../../CONTRIBUTING.md)提交脱敏案例；另见[更新记录](../../../CHANGELOG.md)和[未代发的中英文推广文案](../../../PROMOTION.md)。建议 topics：`github-actions`、`artifact-integrity`、`ci-evidence`、`coding-agents`。搜索词：GitHub Actions 附件运行关联、CI 附件提交 SHA 核对。
