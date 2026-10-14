#!/usr/bin/env python3
"""Resolve a public paper URL and create a Reading List issue.

The script is intentionally dependency-free so the owner-only GitHub workflow can
run it without installing packages. It rejects local/private network targets,
limits downloads, and extracts standard scholarly or social metadata.
"""

from __future__ import annotations

import argparse
import html
import ipaddress
import json
import os
import re
import socket
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_RESPONSE_BYTES = 2_000_000
USER_AGENT = "stayfish-wiki-reading-list/1.0 (+https://github.com/stayfish/wiki)"
TITLE_PREFIX = "[待读] "


class ResolutionError(RuntimeError):
    pass


class MetadataParser(HTMLParser):
    priorities = {
        "citation_title": 50,
        "dc.title": 40,
        "dcterms.title": 40,
        "og:title": 30,
        "twitter:title": 20,
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.candidates: list[tuple[int, str]] = []
        self.in_title = False
        self.title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "meta":
            key = (values.get("name") or values.get("property") or "").lower()
            content = values.get("content", "").strip()
            if key in self.priorities and content:
                self.candidates.append((self.priorities[key], content))
        elif tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    def best_title(self) -> str:
        if self.title_parts:
            self.candidates.append((10, " ".join(self.title_parts)))
        if not self.candidates:
            raise ResolutionError("网页没有可识别的标题元数据")
        return max(self.candidates, key=lambda item: item[0])[1]


def normalize_title(value: str) -> str:
    title = re.sub(r"\s+", " ", html.unescape(value)).strip()
    title = "".join(character for character in title if character.isprintable())
    if not title:
        raise ResolutionError("论文标题为空")
    return title[:220].rstrip()


def normalize_paper_url(value: str) -> str:
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ResolutionError("论文链接必须是公开的 http:// 或 https:// URL")
    return value


def metadata_url(paper_url: str) -> str:
    parsed = urlparse(paper_url)
    host = (parsed.hostname or "").lower()
    path = parsed.path
    if host in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}:
        match = re.match(r"/(?:abs|pdf|html)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?/?$", path)
        if match:
            return f"https://arxiv.org/abs/{match.group(1)}"
    if host == "huggingface.co":
        match = re.match(r"/papers/(\d{4}\.\d{4,5})(?:v\d+)?/?$", path)
        if match:
            return f"https://arxiv.org/abs/{match.group(1)}"
    return paper_url


def require_public_host(url: str) -> None:
    host = urlparse(url).hostname
    if not host or host.lower() == "localhost" or host.lower().endswith((".localhost", ".local")):
        raise ResolutionError("拒绝访问本机或局域网地址")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        try:
            addresses = {item[4][0] for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)}
        except socket.gaierror as error:
            raise ResolutionError(f"无法解析论文链接域名：{host}") from error
        if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
            raise ResolutionError("拒绝访问非公网地址")
    else:
        if not literal.is_global:
            raise ResolutionError("拒绝访问非公网地址")


class PublicRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):  # type: ignore[no-untyped-def]
        require_public_host(new_url)
        return super().redirect_request(request, file_pointer, code, message, headers, new_url)


def resolve_title(paper_url: str) -> str:
    target = metadata_url(normalize_paper_url(paper_url))
    require_public_host(target)
    request = Request(target, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    try:
        with build_opener(PublicRedirectHandler()).open(request, timeout=20) as response:
            content_type = response.headers.get_content_type()
            if content_type not in {"text/html", "application/xhtml+xml", "application/xml", "text/xml"}:
                raise ResolutionError(f"链接返回了不支持的内容类型：{content_type}")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ResolutionError("网页超过标题读取大小限制")
            charset = response.headers.get_content_charset() or "utf-8"
    except (HTTPError, URLError, TimeoutError) as error:
        raise ResolutionError(f"无法读取论文页面：{error}") from error
    parser = MetadataParser()
    parser.feed(raw.decode(charset, errors="replace"))
    return normalize_title(parser.best_title())


def github_request(method: str, path: str, token: str, payload: dict[str, object] | None = None) -> object:
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        f"https://api.github.com{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with build_opener().open(request, timeout=20) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError) as error:
        raise ResolutionError(f"GitHub API 请求失败：{error}") from error


def existing_issue(repository: str, token: str, paper_url: str) -> str | None:
    result = github_request("GET", f"/repos/{repository}/issues?state=open&per_page=100", token)
    if not isinstance(result, list):
        raise ResolutionError("GitHub Issues 返回了意外数据")
    for issue in result:
        if not isinstance(issue, dict) or "pull_request" in issue:
            continue
        user = issue.get("user")
        if not isinstance(user, dict) or user.get("login") != "github-actions[bot]":
            continue
        if "<!-- reading-list -->" not in str(issue.get("body", "")):
            continue
        if paper_url in str(issue.get("body", "")):
            return str(issue.get("html_url", ""))
    return None


def create_reading_issue(repository: str, token: str, paper_url: str, title: str) -> str:
    duplicate = existing_issue(repository, token, paper_url)
    if duplicate:
        return duplicate
    body = f"<!-- reading-list -->\n\n### 论文链接\n\n{paper_url}\n\n由仓库所有者通过 `Add to Reading List` 工作流创建。"
    result = github_request(
        "POST",
        f"/repos/{repository}/issues",
        token,
        {"title": f"{TITLE_PREFIX}{title}", "body": body},
    )
    if not isinstance(result, dict) or not result.get("html_url"):
        raise ResolutionError("GitHub 没有返回新 Issue 地址")
    return str(result["html_url"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paper_url")
    parser.add_argument("--title-only", action="store_true")
    args = parser.parse_args()
    try:
        paper_url = normalize_paper_url(args.paper_url)
        title = resolve_title(paper_url)
        if args.title_only:
            print(title)
            return 0
        repository = os.environ.get("GITHUB_REPOSITORY", "")
        token = os.environ.get("GH_TOKEN", "")
        if not repository or not token:
            raise ResolutionError("缺少 GITHUB_REPOSITORY 或 GH_TOKEN")
        issue_url = create_reading_issue(repository, token, paper_url, title)
        print(f"Reading issue: {issue_url}")
        return 0
    except ResolutionError as error:
        print(f"Reading list failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
