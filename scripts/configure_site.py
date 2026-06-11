#!/usr/bin/env python3
"""Generate Quarto configuration files from environment variables."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
QUARTO_TEMPLATE = ROOT / "_quarto.template.yml"
VARIABLES_TEMPLATE = ROOT / "_variables.template.yml"
QUARTO_OUTPUT = ROOT / "_quarto.yml"
VARIABLES_OUTPUT = ROOT / "_variables.yml"
ORCID_API = "https://pub.orcid.org/v3.0"
DISPLAY_ALIAS_REPLACEMENTS = {
    "Mougui Tang": "Miao-Jiong Tang",
}
DISPLAY_NAME_REPLACEMENTS = {
    "Miao-jiong Tang": "Miao-Jiong Tang",
}


def env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return default


def clean_orcid(value: str) -> str:
    value = value.strip()
    value = value.removeprefix("https://orcid.org/")
    value = value.removeprefix("http://orcid.org/")
    return value


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def request_json(url: str) -> Any:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "quarto-academic-homepage",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ORCID request failed: {exc.code} {exc.reason}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"ORCID request failed: {exc.reason}") from exc


def fetch_orcid_person(orcid: str) -> dict[str, Any]:
    payload = request_json(f"{ORCID_API}/{quote(orcid)}/person")
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected ORCID person response for {orcid}: {payload!r}")
    return payload


def fetch_orcid_person_or_empty(orcid: str) -> dict[str, Any]:
    try:
        return fetch_orcid_person(orcid)
    except RuntimeError as exc:
        if env_flag("STRICT_UPDATES"):
            raise SystemExit(str(exc)) from exc
        print(f"warning: {exc}", file=sys.stderr)
        print("warning: falling back to local profile defaults", file=sys.stderr)
        return {}


def value_field(payload: Any) -> str:
    if isinstance(payload, dict):
        value = payload.get("value")
        if isinstance(value, str):
            return value.strip()
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
        content = str(item.get("content") or "").strip()
        key = content.casefold()
        if content and key not in seen:
            seen.add(key)
            values.append(content)
    return values


def has_cjk(value: str) -> bool:
    return bool(re.search(r"[\u3400-\u9fff]", value))


def profile_aliases_line(aliases: str, language_code: str) -> str:
    if not aliases:
        return ""
    prefix = "其他署名：" if language_code == "zh" else "Also published as: "
    return f"{prefix}{aliases}"


def profile_academic_line(group: str, advisor: str, language_code: str) -> str:
    parts: list[str] = []
    if group:
        label = "课题组" if language_code == "zh" else "Group"
        parts.append(f"{label}: {group}")
    if advisor:
        label = "导师" if language_code == "zh" else "Advisor"
        parts.append(f"{label}: {advisor}")
    separator = "；" if language_code == "zh" else "; "
    return separator.join(parts)


def yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def should_keep_alias(alias: str, primary_names: set[str]) -> bool:
    if alias in primary_names:
        return False
    if has_cjk(alias):
        return False
    return True


def display_alias(alias: str) -> str:
    return DISPLAY_ALIAS_REPLACEMENTS.get(alias, alias)


def display_name(name: str) -> str:
    return DISPLAY_NAME_REPLACEMENTS.get(name, name)


def display_aliases(aliases: list[str], primary_names: set[str]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for alias in aliases:
        alias = display_alias(alias)
        key = alias.casefold()
        if should_keep_alias(alias, primary_names) and key not in seen:
            seen.add(key)
            values.append(alias)
    return values


def build_context() -> dict[str, str]:
    github_username = env_first(
        "GITHUB_USERNAME",
        "PROFILE_GITHUB_USERNAME",
        default="gentle1999",
    )
    configured_profile_name = env_first(
        "PROFILE_NAME",
        "PROFILE_DISPLAY_NAME",
        "DISPLAY_NAME",
    )
    orcid = clean_orcid(env_first("PROFILE_ORCID", "ORCID_ID"))
    orcid_person = fetch_orcid_person_or_empty(orcid) if orcid else {}
    orcid_name = orcid_registered_name(orcid_person)
    orcid_aliases = orcid_other_names(orcid_person)

    profile_name = display_name(configured_profile_name or orcid_name or "Miao-Jiong Tang")
    profile_name_zh = env_first(
        "PROFILE_NAME_ZH",
        default=next((alias for alias in orcid_aliases if has_cjk(alias)), "汤缪炅"),
    )
    deduped_aliases = display_aliases(orcid_aliases, {profile_name, profile_name_zh})
    profile_aliases = env_first("PROFILE_ALIASES", default="; ".join(deduped_aliases))
    profile_aliases_zh = env_first("PROFILE_ALIASES_ZH", default="；".join(deduped_aliases))
    website_title = env_first("SITE_TITLE", default=profile_name)

    github_repository = env_first(
        "GITHUB_REPOSITORY",
        default=f"{github_username}/{github_username}.github.io",
    )
    site_url = env_first("SITE_URL", default=f"https://{github_username}.github.io")
    repo_url = env_first(
        "SITE_REPO_URL",
        "REPOSITORY_URL",
        default=f"https://github.com/{github_repository}",
    )
    github_url = env_first("PROFILE_GITHUB_URL", default=f"https://github.com/{github_username}")
    orcid_url = env_first(
        "PROFILE_ORCID_URL",
        default=f"https://orcid.org/{orcid}" if orcid else "#",
    )
    profile_advisor = env_first("PROFILE_ADVISOR")
    profile_advisor_zh = env_first("PROFILE_ADVISOR_ZH")
    profile_group = env_first("PROFILE_GROUP")
    profile_group_zh = env_first("PROFILE_GROUP_ZH")

    values = {
        "website_title": website_title,
        "site_url": site_url,
        "repo_url": repo_url,
        "site_description": env_first(
            "SITE_DESCRIPTION",
            default=(
                "Personal academic homepage of Miao-Jiong Tang, focused on data-driven "
                "computational chemistry, reaction modeling, molecular data infrastructure, "
                "and cheminformatics."
            ),
        ),
        "site_keywords": env_first(
            "SITE_KEYWORDS",
            default=(
                "computational chemistry, machine learning, reaction modeling, molecular "
                "descriptors, asymmetric catalysis, quantum chemistry data, cheminformatics"
            ),
        ),
        "footer_left": f"© {datetime.now().year} {website_title}",
        "profile_name": profile_name,
        "profile_name_zh": profile_name_zh,
        "profile_aliases": profile_aliases,
        "profile_aliases_zh": profile_aliases_zh,
        "profile_aliases_line": profile_aliases_line(profile_aliases, "en"),
        "profile_aliases_line_zh": profile_aliases_line(profile_aliases_zh, "zh"),
        "profile_role_zh": env_first("PROFILE_ROLE_ZH", default="化学硕博连读研究生"),
        "profile_affiliation_zh": env_first("PROFILE_AFFILIATION_ZH", default="浙江大学化学系"),
        "profile_role": env_first(
            "PROFILE_ROLE",
            default="Integrated M.S.-Ph.D. student in chemistry",
        ),
        "profile_affiliation": env_first(
            "PROFILE_AFFILIATION",
            default="Department of Chemistry, Zhejiang University",
        ),
        "profile_advisor": profile_advisor,
        "profile_advisor_zh": profile_advisor_zh,
        "profile_group": profile_group,
        "profile_group_zh": profile_group_zh,
        "profile_academic_line": profile_academic_line(
            profile_group,
            profile_advisor,
            "en",
        ),
        "profile_academic_line_zh": profile_academic_line(
            profile_group_zh,
            profile_advisor_zh,
            "zh",
        ),
        "profile_location": env_first("PROFILE_LOCATION", default="Hangzhou, China"),
        "profile_email": env_first("PROFILE_EMAIL", default="mj_t@zju.edu.cn"),
        "profile_phone": env_first("PROFILE_PHONE", default="(+86)136-5663-9176"),
        "profile_political_status": env_first(
            "PROFILE_POLITICAL_STATUS",
            default="Political status: CPC member",
        ),
        "profile_political_status_zh": env_first(
            "PROFILE_POLITICAL_STATUS_ZH",
            default="政治面貌：中共党员",
        ),
        "profile_english_level": env_first(
            "PROFILE_ENGLISH_LEVEL",
            default="English: CET-6",
        ),
        "profile_english_level_zh": env_first(
            "PROFILE_ENGLISH_LEVEL_ZH",
            default="英语水平：CET-6",
        ),
        "profile_birth_ym": env_first("PROFILE_BIRTH_YM", default="Born: 1999.10"),
        "profile_birth_ym_zh": env_first("PROFILE_BIRTH_YM_ZH", default="出生年月：1999.10"),
        "profile_image": env_first("PROFILE_IMAGE", default="assets/profile.png"),
        "github_username": github_username,
        "profile_github_url": github_url,
        "profile_orcid": orcid,
        "profile_orcid_url": orcid_url,
        "profile_google_scholar_url": env_first(
            "PROFILE_GOOGLE_SCHOLAR_URL",
            default="https://scholar.google.com/citations?user=86_ftaAAAAAJ",
        ),
        "profile_cv_pdf": env_first(
            "PROFILE_CV_PDF",
            default="assets/miao-jiong-tang-cv.pdf",
        ),
        "profile_cv_pdf_zh": env_first(
            "PROFILE_CV_PDF_ZH",
            default="assets/tang-miaojiong-cv-zh.pdf",
        ),
        "profile_research_summary": env_first(
            "PROFILE_RESEARCH_SUMMARY",
            default=(
                "My research focuses on data-driven computational chemistry, combining "
                "cheminformatics, molecular and reaction data infrastructure, quantum-chemical "
                "workflows, and machine-learning methods for reaction modeling and molecular "
                "representation."
            ),
        ),
        "profile_research_summary_zh": env_first(
            "PROFILE_RESEARCH_SUMMARY_ZH",
            default=(
                "我的研究聚焦数据驱动的计算化学，结合化学信息学、分子与反应数据基础设施、"
                "量子化学计算流程和机器学习方法，用于反应建模与分子表征。"
            ),
        ),
    }
    return {key: yaml_scalar(value) for key, value in values.items()}


def render_template(path: Path, context: dict[str, str]) -> str:
    template = path.read_text(encoding="utf-8")
    placeholders = set(re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", template))
    missing = sorted(placeholders - context.keys())
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(f"{path.name} has unknown placeholders: {names}")
    return Template(template).substitute(context)


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with an error if generated files are out of date.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    context = build_context()
    outputs = {
        QUARTO_OUTPUT: render_template(QUARTO_TEMPLATE, context),
        VARIABLES_OUTPUT: render_template(VARIABLES_TEMPLATE, context),
    }
    changed = []
    if args.check:
        for path, content in outputs.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                changed.append(path.name)
        if changed:
            names = ", ".join(changed)
            raise SystemExit(f"Generated configuration is out of date: {names}")
        print("Generated configuration is up to date.")
        return 0

    for path, content in outputs.items():
        if write_if_changed(path, content):
            changed.append(path.name)
    if changed:
        print(f"Updated generated configuration: {', '.join(changed)}")
    else:
        print("Generated configuration is up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
