#import "theme.typ": *
#import "journal_metrics.typ": *

#let input(key, default: "") = {
  let value = sys.inputs.at(key, default: default)
  if value == "" { default } else { value }
}

#let name = input("profile_name", default: "Miao-Jiong Tang")
#let role = input("profile_role", default: "Integrated M.S.-Ph.D. student in chemistry")
#let affiliation = input("profile_affiliation", default: "Department of Chemistry, Zhejiang University")
#let location = input("profile_location", default: "Hangzhou, China")
#let email = input("profile_email", default: "mj_t@zju.edu.cn")
#let phone = input("profile_phone", default: "(+86)136-5663-9176")
#let political-status = "CPC member"
#let english-level = "CET-6"
#let photo = input("profile_image", default: "assets/profile.png")
#let github-url = input("profile_github_url", default: "https://github.com/gentle1999")
#let orcid-url = input("profile_orcid_url", default: "https://orcid.org/0000-0003-2075-366X")
#let google-scholar-url = input("profile_google_scholar_url", default: "https://scholar.google.com/citations?user=86_ftaAAAAAJ")

#let metadata = make-metadata(
  first-name: "Miao-Jiong",
  last-name: "Tang",
  display-name: name,
  quote: role + " · " + affiliation + " · data-driven chemistry / chemical AI",
  footer: "Curriculum vitae",
  github: github-url,
  email: email,
  phone: phone,
  political-status: political-status,
  english-level: english-level,
  orcid: orcid-url,
  scholar: google-scholar-url,
  location: location,
  section-highlight: "full",
  date-width: "3.75cm",
  font-size: "8.15pt",
  photo-radius: "50%",
  show-online-links: false,
  two-line-contact: true,
)

#show: doc => cv-with-custom-header(
  metadata,
  resume-repeat-header(
    name,
    email,
    phone,
    political-status,
    english-level,
    photo,
    location: location,
    subtitle: [#role · #affiliation · data-driven chemistry / chemical AI],
    name-size: 28pt,
    info-size: 8.05pt,
  ),
  doc,
)

#compact-note([
  Integrated M.S.-Ph.D. student in chemistry at Zhejiang University, working on data-driven organic synthesis reaction modeling and computational acceleration. My research connects asymmetric catalysis, molecular/reaction data infrastructure, quantum-chemical computation, and graph representation learning; first-author papers in #text(style: "italic")[Angew. Chem., Int. Ed.], #text(style: "italic")[Sci. Data], and #text(style: "italic")[Chem. Asian J.], with contribution to the #text(style: "italic")[Nat. Mach. Intell.] RXNGraphormer framework.
])

#v(7pt)

#cv-section("Education")

#cv-entry(
  title: [Zhejiang University · Chemistry, Integrated M.S.-Ph.D.],
  society: [Department of Chemistry | Research: data-driven organic synthesis reaction modeling and computational acceleration | Advisor: Prof. Xin Hong],
  date: [2022.09 - 2027.06 expected],
  location: [Hangzhou, China],
)

#cv-entry(
  title: [Zhejiang University · B.S. in Chemistry],
  society: [Chu Kochen Honors College, Qiushi Chemistry Program | GPA 3.77/4.0 | Advisor: Prof. Xin Hong],
  date: [2018.09 - 2022.06],
  location: [Hangzhou, China],
)

#cv-section("Honors, Awards, and Funding")

#cv-honor(
  date: [2026],
  title: [Zhejiang University Qiushi Rising Star doctoral funding],
  location: [Funding],
)

#cv-honor(
  date: [Graduate],
  title: [Zhejiang University Outstanding Graduate Student; NHU Innovation Scholarship],
  location: [Award],
)

#cv-honor(
  date: [Undergraduate],
  title: [Zhejiang University Outstanding Graduate; Outstanding Communist Youth League Member; MCM Meritorious Winner twice],
  location: [Award],
)

#cv-honor(
  date: [Undergraduate],
  title: [Zhejiang University Academic Scholarship: Second Class once and Third Class twice; Chu Kochen Honors College Elite Student Scholarship; provincial SRTP project; National Chemistry Experiment Innovation Design Competition Third Prize],
  location: [Scholarship],
)

#cv-section("Project Experience")

#project-entry(
  title: [MolGR molecular graph reconstruction toolkit],
  outcome: [XYZ-to-RDKit molecular graph reconstruction Python package],
  date: [2025.12 - present],
  role: [Lead developer],
  description: list(
    [Developed a C++/Python toolkit that converts XYZ text, total charge, and spin multiplicity into RDKit molecules with bond orders, 3D conformers, optional dative bonds, and optional stereochemistry.],
    [Optimized candidate enumeration, scoring, and RDKit post-processing; internal benchmarks show millisecond-level reconstruction and improved handling of metal/spin systems compared with xyz2graph-like tools.],
  ),
)

