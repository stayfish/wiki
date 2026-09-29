from __future__ import annotations

import argparse
import html
import json
import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
WIKI_ROOT = ROOT / "wiki"
OUTPUT_ROOT = ROOT / "site"
ALLOWED_TYPES = {"source", "concept", "topic", "thread"}
ALLOWED_ACCENTS = {"brick", "ochre", "moss", "deep"}
TYPE_META = {
    "source": ("Sources", "来源", "论文、文章、视频与代码仓库的精读页"),
    "concept": ("Concepts", "概念", "跨来源复用的概念与机制"),
    "topic": ("Topics", "综合", "连接多个来源的横向主题"),
    "thread": ("Threads", "线索", "持续追踪的问题与思考"),
}
WIKILINK = re.compile(r"\[\[([a-z0-9][a-z0-9-]*)(?:\|([^\]]+))?\]\]")
INLINE = re.compile(r"(`[^`]+`|\*\*[^*]+\*|\[[^\]]+\]\([^)]+\)|\[\[[^\]]+\]\])")


class BuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class Page:
    path: Path
    title: str
    slug: str
    kind: str
    summary: str
    updated: str
    accent: str
    body: str

    @property
    def url(self) -> str:
        return f"{self.kind}s/{self.slug}.html"


def parse_page(path: Path) -> Page:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise BuildError(f"{path.relative_to(ROOT)}: 缺少 frontmatter")
    raw_meta, body = text[4:].split("\n---\n", 1)
    meta = dict(line.split(":", 1) for line in raw_meta.splitlines() if line.strip() and ":" in line)
    meta = {key.strip(): value.strip() for key, value in meta.items()}
    missing = {"title", "slug", "type", "summary", "updated"} - meta.keys()
    if missing:
        raise BuildError(f"{path.relative_to(ROOT)}: 缺少 {', '.join(sorted(missing))}")
    if meta["type"] not in ALLOWED_TYPES:
        raise BuildError(f"{path.relative_to(ROOT)}: 不支持 type={meta['type']}")
    accent = meta.get("accent", "brick")
    if accent not in ALLOWED_ACCENTS:
        raise BuildError(f"{path.relative_to(ROOT)}: 不支持 accent={accent}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", meta["slug"]):
        raise BuildError(f"{path.relative_to(ROOT)}: slug 必须使用 kebab-case")
    return Page(path, meta["title"], meta["slug"], meta["type"], meta["summary"], meta["updated"], accent, body.strip())


def load_pages() -> list[Page]:
    pages = [parse_page(path) for path in sorted(WIKI_ROOT.rglob("*.md"))]
    slugs: set[str] = set()
    for page in pages:
        if page.slug in slugs:
            raise BuildError(f"重复 slug: {page.slug}")
        slugs.add(page.slug)
    return pages


def validate_links(pages: list[Page]) -> None:
    known = {page.slug for page in pages}
    failures: list[str] = []

    def prose(text: str) -> str:
        return re.sub(r"`[^`]*`", "", re.sub(r"```.*?```", "", text, flags=re.DOTALL))

    sources = [(str(page.path.relative_to(ROOT)), page.body) for page in pages]
    sources.append(("index.md", (ROOT / "index.md").read_text(encoding="utf-8")))
    for source, text in sources:
        for slug, _ in WIKILINK.findall(prose(text)):
            if slug not in known:
                failures.append(f"{source} -> [[{slug}]]")
    if failures:
        raise BuildError("无法解析的 Wiki 链接:\n  " + "\n  ".join(failures))


def inline_markup(text: str, pages: dict[str, Page]) -> str:
    result: list[str] = []
    cursor = 0
    for match in INLINE.finditer(text):
        result.append(html.escape(text[cursor:match.start()]))
        token = match.group()
        if token.startswith("[["):
            link = WIKILINK.fullmatch(token)
            assert link
            slug, label = link.groups()
            page = pages[slug]
            result.append(f'<a href="../{page.url}">{html.escape(label or page.title)}</a>')
        elif token.startswith("`"):
            result.append(f"<code>{html.escape(token[1:-1])}</code>")
        elif token.startswith("**"):
            result.append(f"<strong>{html.escape(token[2:-2])}</strong>")
        else:
            link = re.fullmatch(r"\[([^]]+)\]\(([^)]+)\)", token)
            assert link
            label, href = link.groups()
            attrs = ' target="_blank" rel="noreferrer"' if href.startswith(("http://", "https://")) else ""
            result.append(f'<a href="{html.escape(href, quote=True)}"{attrs}>{html.escape(label)}</a>')
        cursor = match.end()
    result.append(html.escape(text[cursor:]))
    return "".join(result)


