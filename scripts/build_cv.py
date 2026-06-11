#!/usr/bin/env python3
"""Compile the Typst CV PDF using generated site variables."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VARIABLES_PATH = ROOT / "_variables.yml"
CV_SOURCE = ROOT / "cv" / "main.typ"
DEFAULT_OUTPUT = ROOT / "assets" / "miao-jiong-tang-cv.pdf"


def env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return default


def load_site_profile(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    profile = payload.get("profile") if isinstance(payload, dict) else {}
    if not isinstance(profile, dict):
        return {}
    return {str(key): "" if value is None else str(value) for key, value in profile.items()}


def profile_value(profile: dict[str, str], key: str, *env_names: str, default: str = "") -> str:
    env_value = env_first(*env_names)
    if env_value:
        return env_value
    return profile.get(key) or default


def typst_path(value: str) -> str:
    if not value:
        return ""
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return os.path.relpath(path, CV_SOURCE.parent).replace(os.sep, "/")


def compile_command(source: Path, output: Path, inputs: dict[str, str]) -> list[str]:
    if shutil.which("quarto"):
        command = ["quarto", "typst", "compile", "--root", str(ROOT)]
    elif shutil.which("typst"):
        command = ["typst", "compile", "--root", str(ROOT)]
    else:
        raise RuntimeError(
            "Neither `quarto` nor `typst` was found on PATH. Install Quarto or Typst first.",
        )

    for key, value in inputs.items():
        command.extend(["--input", f"{key}={value}"])
    command.extend([str(source.relative_to(ROOT)), str(output.relative_to(ROOT))])
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variables", type=Path, default=VARIABLES_PATH)
    parser.add_argument("--source", type=Path, default=CV_SOURCE)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    variables = args.variables if args.variables.is_absolute() else ROOT / args.variables
    source = args.source if args.source.is_absolute() else ROOT / args.source
    profile = load_site_profile(variables)
    output = args.output or Path(profile.get("cv_pdf") or DEFAULT_OUTPUT)
    if not output.is_absolute():
        output = ROOT / output

    inputs = {
        "profile_name": profile_value(profile, "name", "PROFILE_NAME", "PROFILE_DISPLAY_NAME"),
        "profile_name_zh": profile_value(profile, "name_zh", "PROFILE_NAME_ZH"),
        "profile_role": profile_value(profile, "role", "PROFILE_ROLE"),
        "profile_role_zh": profile_value(profile, "role_zh", "PROFILE_ROLE_ZH"),
        "profile_affiliation": profile_value(profile, "affiliation", "PROFILE_AFFILIATION"),
        "profile_affiliation_zh": profile_value(
            profile,
            "affiliation_zh",
            "PROFILE_AFFILIATION_ZH",
        ),
        "profile_location": profile_value(profile, "location", "PROFILE_LOCATION"),
        "profile_email": profile_value(profile, "email", "PROFILE_EMAIL"),
        "profile_phone": profile_value(profile, "phone", "PROFILE_PHONE"),
        "profile_political_status": profile_value(
            profile,
            "political_status",
            "PROFILE_POLITICAL_STATUS",
        ),
        "profile_political_status_zh": profile_value(
            profile,
            "political_status_zh",
            "PROFILE_POLITICAL_STATUS_ZH",
        ),
        "profile_english_level": profile_value(
            profile,
            "english_level",
            "PROFILE_ENGLISH_LEVEL",
        ),
        "profile_english_level_zh": profile_value(
            profile,
            "english_level_zh",
            "PROFILE_ENGLISH_LEVEL_ZH",
        ),
        "profile_birth_ym": profile_value(profile, "birth_ym", "PROFILE_BIRTH_YM"),
        "profile_birth_ym_zh": profile_value(profile, "birth_ym_zh", "PROFILE_BIRTH_YM_ZH"),
        "profile_image": typst_path(profile_value(profile, "image", "PROFILE_IMAGE")),
        "profile_github_url": profile_value(profile, "github_url", "PROFILE_GITHUB_URL"),
        "profile_orcid_url": profile_value(profile, "orcid_url", "PROFILE_ORCID_URL"),
        "profile_google_scholar_url": profile_value(
            profile,
            "google_scholar_url",
            "PROFILE_GOOGLE_SCHOLAR_URL",
        ),
        "profile_cv_pdf": str(output.relative_to(ROOT)),
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    command = compile_command(source, output, inputs)
    subprocess.run(command, cwd=ROOT, check=True)
    print(f"Wrote CV PDF to {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
