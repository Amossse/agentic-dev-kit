# Release Asset Audit

核对本地构建文件与 GitHub Release 已上传附件的大小和 SHA-256 摘要。

[English](README.md) · [工具包](../../../README.zh-CN.md)

## 解决的问题

Release 页面存在，不代表附件齐全，也不代表上传的文件就是刚刚验证过的构建物。这个命令在发布后逐个核对指定文件，发现缺失或内容不一致就返回非零退出码。

## 五分钟上手

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.9.0
release-asset-audit OWNER/REPO --tag v1.2.3 dist/package-1.2.3.whl dist/package-1.2.3.tar.gz
```

实时查询需要已登录的 `gh`；未登录时先运行 `gh auth login`。退出码 `0` 表示所选文件的名称、大小和摘要都匹配；`1` 表示缺失或不匹配；`2` 表示输入、API 或文件读取失败。

不接入 GitHub 也能复现两种结果：

```bash
python3.11 -m agentic_devkit.release_asset_audit owner/repo --tag v0.8.0 --snapshot examples/release_asset_matched.json LICENSE
python3.11 -m agentic_devkit.release_asset_audit owner/repo --tag v0.8.0 --snapshot examples/release_asset_mismatch.json LICENSE
```

实际结果分别是退出 `0`、`"state": "matched"`，以及退出 `1`、`"state": "rejected"`。两份 JSON 是合成数据，不是 v0.8.0 的真实发布记录。真实运行可拿本仓库 `dist/` 中的 v0.8.0 构建文件，与[公开版本](https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.8.0)比较。

## 实现与配置

命令通过 `gh api` 读取指定 tag 的 Release，要求 Release 非草稿，并校验附件名称、大小、上传状态和 `sha256:` 摘要。本地文件按块计算摘要。`--snapshot FILE` 可替代网络响应，适合离线复现；它不认证仓库来源。配置仅包括 `OWNER/REPO`、`--tag` 和要核对的本地文件。

## 安全、隐私与限制

- 全程只读，不执行项目代码、不上传文件内容，也不输出 API 错误正文。认证由 `gh` 管理。
- 输出包含文件名和摘要，分享前请检查。工具只读取显式传入的常规文件，拒绝符号链接。
- GitHub 提供的摘要与本地摘要相同，不等于文件已签名，也不证明构建来源、CI 测试对象或未指定的其他附件。需要来源证明时应另用 attestation 或等效机制。
- 缺少摘要、响应异常、API 不可用、草稿版本或文件不可读时退出 `2`。伪造的 `--snapshot` 可以产生伪结果，发布检查应使用实时查询。

采用 [MIT 许可](../../../LICENSE)。欢迎按[贡献指南](../../../CONTRIBUTING.md)提交脱敏边界案例；另见[更新记录](../../../CHANGELOG.md)、[研究记录](../../../docs/research-2026-09-27.md)、[验证记录](../../../docs/validation-2026-09-27.md)和[未代发的推广文案](../../../PROMOTION.md)。

建议 topics：`release-engineering`、`github-releases`、`artifact-integrity`、`coding-agents`。搜索词：GitHub Release 附件 SHA-256 核对、coding agent 发布验证。