def markdown_to_html(source: str, pages: dict[str, Page]) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    bullets: list[str] = []
    raw: list[str] = []
    in_figure = False

    def flush() -> None:
        if paragraph:
            output.append(f"<p>{inline_markup(' '.join(paragraph), pages)}</p>")
            paragraph.clear()
        if bullets:
            output.append("<ul>" + "".join(f"<li>{item}</li>" for item in bullets) + "</ul>")
            bullets.clear()

    for line in source.splitlines():
        stripped = line.strip()
        if in_figure:
            raw.append(line)
            if stripped == "</figure>":
                output.append("\n".join(raw)); raw.clear(); in_figure = False
            continue
        if stripped.startswith("<figure"):
            flush(); in_figure = True; raw.append(line); continue
        if not stripped:
            flush(); continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            flush(); level = len(heading.group(1))
            if level > 1:
                output.append(f"<h{level}>{inline_markup(heading.group(2), pages)}</h{level}>")
            continue
        bullet = re.match(r"^-\s+(.+)$", stripped)
        if bullet:
            if paragraph: flush()
            bullets.append(inline_markup(bullet.group(1), pages)); continue
        paragraph.append(stripped)
    flush()
    if in_figure:
        raise BuildError("未闭合的 <figure>")
    return "\n".join(output)


def shell(title: str, css_path: str, body: str) -> str:
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,300..900,0..100,0..1&family=Newsreader:opsz,wght@6..72,300..700&family=Noto+Serif+SC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet"><link rel="stylesheet" href="{css_path}"></head>{body}</html>'''


def page_document(page: Page, pages: list[Page], page_map: dict[str, Page]) -> str:
    links = [item for item in pages if item.slug != page.slug and re.search(rf"\[\[{re.escape(page.slug)}(?:\||\]\])", item.body)]
    backlinks = ""
    if links:
        backlinks = '<aside><span class="eyebrow">引用此页</span><ul>' + "".join(f'<li><a href="../{item.url}">{html.escape(item.title)}</a></li>' for item in links) + "</ul></aside>"
    body = f'''<body data-accent="{page.accent}"><nav><a href="../index.html">← Wiki Index</a><span>{page.kind} · {page.slug}</span></nav><main class="page"><header class="hero"><span class="eyebrow">{page.kind} · {page.updated}</span><h1>{html.escape(page.title)}</h1><p>{html.escape(page.summary)}</p></header><article>{markdown_to_html(page.body, page_map)}</article>{backlinks}<footer>AI maintained · Human reviewed</footer></main><script src="../wiki.js"></script></body>'''
    return shell(f"{page.title} · Wiki", "../style.css", body)


def type_overview(pages: list[Page]) -> str:
    blocks: list[str] = []
    for kind, (english, chinese, description) in TYPE_META.items():
        count = sum(page.kind == kind for page in pages)
        blocks.append(
            f'<a class="type-block" href="types/{kind}.html">'
            f'<strong>{count:02}</strong><span>{english} · {chinese}</span>'
            f'<small>{description}</small></a>'
        )
    return '<section class="type-overview" aria-label="按页面类型浏览">' + "".join(blocks) + "</section>"


def page_rows(pages: list[Page], page_prefix: str = "") -> str:
    ordered = sorted(pages, key=lambda page: (page.updated, page.title), reverse=True)
    rows: list[str] = []
    for page in ordered:
        rows.append(
            f'<details class="recent-item" data-accent="{page.accent}">'
            '<summary>'
            f'<time datetime="{html.escape(page.updated, quote=True)}">{html.escape(page.updated)}</time>'
            f'<span class="recent-type">{html.escape(page.kind)}</span>'
            f'<strong>{html.escape(page.title)}</strong>'
            f'<span class="recent-summary">{html.escape(page.summary)}</span>'
            '<span class="recent-toggle" aria-hidden="true">+</span>'
            '</summary>'
            '<div class="recent-preview">'
            f'<div><span class="eyebrow">{html.escape(page.kind)} · updated {html.escape(page.updated)}</span>'
            f'<h3>{html.escape(page.title)}</h3><p>{html.escape(page.summary)}</p></div>'
            f'<a class="page-link" href="{page_prefix}{page.url}">进入完整页面 <span aria-hidden="true">→</span></a>'
            '</div></details>'
        )
    empty = '<p class="empty-state">还没有知识页面。添加第一份来源后，它会出现在这里。</p>'
    return "".join(rows) if rows else empty


