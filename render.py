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
ALLOWED_TYPES = {"glance", "deepnote", "concept", "topic", "thread"}
ALLOWED_ACCENTS = {"brick", "ochre", "moss", "deep"}
TYPE_META = {
    "glance": ("Glances", "速览", "完成价值判断的紧凑来源卡片"),
    "deepnote": ("Deepnotes", "精读", "重建方法、证据与后续问题的深入笔记"),
    "concept": ("Concepts", "概念", "跨来源复用的概念与机制"),
    "topic": ("Topics", "综合", "连接多个来源的横向主题"),
    "thread": ("Threads", "线索", "持续追踪的问题与思考"),
}
WIKILINK = re.compile(r"\[\[([a-z0-9][a-z0-9-]*)(?:\|([^\]]+))?\]\]")
INLINE = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\)|\[\[[^\]]+\]\])")
IMAGE = re.compile(r'^!\[([^]]+)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)$')
SECTION_ROLES = (
    ("reference", "Reference", ("来源", "wiki", "连接")),
    ("frontier", "Frontier", ("复现", "后续", "follow-up", "研究响应", "下一步")),
    ("contribution", "Contribution", ("贡献", "takeaway", "结论")),
    ("critique", "Critique", ("局限", "假设", "反例", "质疑", "边界")),
    ("evidence", "Evidence", ("实验", "证据", "验证", "结果", "论证")),
    ("method", "Method", ("方法", "数学", "理论", "机制", "pipeline", "formulation")),
    ("insight", "Insight", ("思路", "观察", "灵感", "猜想", "直觉", "idea")),
    ("context", "Context", ("为什么读", "问题", "背景", "相关工作", "挑战", "缺口")),
)


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
        directory = "sources" if self.kind in {"glance", "deepnote"} else f"{self.kind}s"
        return f"{directory}/{self.slug}.html"


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


def validate_assets(pages: list[Page]) -> None:
    failures: list[str] = []
    for page in pages:
        for line in page.body.splitlines():
            match = IMAGE.fullmatch(line.strip())
            if not match:
                continue
            src = match.group(2)
            if src.startswith(("http://", "https://", "data:")):
                continue
            target = (page.path.parent / src).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                failures.append(f"{page.path.relative_to(ROOT)} -> 路径越界: {src}")
                continue
            if not target.is_file():
                failures.append(f"{page.path.relative_to(ROOT)} -> 缺少图片: {src}")
    if failures:
        raise BuildError("无法解析的图片资源:\n  " + "\n  ".join(failures))


def heading_text(source: str) -> str:
    source = WIKILINK.sub(lambda match: match.group(2) or match.group(1), source)
    return re.sub(r"[`*_]", "", source).strip()


def section_role(title: str) -> tuple[str, str]:
    lowered = title.lower()
    for role, label, keywords in SECTION_ROLES:
        if any(keyword.lower() in lowered for keyword in keywords):
            return role, label
    return "note", "Reading Note"


def reading_outline(source: str) -> list[dict[str, object]]:
    outline: list[dict[str, object]] = []
    in_code = False
    section_number = 0
    child_number = 0
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        heading = re.match(r"^(#{2,3})\s+(.+)$", stripped)
        if not heading:
            continue
        title = heading_text(heading.group(2))
        if len(heading.group(1)) == 2:
            section_number += 1
            child_number = 0
            role, label = section_role(title)
            outline.append({"id": f"block-{section_number:02}", "title": title, "role": role, "label": label, "children": []})
        elif outline:
            child_number += 1
            children = outline[-1]["children"]
            assert isinstance(children, list)
            children.append({"id": f"block-{section_number:02}-{child_number:02}", "title": title})
    return outline


