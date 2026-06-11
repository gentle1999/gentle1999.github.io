#!/usr/bin/env python3
"""Fetch publication metadata from ORCID and Crossref and render Quarto snippets."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "publications.json"
OVERRIDES_PATH = ROOT / "data" / "publication_overrides.json"
IMAGE_MANIFEST_PATH = ROOT / "data" / "publication_images.json"
PDF_MANIFEST_PATH = ROOT / "data" / "publication_pdfs.json"
BIB_PATH = ROOT / "publications.bib"
GENERATED_DIR = ROOT / "_generated"
GENERATED_PATHS = {
    "en": GENERATED_DIR / "publications.en.qmd",
    "zh": GENERATED_DIR / "publications.zh.qmd",
}
LEGACY_GENERATED_PATH = GENERATED_DIR / "publications.qmd"
ORCID_API = "https://pub.orcid.org/v3.0"
CROSSREF_API = "https://api.crossref.org/works"


@dataclass(frozen=True)
class Publication:
    title: str
    year: int | None
    type: str
    authors: list[str]
    journal: str | None
    journal_short: str | None
    volume: str | None
    issue: str | None
    pages: str | None
    article_number: str | None
    doi: str | None
    url: str | None
    source: str
    abstract: str | None = None
    image: str | None = None
    image_alt: str | None = None


@dataclass(frozen=True)
class AuthorIdentity:
    orcid: str | None
    primary_name: str | None
    aliases: list[str]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def request_json(url: str, headers: dict[str, str] | None = None) -> Any:
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "quarto-academic-homepage",
    }
    if headers:
        request_headers.update(headers)
    request = Request(url, headers=request_headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Request failed: {exc.code} {exc.reason}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Request failed: {exc.reason}") from exc


def first(value: Any) -> Any:
    if isinstance(value, list) and value:
        return value[0]
    return None


def parse_year(date_parts: Any) -> int | None:
    part = first(date_parts)
    if isinstance(part, list) and part:
        try:
            return int(part[0])
        except (TypeError, ValueError):
            return None
    return None


def clean_text(value: object | None) -> str:
    if not value:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = value.replace("\x85", "...").replace("\x91", "'").replace("\x92", "'")
    value = value.replace("\x93", '"').replace("\x94", '"').replace("\x96", "-")
    value = value.replace("\x97", "-")
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def clean_abstract(value: str | None) -> str:
    value = clean_text(value)
    if not value:
        return ""

    for _ in range(3):
        updated = re.sub(
            r"^\s*(?:abstract|summary)(?:\s*[\.:：\-–—]\s*|\s+|(?=[A-Z0-9(]))",
            "",
            value,
            flags=re.IGNORECASE,
        )
        updated = re.sub(r"^\s*摘要\s*[\.:：\-–—]?\s*", "", updated)
        updated = updated.strip()
        if updated == value:
            break
        value = updated
    return value


def clean_orcid(orcid: str) -> str:
    value = orcid.strip()
    value = value.removeprefix("https://orcid.org/")
    value = value.removeprefix("http://orcid.org/")
    return value


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    value = doi.strip()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    return value.lower() or None


def doi_url(doi: str | None) -> str | None:
    return f"https://doi.org/{doi}" if doi else None


def fetch_orcid_person(orcid: str) -> dict[str, Any]:
    url = f"{ORCID_API}/{quote(orcid)}/person"
    payload = request_json(url, headers={"Accept": "application/vnd.orcid+json"})
    if not isinstance(payload, dict):
        return {}
    return payload


def value_field(payload: Any) -> str:
    if isinstance(payload, dict):
        value = payload.get("value")
        if isinstance(value, str):
            return clean_text(value)
    return ""


def orcid_registered_name(person: dict[str, Any]) -> str:
    name = person.get("name")
    if not isinstance(name, dict):
        return ""

    credit_name = value_field(name.get("credit-name"))
    if credit_name:
        return credit_name

    given_names = value_field(name.get("given-names"))
    family_name = value_field(name.get("family-name"))
    return " ".join(part for part in [given_names, family_name] if part).strip()


def orcid_other_names(person: dict[str, Any]) -> list[str]:
    other_names = (person.get("other-names") or {}).get("other-name") if person else []
    if not isinstance(other_names, list):
        return []

    values: list[str] = []
    seen: set[str] = set()
    for item in other_names:
        if not isinstance(item, dict):
            continue
        content = clean_text(str(item.get("content") or ""))
        key = normalize_author_name(content)
        if content and key not in seen:
            seen.add(key)
            values.append(content)
    return values


def author_identity_from_orcid(orcid: str) -> AuthorIdentity:
    person = fetch_orcid_person(orcid)
    primary_name = orcid_registered_name(person) or None
    aliases = []
    if primary_name:
        aliases.append(primary_name)
    aliases.extend(orcid_other_names(person))
    return AuthorIdentity(
        orcid=orcid,
        primary_name=primary_name,
        aliases=deduplicate_author_aliases(aliases),
    )


def deduplicate_author_aliases(aliases: list[str]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for alias in aliases:
        alias = clean_text(alias)
        key = normalize_author_name(alias)
        if alias and key and key not in seen:
            seen.add(key)
            values.append(alias)
    return values


def fallback_author_aliases(author_query: str) -> list[str]:
    values = []
    for value in [
        os.getenv("PROFILE_NAME", ""),
        os.getenv("PROFILE_DISPLAY_NAME", ""),
        os.getenv("DISPLAY_NAME", ""),
        os.getenv("PROFILE_NAME_ZH", ""),
        os.getenv("PROFILE_ALIASES", ""),
        os.getenv("PROFILE_ALIASES_ZH", ""),
        author_query,
    ]:
        values.extend(part.strip() for part in re.split(r"[;,；]", value) if part.strip())
    return deduplicate_author_aliases(values)


def normalize_author_name(value: str) -> str:
    value = clean_text(value)
    value = unicodedata.normalize("NFKC", value)
    value = value.translate(UNICODE_BIBTEX_REPLACEMENTS)
    value = value.casefold()
    value = value.replace("-", "")
    value = re.sub(r"[\W_]+", "", value, flags=re.UNICODE)
    return value


def is_target_author(author: str, aliases: list[str]) -> bool:
    normalized_author = normalize_author_name(author)
    return bool(normalized_author) and normalized_author in {
        normalize_author_name(alias) for alias in aliases
    }


def authors_from_crossref(item: dict[str, Any]) -> list[str]:
    authors: list[str] = []
    for author in item.get("author") or []:
        given = author.get("given") or ""
        family = author.get("family") or ""
        name = clean_text(" ".join(part for part in [given, family] if part).strip())
        if name:
            authors.append(name)
    return authors


def publication_from_crossref_item(item: dict[str, Any], source: str = "crossref") -> Publication:
    doi = normalize_doi(item.get("DOI"))
    year = (
        parse_year((item.get("published-print") or {}).get("date-parts"))
        or parse_year((item.get("published-online") or {}).get("date-parts"))
        or parse_year((item.get("issued") or {}).get("date-parts"))
    )
    container = first(item.get("container-title")) or first(item.get("short-container-title"))
    short_container = first(item.get("short-container-title"))
    return Publication(
        title=clean_text(first(item.get("title")) or "Untitled publication"),
        year=year,
        type=str(item.get("type") or "publication"),
        authors=authors_from_crossref(item),
        journal=clean_text(container),
        journal_short=clean_text(short_container) or None,
        volume=clean_text(item.get("volume")) or None,
        issue=clean_text(item.get("issue")) or None,
        pages=clean_text(item.get("page")) or None,
        article_number=clean_text(item.get("article-number") or item.get("article_number"))
        or None,
        doi=doi,
        url=item.get("URL") or doi_url(doi),
        source=source,
        abstract=clean_abstract(item.get("abstract")) or None,
    )


def fetch_crossref_by_doi(doi: str, email: str | None) -> Publication | None:
    params = {"mailto": email} if email else {}
    url = f"{CROSSREF_API}/{quote(doi)}"
    if params:
        url = f"{url}?{urlencode(params)}"
    payload = request_json(url)
    item = payload.get("message")
    if not isinstance(item, dict):
        return None
    return publication_from_crossref_item(item, source="orcid+crossref")


def fetch_orcid_works(orcid: str) -> list[dict[str, Any]]:
    url = f"{ORCID_API}/{quote(orcid)}/works"
    payload = request_json(url, headers={"Accept": "application/vnd.orcid+json"})
    groups = payload.get("group") or []
    if not isinstance(groups, list):
        return []
    return groups


def external_ids(summary: dict[str, Any]) -> list[dict[str, Any]]:
    ids = ((summary.get("external-ids") or {}).get("external-id")) or []
    return ids if isinstance(ids, list) else []


def doi_from_orcid_summary(summary: dict[str, Any]) -> str | None:
    for item in external_ids(summary):
        if str(item.get("external-id-type") or "").lower() == "doi":
            return normalize_doi(item.get("external-id-value"))
    return None


def publication_from_orcid_summary(summary: dict[str, Any]) -> Publication:
    title_block = summary.get("title") or {}
    title = ((title_block.get("title") or {}).get("value")) or "Untitled publication"
    journal = ((summary.get("journal-title") or {}).get("value")) or None
    year = None
    publication_date = summary.get("publication-date") or {}
    if publication_date.get("year"):
        try:
            year = int(publication_date["year"]["value"])
        except (KeyError, TypeError, ValueError):
            year = None
    doi = doi_from_orcid_summary(summary)
    url = None
    if summary.get("url"):
        url = summary["url"].get("value")
    return Publication(
        title=clean_text(title),
        year=year,
        type=str(summary.get("type") or "publication"),
        authors=[],
        journal=clean_text(journal),
        journal_short=None,
        volume=None,
        issue=None,
        pages=None,
        article_number=None,
        doi=doi,
        url=url or doi_url(doi),
        source="orcid",
    )


def publications_from_orcid(orcid: str, crossref_email: str | None) -> list[Publication]:
    publications: list[Publication] = []
    for group in fetch_orcid_works(orcid):
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        summary = summaries[0]
        doi = doi_from_orcid_summary(summary)
        publication = None
        if doi:
            try:
                publication = fetch_crossref_by_doi(doi, crossref_email)
            except RuntimeError as exc:
                print(f"warning: Crossref lookup failed for DOI {doi}: {exc}", file=sys.stderr)
        publications.append(publication or publication_from_orcid_summary(summary))
    return publications


def publications_from_crossref_author(
    author_query: str,
    email: str | None,
    limit: int,
) -> list[Publication]:
    params = {
        "query.author": author_query,
        "rows": str(limit),
        "sort": "published",
        "order": "desc",
    }
    if email:
        params["mailto"] = email
    payload = request_json(f"{CROSSREF_API}?{urlencode(params)}")
    items = ((payload.get("message") or {}).get("items")) or []
    if not isinstance(items, list):
        return []
    return [publication_from_crossref_item(item) for item in items]


def deduplicate(publications: list[Publication]) -> list[Publication]:
    seen: set[str] = set()
    deduped: list[Publication] = []
    for publication in publications:
        key = publication.doi or re.sub(r"\W+", "", publication.title.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(publication)
    return deduped


def publication_sort_key(publication: Publication) -> tuple[int, str]:
    return (publication.year or 0, publication.title.lower())


def load_overrides() -> dict[str, dict[str, str]]:
    if not OVERRIDES_PATH.exists():
        return {}
    payload = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{OVERRIDES_PATH.relative_to(ROOT)} must contain a JSON object.")

    overrides: dict[str, dict[str, str]] = {}
    for key, value in payload.items():
        if not isinstance(value, dict):
            continue
        normalized_key = normalize_doi(str(key)) or str(key).strip().lower()
        overrides[normalized_key] = {
            str(field): str(field_value)
            for field, field_value in value.items()
            if isinstance(field_value, str)
        }
    return overrides


def load_raw_overrides() -> dict[str, dict[str, Any]]:
    if not OVERRIDES_PATH.exists():
        return {}
    payload = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{OVERRIDES_PATH.relative_to(ROOT)} must contain a JSON object.")

    overrides: dict[str, dict[str, Any]] = {}
    for key, value in payload.items():
        if not isinstance(value, dict):
            continue
        normalized_key = normalize_doi(str(key)) or str(key).strip().lower()
        overrides[normalized_key] = value
    return overrides


def load_image_manifest() -> dict[str, dict[str, Any]]:
    if not IMAGE_MANIFEST_PATH.exists():
        return {}
    payload = json.loads(IMAGE_MANIFEST_PATH.read_text(encoding="utf-8"))
    images = payload.get("images") if isinstance(payload, dict) else {}
    if not isinstance(images, dict):
        raise RuntimeError(f"{IMAGE_MANIFEST_PATH.relative_to(ROOT)} has invalid image data.")

    overrides: dict[str, dict[str, Any]] = {}
    for key, value in images.items():
        if not isinstance(value, dict):
            continue
        normalized_key = normalize_doi(str(key)) or str(key).strip().lower()
        image = value.get("image")
        if not isinstance(image, str) or not image.strip():
            continue
        overrides[normalized_key] = {
            "image": image,
            "image_alt": value.get("image_alt"),
            "image_source_url": value.get("source_url"),
            "image_confidence": value.get("confidence"),
            "image_kind": value.get("kind"),
        }
    return overrides


def load_pdf_manifest() -> dict[str, dict[str, Any]]:
    if not PDF_MANIFEST_PATH.exists():
        return {}
    payload = json.loads(PDF_MANIFEST_PATH.read_text(encoding="utf-8"))
    pdfs = payload.get("pdfs") if isinstance(payload, dict) else {}
    if not isinstance(pdfs, dict):
        raise RuntimeError(f"{PDF_MANIFEST_PATH.relative_to(ROOT)} has invalid PDF data.")

    overrides: dict[str, dict[str, Any]] = {}
    for key, value in pdfs.items():
        if not isinstance(value, dict):
            continue
        normalized_key = normalize_doi(str(key)) or str(key).strip().lower()
        pdf = value.get("pdf")
        if not isinstance(pdf, str) or not pdf.strip():
            continue
        overrides[normalized_key] = {
            "pdf": pdf,
            "pdf_source_url": value.get("source_url"),
            "pdf_kind": value.get("kind"),
            "pdf_license_note": value.get("license_note"),
        }
    return overrides


def merge_overrides(
    generated: dict[str, dict[str, Any]],
    manual: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for source in [generated, manual]:
        for key, value in source.items():
            merged.setdefault(key, {}).update(value)
    return merged


def overrides_for_publication(
    publication: Publication,
    overrides: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    keys = []
    if publication.doi:
        keys.append(publication.doi)
    keys.append(re.sub(r"\W+", "", publication.title.lower()))
    for key in keys:
        if key in overrides:
            return overrides[key]
    return {}


def author_replacements_for_publication(
    publication: Publication,
    overrides: dict[str, dict[str, Any]],
) -> dict[str, str]:
    replacement_payload = overrides_for_publication(publication, overrides).get(
        "author_replacements",
        {},
    )
    if not isinstance(replacement_payload, dict):
        return {}
    return {
        normalize_author_name(str(source)): clean_text(str(target))
        for source, target in replacement_payload.items()
        if clean_text(str(target))
    }


def corrected_author(author: str, replacements: dict[str, str]) -> str:
    return replacements.get(normalize_author_name(author), author)


def corrected_authors(publication: Publication, overrides: dict[str, dict[str, Any]]) -> list[str]:
    replacements = author_replacements_for_publication(publication, overrides)
    return [corrected_author(author, replacements) for author in publication.authors]


def corrected_publication(
    publication: Publication,
    overrides: dict[str, dict[str, Any]],
) -> Publication:
    publication_overrides = overrides_for_publication(publication, overrides)
    title = str(publication_overrides.get("title", publication.title))
    journal = publication_overrides.get("journal", publication.journal)
    journal_short = publication_overrides.get("journal_short", publication.journal_short)
    volume = publication_overrides.get("volume", publication.volume)
    issue = publication_overrides.get("issue", publication.issue)
    pages = publication_overrides.get("pages", publication.pages)
    article_number = publication_overrides.get("article_number", publication.article_number)
    abstract = publication_overrides.get("abstract", publication.abstract)
    image = publication_overrides.get("image") or publication_overrides.get("toc_image")
    image_alt = publication_overrides.get("image_alt") or publication_overrides.get(
        "toc_image_alt",
    )
    return Publication(
        title=clean_text(title),
        year=publication.year,
        type=publication.type,
        authors=corrected_authors(publication, overrides),
        journal=clean_text(str(journal)) if journal else None,
        journal_short=clean_text(str(journal_short)) if journal_short else None,
        volume=clean_text(str(volume)) if volume else None,
        issue=clean_text(str(issue)) if issue else None,
        pages=clean_text(str(pages)) if pages else None,
        article_number=clean_text(str(article_number)) if article_number else None,
        doi=publication.doi,
        url=publication.url,
        source=publication.source,
        abstract=clean_abstract(str(abstract)) if abstract else None,
        image=clean_text(str(image)) if image else None,
        image_alt=clean_text(str(image_alt)) if image_alt else None,
    )


def author_match_positions(publication: Publication, aliases: list[str]) -> list[int]:
    return [
        index
        for index, author in enumerate(publication.authors, start=1)
        if is_target_author(author, aliases)
    ]


def publication_payload(
    publication: Publication,
    identity: AuthorIdentity,
    overrides: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    corrected = corrected_publication(publication, overrides)
    payload = asdict(corrected)
    payload["matched_author_positions"] = author_match_positions(corrected, identity.aliases)
    publication_overrides = overrides_for_publication(corrected, overrides)
    if publication_overrides.get("pdf"):
        payload["pdf"] = publication_overrides["pdf"]
    if corrected.authors != publication.authors:
        payload["source_authors"] = publication.authors
    return payload


def write_json(
    publications: list[Publication],
    sources: list[str],
    orcid: str | None,
    identity: AuthorIdentity,
    overrides: dict[str, dict[str, Any]],
) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "generated_at": utc_now(),
            "sources": sources,
            "orcid": orcid,
            "count": len(publications),
            "author_identity": {
                "orcid": identity.orcid,
                "primary_name": identity.primary_name,
                "aliases": identity.aliases,
            },
        },
        "publications": [
            publication_payload(publication, identity, overrides) for publication in publications
        ],
    }
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def html_text(value: str) -> str:
    return html.escape(value, quote=False)


def html_attr(value: str) -> str:
    return html.escape(value, quote=True)


def page_asset_path(path: str, language_code: str) -> str:
    if re.match(r"^(?:[a-z][a-z0-9+.-]*:|/|#)", path, flags=re.IGNORECASE):
        return path
    return "/" + path.lstrip("./")


def override_text(
    publication: Publication,
    overrides: dict[str, dict[str, Any]],
    field: str,
) -> str | None:
    value = overrides_for_publication(publication, overrides).get(field)
    if not isinstance(value, str):
        return None
    return clean_abstract(value) or None


def render_author(author: str, aliases: list[str]) -> str:
    escaped_author = html_text(markdown_escape(author))
    if is_target_author(author, aliases):
        return f"<span class=\"self-author\">{escaped_author}</span>"
    return escaped_author


def render_authors(authors: list[str], aliases: list[str]) -> str:
    if not authors:
        return ""
    return ", ".join(render_author(author, aliases) for author in authors)


def render_publication(
    publication: Publication,
    language_code: str,
    identity: AuthorIdentity,
    overrides: dict[str, dict[str, Any]],
) -> str:
    is_zh = language_code == "zh"
    title = html_text(markdown_escape(publication.title))
    year = str(publication.year) if publication.year else ("日期未知" if is_zh else "n.d.")
    venue = html_text(markdown_escape(publication.journal or publication.type))
    authors = render_authors(publication.authors, identity.aliases)
    doi = (
        f" · <a href=\"https://doi.org/{html_attr(publication.doi)}\">DOI</a>"
        if publication.doi
        else ""
    )
    link_label = "链接" if is_zh else "Link"
    url = (
        f" · <a href=\"{html_attr(publication.url)}\">{link_label}</a>"
        if publication.url and not publication.doi
        else ""
    )
    publication_overrides = overrides_for_publication(publication, overrides)
    pdf = publication_overrides.get("pdf")
    pdf_label = "PDF" if not is_zh else "PDF"
    pdf_link = ""
    if isinstance(pdf, str) and pdf.strip():
        pdf_path = page_asset_path(pdf, language_code)
        pdf_link = (
            f" · <a class=\"publication-pdf-link\" "
            f"href=\"{html_attr(pdf_path)}\" download>{pdf_label}</a>"
        )
    code_url = publication_overrides.get("code_url")
    code_label = str(publication_overrides.get("code_label") or ("代码" if is_zh else "Code"))
    code_link = ""
    if isinstance(code_url, str) and code_url.strip():
        code_link = (
            f" · <a class=\"publication-code-link\" "
            f"href=\"{html_attr(code_url)}\">{html_text(code_label)}</a>"
        )
    image = publication.image
    image_alt = publication.image_alt or publication.title
    abstract = override_text(publication, overrides, "abstract_zh") if is_zh else None
    abstract = abstract or publication.abstract
    abstract_label = "摘要" if is_zh else "Abstract"
    image_label = "TOC 图" if is_zh else "TOC image"
    details_label = "详情" if is_zh else "Details"
    details_available = bool(abstract or image)
    thumbnail = ""
    expanded_image = ""
    if image:
        image_path = page_asset_path(image, language_code)
        thumbnail = (
            f"<img class=\"publication-thumbnail\" src=\"{html_attr(image_path)}\" "
            f"alt=\"{html_attr(image_alt)}\">"
        )
        expanded_image = "\n".join(
            [
                "<figure class=\"publication-expanded-figure\">",
                (
                    f"<img src=\"{html_attr(image_path)}\" "
                    f"alt=\"{html_attr(image_alt)}\">"
                ),
                f"<figcaption>{image_label}</figcaption>",
                "</figure>",
            ]
        )
    abstract_block = ""
    if abstract:
        abstract_block = "\n".join(
            [
                "<div class=\"publication-abstract\">",
                f"<strong>{abstract_label}.</strong> {html_text(abstract)}",
                "</div>",
            ]
        )
    details_block = ""
    if details_available:
        expanded_class = (
            "publication-expanded publication-expanded-with-image"
            if image
            else "publication-expanded publication-expanded-no-image"
        )
        details_block = "\n".join(
            [
                f"<div class=\"{expanded_class}\">",
                expanded_image,
                abstract_block,
                "</div>",
            ]
        )
    summary_class = (
        "publication-summary publication-summary-clickable"
        if details_available
        else "publication-summary"
    )
    header_tag = "summary" if details_available else "div"
    body = "\n".join(
        part
        for part in [
            f"<{header_tag} class=\"{summary_class}\">",
            "<div class=\"publication-main\">",
            f"<h3>{title}</h3>",
            f"<p class=\"publication-authors\">{authors}</p>" if authors else "",
            (
                "<p class=\"publication-meta\">"
                f"<span class=\"meta-pill\">{year}</span> "
                f"<span class=\"meta-pill\">{venue}</span>{doi}{url}{pdf_link}{code_link}</p>"
            ),
            (
                f"<span class=\"publication-toggle\">{details_label}</span>"
                if details_available
                else ""
            ),
            "</div>",
            (
                f"<div class=\"publication-media\">{thumbnail}</div>"
                if thumbnail
                else ""
            ),
            f"</{header_tag}>",
            details_block,
        ]
        if part
    )
    tag = "details" if details_available else "div"
    return "\n".join(
        [
            f"<{tag} class=\"publication-entry\">",
            body,
            f"</{tag}>",
        ]
    )


def render_quarto_snippet(
    publications: list[Publication],
    sources: list[str],
    language_code: str,
    identity: AuthorIdentity,
    overrides: dict[str, dict[str, Any]],
) -> str:
    is_zh = language_code == "zh"
    if not publications:
        message = (
            "暂无论文元数据。请配置 `ORCID_ID` 后运行 `make update-publications`。"
            if is_zh
            else (
                "No publication metadata are available yet. Configure `ORCID_ID` "
                "and run `make update-publications`."
            )
        )
        return "\n".join(
            [
                "::: {.notice}",
                message,
                ":::",
                "",
            ]
        )

    grouped: dict[int | None, list[Publication]] = {}
    for publication in publications:
        grouped.setdefault(publication.year, []).append(publication)
    sections: list[str] = []
    for year in sorted(grouped.keys(), key=lambda value: value or 0, reverse=True):
        heading = str(year) if year else ("日期未知" if is_zh else "No Date")
        sections.append(f"## {heading}")
        sections.extend(
            render_publication(publication, language_code, identity, overrides)
            for publication in grouped[year]
        )
        sections.append("")
    return "\n\n".join(sections)


def write_quarto_snippets(
    publications: list[Publication],
    sources: list[str],
    identity: AuthorIdentity,
    overrides: dict[str, dict[str, Any]],
) -> None:
    display_publications = [
        corrected_publication(publication, overrides) for publication in publications
    ]
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    for language_code, path in GENERATED_PATHS.items():
        path.write_text(
            render_quarto_snippet(
                display_publications,
                sources,
                language_code,
                identity,
                overrides,
            ),
            encoding="utf-8",
        )
    LEGACY_GENERATED_PATH.write_text(
        render_quarto_snippet(display_publications, sources, "en", identity, overrides),
        encoding="utf-8",
    )


UNICODE_BIBTEX_REPLACEMENTS = str.maketrans(
    {
        "\u00a0": " ",
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "−": "-",
        "‘": "'",
        "’": "'",
        "‚": "'",
        "‛": "'",
        "′": "'",
        "“": '"',
        "”": '"',
        "„": '"',
        "…": "...",
    }
)


def normalize_bibtex_text(value: str) -> str:
    value = clean_text(value)
    value = unicodedata.normalize("NFKC", value)
    value = value.translate(UNICODE_BIBTEX_REPLACEMENTS)
    value = re.sub(r"(?<=')\s+-\s*(?=[A-Za-z0-9])", "-", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def ascii_slug(value: str, default: str = "") -> str:
    normalized = normalize_bibtex_text(value)
    ascii_text = unicodedata.normalize("NFKD", normalized).encode("ascii", "ignore").decode()
    slug = "".join(re.findall(r"[A-Za-z0-9]+", ascii_text.lower()))
    return slug or default


def bibtex_key_base(publication: Publication) -> str:
    author_part = "work"
    if publication.authors:
        author_part = ascii_slug(publication.authors[0].split()[-1], default="work")
    title_part = ascii_slug(publication.title)[:24]
    if not title_part and publication.doi:
        title_part = ascii_slug(publication.doi)[-24:]
    title_part = title_part or "publication"
    year_part = str(publication.year or "nd")
    return f"{author_part}{year_part}{title_part}"


def unique_bibtex_key(publication: Publication, used_keys: set[str]) -> str:
    base = bibtex_key_base(publication)
    key = base
    counter = 2
    while key in used_keys:
        key = f"{base}_{counter}"
        counter += 1
    used_keys.add(key)
    return key


def bibtex_type(publication_type: str) -> str:
    mapping = {
        "journal-article": "article",
        "proceedings-article": "inproceedings",
        "book-chapter": "incollection",
        "book": "book",
        "posted-content": "misc",
        "preprint": "misc",
    }
    return mapping.get(publication_type, "misc")


def bibtex_escape(value: str) -> str:
    special_chars = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(special_chars.get(char, char) for char in normalize_bibtex_text(value))


def write_bibtex(publications: list[Publication], overrides: dict[str, dict[str, Any]]) -> None:
    entries: list[str] = [
        "% Generated by scripts/update_publications.py.",
        "% Manual edits may be overwritten.",
        "",
    ]
    used_keys: set[str] = set()
    for publication in publications:
        publication_overrides = overrides_for_publication(publication, overrides)
        publication = corrected_publication(publication, overrides)
        fields = {
            "title": publication_overrides.get("bibtex_title", publication.title),
            "year": str(publication.year) if publication.year else None,
            "author": " and ".join(publication.authors) if publication.authors else None,
            "journal": publication_overrides.get("bibtex_journal", publication.journal or ""),
            "volume": publication.volume,
            "number": publication.issue,
            "pages": publication.pages or publication.article_number,
            "doi": publication.doi,
            "url": publication.url,
        }
        entry_type = bibtex_type(publication.type)
        entry_key = unique_bibtex_key(publication, used_keys)
        entries.append(f"@{entry_type}{{{entry_key},")
        for field, value in fields.items():
            if value:
                entries.append(f"  {field} = {{{bibtex_escape(value)}}},")
        entries.append("}")
        entries.append("")
    BIB_PATH.write_text("\n".join(entries), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orcid", default=os.getenv("ORCID_ID", ""))
    parser.add_argument("--crossref-email", default=os.getenv("CROSSREF_EMAIL", ""))
    parser.add_argument("--crossref-query-author", default=os.getenv("CROSSREF_QUERY_AUTHOR", ""))
    parser.add_argument(
        "--limit",
        type=int,
        default=int(os.getenv("PUBLICATIONS_LIMIT", "80")),
        help="Maximum number of publications to retain.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    orcid = clean_orcid(args.orcid) if args.orcid else ""
    sources: list[str] = []
    publications: list[Publication] = []
    identity = AuthorIdentity(
        orcid=orcid or None,
        primary_name=None,
        aliases=fallback_author_aliases(args.crossref_query_author),
    )

    try:
        if orcid:
            identity = author_identity_from_orcid(orcid)
            publications.extend(publications_from_orcid(orcid, args.crossref_email or None))
            sources.append("ORCID")
        elif args.crossref_query_author:
            publications.extend(
                publications_from_crossref_author(
                    args.crossref_query_author,
                    args.crossref_email or None,
                    limit=args.limit,
                )
            )
            sources.append("Crossref")
    except RuntimeError as exc:
        if env_flag("STRICT_UPDATES"):
            raise SystemExit(str(exc)) from exc
        print(f"warning: publication update failed: {exc}", file=sys.stderr)
        print("warning: leaving existing publication data unchanged", file=sys.stderr)
        return 0

    publications = sorted(
        deduplicate(publications),
        key=publication_sort_key,
        reverse=True,
    )[: args.limit]
    overrides = merge_overrides(
        merge_overrides(load_image_manifest(), load_pdf_manifest()),
        load_raw_overrides(),
    )
    write_json(
        publications,
        sources=sources,
        orcid=orcid or None,
        identity=identity,
        overrides=overrides,
    )
    write_quarto_snippets(
        publications,
        sources=sources or ["local placeholder"],
        identity=identity,
        overrides=overrides,
    )
    write_bibtex(publications, overrides)
    print(f"Wrote {len(publications)} publications to {DATA_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
