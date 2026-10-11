from __future__ import annotations

import argparse
import html
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from render import BuildError, markdown_to_html, reading_map, shell

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
SESSIONS_ROOT = ROOT / "sessions"
ALLOWED_STATUS = {"active", "ready-to-compile", "closed"}


@dataclass(frozen=True)
class Session:
    path: Path
    title: str
    slug: str
    created: str
    updated: str
    status: str
    source: str
    body: str


def parse_session(path: Path) -> Session:
    resolved = path.resolve()
    try:
        resolved.relative_to(SESSIONS_ROOT.resolve())
    except ValueError as error:
        raise BuildError("session 文件必须位于 sessions/ 下") from error
    if resolved.name != "session.md":
        raise BuildError("session 源文件必须命名为 session.md")

    text = resolved.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise BuildError("session.md: 缺少 frontmatter")
    raw_meta, body = text[4:].split("\n---\n", 1)
    meta = dict(line.split(":", 1) for line in raw_meta.splitlines() if line.strip() and ":" in line)
    meta = {key.strip(): value.strip() for key, value in meta.items()}
    required = {"title", "slug", "created", "updated", "status"}
    missing = required - meta.keys()
    if missing:
        raise BuildError(f"session.md: 缺少 {', '.join(sorted(missing))}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", meta["slug"]):
        raise BuildError("session.md: slug 必须使用 kebab-case")
    if resolved.parent.name != meta["slug"]:
        raise BuildError("session.md: 父目录名必须与 slug 一致")
    if meta["status"] not in ALLOWED_STATUS:
        raise BuildError(f"session.md: 不支持 status={meta['status']}")

    turns = re.findall(r"^## Turn (\d{2})\b", body, flags=re.MULTILINE)
    if not turns:
        raise BuildError("session.md: 至少需要一个 `## Turn NN` 块")
    expected = [f"{number:02}" for number in range(1, len(turns) + 1)]
    if turns != expected:
        raise BuildError("session.md: Turn 编号必须从 01 开始连续递增")
    for block in re.split(r"(?=^## Turn \d{2}\b)", body, flags=re.MULTILINE)[1:]:
        if "\n### 用户" not in block or "\n### Codex" not in block:
            raise BuildError("session.md: 每个 Turn 都必须包含 `### 用户` 与 `### Codex`")

    return Session(
        path=resolved,
        title=meta["title"],
        slug=meta["slug"],
        created=meta["created"],
        updated=meta["updated"],
        status=meta["status"],
        source=meta.get("source", "none"),
        body=body.strip(),
    )


def session_document(session: Session) -> str:
    block_ids = {
        f"Turn {number} · {title.strip()}": f"block-{number}"
        for number, title in re.findall(r"^## Turn (\d{2})\s*·\s*(.+)$", session.body, flags=re.MULTILINE)
    }
    rendered = markdown_to_html(
        session.body,
        {},
        card_sections=True,
        paper_asset_prefix=None,
        section_role_override=("session", "Conversation Turn"),
        block_ids=block_ids,
    )
    controls = (
        '<div class="reading-toolbar" role="toolbar" aria-label="阅读控制">'
        '<button type="button" data-reading-action="expand">全部展开</button>'
        '<button type="button" data-reading-action="collapse">全部折叠</button>'
        '<button type="button" data-reading-action="focus" aria-pressed="false">聚焦当前</button>'
        '</div>'
    )
    source = "未绑定公开来源" if session.source == "none" else session.source
    research_panel = (
        '<aside class="research-panel" id="research-panel" aria-label="讨论信息">'
        '<div class="panel-heading"><div><span class="eyebrow">Workspace</span><h2>讨论信息</h2></div>'
        '<button type="button" class="panel-close" data-panel-close="research" aria-label="关闭讨论信息">×</button></div>'
        '<section class="panel-section"><span class="panel-label">Session</span><h3>本地状态</h3><dl>'
        f'<div><dt>状态</dt><dd>{html.escape(session.status)}</dd></div><div><dt>更新</dt><dd>{html.escape(session.updated)}</dd></div>'
        '</dl></section><section class="panel-section"><span class="panel-label">Reading</span><h3>阅读控制</h3>'
        f'{controls}</section><section class="panel-section panel-placeholder"><span class="panel-label">Privacy</span>'
        '<h3>仅限本地</h3><p>本页不会自动写入或发布到 Wiki。</p></section></aside>'
    )
    body = (
        '<body class="reading-page-body session-page" data-accent="deep">'
        '<nav class="topbar"><span class="brand"><span aria-hidden="true">R·</span> Local Session</span>'
        f'<span class="topbar-title">{html.escape(session.title)}</span><div class="workspace-actions">'
        '<button type="button" data-panel-toggle="map" aria-controls="reading-map" aria-expanded="false">目录</button>'
        '<button type="button" data-panel-toggle="research" aria-controls="research-panel" aria-expanded="false">讨论信息</button></div></nav>'
        '<div class="reading-progress" aria-hidden="true"><span></span></div>'
        '<main class="page reading-page">'
        '<header class="hero"><span class="eyebrow">Session · private workspace</span>'
        f'<h1>{html.escape(session.title)}</h1>'
        f'<p>{html.escape(source)}</p></header>'
        f'<div class="reading-shell">{reading_map(session.body, ("session", "Conversation Turn"), block_ids=block_ids)}'
        f'<article class="block-article">{rendered}</article>{research_panel}</div>'
        '<footer>Local session · Compile to Wiki only on explicit request</footer>'
        '</main><div class="panel-scrim" data-panel-scrim hidden></div><script src="../../assets/wiki.js"></script></body>'
    )
    return shell(f"{session.title} · Session", "../../assets/style.css", body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        session = parse_session(args.source)
        if args.check:
            LOGGER.info("Session: validated %s", session.slug)
        else:
            target = session.path.parent / "index.html"
            target.write_text(session_document(session), encoding="utf-8")
            LOGGER.info("Session: rendered %s", target.relative_to(ROOT))
        return 0
    except (BuildError, OSError) as error:
        LOGGER.error("Session build failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
