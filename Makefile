SHELL := /usr/bin/env bash

PYTHON := uv run python
QUARTO := uv run quarto
CV_PDF ?= assets/miao-jiong-tang-cv.pdf
CV_PDF_ZH ?= assets/tang-miaojiong-cv-zh.pdf
UV_SYNC_FLAGS ?=

GITHUB_USERNAME ?= gentle1999
GITHUB_TOKEN ?=
PROFILE_NAME ?=
PROFILE_DISPLAY_NAME ?=
DISPLAY_NAME ?=
PROFILE_ALIASES ?=
PROFILE_ALIASES_ZH ?=
SITE_TITLE ?=
SITE_URL ?=
SITE_REPO_URL ?=
SITE_DESCRIPTION ?=
SITE_KEYWORDS ?=
PROFILE_NAME_ZH ?=
PROFILE_ROLE_ZH ?=
PROFILE_AFFILIATION_ZH ?=
PROFILE_ROLE ?=
PROFILE_AFFILIATION ?=
PROFILE_LOCATION ?=
PROFILE_EMAIL ?=
PROFILE_PHONE ?=
PROFILE_POLITICAL_STATUS ?=
PROFILE_POLITICAL_STATUS_ZH ?=
PROFILE_ENGLISH_LEVEL ?=
PROFILE_ENGLISH_LEVEL_ZH ?=
PROFILE_BIRTH_YM ?=
PROFILE_BIRTH_YM_ZH ?=
PROFILE_IMAGE ?=
PROFILE_GITHUB_USERNAME ?=
PROFILE_GITHUB_URL ?=
PROFILE_ORCID ?=
PROFILE_ORCID_URL ?=
PROFILE_GOOGLE_SCHOLAR_URL ?=
PROFILE_CV_PDF ?= $(CV_PDF)
PROFILE_CV_PDF_ZH ?= $(CV_PDF_ZH)
PROFILE_RESEARCH_SUMMARY ?=
PROFILE_RESEARCH_SUMMARY_ZH ?=
ORCID_ID ?= 0000-0003-2075-366X
CROSSREF_EMAIL ?=
CROSSREF_QUERY_AUTHOR ?=
STRICT_UPDATES ?= 0
PUBLICATION_IMAGE_MIN_CONFIDENCE ?= medium
PUBLICATION_IMAGE_TIMEOUT ?= 30
PUBLICATION_IMAGE_FORCE ?= 0
PUBLICATION_IMAGE_STRICT ?= 0
PUBLICATION_PDF_MIN_CONFIDENCE ?= medium
PUBLICATION_PDF_TIMEOUT ?= 15
PUBLICATION_PDF_FORCE ?= 0
PUBLICATION_PDF_STRICT ?= 0
PUBLICATION_PDF_AUTO_DOWNLOAD ?= 1
UNPAYWALL_EMAIL ?=

export GITHUB_USERNAME
export GITHUB_TOKEN
export PROFILE_NAME
export PROFILE_DISPLAY_NAME
export DISPLAY_NAME
export PROFILE_ALIASES
export PROFILE_ALIASES_ZH
export SITE_TITLE
export SITE_URL
export SITE_REPO_URL
export SITE_DESCRIPTION
export SITE_KEYWORDS
export PROFILE_NAME_ZH
export PROFILE_ROLE_ZH
export PROFILE_AFFILIATION_ZH
export PROFILE_ROLE
export PROFILE_AFFILIATION
export PROFILE_LOCATION
export PROFILE_EMAIL
export PROFILE_PHONE
export PROFILE_POLITICAL_STATUS
export PROFILE_POLITICAL_STATUS_ZH
export PROFILE_ENGLISH_LEVEL
export PROFILE_ENGLISH_LEVEL_ZH
export PROFILE_BIRTH_YM
export PROFILE_BIRTH_YM_ZH
export PROFILE_IMAGE
export PROFILE_GITHUB_USERNAME
export PROFILE_GITHUB_URL
export PROFILE_ORCID
export PROFILE_ORCID_URL
export PROFILE_GOOGLE_SCHOLAR_URL
export PROFILE_CV_PDF
export PROFILE_CV_PDF_ZH
export PROFILE_RESEARCH_SUMMARY
export PROFILE_RESEARCH_SUMMARY_ZH
export ORCID_ID
export CROSSREF_EMAIL
export CROSSREF_QUERY_AUTHOR
export STRICT_UPDATES
export PUBLICATION_IMAGE_MIN_CONFIDENCE
export PUBLICATION_IMAGE_TIMEOUT
export PUBLICATION_IMAGE_FORCE
export PUBLICATION_IMAGE_STRICT
export PUBLICATION_PDF_MIN_CONFIDENCE
export PUBLICATION_PDF_TIMEOUT
export PUBLICATION_PDF_FORCE
export PUBLICATION_PDF_STRICT
export PUBLICATION_PDF_AUTO_DOWNLOAD
export UNPAYWALL_EMAIL

.PHONY: install configure update-repos update-publications update-publication-images update-publication-pdfs generate-cv-publications build-cv update-cv update render preview clean check audit

install:
	uv sync $(UV_SYNC_FLAGS)

configure:
	$(PYTHON) scripts/configure_site.py

update-repos:
	$(PYTHON) scripts/update_github_repos.py

update-publications:
	$(PYTHON) scripts/update_publications.py

update-publication-images: update-publications
	$(PYTHON) scripts/update_publication_images.py
	$(PYTHON) scripts/update_publications.py

update-publication-pdfs: update-publications
	$(PYTHON) scripts/update_publication_pdfs.py
	$(PYTHON) scripts/update_publications.py

generate-cv-publications:
	$(PYTHON) scripts/generate_cv_publications.py --language en --output cv/publications.typ --full
	$(PYTHON) scripts/generate_cv_publications.py --language zh --output cv/publications.zh.typ --full

build-cv: configure generate-cv-publications
	$(PYTHON) scripts/build_cv.py --source cv/main.typ --output $(CV_PDF)
	$(PYTHON) scripts/build_cv.py --source cv/main.zh.typ --output $(CV_PDF_ZH)

update-cv: update-publications build-cv

update: update-repos update-publication-images update-publication-pdfs build-cv

render: configure build-cv
	$(QUARTO) render

audit:
	$(PYTHON) scripts/audit_privacy.py

preview: configure build-cv
	$(QUARTO) preview --no-browser --port $${PORT:-4200}

clean:
	rm -rf _site .quarto
	rm -f cv/publications.typ $(CV_PDF) $(CV_PDF_ZH)

check: configure generate-cv-publications
	uv run ruff check scripts
	$(PYTHON) -m compileall scripts
	$(PYTHON) -m json.tool data/repos.json >/dev/null
	$(PYTHON) -m json.tool data/publications.json >/dev/null
	@if [ -f data/publication_images.json ]; then $(PYTHON) -m json.tool data/publication_images.json >/dev/null; fi
	@if [ -f data/publication_pdfs.json ]; then $(PYTHON) -m json.tool data/publication_pdfs.json >/dev/null; fi
