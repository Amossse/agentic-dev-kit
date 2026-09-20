# Contributing

Start with a public issue describing an engineering task, a concrete input,
expected evidence, existing tools and why the gap belongs in this toolkit.
Do not attach private code, real credentials or sensitive filenames.

For Staged Scope, include a disposable Git reproduction and the exact allow rules.
Changes to matching, Git arguments, framing or exit precedence need a regression
case in the existing acceptance check. Keep stdlib runtime dependencies and
literal path semantics unless a measured need justifies a change.

From a clone with Python 3.11+ and Git:

```bash
python3.11 -m unittest discover -s tests -v
python3.11 examples/staged_scope_demo.py
python3.11 examples/range_scope_demo.py
uvx ruff check .
uvx ruff format --check .
uvx ty check .
uv build
uvx twine check dist/*
```

Tests and the demo write synthetic files only in temporary repositories. Never
run a submitted reproduction in a private checkout before reviewing it.

Add a capability only after a real need is clear. Place documentation under
`capabilities/<type>/<name>/`, keep code in the installable package, add a
reproducible example and update the main matrix, bilingual docs and CHANGELOG.
One narrow runnable capability is preferable to placeholder agents or wrappers.

Submit a PR explaining the problem, resulting behavior and validation. By
contributing you agree your contribution is licensed under this project's MIT
license. For security concerns, avoid publishing working credentials or private
repositories; use GitHub private vulnerability reporting when available.
