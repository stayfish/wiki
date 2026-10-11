from __future__ import annotations

import argparse
import html
import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from render import BuildError, markdown_to_html, reading_map, shell

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
SESSIONS_ROOT = ROOT / "sessions"
ALLOWED_STATUS = {"active", "ready-to-compile", "closed"}
STATUS_LABELS = {
    "active": "进行中",
    "ready-to-compile": "待编译",
    "closed": "已结束",
}


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

    @property
    def turn_count(self) -> int:
        return len(re.findall(r"^## Turn \d{2}\b", self.body, flags=re.MULTILINE))

    @property
    def latest_topic(self) -> str:
        topics = re.findall(r"^## Turn \d{2}\s*·\s*(.+)$", self.body, flags=re.MULTILINE)
        return topics[-1].strip() if topics else "未命名讨论"


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


def session_switcher(current: Session, sessions: list[Session]) -> str:
    ordered = sorted(
        sessions,
        key=lambda item: (item.updated, item.created, item.slug),
        reverse=True,
    )
    active_attrs = {current.slug: ' class="is-active" aria-current="page"'}
    items = "".join(
        '<li>'
        f'<a href="../{html.escape(item.slug, quote=True)}/index.html"'
        f'{active_attrs.get(item.slug, "")}>'
        f'<span class="session-switcher-title">{html.escape(item.title)}</span>'
        f'<span class="session-switcher-meta">{html.escape(item.updated)} · {item.turn_count * 2} 条消息</span>'
        '</a></li>'
        for item in ordered
    )
    if not items:
        items = '<li class="session-switcher-empty">暂无其他对话</li>'
    return (
        '<aside class="session-list-panel" id="session-list-panel" aria-label="研究会话">'
        '<div class="panel-heading"><div><span class="eyebrow">Sessions</span><h2>研究会话</h2></div>'
        '<button type="button" class="panel-close" data-panel-close="sessions" aria-label="关闭研究会话">×</button></div>'
        f'<nav class="session-switcher"><ul>{items}</ul>'
        '<a class="session-switcher-all" href="../index.html">查看全部 Session <span aria-hidden="true">→</span></a>'
        '</nav></aside>'
    )


def session_document(session: Session, sessions: list[Session]) -> str:
    block_ids = {
        f"Turn {number} · {title.strip()}": f"block-{number}"
        for number, title in re.findall(r"^## Turn (\d{2})\s*·\s*(.+)$", session.body, flags=re.MULTILINE)
    }
    rendered = markdown_to_html(
        session.body,
        {},
        card_sections=True,
        paper_asset_prefix=None,
        section_role_override=("session", "Turn"),
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
    map_html = reading_map(session.body, ("session", "Turn"), block_ids=block_ids)
    map_html = (
        map_html.replace('aria-label="分层阅读地图"', 'aria-label="对话大纲"')
        .replace('<span class="eyebrow">Reading map</span><h2>论文结构</h2>', '<span class="eyebrow">Outline</span><h2>对话大纲</h2>')
        .replace('aria-label="关闭论文结构"', 'aria-label="关闭对话大纲"')
    )
    switcher_html = session_switcher(session, sessions)
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
        '<nav class="topbar"><a class="brand" href="../index.html" aria-label="返回 Session 仪表盘">'
        '<span aria-hidden="true">R·</span> Local Session</a>'
        f'<span class="topbar-title">{html.escape(session.title)}</span><div class="workspace-actions">'
        '<button type="button" data-panel-toggle="sessions" aria-controls="session-list-panel" aria-expanded="false">对话</button>'
        '<button type="button" data-panel-toggle="map" aria-controls="reading-map" aria-expanded="false">大纲</button>'
        '<button type="button" data-panel-toggle="research" aria-controls="research-panel" aria-expanded="false">讨论信息</button></div></nav>'
        '<div class="reading-progress" aria-hidden="true"><span></span></div>'
        '<main class="page reading-page">'
        '<header class="hero"><span class="eyebrow">Session · private workspace</span>'
        f'<h1>{html.escape(session.title)}</h1>'
        f'<p>{html.escape(source)}</p></header>'
        f'<div class="reading-shell">{switcher_html}'
        f'<article class="block-article">{rendered}</article>{map_html}{research_panel}</div>'
        '<footer>Local session · Compile to Wiki only on explicit request</footer>'
        '</main><div class="panel-scrim" data-panel-scrim hidden></div><script src="../../assets/wiki.js"></script></body>'
    )
    return shell(f"{session.title} · Session", "../../assets/style.css", body)


