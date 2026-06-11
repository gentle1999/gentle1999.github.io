#!/usr/bin/env python3
"""Fetch pinned GitHub repository metadata and render Quarto snippets."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "repos.json"
GENERATED_DIR = ROOT / "_generated"
GENERATED_PATHS = {
    "en": GENERATED_DIR / "projects.en.qmd",
    "zh": GENERATED_DIR / "projects.zh.qmd",
}
LEGACY_GENERATED_PATH = GENERATED_DIR / "projects.qmd"
GITHUB_API = "https://api.github.com"
GITHUB_WEB = "https://github.com"


@dataclass(frozen=True)
class Repository:
    name: str
    full_name: str
    description: str
    url: str
    homepage: str | None
    language: str | None
    stars: int
    forks: int
    topics: list[str]
    archived: bool
    fork: bool
    pushed_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class PinnedRepository:
    owner: str
    name: str
    description: str | None = None
    language: str | None = None
    stars: int | None = None
    forks: int | None = None


class PinnedHTMLParser(HTMLParser):
    """Extract pinned repositories from a GitHub profile page."""

    def __init__(self) -> None:
        super().__init__()
        self._in_container = False
        self._container_depth = 0
        self._current_item_depth = 0
        self._current_repo: dict[str, Any] | None = None
        self._current_text_target: str | None = None
        self._current_anchor_href: str | None = None
        self._in_language = False
        self._in_stars = False
        self._in_forks = False
        self._in_description = False
        self.repositories: list[PinnedRepository] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if not self._in_container:
            if tag == "div" and "js-pinned-items-reorder-container" in classes:
                self._in_container = True
                self._container_depth = 1
            return

        self._container_depth += 1

        if tag == "li" and "pinned-item-list-item" in classes:
            self._current_item_depth = self._container_depth
            self._current_repo = {}
            return

        if self._current_repo is None:
            return

        if tag == "a" and "text-bold" in classes and "wb-break-word" in classes:
            self._current_text_target = "repo_name"
            self._current_anchor_href = attr.get("href")
            return

        if tag == "p" and "pinned-item-desc" in classes:
            self._in_description = True
            return

        if tag == "span" and attr.get("itemprop") == "programmingLanguage":
            self._in_language = True
            self._current_text_target = "language"
            return

        if tag == "a" and "pinned-item-meta" in classes and "stargazers" in (
            attr.get("href") or ""
        ):
            self._in_stars = True
            self._current_text_target = "stars"
            return

        if tag == "a" and "pinned-item-meta" in classes and "forks" in (
            attr.get("href") or ""
        ):
            self._in_forks = True
            self._current_text_target = "forks"
            return

    def handle_endtag(self, tag: str) -> None:
        if not self._in_container:
            return

        if self._current_repo is not None:
            if tag == "a" and self._current_text_target in {"repo_name", "stars", "forks"}:
                self._current_text_target = None
                self._current_anchor_href = None
                self._in_stars = False
                self._in_forks = False
            elif tag == "span" and self._current_text_target == "language":
                self._current_text_target = None
                self._in_language = False
            elif tag == "p" and self._in_description:
                self._in_description = False

            if tag == "li" and self._container_depth == self._current_item_depth:
                owner = str(self._current_repo.get("owner") or "")
                name = str(self._current_repo.get("name") or "")
                if owner and name:
                    self.repositories.append(
                        PinnedRepository(
                            owner=owner,
                            name=name,
                            description=self._current_repo.get("description"),
                            language=self._current_repo.get("language"),
                            stars=self._current_repo.get("stars"),
                            forks=self._current_repo.get("forks"),
                        )
                    )
                self._current_repo = None
                self._current_item_depth = 0

        self._container_depth -= 1
        if self._container_depth <= 0:
            self._in_container = False
            self._container_depth = 0

    def handle_data(self, data: str) -> None:
        if not self._in_container or self._current_repo is None:
            return

        text = data.strip()
        if not text:
            return

        if self._current_text_target == "repo_name":
            href = self._current_anchor_href or ""
            match = re.match(r"/([^/]+)/([^/]+)$", href)
            if match:
                self._current_repo["owner"] = match.group(1)
                self._current_repo["name"] = match.group(2)
            elif not self._current_repo.get("name"):
                self._current_repo["name"] = text
        elif self._current_text_target == "language":
            self._current_repo["language"] = text
        elif self._current_text_target == "stars":
            try:
                self._current_repo["stars"] = int(text.replace(",", ""))
            except ValueError:
                pass
        elif self._current_text_target == "forks":
            try:
                self._current_repo["forks"] = int(text.replace(",", ""))
            except ValueError:
                pass
        elif self._in_description and not self._current_repo.get("description"):
            self._current_repo["description"] = text


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def github_headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "quarto-academic-homepage",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def request_text(url: str, headers: dict[str, str]) -> tuple[str, dict[str, str]]:
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
            return payload, dict(response.headers.items())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub request failed: {exc.code} {exc.reason}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"GitHub request failed: {exc.reason}") from exc


def request_json(url: str, headers: dict[str, str]) -> tuple[Any, dict[str, str]]:
    payload, response_headers = request_text(url, headers)
    return json.loads(payload), response_headers


def fetch_profile_html(username: str) -> str:
    headers = {"User-Agent": "quarto-academic-homepage"}
    html, _ = request_text(f"{GITHUB_WEB}/{username}", headers)
    return html


def iter_pinned_repositories(username: str) -> list[PinnedRepository]:
    html = fetch_profile_html(username)
    parser = PinnedHTMLParser()
    parser.feed(html)
    return parser.repositories


def normalize_repository(raw: dict[str, Any]) -> Repository:
    return Repository(
        name=str(raw.get("name") or ""),
        full_name=str(raw.get("full_name") or ""),
        description=str(raw.get("description") or "").strip(),
        url=str(raw.get("html_url") or ""),
        homepage=(str(raw.get("homepage")).strip() or None) if raw.get("homepage") else None,
        language=raw.get("language"),
        stars=int(raw.get("stargazers_count") or 0),
        forks=int(raw.get("forks_count") or 0),
        topics=list(raw.get("topics") or []),
        archived=bool(raw.get("archived")),
        fork=bool(raw.get("fork")),
        pushed_at=raw.get("pushed_at"),
        updated_at=raw.get("updated_at"),
    )


def repository_from_cache(raw: dict[str, Any]) -> Repository:
    return Repository(
        name=str(raw.get("name") or ""),
        full_name=str(raw.get("full_name") or ""),
        description=str(raw.get("description") or "").strip(),
        url=str(raw.get("url") or ""),
        homepage=(str(raw.get("homepage")).strip() or None) if raw.get("homepage") else None,
        language=raw.get("language"),
        stars=int(raw.get("stars") or 0),
        forks=int(raw.get("forks") or 0),
        topics=list(raw.get("topics") or []),
        archived=bool(raw.get("archived")),
        fork=bool(raw.get("fork")),
        pushed_at=raw.get("pushed_at"),
        updated_at=raw.get("updated_at"),
    )


def load_cached_repositories(username: str) -> list[Repository]:
    if not DATA_PATH.exists():
        return []
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return []
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        cached_username = str(metadata.get("username") or "")
        if cached_username and cached_username != username:
            return []
    repositories = payload.get("repositories")
    if not isinstance(repositories, list):
        return []
    return [
        repository_from_cache(item)
        for item in repositories
        if isinstance(item, dict) and item.get("name") and item.get("url")
    ]


def fetch_repository(owner: str, name: str, token: str | None) -> Repository:
    headers = github_headers(token)
    url = f"{GITHUB_API}/repos/{owner}/{name}"
    raw, response_headers = request_json(url, headers)
    if not isinstance(raw, dict):
        raise RuntimeError(f"Unexpected GitHub API response for {owner}/{name}: {raw!r}")
    repository = normalize_repository(raw)
    remaining = int(response_headers.get("x-ratelimit-remaining", "1"))
    if remaining <= 1:
        reset_at = int(response_headers.get("x-ratelimit-reset", "0"))
        sleep_seconds = max(reset_at - int(time.time()), 0) + 1
        time.sleep(min(sleep_seconds, 60))
    return repository


def write_json(username: str, repositories: list[Repository]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "generated_at": utc_now(),
            "source": "github-pinned",
            "username": username,
            "count": len(repositories),
            "pinned_count": len(repositories),
        },
        "repositories": [asdict(repo) for repo in repositories],
    }
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_topics(topics: list[str]) -> str:
    if not topics:
        return ""
    return " ".join(f"`{markdown_escape(topic)}`" for topic in topics[:8])


def render_repository_card(repo: Repository, language_code: str) -> str:
    is_zh = language_code == "zh"
    description = markdown_escape(
        repo.description or ("暂无描述。" if is_zh else "No description provided.")
    )
    language = markdown_escape(repo.language or ("未注明" if is_zh else "Not specified"))
    updated = markdown_escape(
        (repo.pushed_at or repo.updated_at or ("未知" if is_zh else "Unknown")).split("T")[0]
    )
    topics = render_topics(repo.topics)
    homepage = f" · [Demo]({repo.homepage})" if repo.homepage else ""
    if repo.archived:
        archive_note = " · 已归档" if is_zh else " · archived"
    else:
        archive_note = ""
    fork_note = " · fork" if repo.fork else ""
    forks_label = "Forks" if not is_zh else "Fork"
    updated_label = "Updated" if not is_zh else "更新"
    topics_block = f"\n\n{topics}" if topics else ""
    return "\n".join(
        [
            "::: {.project-card}",
            f"### [{markdown_escape(repo.name)}]({repo.url})",
            "",
            description,
            "",
            (
                f"<span class=\"meta-pill\">{language}</span> "
                f"<span class=\"meta-pill\">★ {repo.stars}</span> "
                f"<span class=\"meta-pill\">{forks_label} {repo.forks}</span> "
                f"<span class=\"meta-pill\">{updated_label} {updated}</span>"
                f"{archive_note}{fork_note}{homepage}"
            ),
            topics_block,
            ":::",
        ]
    )


def render_quarto_snippet(username: str, repositories: list[Repository], language_code: str) -> str:
    is_zh = language_code == "zh"
    if not repositories:
        message = (
            f"未找到 `{username}` 的 pinned GitHub 仓库。"
            if is_zh
            else f"No pinned repositories were found for `{username}`."
        )
        return "\n".join(
            [
                "::: {.notice}",
                message,
                ":::",
                "",
            ]
        )

    cards = "\n\n".join(render_repository_card(repo, language_code) for repo in repositories)
    return "\n".join(
        [
            "::: {.project-grid}",
            cards,
            ":::",
            "",
        ]
    )


def write_quarto_snippets(username: str, repositories: list[Repository]) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    for language_code, path in GENERATED_PATHS.items():
        path.write_text(
            render_quarto_snippet(username, repositories, language_code),
            encoding="utf-8",
        )
    LEGACY_GENERATED_PATH.write_text(
        render_quarto_snippet(username, repositories, "en"),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default=os.getenv("GITHUB_USERNAME", "gentle1999"))
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    username = args.username.strip()
    if not username:
        raise SystemExit("GITHUB_USERNAME is empty.")

    try:
        pinned_repositories = iter_pinned_repositories(username=username)
        repositories = [
            fetch_repository(owner=repo.owner, name=repo.name, token=args.token)
            for repo in pinned_repositories
        ]
    except RuntimeError as exc:
        if env_flag("STRICT_UPDATES"):
            raise SystemExit(str(exc)) from exc
        print(f"warning: {exc}", file=sys.stderr)
        repositories = load_cached_repositories(username)
        if not repositories:
            print("warning: leaving existing repository data unchanged", file=sys.stderr)
            return 0
        write_quarto_snippets(username=username, repositories=repositories)
        print(f"Rendered {len(repositories)} cached pinned repositories")
        return 0

    write_json(username=username, repositories=repositories)
    write_quarto_snippets(username=username, repositories=repositories)
    print(f"Wrote {len(repositories)} pinned repositories to {DATA_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
