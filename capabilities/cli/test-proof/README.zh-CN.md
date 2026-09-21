# Test Proof

把测试结果绑定到当时实际测试的 Git 状态。

## 问题

Coding agent 可以先跑完测试，再继续修改代码后交付。“测试已通过”无法说明当前
文件仍是被测试的那一版。Test Proof 执行显式测试命令，在执行前后对 Git HEAD
与已跟踪差异做指纹，并生成可本地复验的凭证。

它是证据检查，不是测试框架，也不是 AI reviewer。

[English](README.md)

## 五分钟开始

需要 Python 3.11+ 与 Git：

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.3.0
git add src/payment.py tests/test_payment.py
test-proof run . -- python -m unittest
test-proof verify .
```

`run` 默认把 `test-proof.json` 写入仓库的 Git 元数据目录，不改变工作树。
有效凭证的验证输出如下：

```json
{
  "diff_matches": true,
  "head_matches": true,
  "receipt_state": "passed",
  "schema_version": 1,
  "state": "valid",
  "untracked_matches": true
}
```

之后只要出现已跟踪编辑、暂存变化、新 commit 或新未跟踪文件，再验证就会返回
`state: "stale"` 和退出码 `1`。

运行包含修改前后对比的临时仓库演示：

```bash
python3.11 examples/test_proof_demo.py --installed
```

预期及实际输出：

```json
{"exit": 0, "state": "passed", "step": "run"}
{"exit": 0, "state": "valid", "step": "verify"}
{"exit": 1, "state": "stale", "step": "edit_then_verify"}
```

固定结果见 [`examples/test_proof_expected.json`](../../../examples/test_proof_expected.json)。

## 命令与配置

```bash
test-proof run [--receipt PATH] [REPOSITORY] -- COMMAND [ARG ...]
test-proof verify [--receipt PATH] [REPOSITORY]
```

自定义凭证必须位于工作树之外或 Git 元数据内部：

```bash
test-proof run --receipt /tmp/payment-tests.json . -- pytest -q
test-proof verify --receipt /tmp/payment-tests.json .
```

`run` 退出码：`0` 测试通过且状态未变；`1` 命令失败；`2` 输入、Git、命令
启动或凭证 I/O 错误；`3` 命令执行期间 Git 状态变化。`verify` 仅在成功凭证
与当前状态一致时返回 `0`，失败/变化/过期返回 `1`，无效输入或凭证返回 `2`。

## 架构与实现

Test Proof 只依赖 Python 标准库和本机 Git：

1. 用固定只读 Git 命令解析仓库与当前 commit。
2. 禁用 external diff/textconv，对 `HEAD` 的 binary/full-index diff 做哈希；
   只统计非忽略的未跟踪文件，不记录文件名。
3. 运行前拒绝已有未跟踪文件，新增源码或测试必须先暂存。
4. 以参数数组、`shell=False` 执行 `--` 后的原始命令。
5. 再次取指纹，原子写入 JSON；执行期间状态变化则失败。
6. `verify` 校验有大小限制的凭证 schema，并与当前状态比较。

凭证包含命令参数、结果、UTC 开始时间、耗时、commit ID、diff 哈希和未跟踪
数量；不保存 diff 内容、文件名、命令输出、环境变量或仓库路径。

## 安全与隐私

- 指定命令会继承用户环境并在仓库根目录执行，运行前必须审阅；它不是沙箱。
- 指纹步骤不运行 shell、模型、网络、hook、external diff 或 textconv。
- 命令参数会写入凭证，不要把 token、密码、个人信息放进命令行；使用测试工具
  自身的安全密钥机制。
- 凭证会暴露 commit ID、命令、时间和状态变化，公开前请审阅。
- 外部凭证上限 1 MiB，读取后严格校验；原子写入避免半成品被当成证据。

## 限制

- 有效凭证只证明某命令返回 `0` 且所表示 Git 状态未变化，不证明测试质量、
  覆盖率、代码正确性、编辑归属或恶意命令的诚实性。
- 凭证是本地 JSON，不是签名证明；能替换文件的人也能伪造凭证。存在对抗信任时
  应使用 CI provenance 或签名系统。
- ignored 文件和外部服务不在指纹内；数据库、时间、网络、缓存和环境仍会漂移。
- 不锁定仓库；并发修改后又恢复为相同状态可能无法发现。
- Git diff 上限 10 MiB；运行前必须暂存、删除或忽略已有未跟踪文件。
- 演示是接近真实的合成 payment 修改，不代表生产验证或第三方安全认证。

## 贡献

项目使用 MIT License。请阅读[贡献指南](../../../CONTRIBUTING.md)，用临时 Git
仓库提供复现，不要上传私有代码、真实凭据或敏感文件名。修改指纹、凭证校验、
命令执行或退出码优先级时必须补验收 Case。

搜索词：测试证据凭证、coding agent 测试验证、过期测试结果、Claude Code 工作流、
CI 证据、Git 状态指纹、agent 交付。
