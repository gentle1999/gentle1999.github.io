#!/usr/bin/env python3
"""Audit publishable files for obvious privacy and leakage risks."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".quarto",
    ".ruff_cache",
    ".tmp",
    ".venv",
    "__pycache__",
    "_freeze",
    "_generated",
    "_site",
}

OFFICE_SUFFIXES = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}
PRIVATE_REFERENCE_NAMES = {
    "2024-汤缪炅-个人简历.pdf",
    "个人简历-徐丽成-最新.pdf",
    "求是新星培养计划.docx",
}

SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gh[oprsu]_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|password|passwd|secret|token)\b\s*[:=]\s*"
        r"[\"'][^\"'\s]{12,}[\"']",
    ),
]

PRIVATE_URL_PATTERNS = [
    re.compile(r"nas\.asymcatml\.net", re.IGNORECASE),
    re.compile(r"https?://[^/\s\"']+:13000\b", re.IGNORECASE),
    re.compile(r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?\b", re.IGNORECASE),
    re.compile(r"https?://10\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?\b"),
    re.compile(r"https?://192\.168\.\d{1,3}\.\d{1,3}(?::\d+)?\b"),
    re.compile(r"https?://172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}(?::\d+)?\b"),
]

ALLOWED_SITE_ASSETS = {
    Path("_site/assets/language-switch.html"),
    Path("_site/assets/profile.png"),
    Path("_site/assets/miao-jiong-tang-cv.pdf"),
    Path("_site/assets/tang-miaojiong-cv-zh.pdf"),
}
ALLOWED_SITE_ASSET_PREFIXES = (
    Path("_site/assets/publications/generated"),
    Path("_site/assets/publications/pdfs"),
)
ALLOWED_SITE_DATA = {
    Path("_site/data/repos.json"),
    Path("_site/data/publications.json"),
    Path("_site/data/publication_images.json"),
    Path("_site/data/publication_pdfs.json"),
}


@dataclass(frozen=True)
class Finding:
    severity: str
    path: Path
    message: str

    def format(self) -> str:
        try:
            rel_path = self.path.relative_to(ROOT)
        except ValueError:
            rel_path = self.path
        return f"{self.severity}: {rel_path.as_posix()}: {self.message}"


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def is_excluded(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return any(part in EXCLUDED_DIRS for part in relative.parts)


def git_candidate_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())

    files: list[Path] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = (ROOT / raw.decode("utf-8", errors="replace")).resolve()
        if path.exists() and path.is_file() and not is_excluded(path):
            files.append(path)
    return sorted(files)


def walk_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(item for item in path.rglob("*") if item.is_file())


def is_probably_text(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:8192]
    except OSError:
        return False
    if b"\0" in chunk:
        return False
    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def scan_text(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(Finding("ERROR", path, "possible hard-coded secret"))
            break
    for pattern in PRIVATE_URL_PATTERNS:
        if pattern.search(text):
            findings.append(Finding("ERROR", path, "private or local URL is present"))
            break
    return findings


def audit_source_files(files: list[Path]) -> tuple[list[Finding], list[Finding]]:
    errors: list[Finding] = []
    warnings: list[Finding] = []

    for path in files:
        if path.suffix.lower() in OFFICE_SUFFIXES:
            errors.append(Finding("ERROR", path, "Office source document would be committed"))
        if path.name in PRIVATE_REFERENCE_NAMES:
            errors.append(Finding("ERROR", path, "private reference asset would be committed"))
        if path.name.startswith(".env"):
            errors.append(Finding("ERROR", path, "environment file would be committed"))
        publication_pdf_root = ROOT / "assets" / "publications" / "pdfs"
        if is_under(path, publication_pdf_root) and path.suffix.lower() == ".pdf":
            warnings.append(
                Finding(
                    "WARNING",
                    path,
                    "publication PDF would be committed; confirm distribution rights",
                ),
            )
        if is_probably_text(path):
            errors.extend(scan_text(path, read_text(path)))

    return errors, warnings


def site_asset_allowed(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if relative in ALLOWED_SITE_ASSETS:
        return True
    return any(is_under(relative, prefix) for prefix in ALLOWED_SITE_ASSET_PREFIXES)


def site_data_allowed(path: Path) -> bool:
    return path.relative_to(ROOT) in ALLOWED_SITE_DATA


def audit_site_files(files: list[Path]) -> tuple[list[Finding], list[Finding]]:
    errors: list[Finding] = []
    warnings: list[Finding] = []

    for path in files:
        if path.suffix.lower() in OFFICE_SUFFIXES:
            errors.append(Finding("ERROR", path, "Office source document is in rendered site"))
        if path.name in PRIVATE_REFERENCE_NAMES:
            errors.append(Finding("ERROR", path, "private reference asset is in rendered site"))
        if is_under(path, ROOT / "_site" / "assets") and not site_asset_allowed(path):
            errors.append(Finding("ERROR", path, "unexpected asset in rendered site"))
        if is_under(path, ROOT / "_site" / "data") and not site_data_allowed(path):
            errors.append(Finding("ERROR", path, "unexpected data file in rendered site"))
        if is_probably_text(path):
            errors.extend(scan_text(path, read_text(path)))

    return errors, warnings


def summarize_pdf_payload(files: list[Path]) -> str | None:
    pdfs = [path for path in files if path.suffix.lower() == ".pdf"]
    if not pdfs:
        return None
    total_bytes = sum(path.stat().st_size for path in pdfs)
    total_mb = total_bytes / (1024 * 1024)
    return f"{len(pdfs)} publication PDFs, {total_mb:.1f} MiB total"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", default="_site", help="Rendered site directory to audit.")
    parser.add_argument(
        "--skip-site",
        action="store_true",
        help="Only audit source files that would be committed.",
    )
    args = parser.parse_args()

    errors: list[Finding] = []
    warnings: list[Finding] = []

    source_files = git_candidate_files()
    source_errors, source_warnings = audit_source_files(source_files)
    errors.extend(source_errors)
    warnings.extend(source_warnings)

    site_files: list[Path] = []
    site_dir = (ROOT / args.site_dir).resolve()
    if not args.skip_site:
        site_files = walk_files(site_dir)
        if not site_files:
            warnings.append(Finding("WARNING", site_dir, "rendered site directory does not exist"))
        site_errors, site_warnings = audit_site_files(site_files)
        errors.extend(site_errors)
        warnings.extend(site_warnings)

    for finding in [*errors, *warnings]:
        print(finding.format())

    publication_pdf_summary = summarize_pdf_payload(
        [
            path
            for path in site_files
            if is_under(path, ROOT / "_site" / "assets" / "publications" / "pdfs")
        ],
    )
    if publication_pdf_summary:
        print(f"INFO: _site/assets/publications/pdfs contains {publication_pdf_summary}.")

    print(f"INFO: audited {len(source_files)} candidate source files.")
    if not args.skip_site:
        print(f"INFO: audited {len(site_files)} rendered site files.")

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