#project-entry(
  title: [N,N′-dioxide asymmetric Michael addition modeling platform],
  outcome: [First-author paper: #text(style: "italic")[Angew. Chem., Int. Ed.] 2026],
  date: [2024.10 - 2025.08],
  role: [First author / lead],
  description: list(
    [Curated N,N′-dioxide/metal-catalyzed Michael addition reactions and built mechanism-aware GNN and similarity-weighted extrapolation workflows for catalyst selection and selectivity prediction.],
  ),
)

#project-entry(
  title: [RXNGraphormer unified pre-trained reaction modeling framework],
  outcome: [Co-author paper: #text(style: "italic")[Nat. Mach. Intell.] 2025],
  date: [2024.07 - 2025.03],
  role: [Algorithm contributor],
  description: list(
    [During internship at Shanghai Academy of AI for Science, designed fictitious reaction generation algorithms for pre-training reaction embeddings, yield/selectivity prediction, and synthesis planning.],
  ),
)

#project-entry(
  title: [MolOP molecular computation log parser and data engine],
  outcome: [Computational chemistry data parsing and automation toolkit],
  date: [2023.10 - present],
  role: [Lead developer],
  description: list(
    [Developed a type-aware, unit-aware, parallelizable parser and data engine for molecular computation logs, supporting quantum-chemical data production and automated workflows.],
  ),
)

#project-entry(
  title: [Tianchi Scientific Intelligence Competition: molecular property prediction],
  outcome: [Quantum-chemical energy and force prediction for organic molecules],
  date: [2023.08 - 2023.10],
  role: [Team member],
  description: list(
    [Used graph neural networks to predict quantum-chemical energies and forces of organic molecules, with model and training-strategy optimization.],
  ),
)

#project-entry(
  title: [QM9star molecular dataset and qm9star_query platform],
  outcome: [First-author paper: #text(style: "italic")[Sci. Data] 2024],
  date: [2023.03 - 2024.06],
  role: [First author / lead],
  description: list(
    [Built a DFT-optimized dataset for ions, radicals, and neutral molecules, plus database queries, API services, GNN examples, and tutorials.],
  ),
)

#project-entry(
  title: [Spectrum-based molecular representations for reaction performance prediction],
  outcome: [First-author paper: #text(style: "italic")[Chem. Asian J.] 2023],
  date: [2022.04 - 2023.02],
  role: [First author / lead],
  description: list(
    [Parsed molecular NMR spectrum images with image-recognition workflows and applied spectrum-derived vectors to reaction performance prediction.],
  ),
)

#pagebreak()

#resume-repeat-header(
  name,
  email,
  phone,
  political-status,
  english-level,
  photo,
  location: location,
  subtitle: [#role · #affiliation · data-driven chemistry / chemical AI],
  info-size: 8.05pt,
)

#cv-section("Professional Skills")

#skill-item(
  [Machine learning],
  [Proficient in Python-based research data mining, scripting, and model experimentation; familiar with supervised learning, GNNs, Transformer/pre-training models, and image-processing workflows for molecular property prediction, reaction selectivity, synthesis planning, and spectrum-based representations.],
  label-width: 4.15cm,
)

#skill-item(
  [Computational chemistry],
  [Experienced with Gaussian, xTB, and related tools; able to combine Python scripts with computation software for mechanism studies, batch optimization, log parsing, and data production; understands electronic structure, transition states, atomic/bond properties, and 3D conformations for molecular representation and model interpretation.],
  label-width: 4.15cm,
)

#skill-item(
  [Ascend and operator optimization],
  [Experienced with the Huawei Ascend platform and operator optimization; able to deploy and profile workloads, locate performance bottlenecks, and improve operator implementations and data flow for Ascend hardware.],
  label-width: 4.15cm,
)

#skill-item(
  [Cheminformatics],
  [Experienced with RDKit, OpenBabel, and molecular toolkit extension; able to build molecular and reaction data infrastructure from XYZ/SMILES, computation logs, literature reactions, spectrum images, and quantum-chemical outputs.],
  label-width: 4.15cm,
)

#skill-item(
  [Research engineering],
  [Experienced in chemical databases, API services, command-line tools, and reproducible data pipelines; familiar with backend development, Linux, CI/CD, containers, and virtualization for maintainable research software and automated workflows.],
  label-width: 4.15cm,
)

#skill-item(
  [GitHub],
  [#link(github-url)[#github-url]],
  label-width: 4.15cm,
)

#skill-item(
  [Google Scholar],
  [#link(google-scholar-url)[#google-scholar-url]],
  label-width: 4.15cm,
)

#skill-item(
  [ORCID],
  [#link(orcid-url)[#orcid-url]],
  label-width: 4.15cm,
)

#cv-section("Publications")

#compact-note([
  Currently 3 first-author SCI papers and 8 co-authored papers. Publications are listed with representative works first.
])

#v(1.5pt)
#include "publications.typ"
