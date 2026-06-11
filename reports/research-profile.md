# Research Profile Report

Generated from ORCID/Crossref metadata, pinned GitHub repositories, selected source trees, and full-text reading notes for local publication PDFs on 2026-06-08. Detailed per-paper notes are maintained in [publication-reading-notes.md](publication-reading-notes.md).

## Executive Summary

Miao-jiong Tang's research profile is best described as **data-driven computational chemistry with an infrastructure-first and mechanism-aware style**. The strongest identity is not generic "AI for chemistry"; it is the construction of reusable molecular and reaction data resources, chemically meaningful representations, predictive models, and scientific software that make chemical information easier to query, model, validate, and reuse.

Across the publications, the recurring workflow is:

1. Identify chemically meaningful information that is difficult to use directly, such as literature reaction tables, low-selectivity records in supporting information, spectra, stereochemical environments, quantum-chemical outputs, reactive intermediates, or reaction bond changes.
2. Convert that information into structured, machine-readable resources through curation, standardization, descriptors, databases, or APIs.
3. Build prediction or interpretation models that incorporate chemical structure, mechanism, similarity, or reaction topology.
4. Package the outcome as a reusable data resource, web platform, GitHub repository, notebook, API, or documented workflow.

This profile is strongest when framed around **chemical data infrastructure, mechanism-aware reaction modeling, molecular representation design, and reusable research software**.

## Evidence Reviewed

- ORCID publication metadata for `0000-0003-2075-366X`, merged with Crossref metadata where available.
- Ten local publication PDFs from 2021 to 2026, read through extracted full text with emphasis on introductions, data construction, methods, results, conclusions, data/code availability, and author contribution statements.
- Pinned repositories: `MolOP`, `qm9star_query`, `NNdioxide-asymMichael`, `spectrum_descriptor`, and `rdkit-dof`.
- Representative collaboration repository: `licheng-xu-echo/RXNGraphormer`.
- Repository documentation and selected source files for data access, parsing, model workflows, visualization, and deployment.

## Research Narrative

### Early Foundation: Chiral Representation and Reaction Data

The early work on SPMS and asymmetric hydrogenation established two durable themes: stereochemical information needs specialized representations, and asymmetric catalysis needs structured reaction data before machine learning can be useful.

SPMS turns a molecular van der Waals surface into a spherical-projection matrix and color diagram. It can distinguish scaffold changes, substituent effects, and enantiomers, while remaining interpretable to chemists. The asymmetric hydrogenation work curated 12619 literature reactions, then used hierarchical learning to address a realistic few-shot catalysis problem: making useful predictions for a new olefin when only dozens of target measurements are available.

### Middle Development: Spectra and Quantum-Chemical Data Infrastructure

The spectrum descriptor paper broadened molecular representation beyond structural graphs and hand-picked physical organic parameters. It converts spectral figures or curves into descriptor vectors and demonstrated strong yield prediction performance on Buchwald-Hartwig reactions. This is a first-author example of turning scientific figures into model-ready chemical information.

QM9star then scaled the infrastructure theme to quantum chemistry. It provides approximately two million optimized structures for ions and radicals derived from QM9, with global and local quantum-chemical fields, PostgreSQL storage, query code, PyTorch Geometric support, and neural-network-potential examples. The author contribution statement identifies Miao-jiong Tang's role in data curation/cleaning, investigation, software, and original drafting, making QM9star a central data-infrastructure contribution.

### Recent Work: Mechanism-Aware Reaction Modeling and Synthesis Intelligence

The N,N'-dioxide/metal-catalyzed asymmetric Michael addition paper is currently the most complete first-author reaction-modeling example. It integrates literature-scale curation, a web platform, substrate/catalyst applicability maps, CGRNN modeling, intermediate-based augmentation, similarity-weighted tuning, and experimental validation. It shows the full cycle from data infrastructure to model-guided catalyst selection.

RXNGraphormer extends reaction modeling to a cross-task pre-trained framework for performance prediction, forward synthesis, and retrosynthesis. The author contribution statement specifies Miao-jiong Tang's contribution to the fictitious reaction generation algorithm, a key part of the pre-training strategy used to teach the model real versus chemically plausible but incorrect bond transformations.

The Cu radical LFER and non-heme iron BDE studies show a complementary mechanistic and transition-metal chemistry dimension. In the Cu work, large-scale DFT calculations and linear free energy relationships map mechanism preferences across 132300 ligand-radical-nucleophile combinations. In the non-heme iron BDE work, machine learning is used to predict diabatic bond dissociation energies for metal complexes, with explicit comparison of 2D fingerprints and 3D descriptors.

The LLM synthesis review should be treated as an emerging extension rather than the center of the profile. Its strongest connection to the rest of the work is not "LLMs replace chemistry models", but LLM-assisted data extraction, knowledge management, and agentic orchestration grounded in reliable chemical tools and structured data.

## Core Research Directions

### 1. Molecular and Reaction Data Infrastructure

Representative evidence:

- QM9star: approximately 1.9 million topological structures and 2.0 million three-dimensional structures for cations, anions, radicals, and re-optimized neutral molecules, with atomic and molecular quantum-chemical properties.
- `qm9star_query`: database deployment, query code, FastAPI access, SQLModel models, tutorials, and model-training examples.
- AHO database: 12619 asymmetric hydrogenation reactions from 355 publications.
- N,N'-dioxide/metal Michael addition platform: 2176 curated reactions from 37 publications, with mechanistic annotations and online querying/analysis.

