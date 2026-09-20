# Range Scope：提交范围门禁

检查 coding agent 已提交分支是否只修改任务允许的文件。它用 base 与 head 的
merge-base 作为起点，因此 base 后续前进的改动不会被误算进候选分支。

## 安装和五分钟开始

需要 Python 3.11+ 和 Git，无运行时 Python 依赖或 API key。

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.2.0
range-scope . --base origin/main --head HEAD --allow src/payments/ --allow tests/
```

`0` 表示非空且全部通过；`1` 表示越界路径；`2` 表示输入、历史或 Git 错误；
`3` 表示没有改动。stdout 是 JSON，stderr 仅输出状态和数量。

完整临时仓库演示：

```bash
git clone https://github.com/Amossse/agentic-dev-kit.git
cd agentic-dev-kit
python3.11 examples/range_scope_demo.py --installed
```

演示依次得到空范围/3、payment 修复夹带 workflow 文件/1、只有 payment
修复/0。脚本检查真实退出码和 JSON，且只在自动清理的临时目录写入合成内容。

## 规则、实现与 CI

`--head` 默认 `HEAD`。两个 revision 先解析为 commit；拒绝以 `-` 开头、含
空白/控制字符/`..` 的输入和范围表达式。允许路径沿用 Staged Scope：结尾
`/` 表示目录前缀，否则精确匹配文件；区分大小写，不支持 glob。

实现依次执行固定参数的 `rev-parse`、`merge-base` 和 NUL 分隔的 name-status
diff。关闭 rename 识别，所以移动文件的删除端和新增端都要通过。复用已有路径
校验、原始文件名字节、Git 安全执行、记录上限和确定性 JSON，不调用网络或模型。

GitHub PR 应使用 `fetch-depth: 0` 并 checkout `pull_request.head.sha`，然后用
`pull_request.base.sha` 作为 `--base`。不要把合成 merge commit 当作候选 head。
fork PR 只应执行受信任 base 分支中的 workflow；本 CLI 不执行候选文件，但同一
workflow 的其他步骤可能执行。

## 安全和限制

使用可信 Git 与仓库；它是只读证据门禁，不是恶意对象库沙箱。清除继承的
`GIT_*` 覆盖，禁用全局/系统 Git 配置、fsmonitor、外部 diff/textconv，命令
10 秒超时。输出会暴露路径和 commit hash，分享前审阅。

浅克隆、缺失 revision、无共同祖先会显式返回 `2`，工具不会自动 fetch。
只模拟 PR 风格 merge-base→head，不模拟 push 的 two-dot、stacked PR、多重
merge-base 或 GitHub 合成 merge 结果。不检查未提交改动、代码内容、作者、测试、
审批和 CODEOWNERS；submodule 只检查 gitlink 路径。分支名可变，合并前应重跑。

[贡献指南](../../../CONTRIBUTING.md) · [MIT](../../../LICENSE) ·
[研究](../../../docs/research-2026-09-20.md) ·
[验证](../../../docs/validation-2026-09-20.md) · [推广文案](../../../PROMOTION.md)