def reading_map(source: str) -> str:
    items: list[str] = []
    for block in reading_outline(source):
        children = block["children"]
        child_html = ""
        if isinstance(children, list) and children:
            child_html = '<ol class="reading-map-children">' + "".join(
                f'<li><a href="#{html.escape(str(child["id"]), quote=True)}">{html.escape(str(child["title"]))}</a></li>'
                for child in children
            ) + "</ol>"
        items.append(
            f'<li data-role="{html.escape(str(block["role"]), quote=True)}">'
            f'<a href="#{html.escape(str(block["id"]), quote=True)}">'
            f'<span>{html.escape(str(block["label"]))}</span>{html.escape(str(block["title"]))}</a>{child_html}</li>'
        )
    return (
        '<aside class="reading-map" aria-label="分层阅读地图">'
        '<span class="eyebrow">Reading map</span><h2>分层阅读地图</h2>'
        '<ol class="reading-map-list">' + "".join(items) + "</ol></aside>"
    )


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


def markdown_to_html(source: str, pages: dict[str, Page], card_sections: bool = False) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    bullets: list[str] = []
    numbered: list[str] = []
    table_rows: list[list[str]] = []
    code: list[str] = []
    raw: list[str] = []
    in_figure = False
    in_code = False
    section_open = False
    section_number = 0
    child_number = 0

    def flush() -> None:
        if paragraph:
            output.append(f"<p>{inline_markup(' '.join(paragraph), pages)}</p>")
            paragraph.clear()
        if bullets:
            output.append("<ul>" + "".join(f"<li>{item}</li>" for item in bullets) + "</ul>")
            bullets.clear()
        if numbered:
            output.append("<ol>" + "".join(f"<li>{item}</li>" for item in numbered) + "</ol>")
            numbered.clear()
        if table_rows:
            if len(table_rows) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in table_rows[1]):
                head = "<thead><tr>" + "".join(f"<th>{inline_markup(cell, pages)}</th>" for cell in table_rows[0]) + "</tr></thead>"
                body_rows = table_rows[2:]
            else:
                head = ""
                body_rows = table_rows
            body = "<tbody>" + "".join(
                "<tr>" + "".join(f"<td>{inline_markup(cell, pages)}</td>" for cell in row) + "</tr>"
                for row in body_rows
            ) + "</tbody>"
            output.append(f'<div class="table-scroll"><table>{head}{body}</table></div>')
            table_rows.clear()

    for line in source.splitlines():
        stripped = line.strip()
        is_table_row = stripped.startswith("|") and stripped.endswith("|")
        if table_rows and not is_table_row:
            flush()
        if in_code:
            if stripped.startswith("```"):
                output.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
                code.clear(); in_code = False
            else:
                code.append(line)
            continue
        if in_figure:
            raw.append(line)
            if stripped == "</figure>":
                output.append("\n".join(raw)); raw.clear(); in_figure = False
            continue
        if stripped.startswith("<figure"):
            flush(); in_figure = True; raw.append(line); continue
        if stripped.startswith("```"):
            flush(); in_code = True; continue
        if not stripped:
            flush(); continue
        if is_table_row:
            if paragraph or bullets or numbered:
                flush()
            table_rows.append([cell.strip() for cell in stripped[1:-1].split("|")])
            continue
        image_match = IMAGE.fullmatch(stripped)
        if image_match:
            flush()
            alt, src, title = image_match.groups()
            if src.startswith("../../assets/papers/"):
                src = "../paper-assets/" + src.removeprefix("../../assets/papers/")
            caption = title or alt
            output.append(
                '<figure class="paper-figure">'
                f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}" loading="lazy">'
                f'<figcaption>{inline_markup(caption, pages)}</figcaption></figure>'
            )
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            flush(); level = len(heading.group(1))
            if level == 2 and card_sections:
                if section_open:
                    output.append("</div></section>")
                section_number += 1
                child_number = 0
                title = heading_text(heading.group(2))
                role, label = section_role(title)
                section_id = f"block-{section_number:02}"
                output.append(
                    f'<section class="note-card role-{role}" id="{section_id}" data-block-role="{role}">'
                    '<header class="note-card-header">'
                    f'<div><span class="block-kicker">Block {section_number:02} · {label}</span>'
                    f'<h2>{inline_markup(heading.group(2), pages)}</h2></div>'
                    '<div class="card-actions">'
                    f'<button type="button" class="section-copy" data-copy-section="{section_id}" aria-label="复制本节链接">复制链接</button>'
                    '<button type="button" class="section-toggle" aria-expanded="true" aria-label="折叠本节">收起</button>'
                    '</div></header><div class="note-card-body">'
                )
                section_open = True
            elif level == 3 and card_sections and section_open:
                child_number += 1
                child_id = f"block-{section_number:02}-{child_number:02}"
                output.append(f'<h3 id="{child_id}">{inline_markup(heading.group(2), pages)}</h3>')
            elif level > 1:
                output.append(f"<h{level}>{inline_markup(heading.group(2), pages)}</h{level}>")
            continue
        bullet = re.match(r"^-\s+(.+)$", stripped)
        if bullet:
            if paragraph or numbered: flush()
            bullets.append(inline_markup(bullet.group(1), pages)); continue
        number = re.match(r"^\d+\.\s+(.+)$", stripped)
        if number:
            if paragraph or bullets: flush()
            numbered.append(inline_markup(number.group(1), pages)); continue
        paragraph.append(stripped)
    flush()
    if in_figure:
        raise BuildError("未闭合的 <figure>")
    if in_code:
        raise BuildError("未闭合的代码块")
    if section_open:
        output.append("</div></section>")
    return "\n".join(output)


