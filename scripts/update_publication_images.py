#!/usr/bin/env python3
"""Discover and download publication TOC/graphical abstract images."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PUBLICATIONS_PATH = ROOT / "data" / "publications.json"
MANIFEST_PATH = ROOT / "data" / "publication_images.json"
OUTPUT_DIR = ROOT / "assets" / "publications" / "generated"

CONFIDENCE_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
}
KIND_ORDER = {
    "graphical_abstract": 4,
    "toc_image": 4,
    "article_image": 3,
    "figure1_candidate": 2,
    "social_image": 1,
    "issue_cover": 0,
}
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


@dataclass(frozen=True)
class PublicationRef:
    doi: str
    title: str
    journal: str | None
    year: int | None


@dataclass(frozen=True)
class ImageCandidate:
    doi: str
    url: str
    kind: str
    confidence: str
    provider: str
    source: str
    alt: str | None = None
    landing_url: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    value = doi.strip()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    return value.lower() or None


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def safe_stem(doi: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", doi.lower()).strip("-")


def request_bytes(
    url: str,
    *,
    accept: str = "*/*",
    referer: str | None = None,
    timeout: int = 30,
) -> tuple[str, str, bytes]:
    headers = {
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 academic-homepage-publication-image-discovery",
    }
    if referer:
        headers["Referer"] = referer
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get_content_type()
        return response.geturl(), content_type, response.read()


def request_text(url: str, *, timeout: int = 30) -> tuple[str, str]:
    final_url, content_type, payload = request_bytes(
        url,
        accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        timeout=timeout,
    )
    if not (content_type.startswith("text/") or content_type.endswith("+xml")):
        return final_url, ""
    return final_url, payload.decode("utf-8", errors="replace")


def try_request_text(url: str, *, timeout: int = 30) -> tuple[str | None, str, str | None]:
    try:
        final_url, text = request_text(url, timeout=timeout)
    except HTTPError as exc:
        return getattr(exc, "url", url), "", f"HTTP {exc.code} {exc.reason}"
    except (TimeoutError, URLError, OSError) as exc:
        return None, "", str(exc)
    return final_url, text, None


def publication_refs() -> list[PublicationRef]:
    if not PUBLICATIONS_PATH.exists():
        raise RuntimeError(
            f"{PUBLICATIONS_PATH.relative_to(ROOT)} does not exist. "
            "Run `make update-publications` first.",
        )
    payload = json.loads(PUBLICATIONS_PATH.read_text(encoding="utf-8"))
    publications = payload.get("publications") or []
    if not isinstance(publications, list):
        raise RuntimeError(f"{PUBLICATIONS_PATH.relative_to(ROOT)} has invalid publications data.")

    refs: list[PublicationRef] = []
    for item in publications:
        if not isinstance(item, dict):
            continue
        doi = normalize_doi(str(item.get("doi") or ""))
        if not doi:
            continue
        year = item.get("year")
        refs.append(
            PublicationRef(
                doi=doi,
                title=clean_text(str(item.get("title") or "")),
                journal=clean_text(str(item.get("journal") or "")) or None,
                year=year if isinstance(year, int) else None,
            ),
        )
    return refs


def tag_attr(tag: str, name: str) -> str | None:
    match = re.search(rf"\b{name}\s*=\s*([\"'])(.*?)\1", tag, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return html.unescape(match.group(2)).strip() or None


def meta_candidates(
    publication: PublicationRef,
    text: str,
    landing_url: str,
    provider: str,
) -> list[ImageCandidate]:
    candidates: list[ImageCandidate] = []
    for match in re.finditer(r"<meta\b[^>]+>", text, flags=re.IGNORECASE | re.DOTALL):
        tag = match.group(0)
        name = (tag_attr(tag, "property") or tag_attr(tag, "name") or "").lower()
        content = tag_attr(tag, "content")
        if not content:
            continue
        if name in {"citation_graphical_abstract", "dc.image"}:
            candidates.append(
                ImageCandidate(
                    doi=publication.doi,
                    url=urljoin(landing_url, content),
                    kind="graphical_abstract",
                    confidence="high",
                    provider=provider,
                    source=name,
                    alt=publication.title,
                    landing_url=landing_url,
                ),
            )
        elif name in {"og:image", "twitter:image"}:
            url = urljoin(landing_url, content)
            kind = "social_image"
            confidence = "low"
            if "media.springernature.com" in url and "fig1" in url.lower():
                kind = "figure1_candidate"
                confidence = "medium"
            if "content/image/ga/" in url.lower():
                kind = "graphical_abstract"
                confidence = "high"
            if "issue" in url.lower():
                kind = "issue_cover"
            candidates.append(
                ImageCandidate(
                    doi=publication.doi,
                    url=url,
                    kind=kind,
                    confidence=confidence,
                    provider=provider,
                    source=name,
                    alt=publication.title,
                    landing_url=landing_url,
                ),
            )
    return candidates


def img_candidates(
    publication: PublicationRef,
    text: str,
    landing_url: str,
    provider: str,
) -> list[ImageCandidate]:
    candidates: list[ImageCandidate] = []
    for match in re.finditer(r"<img\b[^>]+>", text, flags=re.IGNORECASE | re.DOTALL):
        tag = match.group(0)
        src = (
            tag_attr(tag, "src")
            or tag_attr(tag, "data-src")
            or tag_attr(tag, "data-original")
            or tag_attr(tag, "data-lazy-src")
        )
        if not src:
            continue
        url = urljoin(landing_url, src)
        alt = clean_text(tag_attr(tag, "alt") or tag_attr(tag, "title") or "")
        combined = f"{url} {alt} {tag}".lower()
        if "ajax-ga-loader" in combined:
            continue
        if "graphical abstract" in combined or "/ga/" in combined or "imagetype=ga" in combined:
            kind = "graphical_abstract"
            confidence = "high"
        elif "toc" in combined:
            kind = "toc_image"
            confidence = "high"
        elif "fig1" in combined or "figure-1" in combined or "fig. 1" in combined:
            kind = "figure1_candidate"
            confidence = "medium"
        elif "abstract" in combined:
            kind = "article_image"
            confidence = "medium"
        else:
            continue
        candidates.append(
            ImageCandidate(
                doi=publication.doi,
                url=url,
                kind=kind,
                confidence=confidence,
                provider=provider,
                source="img",
                alt=alt or publication.title,
                landing_url=landing_url,
            ),
        )
    return candidates


def provider_for_url(url: str) -> str:
    host = url.lower()
    if "pubs.rsc.org" in host:
        return "RSC"
    if "nature.com" in host or "springernature.com" in host:
        return "Springer Nature"
    if "thieme-connect.de" in host:
        return "Thieme"
    if "sciengine.com" in host:
        return "Science China Press"
    if "wiley.com" in host:
        return "Wiley"
    return "Publisher"


def deterministic_candidates(publication: PublicationRef) -> list[ImageCandidate]:
    doi = publication.doi
    candidates: list[ImageCandidate] = []
    if doi.startswith("10.1039/"):
        manuscript_id = doi.rsplit("/", maxsplit=1)[-1].upper()
        candidates.append(
            ImageCandidate(
                doi=doi,
                url=f"https://pubs.rsc.org/en/Content/Image/GA/{manuscript_id}",
                kind="graphical_abstract",
                confidence="high",
                provider="RSC",
                source="rsc-ga-pattern",
                alt=f"Graphical abstract for {publication.title}",
                landing_url=(
                    "https://pubs.rsc.org/en/content/articlelanding/"
                    f"{publication.year or ''}"
                ),
            ),
        )
    nature_match = re.fullmatch(r"10\.1038/(s\d+)-(\d+)-(\d+)-(.+)", doi)
    if nature_match and publication.year:
        journal_code, _, article_code, _ = nature_match.groups()
        media_object = (
            f"{journal_code.removeprefix('s')}_{publication.year}_"
            f"{int(article_code)}_Fig1_HTML.png"
        )
        candidates.append(
            ImageCandidate(
                doi=doi,
                url=(
                    "https://media.springernature.com/lw1200/springer-static/image/"
                    f"art%3A{quote(doi, safe='')}/MediaObjects/{media_object}"
                ),
                kind="figure1_candidate",
                confidence="medium",
                provider="Springer Nature",
                source="springer-figure1-pattern",
                alt=f"Figure 1 candidate for {publication.title}",
                landing_url=f"https://www.nature.com/articles/{doi.rsplit('/', maxsplit=1)[-1]}",
            ),
        )
    return candidates


def html_discovery(
    publication: PublicationRef,
    timeout: int,
) -> tuple[list[ImageCandidate], str | None]:
    landing_url, text, error = try_request_text(
        f"https://doi.org/{quote(publication.doi)}",
        timeout=timeout,
    )
    if error or not text or not landing_url:
        return [], error
    provider = provider_for_url(landing_url)
    candidates = meta_candidates(publication, text, landing_url, provider)
    candidates.extend(img_candidates(publication, text, landing_url, provider))
    return candidates, None


def unique_candidates(candidates: list[ImageCandidate]) -> list[ImageCandidate]:
    seen: set[str] = set()
    unique: list[ImageCandidate] = []
    for candidate in sorted(
        candidates,
        key=lambda item: (
            CONFIDENCE_ORDER.get(item.confidence, -1),
            KIND_ORDER.get(item.kind, -1),
        ),
        reverse=True,
    ):
        key = candidate.url.split("?", maxsplit=1)[0]
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def is_confident_enough(candidate: ImageCandidate, minimum: str) -> bool:
    return CONFIDENCE_ORDER.get(candidate.confidence, -1) >= CONFIDENCE_ORDER[minimum]


def image_extension(content_type: str, url: str) -> str:
    if content_type in CONTENT_TYPE_EXTENSIONS:
        return CONTENT_TYPE_EXTENSIONS[content_type]
    match = re.search(r"\.(png|jpe?g|gif|webp|svg)(?:[?#]|$)", url, flags=re.IGNORECASE)
    if match:
        suffix = match.group(1).lower()
        return ".jpg" if suffix == "jpeg" else f".{suffix}"
    return ".img"


def is_image_payload(content_type: str, payload: bytes) -> bool:
    if content_type.startswith("image/"):
        return True
    return payload.startswith((b"\xff\xd8\xff", b"\x89PNG", b"GIF8", b"RIFF", b"<svg"))


def is_rejected_candidate(candidate: ImageCandidate) -> bool:
    value = f"{candidate.url} {candidate.alt or ''} {candidate.kind}".lower()
    rejected_terms = [
        "customer",
        "logo",
        "favicon",
        "icon",
        "spinner",
        "loader",
        "issue",
        "cover",
        "advert",
        "facebook",
        "twitter",
        "linkedin",
        "youtube",
    ]
    return any(term in value for term in rejected_terms)


def download_candidate(
    candidate: ImageCandidate,
    *,
    force: bool,
    timeout: int,
) -> dict[str, Any] | None:
    if is_rejected_candidate(candidate):
        return None
    try:
        final_url, content_type, payload = request_bytes(
            candidate.url,
            accept="image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            referer=candidate.landing_url,
            timeout=timeout,
        )
    except (HTTPError, TimeoutError, URLError, OSError) as exc:
        print(f"warning: image download failed for {candidate.doi}: {exc}", file=sys.stderr)
        return None

    if len(payload) < 500 or not is_image_payload(content_type, payload):
        return None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    extension = image_extension(content_type, final_url)
    relative_path = (
        Path("assets")
        / "publications"
        / "generated"
        / f"{safe_stem(candidate.doi)}{extension}"
    )
    output_path = ROOT / relative_path
    if force or not output_path.exists() or output_path.read_bytes() != payload:
        output_path.write_bytes(payload)

    return {
        "image": relative_path.as_posix(),
        "image_alt": candidate.alt or f"TOC image for {candidate.doi}",
        "source_url": final_url,
        "landing_url": candidate.landing_url,
        "provider": candidate.provider,
        "kind": candidate.kind,
        "confidence": candidate.confidence,
        "content_type": content_type,
        "bytes": len(payload),
    }


def discover_publication_image(
    publication: PublicationRef,
    *,
    minimum_confidence: str,
    force: bool,
    timeout: int,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str | None]:
    candidates = deterministic_candidates(publication)
    html_candidates, error = html_discovery(publication, timeout)
    candidates.extend(html_candidates)
    candidates = unique_candidates(candidates)

    for candidate in candidates:
        if not is_confident_enough(candidate, minimum_confidence):
            continue
        downloaded = download_candidate(candidate, force=force, timeout=timeout)
        if downloaded:
            return downloaded, [asdict(item) for item in candidates], None

    if candidates:
        return (
            None,
            [asdict(item) for item in candidates],
            "no downloadable candidate met threshold",
        )
    return None, [], error or "no candidate discovered"


def write_manifest(
    images: dict[str, Any],
    failures: dict[str, Any],
    minimum_confidence: str,
) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "generated_at": utc_now(),
            "minimum_confidence": minimum_confidence,
            "count": len(images),
            "failures": len(failures),
        },
        "images": images,
        "failures": failures,
    }
    MANIFEST_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--minimum-confidence",
        choices=sorted(CONFIDENCE_ORDER),
        default=os.getenv("PUBLICATION_IMAGE_MIN_CONFIDENCE", "medium"),
        help="Minimum confidence for downloading a discovered image.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("PUBLICATION_IMAGE_TIMEOUT", "30")),
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=env_flag("PUBLICATION_IMAGE_FORCE"),
        help="Rewrite existing downloaded image files even when they already exist.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=env_flag("PUBLICATION_IMAGE_STRICT") or env_flag("STRICT_UPDATES"),
        help="Fail if any publication image cannot be downloaded.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    refs = publication_refs()
    images: dict[str, Any] = {}
    failures: dict[str, Any] = {}

    for publication in refs:
        record, candidates, reason = discover_publication_image(
            publication,
            minimum_confidence=args.minimum_confidence,
            force=args.force,
            timeout=args.timeout,
        )
        if record:
            images[publication.doi] = record
            print(f"Downloaded {publication.doi}: {record['image']}")
            continue
        failures[publication.doi] = {
            "title": publication.title,
            "journal": publication.journal,
            "reason": reason,
            "candidates": candidates,
        }
        print(f"warning: no publication image for {publication.doi}: {reason}", file=sys.stderr)

    write_manifest(images, failures, args.minimum_confidence)
    print(
        f"Wrote {len(images)} publication images and {len(failures)} failures "
        f"to {MANIFEST_PATH.relative_to(ROOT)}",
    )
    if args.strict and failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