def recent_pages(pages: list[Page]) -> str:
    return (
        '<section class="recent" aria-labelledby="recent-title">'
        '<div class="section-heading"><span class="section-number">§ 01</span>'
        '<div><span class="eyebrow">All pages · no pagination</span>'
        '<h2 id="recent-title"><a href="recent.html">最近更新 <em>Recent</em></a></h2>'
        '<a class="section-link" href="recent.html">浏览全部页面 →</a></div></div>'
        f'<div class="recent-list">{page_rows(pages)}</div></section>'
    )


def listing_document(pages: list[Page], kind: str | None = None) -> str:
    if kind is None:
        title = "最近更新"
        english = "Recent"
        description = "全部知识页面，按更新时间倒序排列。"
        selected = pages
        css_path = "style.css"
        script_path = "wiki.js"
        home_path = "index.html"
        page_prefix = ""
    else:
        english, chinese, description = TYPE_META[kind]
        title = f"{english} · {chinese}"
        selected = [page for page in pages if page.kind == kind]
        css_path = "../style.css"
        script_path = "../wiki.js"
        home_path = "../index.html"
        page_prefix = "../"
    body = (
        f'<body class="listing"><nav><a href="{home_path}">← Wiki Index</a>'
        f'<span>{len(selected):02} pages</span></nav><main class="page">'
        f'<header class="listing-hero"><span class="eyebrow">Browse · no pagination</span>'
        f'<h1>{html.escape(title)}</h1><p>{html.escape(description)}</p></header>'
        f'<div class="recent-list">{page_rows(selected, page_prefix)}</div>'
        '<footer>Static HTML · GitHub Pages</footer></main>'
        f'<script src="{script_path}"></script></body>'
    )
    return shell(f"{title} · Wiki", css_path, body)


def index_document(pages: list[Page]) -> str:
    body = f'''<body class="home"><main class="page"><header class="mast"><span>Personal Wiki</span><span>AI maintained · Human reviewed</span></header><div class="cover"><span class="eyebrow">Living notes · {len(pages):03} pages</span><h1>Knowledge,<br><em>kept in motion.</em></h1><p>原始资料负责追溯，Markdown 负责结构，AI 协助整理，人负责判断。</p></div>{type_overview(pages)}{recent_pages(pages)}<footer>Static HTML · GitHub Pages</footer></main><script src="wiki.js"></script></body>'''
    return shell("Personal Knowledge Wiki", "style.css", body)


def write_site(pages: list[Page]) -> None:
    if OUTPUT_ROOT.exists(): shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir()
    shutil.copy2(ROOT / "assets/style.css", OUTPUT_ROOT / "style.css")
    shutil.copy2(ROOT / "assets/wiki.js", OUTPUT_ROOT / "wiki.js")
    page_map = {page.slug: page for page in pages}
    (OUTPUT_ROOT / "index.html").write_text(index_document(pages), encoding="utf-8")
    (OUTPUT_ROOT / "recent.html").write_text(listing_document(pages), encoding="utf-8")
    types_root = OUTPUT_ROOT / "types"
    types_root.mkdir()
    for kind in TYPE_META:
        (types_root / f"{kind}.html").write_text(listing_document(pages, kind), encoding="utf-8")
    for page in pages:
        target = OUTPUT_ROOT / page.url; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_document(page, pages, page_map), encoding="utf-8")
    manifest = [
        {
            "title": page.title,
            "slug": page.slug,
            "type": page.kind,
            "summary": page.summary,
            "updated": page.updated,
            "url": page.url,
        }
        for page in pages
    ]
    (OUTPUT_ROOT / "manifest.json").write_text(json.dumps({"version": 1, "pages": manifest}, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true"); args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        pages = load_pages(); validate_links(pages)
        if not args.check: write_site(pages)
        LOGGER.info("Wiki: %s %d page(s)", "validated" if args.check else "rendered", len(pages))
        return 0
    except BuildError as error:
        LOGGER.error("Wiki build failed: %s", error); return 1


if __name__ == "__main__":
    raise SystemExit(main())
