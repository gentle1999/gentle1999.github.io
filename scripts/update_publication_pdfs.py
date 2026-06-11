#!/usr/bin/env python3
"""Discover publication PDFs and write a PDF manifest for publication pages."""

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
from urllib.parse import quote, urlencode, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PUBLICATIONS_PATH = ROOT / "data" / "publications.json"
MANIFEST_PATH = ROOT / "data" / "publication_pdfs.json"
PDF_ROOT = ROOT / "assets" / "publications" / "pdfs"
CROSSREF_API = "https://api.crossref.org/works"
UNPAYWALL_API = "https://api.unpaywall.org/v2"


@dataclass(frozen=True)
class PublicationRef:
    doi: str
    title: str
    journal: str | None
    year: int | None
    url: str | None


@dataclass(frozen=True)
class PdfCandidate:
    doi: str
    url: str
    provider: str
    source: str
    confidence: str
    landing_url: str | None = None
    license_note: str | None = None


CONFIDENCE_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
}


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
        "User-Agent": "Mozilla/5.0 academic-homepage-publication-pdf-discovery",
    }
    if referer:
        headers["Referer"] = referer
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get_content_type()
        return response.geturl(), content_type, response.read()


def request_json(url: str, *, timeout: int = 30) -> Any:
    final_url, content_type, payload = request_bytes(
        url,
        accept="application/json",
        timeout=timeout,
    )
    if content_type != "application/json":
        raise RuntimeError(f"{final_url} returned {content_type}, not JSON")
    return json.loads(payload.decode("utf-8"))


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
                url=clean_text(str(item.get("url") or "")) or None,
            ),
        )
    return refs


def is_pdf_payload(content_type: str, payload: bytes) -> bool:
    return content_type == "application/pdf" or payload.startswith(b"%PDF-")


def pdf_dir_for_doi(doi: str) -> Path:
    return PDF_ROOT / safe_stem(doi)


def publication_pdf_dir(publication: PublicationRef) -> Path:
    return pdf_dir_for_doi(publication.doi)


def sorted_local_pdfs(path: Path) -> list[Path]:
    if not path.exists() or not path.is_dir():
        return []
    pdfs = [item for item in path.iterdir() if item.is_file() and item.suffix.lower() == ".pdf"]
    return sorted(pdfs, key=lambda item: (item.name != "paper.pdf", item.name.casefold()))


def local_pdf_record(publication: PublicationRef) -> dict[str, Any] | None:
    directory = publication_pdf_dir(publication)
    directory.mkdir(parents=True, exist_ok=True)
    candidates = sorted_local_pdfs(directory)
    for path in candidates:
        if path.exists() and path.is_file():
            return {
                "pdf": path.relative_to(ROOT).as_posix(),
                "source_url": None,
                "provider": "Local",
                "kind": "local",
                "confidence": "high",
                "license_note": "Local PDF; confirm distribution rights before publishing.",
                "bytes": path.stat().st_size,
            }
    return None


def crossref_candidates(
    publication: PublicationRef,
    *,
    email: str | None,
    timeout: int,
) -> tuple[list[PdfCandidate], str | None]:
    params = {"mailto": email} if email else {}
    url = f"{CROSSREF_API}/{quote(publication.doi)}"
    if params:
        url = f"{url}?{urlencode(params)}"
    try:
        payload = request_json(url, timeout=timeout)
    except (RuntimeError, HTTPError, TimeoutError, URLError, OSError) as exc:
        return [], str(exc)

    item = payload.get("message")
    if not isinstance(item, dict):
        return [], "invalid Crossref response"

    candidates: list[PdfCandidate] = []
    for link in item.get("link") or []:
        if not isinstance(link, dict):
            continue
        content_type = str(link.get("content-type") or "").lower()
        link_url = str(link.get("URL") or "").strip()
        intended = str(link.get("intended-application") or "")
        if not link_url:
            continue
        if content_type == "application/pdf" or link_url.lower().split("?", 1)[0].endswith(".pdf"):
            candidates.append(
                PdfCandidate(
                    doi=publication.doi,
                    url=link_url,
                    provider="Crossref",
                    source=f"crossref-link:{intended or content_type}",
                    confidence="medium",
                    landing_url=publication.url,
                ),
            )
    return candidates, None