def shell(title: str, css_path: str, body: str) -> str:
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,300..900,0..100,0..1&family=Newsreader:opsz,wght@6..72,300..700&family=Noto+Serif+SC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet"><link rel="stylesheet" href="{css_path}"><script>MathJax={{tex:{{inlineMath:[['$','$']],displayMath:[['$$','$$']]}}}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script></head>{body}</html>'''


def page_document(page: Page, pages: list[Page], page_map: dict[str, Page]) -> str:
    links = [item for item in pages if item.slug != page.slug and re.search(rf"\[\[{re.escape(page.slug)}(?:\||\]\])", item.body)]
    backlinks = ""
    if links:
        backlinks = '<aside><span class="eyebrow">引用此页</span><ul>' + "".join(f'<li><a href="../{item.url}">{html.escape(item.title)}</a></li>' for item in links) + "</ul></aside>"
    is_deepnote = page.kind == "deepnote"
    rendered = markdown_to_html(page.body, page_map, card_sections=is_deepnote)
    if is_deepnote:
        controls = (
            '<div class="reading-toolbar" role="toolbar" aria-label="阅读控制">'
            '<button type="button" data-reading-action="expand">全部展开</button>'
            '<button type="button" data-reading-action="collapse">全部折叠</button>'
            '<button type="button" data-reading-action="focus" aria-pressed="false">聚焦当前</button>'
            '</div>'
        )
        content = f'{controls}<div class="reading-shell">{reading_map(page.body)}<article class="block-article">{rendered}</article></div>'
        progress = '<div class="reading-progress" aria-hidden="true"><span></span></div>'
        body_class = ' class="reading-page-body"'
        main_class = "page reading-page"
    else:
        content = f'<article>{rendered}</article>'
        progress = ""
        body_class = ""
        main_class = "page"
    body = f'''<body{body_class} data-accent="{page.accent}"><nav><a href="../index.html">← Wiki Index</a><span>{page.kind} · {page.slug}</span></nav>{progress}<main class="{main_class}"><header class="hero"><span class="eyebrow">{page.kind} · {page.updated}</span><h1>{html.escape(page.title)}</h1><p>{html.escape(page.summary)}</p></header>{content}{backlinks}<footer>AI maintained · Human reviewed</footer></main><script src="../wiki.js"></script></body>'''
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
    paper_assets = ROOT / "assets/papers"
    if paper_assets.exists():
        shutil.copytree(paper_assets, OUTPUT_ROOT / "paper-assets")
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
        pages = load_pages(); validate_links(pages); validate_assets(pages)
        if not args.check: write_site(pages)
        LOGGER.info("Wiki: %s %d page(s)", "validated" if args.check else "rendered", len(pages))
        return 0
    except BuildError as error:
        LOGGER.error("Wiki build failed: %s", error); return 1


if __name__ == "__main__":
    raise SystemExit(main())
