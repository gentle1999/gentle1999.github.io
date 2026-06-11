#!/usr/bin/env python3
"""Generate Typst include files for CV publications."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PUBLICATIONS_PATH = ROOT / "data" / "publications.json"
OUTPUT_PATH = ROOT / "cv" / "publications.typ"
OUTPUT_PATH_ZH = ROOT / "cv" / "publications.zh.typ"
DEFAULT_REPRESENTATIVE_DOIS = (
    "10.1002/anie.202518560",
    "10.1038/s41597-024-03933-6",
    "10.1002/asia.202300011",
    "10.1038/s42256-025-01098-4",
)
DEFAULT_FULL_DOIS = (
    "10.1002/anie.202518560",
    "10.1038/s41597-024-03933-6",
    "10.1002/asia.202300011",
    "10.1038/s42256-025-01098-4",
    "10.1038/s41467-025-67770-w",
    "10.1002/anie.202106880",
    "10.1002/chem.71074",
    "10.1002/chem.71220",
    "10.1039/d5ob00007f",
    "10.1360/tb-2024-0812",
    "10.1055/s-0040-1705977",
)
LABELS = {
    "en": {
        "empty": "[No publication metadata available. Run `make update-publications` first.]",
        "representative": "Representative works",
        "additional": "Other papers",
    },
    "zh": {
        "empty": "[暂无论文元数据。请先运行 `make update-publications`。]",
        "representative": "主要工作",
        "additional": "其他论文",
    },
}
ROLE_LABELS = {
    "10.1002/anie.202518560": {
        "en": "First author; reaction modeling",
        "zh": "一作；反应建模",
    },
    "10.1038/s41597-024-03933-6": {
        "en": "First author; dataset/software",
        "zh": "一作；数据集/软件",
    },
    "10.1002/asia.202300011": {
        "en": "First author; representation",
        "zh": "一作；分子表征",
    },
    "10.1038/s42256-025-01098-4": {
        "en": "Co-author; pre-training algorithm",
        "zh": "共同作者；预训练算法",
    },
}
JOURNAL_ABBREVIATIONS = {
    "angewandte chemie international edition": "Angew. Chem., Int. Ed.",
    "angew chem int ed": "Angew. Chem., Int. Ed.",
    "chemistry - a european journal": "Chem. Eur. J.",
    "chemistry a european j": "Chem. Eur. J.",
    "chemistry - an asian journal": "Chem. Asian J.",
    "chemistry – an asian journal": "Chem. Asian J.",
    "scientific data": "Sci. Data",
    "sci data": "Sci. Data",
    "organic & biomolecular chemistry": "Org. Biomol. Chem.",
    "org. biomol. chem.": "Org. Biomol. Chem.",
    "nature communications": "Nat. Commun.",
    "nat commun": "Nat. Commun.",
    "nature machine intelligence": "Nat. Mach. Intell.",
    "nat mach intell": "Nat. Mach. Intell.",
    "chinese science bulletin": "Chin. Sci. Bull.",
    "chin. sci. bull.": "Chin. Sci. Bull.",
    "synlett": "Synlett",
}
JOURNAL_IMPACT_VARIABLES = {
    "Angew. Chem., Int. Ed.": "jif-anie",
    "Sci. Data": "jif-sci-data",
    "Chem. Asian J.": "jif-chem-asian",
    "Nat. Mach. Intell.": "jif-nat-mach-intell",
    "Nat. Commun.": "jif-nat-commun",
    "Chem. Eur. J.": "jif-chem-eur",
    "Org. Biomol. Chem.": "jif-obc",
    "Chin. Sci. Bull.": "jif-csb",
    "Synlett": "jif-synlett",
}

def typst_string(value: object) -> str:
    text = "" if value is None else str(value)
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
        .replace("\r", " ")
    )
    return f'"{escaped}"'


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_lookup_key(value: str) -> str:
    value = normalize_name_punctuation(value)
    value = value.replace("&amp;", "&")
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"\s+", " ", value)
    return value.strip().casefold()


def journal_abbreviation(item: dict[str, Any]) -> str:
    candidates = [
        normalize_whitespace(str(item.get("journal") or "")),
        normalize_whitespace(str(item.get("journal_short") or "")),
    ]
    for candidate in candidates:
        key = normalize_lookup_key(candidate)
        if key in JOURNAL_ABBREVIATIONS:
            return JOURNAL_ABBREVIATIONS[key]

    short_title = normalize_whitespace(str(item.get("journal_short") or ""))
    return (
        short_title
        or candidates[0]
        or normalize_whitespace(str(item.get("type") or "Publication"))
    )


def impact_factor_variable(item: dict[str, Any]) -> str:
    return JOURNAL_IMPACT_VARIABLES.get(journal_abbreviation(item), "")


def load_publications(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise RuntimeError(
            f"{path.relative_to(ROOT)} does not exist. Run `make update-publications` first.",
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    publications = payload.get("publications") or []
    if not isinstance(publications, list):
        raise RuntimeError(f"{path.relative_to(ROOT)} has invalid publication data.")
    return [item for item in publications if isinstance(item, dict)]


def publication_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    year = item.get("year")
    title = normalize_whitespace(str(item.get("title") or ""))
    return (year if isinstance(year, int) else 0, title.lower())


def normalize_doi(value: object) -> str:
    doi = normalize_whitespace(str(value or "")).lower()
    doi = doi.removeprefix("https://doi.org/")
    doi = doi.removeprefix("http://doi.org/")
    doi = doi.removeprefix("doi:")
    return doi.strip()


def split_publications(
    publications: list[dict[str, Any]],
    representative_dois: tuple[str, ...],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sorted_publications = sorted(publications, key=publication_sort_key, reverse=True)
    items_by_doi = {
        doi: item
        for item in sorted_publications
        if (doi := normalize_doi(item.get("doi")))
    }

    representatives: list[dict[str, Any]] = []
    used_dois: set[str] = set()
    for doi in representative_dois:
        key = normalize_doi(doi)
        item = items_by_doi.get(key)
        if item is not None:
            representatives.append(item)
            used_dois.add(key)

    additional = [
        item for item in sorted_publications if normalize_doi(item.get("doi")) not in used_dois
    ]
    return representatives, additional


def ordered_publications(
    publications: list[dict[str, Any]],
    ordered_dois: tuple[str, ...],
) -> list[dict[str, Any]]:
    sorted_publications = sorted(publications, key=publication_sort_key, reverse=True)
    items_by_doi = {
        doi: item
        for item in sorted_publications
        if (doi := normalize_doi(item.get("doi")))
    }

    ordered_items: list[dict[str, Any]] = []
    used_dois: set[str] = set()
    for doi in ordered_dois:
        key = normalize_doi(doi)
        item = items_by_doi.get(key)
        if item is not None:
            ordered_items.append(item)
            used_dois.add(key)

    ordered_items.extend(
        item for item in sorted_publications if normalize_doi(item.get("doi")) not in used_dois
    )
    return ordered_items


def typst_int_tuple(values: object) -> str:
    if not isinstance(values, list):
        return "()"
    numbers = []
    for value in values:
        if isinstance(value, int) and value > 0:
            numbers.append(str(value))
    if not numbers:
        return "()"
    if len(numbers) == 1:
        return f"({numbers[0]},)"
    return f"({', '.join(numbers)})"


def normalize_name_punctuation(value: str) -> str:
    return (
        value.replace("\u00a0", " ")
        .replace("‐", "-")
        .replace("‑", "-")
        .replace("‒", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
    )


def name_initial(value: str) -> str:
    match = re.search(r"[A-Za-z]", value)
    if not match:
        return ""
    return f"{match.group(0).upper()}."


def acs_initials(given_names: str) -> str:
    given_names = normalize_name_punctuation(given_names)
    tokens = [token for token in re.split(r"\s+", given_names) if token]
    values: list[str] = []
    for token in tokens:
        hyphen_parts = [part for part in token.split("-") if part]
        initials = [initial for part in hyphen_parts if (initial := name_initial(part))]
        if initials:
            values.append("-".join(initials))
    return " ".join(values)


def acs_author_name(author: str) -> str:
    author = normalize_whitespace(normalize_name_punctuation(author))
    if not author or "," in author:
        return author
    parts = author.rsplit(" ", 1)
    if len(parts) != 2:
        return author
    given_names, family_name = parts
    initials = acs_initials(given_names)
    if not initials:
        return author
    return f"{family_name}, {initials}"


def acs_page_range(value: str) -> str:
    value = normalize_whitespace(normalize_name_punctuation(value))
    return re.sub(r"\s*-\s*", "-", value)


def render_authors(authors: list[object], positions: str) -> str:
    author_values = [
        typst_string(acs_author_name(str(author)))
        for author in authors
        if normalize_whitespace(str(author))
    ]
    author_tuple = f"({', '.join(author_values)}{',' if len(author_values) == 1 else ''})"
    return author_tuple


def render_publication(
    item: dict[str, Any],
    language: str,
    number: int | None = None,
    include_note: bool = True,
) -> str:
    title = normalize_whitespace(str(item.get("title") or "Untitled publication"))
    authors = item.get("authors") or []
    if not isinstance(authors, list):
        authors = []
    venue = normalize_whitespace(str(item.get("journal") or item.get("type") or "Publication"))
    venue_short = journal_abbreviation(item)
    volume = normalize_whitespace(str(item.get("volume") or ""))
    issue = normalize_whitespace(str(item.get("issue") or ""))
    pages = acs_page_range(str(item.get("pages") or ""))
    article_number = normalize_whitespace(str(item.get("article_number") or ""))
    year = item.get("year")
    doi = normalize_whitespace(str(item.get("doi") or ""))
    doi_key = normalize_doi(doi)
    role = ROLE_LABELS.get(doi_key, {}).get(language, "") if include_note else ""
    impact = impact_factor_variable(item)
    positions = typst_int_tuple(item.get("matched_author_positions"))

    lines = [
        "#publication-citation(",
        f"  {render_authors(authors, positions)},",
        f"  {typst_string(title)},",
        f"  {typst_string(venue)},",
        f"  {typst_string(year) if isinstance(year, int) else 'none'},",
        f"  self-positions: {positions},",
    ]
    if number is not None:
        lines.append(f"  number: {number},")
    if venue_short:
        lines.append(f"  journal-short: {typst_string(venue_short)},")
    if volume:
        lines.append(f"  volume: {typst_string(volume)},")
    if issue:
        lines.append(f"  issue: {typst_string(issue)},")
    if pages:
        lines.append(f"  pages: {typst_string(pages)},")
    if article_number:
        lines.append(f"  article-number: {typst_string(article_number)},")
    if doi:
        lines.append(f"  doi: {typst_string(doi_key)},")
    if impact:
        lines.append(f"  impact: impact-factor({impact}),")
    if role:
        lines.append(f"  note: {typst_string(role)},")
    lines.append(")")
    return "\n".join(lines)


def venue_item(item: dict[str, Any]) -> str:
    venue = journal_abbreviation(item)
    year = item.get("year")
    volume = normalize_whitespace(str(item.get("volume") or ""))
    pages = acs_page_range(str(item.get("pages") or item.get("article_number") or ""))
    parts = [venue]
    if isinstance(year, int):
        parts.append(str(year))
    if volume:
        parts.append(volume)
    if pages:
        parts.append(pages)
    if len(parts) <= 1:
        return venue
    return f"{parts[0]} {parts[1]}" + (f", {', '.join(parts[2:])}" if len(parts) > 2 else "")


def render_publication_summary(label: str, items: list[dict[str, Any]]) -> str:
    venue_values = [venue_item(item) for item in items if venue_item(item)]
    if not venue_values:
        return ""
    info = " #hsep() ".join(venue_values)
    lines = [
        "#publication-summary(",
        f"  {typst_string(label)},",
        f"  [{info}],",
        ")",
    ]
    return "\n".join(lines)


def render(
    publications: list[dict[str, Any]],
    representative_dois: tuple[str, ...],
    language: str,
    full: bool = False,
    full_dois: tuple[str, ...] = DEFAULT_FULL_DOIS,
) -> str:
    representatives, additional = split_publications(publications, representative_dois)
    labels = LABELS[language]
    sorted_publications = ordered_publications(publications, full_dois)
    lines = [
        "// Generated by scripts/generate_cv_publications.py.",
        "// Do not edit by hand.",
        '#import "theme.typ": hsep, publication-citation, publication-summary',
        '#import "journal_metrics.typ": *',
        "",
    ]
    if not sorted_publications:
        lines.append(labels["empty"])
        return "\n".join(lines).rstrip() + "\n"

    if full:
        for index, item in enumerate(sorted_publications, start=1):
            lines.append(
                render_publication(
                    item,
                    language=language,
                    number=index,
                    include_note=False,
                ),
            )
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    for item in representatives:
        lines.append(render_publication(item, language=language))
        lines.append("")

    summary = render_publication_summary(labels["additional"], additional)
    if summary:
        lines.append(summary)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=PUBLICATIONS_PATH)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--language", choices=("en", "zh"), default="en")
    parser.add_argument(
        "--representative-doi",
        action="append",
        default=None,
        help="DOI to keep in full CV format. Repeat to set ordering.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Render every publication as a full ACS-style citation.",
    )
    parser.add_argument(
        "--full-doi",
        action="append",
        default=None,
        help="DOI ordering for --full output. Repeat to set priority ordering.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input if args.input.is_absolute() else ROOT / args.input
    publications = load_publications(input_path)
    representative_dois = tuple(args.representative_doi or DEFAULT_REPRESENTATIVE_DOIS)
    full_dois = tuple(args.full_doi or DEFAULT_FULL_DOIS)
    output = args.output or (OUTPUT_PATH_ZH if args.language == "zh" else OUTPUT_PATH)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render(
            publications,
            representative_dois,
            args.language,
            full=args.full,
            full_dois=full_dois,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {args.language} CV publications to {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
