# Required Check Audit

检查 GitHub 分支保护是否把指定的 PR 检查设为必过项。

[English](README.md) · [工具包](../../../README.zh-CN.md)

## 解决的问题

PR Event Gate 跑绿了，不代表合并时必须通过它。仓库还要在目标分支的保护规则里，把实际出现的检查名称设为 required check。这个只读命令帮助仓库维护者核对设置。

## 五分钟上手

先在 PR 的 Checks 页确认完整检查名称，再运行：

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.8.0
gh auth login
required-check-audit OWNER/REPO --branch main --check 'policy'
```

已经登录 `gh` 的用户无需重新登录。退出码 `0` 表示分支保护中有同名必过检查；`1` 表示读取到的分支保护未要求它；`2` 表示输入、权限、API 或 JSON 出错。GitHub 返回 404 时，工具不会猜测是“没有保护”还是“没有权限”。

不用 GitHub 账号也能复现输入输出：

```bash
python3.11 -m agentic_devkit.required_check_audit owner/repo --branch main --check policy --snapshot examples/required_check_missing.json
python3.11 -m agentic_devkit.required_check_audit owner/repo --branch main --check policy --snapshot examples/required_check_protected.json
```

第一条实际退出 `1`，输出 `"state": "not_required"`；第二条实际退出 `0`，输出 `"state": "required"` 和 `"admin_enforced": true`。这两份文件只是接近 GitHub API 的测试数据，不代表某个真实仓库目前的设置。

## 实现与配置

命令通过 `gh api` 只读查询指定分支的 protection endpoint，同时支持 `checks[].context` 和旧版 `contexts[]`。`--snapshot FILE` 可离线检查保存的 JSON。配置在 GitHub 分支保护页面完成；本工具不修改仓库设置。

## 安全、隐私与限制

- 工具不执行 PR 代码，不打印令牌，也不用 shell 拼接命令。认证交给 `gh`。
- 私有仓库的保护规则快照可能敏感，分享前请检查。JSON 超过 1 MiB、含重复键或字段异常时会报错。
- 这里只检查分支保护，不检查 ruleset、绕过权限、检查来源 App 或工作流是否真的执行。输出 `required` 不等于所有人都无法绕过合并限制。
- 工作流名称或保护规则变化后要重新检查。实际检查名称应从 PR 页面核对。

采用 [MIT 许可](../../../LICENSE)。欢迎按[贡献指南](../../../CONTRIBUTING.md)提交真实但已脱敏的边界案例；另见[更新记录](../../../CHANGELOG.md)、[研究记录](../../../docs/research-2026-09-26.md)、[验证记录](../../../docs/validation-2026-09-26.md)及[未代发的推广文案](../../../PROMOTION.md)。

建议 topics：`github-actions`、`branch-protection`、`required-status-checks`、`coding-agents`。搜索词：GitHub 必过检查核对、AI agent PR 合并门禁。
