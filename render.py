from __future__ import annotations

import argparse
import html
import json
import logging
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
WIKI_ROOT = ROOT / "wiki"
OUTPUT_ROOT = ROOT / "site"
ALLOWED_TYPES = {"source", "concept", "topic", "thread"}
ALLOWED_ACCENTS = {"brick", "ochre", "moss", "deep"}
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


def index_document(pages: list[Page]) -> str:
    groups: list[str] = []
    for kind in ("source", "concept", "topic", "thread"):
        items = [page for page in pages if page.kind == kind]
        if not items: continue
        cards = "".join(f'<a class="card" href="{page.url}"><span>{kind}</span><h2>{html.escape(page.title)}</h2><p>{html.escape(page.summary)}</p><small>{page.updated}</small></a>' for page in items)
        groups.append(f'<section><div class="rule"><span>{kind}s</span><span>{len(items):02}</span></div><div class="grid">{cards}</div></section>')
    body = f'''<body><main class="page"><header class="mast"><span>Personal Wiki</span><span>AI maintained · Human reviewed</span></header><div class="cover"><span class="eyebrow">Living notes · {len(pages):03} pages</span><h1>Knowledge,<br><em>kept in motion.</em></h1><p>原始资料负责追溯，Markdown 负责结构，AI 协助整理，人负责判断。</p></div>{''.join(groups)}<footer>Static HTML · GitHub Pages</footer></main></body>'''
    return shell("Personal Knowledge Wiki", "style.css", body)


def write_site(pages: list[Page]) -> None:
    if OUTPUT_ROOT.exists(): shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir()
    shutil.copy2(ROOT / "assets/style.css", OUTPUT_ROOT / "style.css")
    shutil.copy2(ROOT / "assets/wiki.js", OUTPUT_ROOT / "wiki.js")
    page_map = {page.slug: page for page in pages}
    (OUTPUT_ROOT / "index.html").write_text(index_document(pages), encoding="utf-8")
    for page in pages:
        target = OUTPUT_ROOT / page.url; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_document(page, pages, page_map), encoding="utf-8")
    manifest = [{**asdict(page), "path": str(page.path.relative_to(ROOT)), "body": None, "url": page.url} for page in pages]
    for item in manifest: item.pop("body")
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
