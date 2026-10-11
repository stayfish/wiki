# Local reading sessions

每个子目录保存一篇论文或一条连续研究线程的多轮讨论：`session.md` 是规范来源，`index.html` 是 Codex 返回给用户的本地静态页面。运行 `render_session.py` 还会生成 `sessions/index.html`，用于本地查看状态分布、最近更新、讨论轮次并进入单个 session。

Session 可能包含私人讨论和未经审核的推断，因此所有子目录都被 Git 忽略。完整格式与编译规则见 [`schema/session.md`](../schema/session.md)。

```bash
# 重建一个 session，并刷新总览
uv run python render_session.py sessions/<session-slug>/session.md

# 校验或重建全部 session
uv run python render_session.py --check
uv run python render_session.py
```