This direction should be described as building reusable computational resources, not just collecting data.

### 2. Mechanism-Aware Reaction Modeling

Representative evidence:

- AHO hierarchical learning uses chemically related data layers and delta learning to approach a sparse target substrate space.
- N,N'-dioxide modeling adds reactive intermediate forms and similarity-weighted tuning to improve leave-one-reaction-out extrapolation.
- RXNGraphormer uses fictitious reaction generation and delta-mol graphs to learn bond-transformation patterns.
- Cu radical LFER uses additive component scales to predict mechanism preferences across a large transition-metal radical space.

The common methodological idea is that realistic reaction prediction requires more than random-split accuracy. The model must handle unseen substrates, catalyst transfer, mechanistic changes, and sparse target data.

### 3. Molecular Representation Design

Representative evidence:

- SPMS represents stereochemical environments as spherical-projection matrices and interpretable steric maps.
- Spectrum descriptors convert NMR/IR/MS-like images or curves into grid descriptors.
- QM9star exposes local atomic properties such as charges, spin densities, NBO bond orders, and forces for downstream representation learning.
- RXNGraphormer encodes bond-change information through delta-mol graphs.
- Non-heme iron BDE work compares Morgan fingerprints, other 2D fingerprints, SOAP, MBTR, and Coulomb Matrix descriptors, clarifying where 3D geometry is useful.

This direction is best framed as designing chemically meaningful representations from nontrivial data modalities.

### 4. Research Software and Reproducible Workflows

Representative evidence:

- MolOP parses computational chemistry files into typed molecular data and command-line workflows.
- `qm9star_query` provides database-backed access and examples for a large quantum-chemical dataset.
- N,N'-dioxide and AHO platforms expose curated reaction data through web or data-access layers.
- Smaller tools such as `spectrum_descriptor` and `rdkit-dof` show consistent attention to practical research workflows and communication.

This is a major differentiator for the website: the research is implemented as software and infrastructure, not only as isolated analyses.

## Representative Work

### Data-Driven N,N'-Dioxide/Metal Asymmetric Michael Additions

This is the most complete first-author reaction-modeling case. It combines a chemically annotated reaction database, online platform, catalyst applicability maps, mechanistically informed CGRNN modeling, similarity-weighted extrapolation, and experimental validation. It should be listed prominently in homepage selected work and CV project descriptions.

### QM9star and `qm9star_query`

This is the clearest data-infrastructure contribution. It combines large-scale DFT data for reactive intermediates with database design, query infrastructure, software, tutorials, and model validation. It should anchor the "molecular data infrastructure" theme.

### RXNGraphormer

This is the strongest cross-task reaction intelligence collaboration. It connects reaction performance prediction with synthesis planning through pre-training, reaction embeddings, fictitious reaction generation, and delta-mol graphs. The website should mention the concrete contribution to the fictitious reaction generation/pre-training pipeline.

### Spectrum Descriptors and SPMS

These works show a long-running interest in molecular representations beyond standard fingerprints: spectra as descriptor sources and stereochemical surfaces as interpretable matrices.

### MolOP and Research Software

MolOP should remain a major software project because it directly supports the infrastructure identity: turning raw computational chemistry output into typed, analysis-ready molecular data.

### Cu Radical LFER and Non-Heme Iron BDE

These collaborations broaden the profile into mechanism maps and transition-metal property prediction. They should support, but not dominate, the main narrative.

## Recommended Homepage Framing

Use concise language around:

- Data-driven computational chemistry.
- Molecular and reaction data infrastructure.
- Mechanism-aware reaction modeling for asymmetric catalysis and synthesis.
- Molecular representations from spectra, stereostructures, quantum-chemical outputs, graph topology, and bond-change patterns.
- Reusable scientific software for parsing, querying, modeling, visualizing, and communicating molecular data.

Recommended English summary:

> I develop data resources, molecular representations, and scientific software for data-driven computational chemistry. My work turns literature reaction records, spectra, stereostructures, quantum-chemical calculations, and reaction bond changes into structured resources for mechanism-aware prediction, catalyst selection, and reusable chemical data infrastructure.

Recommended Chinese summary:

> 我的研究围绕数据驱动的计算化学展开，重点构建分子与反应数据资源、分子表征方法和科研软件。我关注如何将文献反应记录、谱图、立体结构、量子化学计算和反应键变化转化为结构化资源，用于机理感知预测、催化剂选择和可复用化学数据基础设施。

## Recommended CV Framing

The CV should emphasize:

- First-author and lead contributions: spectrum descriptors, QM9star, N,N'-dioxide/metal Michael addition platform.
- Concrete contribution in collaborations: fictitious reaction generation for RXNGraphormer; data analysis in Cu radical LFER; model training in non-heme iron BDE.
- Technical skill groups that reflect actual work: quantum chemistry pipelines, cheminformatics, reaction modeling, database-backed APIs, typed Python tooling, and reproducible documentation.

## Remaining Information That Would Improve Accuracy

- Advisor, lab/group, and thesis topic if intended for public display.
- Official English names and years for awards.
- Teaching assistant roles, invited talks, posters, and conference presentations.
- Public links for deployed datasets, APIs, and web demos.
- Manual ranking of representative publications if the automated order is not the intended public order.