def deterministic_candidates(publication: PublicationRef) -> list[PdfCandidate]:
    doi = publication.doi
    candidates: list[PdfCandidate] = []
    if doi.startswith("10.1038/"):
        article_id = doi.rsplit("/", maxsplit=1)[-1]
        candidates.append(
            PdfCandidate(
                doi=doi,
                url=f"https://www.nature.com/articles/{article_id}.pdf",
                provider="Springer Nature",
                source="nature-pdf-pattern",
                confidence="medium",
                landing_url=f"https://www.nature.com/articles/{article_id}",
            ),
        )
    if doi.startswith("10.1039/") and publication.year:
        manuscript_id = doi.rsplit("/", maxsplit=1)[-1].lower()
        journal_code = re.sub(r"[^a-z]", "", manuscript_id)
        candidates.append(
            PdfCandidate(
                doi=doi,
                url=(
                    "https://pubs.rsc.org/en/content/articlepdf/"
                    f"{publication.year}/{journal_code}/{manuscript_id}"
                ),
                provider="RSC",
                source="rsc-pdf-pattern",
                confidence="medium",
                landing_url=publication.url,
            ),
        )
    if doi.startswith("10.1002/"):
        for host in [
            "chemistry-europe.onlinelibrary.wiley.com",
            "onlinelibrary.wiley.com",
        ]:
            candidates.append(
                PdfCandidate(
                    doi=doi,
                    url=f"https://{host}/doi/pdf/{doi}",
                    provider="Wiley",
                    source="wiley-pdf-pattern",
                    confidence="medium",
                    landing_url=publication.url,
                ),
            )
    return candidates


def unpaywall_candidates(
    publication: PublicationRef,
    *,
    email: str | None,
    timeout: int,
) -> tuple[list[PdfCandidate], str | None]:
    if not email:
        return [], "UNPAYWALL_EMAIL not configured"
    url = f"{UNPAYWALL_API}/{quote(publication.doi)}?{urlencode({'email': email})}"
    try:
        payload = request_json(url, timeout=timeout)
    except (RuntimeError, HTTPError, TimeoutError, URLError, OSError) as exc:
        return [], str(exc)
    if not isinstance(payload, dict):
        return [], "invalid Unpaywall response"

    candidates: list[PdfCandidate] = []
    for location in [payload.get("best_oa_location"), *(payload.get("oa_locations") or [])]:
        if not isinstance(location, dict):
            continue
        pdf_url = location.get("url_for_pdf")
        if not isinstance(pdf_url, str) or not pdf_url.strip():
            continue
        license_value = location.get("license")
        candidates.append(
            PdfCandidate(
                doi=publication.doi,
                url=pdf_url.strip(),
                provider=str(location.get("host_type") or "Unpaywall"),
                source="unpaywall",
                confidence="high",
                landing_url=location.get("url") if isinstance(location.get("url"), str) else None,
                license_note=(
                    str(license_value) if license_value else "open access location from Unpaywall"
                ),
            ),
        )
    return candidates, None


def tag_attr(tag: str, name: str) -> str | None:
    match = re.search(rf"\b{name}\s*=\s*([\"'])(.*?)\1", tag, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return html.unescape(match.group(2)).strip() or None


def html_candidates(
    publication: PublicationRef,
    timeout: int,
) -> tuple[list[PdfCandidate], str | None]:
    landing_url, text, error = try_request_text(
        f"https://doi.org/{quote(publication.doi)}",
        timeout=timeout,
    )
    if error or not text or not landing_url:
        return [], error

    candidates: list[PdfCandidate] = []
    for match in re.finditer(r"<meta\b[^>]+>", text, flags=re.IGNORECASE | re.DOTALL):
        tag = match.group(0)
        name = (tag_attr(tag, "property") or tag_attr(tag, "name") or "").lower()
        content = tag_attr(tag, "content")
        if not content:
            continue
        if name in {"citation_pdf_url", "dc.identifier"} and ".pdf" in content.lower():
            candidates.append(
                PdfCandidate(
                    doi=publication.doi,
                    url=urljoin(landing_url, content),
                    provider="Publisher",
                    source=name,
                    confidence="medium",
                    landing_url=landing_url,
                ),
            )

    for match in re.finditer(r"<a\b[^>]+>", text, flags=re.IGNORECASE | re.DOTALL):
        tag = match.group(0)
        href = tag_attr(tag, "href")
        if not href:
            continue
        combined = f"{href} {tag}".lower()
        if ".pdf" not in combined and "article-pdf" not in combined and "pdf" not in combined:
            continue
        if any(term in combined for term in ["supplement", "supporting", "si.pdf", "esm"]):
            continue
        candidates.append(
            PdfCandidate(
                doi=publication.doi,
                url=urljoin(landing_url, href),
                provider="Publisher",
                source="publisher-html-link",
                confidence="low",
                landing_url=landing_url,
            ),
        )
    return candidates, None


def unique_candidates(candidates: list[PdfCandidate]) -> list[PdfCandidate]:
    seen: set[str] = set()
    unique: list[PdfCandidate] = []
    for candidate in sorted(
        candidates,
        key=lambda item: CONFIDENCE_ORDER.get(item.confidence, -1),
        reverse=True,
    ):
        key = candidate.url.split("?", maxsplit=1)[0]
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def is_confident_enough(candidate: PdfCandidate, minimum: str) -> bool:
    return CONFIDENCE_ORDER.get(candidate.confidence, -1) >= CONFIDENCE_ORDER[minimum]


def download_candidate(
    candidate: PdfCandidate,
    *,
    force: bool,
    timeout: int,
) -> dict[str, Any] | None:
    try:
        final_url, content_type, payload = request_bytes(
            candidate.url,
            accept="application/pdf,*/*;q=0.8",
            referer=candidate.landing_url,
            timeout=timeout,
        )
    except (HTTPError, TimeoutError, URLError, OSError) as exc:
        print(f"warning: PDF download failed for {candidate.doi}: {exc}", file=sys.stderr)
        return None

    if len(payload) < 1024 or not is_pdf_payload(content_type, payload):
        return None

    output_dir = pdf_dir_for_doi(candidate.doi)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "paper.pdf"
    relative_path = output_path.relative_to(ROOT)
    if force or not output_path.exists() or output_path.read_bytes() != payload:
        output_path.write_bytes(payload)

    return {
        "pdf": relative_path.as_posix(),
        "source_url": final_url,
        "provider": candidate.provider,
        "kind": "auto",
        "source": candidate.source,
        "confidence": candidate.confidence,
        "content_type": content_type,
        "license_note": candidate.license_note,
        "bytes": len(payload),
    }


def discover_publication_pdf(
    publication: PublicationRef,
    *,
    minimum_confidence: str,
    force: bool,
    timeout: int,
    crossref_email: str | None,
    unpaywall_email: str | None,
    auto_download: bool,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str | None]:
    local = local_pdf_record(publication)
    if local:
        return local, [], None
    if not auto_download:
        return None, [], "no local PDF and auto download disabled"

    candidates: list[PdfCandidate] = []
    reasons: list[str] = []
    candidates.extend(deterministic_candidates(publication))
    for discovered, error in [
        unpaywall_candidates(publication, email=unpaywall_email, timeout=timeout),
        crossref_candidates(publication, email=crossref_email, timeout=timeout),
        html_candidates(publication, timeout),
    ]:
        candidates.extend(discovered)
        if error:
            reasons.append(error)

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
            "no downloadable PDF candidate met threshold",
        )
    reason = "; ".join(dict.fromkeys(reasons))
    return None, [], reason or "no PDF candidate discovered"