def discover_sessions() -> list[Path]:
    return sorted(SESSIONS_ROOT.glob("*/session.md"))


def dashboard_document(sessions: list[Session]) -> str:
    ordered = sorted(sessions, key=lambda item: (item.updated, item.created, item.slug), reverse=True)
    counts = Counter(session.status for session in ordered)
    total = len(ordered)
    total_turns = sum(session.turn_count for session in ordered)

    distribution = "".join(
        f'<span class="status-segment status-{status}" style="--segment:{counts[status]}" '
        f'title="{STATUS_LABELS[status]}：{counts[status]}"></span>'
        for status in ("active", "ready-to-compile", "closed")
        if counts[status]
    )
    legend = "".join(
        f'<li><span class="status-dot status-{status}"></span>{STATUS_LABELS[status]} '
        f'<strong>{counts[status]}</strong></li>'
        for status in ("active", "ready-to-compile", "closed")
    )

    cards: list[str] = []
    for session in ordered:
        cards.append(
            '<article class="session-summary">'
            f'<a href="{html.escape(session.slug, quote=True)}/index.html">'
            '<div class="session-summary-main">'
            f'<h2>{html.escape(session.title)}</h2>'
            f'<p class="session-latest">{html.escape(session.latest_topic)}</p></div>'
            '<div class="session-summary-meta">'
            f'<time datetime="{html.escape(session.updated, quote=True)}">{html.escape(session.updated)}</time>'
            f'<span>{session.turn_count * 2} 条消息</span>'
            f'<span class="session-status status-{session.status}">{STATUS_LABELS[session.status]}</span>'
            '<span class="session-row-arrow" aria-hidden="true">→</span></div></a>'
            '</article>'
        )

    empty = (
        '<section class="session-empty"><p>还没有本地 session。</p>'
        '<code>uv run python render_session.py sessions/&lt;slug&gt;/session.md</code></section>'
    )
    body = (
        '<body class="session-dashboard" data-accent="deep">'
        '<nav class="topbar"><span class="brand"><span aria-hidden="true">R·</span> Local Sessions</span>'
        '<span class="topbar-title">Private reading workspace</span></nav>'
        '<main class="session-dashboard-page">'
        '<header class="session-dashboard-hero"><span class="eyebrow">Private · local only</span>'
        '<h1>阅读 Session</h1><p>从最近一次讨论继续，或检查哪些内容已经可以编译进 Wiki。</p></header>'
        '<section class="session-overview" aria-label="Session 概览">'
        f'<div class="overview-number"><strong>{total}</strong><span>Sessions</span></div>'
        f'<div class="overview-number"><strong>{total_turns}</strong><span>Turns</span></div>'
        '<div class="status-overview"><div class="status-bar" aria-label="状态分布">'
        f'{distribution}</div><ul>{legend}</ul></div></section>'
        f'<section class="session-grid" aria-label="全部 Session">{"".join(cards)}</section>'
        f'{empty if not ordered else ""}'
        '<footer>Generated from local session.md files · Nothing here is published automatically</footer>'
        '</main></body>'
    )
    return shell("Local reading sessions", "../assets/style.css", body)


def render_dashboard(sessions: list[Session]) -> Path:
    target = SESSIONS_ROOT / "index.html"
    target.write_text(dashboard_document(sessions), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", type=Path)
    parser.add_argument("--all", action="store_true", help="校验或重建全部 session")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.source and args.all:
        parser.error("source 与 --all 不能同时使用")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        paths = discover_sessions() if args.all or args.source is None else [args.source]
        sessions = [parse_session(path) for path in paths]
        if args.check:
            if len(sessions) == 1:
                LOGGER.info("Session: validated %s", sessions[0].slug)
            else:
                LOGGER.info("Sessions: validated %d", len(sessions))
        else:
            dashboard_sessions = [parse_session(path) for path in discover_sessions()]
            for session in dashboard_sessions:
                target = session.path.parent / "index.html"
                target.write_text(session_document(session, dashboard_sessions), encoding="utf-8")
                LOGGER.info("Session: rendered %s", target.relative_to(ROOT))
            dashboard = render_dashboard(dashboard_sessions)
            LOGGER.info("Sessions: rendered dashboard %s", dashboard.relative_to(ROOT))
        return 0
    except (BuildError, OSError) as error:
        LOGGER.error("Session build failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
