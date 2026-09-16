# Staged Scope：暂存改动范围门禁

任务只允许修改 payment 模块，agent 却额外暂存了 CI 文件。这个 CLI 直接检查
Git index 中每个文件的路径，给出拒绝原因和退出码。

## 安装、运行与示例

需要 Python 3.11+、Git，无运行时 Python 依赖。

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.1.0
staged-scope . --allow src/ --allow tests/test_payment.py
```

`--allow src/` 放行该目录后代；`--allow src/payment.py` 只放行一个文件。
全部相对于仓库根目录，区分大小写，不支持 glob，文件名以 `-` 开头时使用
`--allow=-option.py`。重复规则去重，多个规则取并集。不能包含绝对路径、
空/`.`/`..` 组件、反斜杠、冒号、`* ? [ ]`、ASCII 控制字符或无效 Unicode。

```bash
git clone https://github.com/Amossse/agentic-dev-kit.git
cd agentic-dev-kit
python3.11 examples/staged_scope_demo.py --installed
```

合成场景：把 `sum(prices)` 修为 `round(sum(prices), 2)`，同时额外暂存
`.github/workflows/ci.yml`。实际演示结果：

| 场景 | 暂存记录 | 拒绝文件 | 退出码 |
| --- | --- | --- | --- |
| 空 index | 0 | 无 | 3 |
| payment 修复 + CI 文件 | 2 | `.github/workflows/ci.yml` | 1 |
| 审阅后撤去 CI 文件暂存 | 1 | 无 | 0 |

演示脚本在临时仓库内写合成文件，检查真实退出码和 JSON，退出时清理示例。
撤去暂存不会删除工作树文件。完整 JSON 输出见[英文说明](README.md)。

## 实现与配置

[源码](../../../agentic_devkit/staged_scope.py) 使用 Python 标准库和固定 Git
参数读取 HEAD 与 index 的 NUL 分隔路径状态，关闭重命名识别，移动文件的
旧路径删除端、新路径增加端都必须通过。初次提交也可检查，`U` 冲突始终拒绝。
嵌套目录运行仍检查整个仓库。原始路径字节通过 `path_bytes_b64` 保留，显示
字段 `path` 对无效 UTF-8 字节进行转义。

最多 100 条范围、每条 4096 字符、10000 个状态记录、每条 Git 命令 10 秒，
捕获 stdout 后检查 10 MiB 上限；该上限不保证极大仓库的峰值内存。
同一冲突文件可能有多个状态记录。无额外配置文件或模型参数。

正常 stdout 为排序稳定的 JSON、stderr 为状态和数量。`0` 非空且全通过，
`1` 越界/冲突，`2` 输入/Git 错误（没有 JSON），`3` 没有暂存改动。
只有 `0` 应继续提交流程，不能自动扩大范围来消除失败。

## 安全与限制

CLI 只读、离线，不执行 shell、用户代码、hook、外部 diff/textconv，不自动
暂存或提交。关闭 fsmonitor、pager、可选锁，清除继承的 `GIT_*` 覆盖，禁用
全局/系统 Git 配置；仍会读取仓库配置。请使用可信 Git 和仓库，此工具不提供
恶意仓库沙箱。CLI 参数错误可能回显参数，不应把秘密放进参数。

输出文件名、白名单及 base64 可能敏感。报告建议输出到仓库外的新文件，分享前
审阅。已有暂存改动必须先审阅；不判断编辑归属、代码内容、正确性、测试覆盖和
未暂存/未跟踪文件。只检查 submodule 的暂存 gitlink，不检查内部脏内容。
检查后 index/HEAD 仍可变化，提交前应重跑。普通 CI checkout 没有 index diff，
需由任务明确准备暂存状态。本版本不支持 PR 提交范围、glob、Unicode 归一化。
含白名单保留字符的文件名不能通过精确文件规则放行，只能由事先明确允许的父目录
覆盖；不能自动扩大范围来消除失败。

[MIT](../../../LICENSE)、[贡献指南](../../../CONTRIBUTING.md)、
[CHANGELOG](../../../CHANGELOG.md)、[验证](../../../docs/validation-2026-09-16.md)、
[中英文推广文案](../../../PROMOTION.md)。