def write_manifest(
    pdfs: dict[str, Any],
    failures: dict[str, Any],
    minimum_confidence: str,
    auto_download: bool,
) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "generated_at": utc_now(),
            "minimum_confidence": minimum_confidence,
            "auto_download": auto_download,
            "pdf_dir": PDF_ROOT.relative_to(ROOT).as_posix(),
            "count": len(pdfs),
            "failures": len(failures),
        },
        "pdfs": pdfs,
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
        default=os.getenv("PUBLICATION_PDF_MIN_CONFIDENCE", "medium"),
        help="Minimum confidence for downloading a discovered PDF.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("PUBLICATION_PDF_TIMEOUT", "15")),
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=env_flag("PUBLICATION_PDF_FORCE"),
        help="Rewrite existing downloaded PDF files even when they already exist.",
    )
    parser.add_argument(
        "--auto-download",
        action=argparse.BooleanOptionalAction,
        default=env_flag("PUBLICATION_PDF_AUTO_DOWNLOAD", True),
        help="Try to download publicly discoverable PDFs after scanning local PDFs.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=env_flag("PUBLICATION_PDF_STRICT") or env_flag("STRICT_UPDATES"),
        help="Fail if any publication PDF cannot be discovered.",
    )
    parser.add_argument("--crossref-email", default=os.getenv("CROSSREF_EMAIL", ""))
    parser.add_argument("--unpaywall-email", default=os.getenv("UNPAYWALL_EMAIL", ""))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    refs = publication_refs()
    pdfs: dict[str, Any] = {}
    failures: dict[str, Any] = {}

    for publication in refs:
        record, candidates, reason = discover_publication_pdf(
            publication,
            minimum_confidence=args.minimum_confidence,
            force=args.force,
            timeout=args.timeout,
            crossref_email=args.crossref_email or None,
            unpaywall_email=args.unpaywall_email or args.crossref_email or None,
            auto_download=args.auto_download,
        )
        if record:
            pdfs[publication.doi] = record
            print(f"Found PDF for {publication.doi}: {record['pdf']}")
            continue
        failures[publication.doi] = {
            "title": publication.title,
            "journal": publication.journal,
            "reason": reason,
            "candidates": candidates,
            "expected_pdf": (publication_pdf_dir(publication) / "paper.pdf")
            .relative_to(ROOT)
            .as_posix(),
        }
        print(f"warning: no publication PDF for {publication.doi}: {reason}", file=sys.stderr)

    write_manifest(pdfs, failures, args.minimum_confidence, args.auto_download)
    print(
        f"Wrote {len(pdfs)} publication PDFs and {len(failures)} failures "
        f"to {MANIFEST_PATH.relative_to(ROOT)}",
    )
    if args.strict and failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
