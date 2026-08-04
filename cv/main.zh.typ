#import "theme.typ": *
#import "journal_metrics.typ": *

#let input(key, default: "") = {
  let value = sys.inputs.at(key, default: default)
  if value == "" { default } else { value }
}

#let name = input("profile_name", default: "Miao-Jiong Tang")
#let name-zh = input("profile_name_zh", default: "汤缪炅")
#let role = input("profile_role_zh", default: "化学硕博连读研究生")
#let affiliation = input("profile_affiliation_zh", default: "浙江大学化学系")
#let location = "杭州"
#let email = input("profile_email", default: "mj_t@zju.edu.cn")
#let phone = input("profile_phone", default: "(+86)136-5663-9176")
#let political-status = input("profile_political_status_zh", default: "政治面貌：中共党员")
#let english-level = input("profile_english_level_zh", default: "英语水平：CET-6")
#let birth-ym = input("profile_birth_ym_zh", default: "出生年月：1999.10")
#let photo = input("profile_image", default: "assets/profile.png")
#let github-url = input("profile_github_url", default: "https://github.com/gentle1999")
#let orcid-url = input("profile_orcid_url", default: "https://orcid.org/0000-0003-2075-366X")
#let google-scholar-url = input("profile_google_scholar_url", default: "https://scholar.google.com/citations?user=86_ftaAAAAAJ")

#let metadata = make-metadata(
  first-name: "",
  last-name: "",
  display-name: name-zh,
  quote: role + " · " + affiliation + " · 数据驱动化学 / 化学人工智能",
  footer: "个人简历",
  github: github-url,
  email: email,
  phone: phone,
  political-status: political-status,
  english-level: english-level,
  birth-ym: birth-ym,
  orcid: orcid-url,
  scholar: google-scholar-url,
  location: location,
  section-highlight: "full",
  date-width: "3.75cm",
  font-size: "8.72pt",
  photo-radius: "50%",
  show-online-links: false,
  two-line-contact: true,
)

#show: doc => cv-with-custom-header(
  metadata,
  resume-repeat-header(
    name-zh,
    email,
    phone,
    political-status,
    english-level,
    photo,
    location: location,
    subtitle: [#role · #affiliation · 数据驱动化学 / 化学人工智能],
    name-size: 32pt,
  ),
  doc,
)

#compact-note([
  浙江大学化学系硕博连读，研究方向为数据驱动的有机合成反应建模和计算加速。围绕不对称催化反应建模、分子与反应数据基础设施、量子化学计算和图表示学习开展研究；以第一作者发表 #text(style: "italic")[Angew. Chem., Int. Ed.]、#text(style: "italic")[Sci. Data]、#text(style: "italic")[Chem. Asian J.] 论文，并参与 #text(style: "italic")[Nat. Mach. Intell.] 反应预训练框架工作。
])

#v(7pt)

#cv-section("教育经历")

#cv-entry(
  title: [浙江大学 · 化学，硕博连读],
  society: [化学系 | 研究方向：数据驱动的有机合成反应建模和计算加速 | 导师：洪鑫教授],
  date: [2022.09 - 预计2027.06],
  location: [杭州],
  description: list(
    [聚焦“量子化学计算-数据构建-模型学习-反应应用”的闭环研究，面向不对称催化、分子性质和反应性能预测建立数据与模型方法。],
  ),
)

#cv-entry(
  title: [浙江大学 · 化学，本科],
  society: [竺可桢学院求是化学班 | GPA 3.77/4.0 | 导师：洪鑫教授 | 科学计算方向训练],
  date: [2018.09 - 2022.06],
  location: [杭州],
  description: list(
    [完成化学、编程、科学计算和机器学习相关训练，早期工作聚焦分子描述符、谱图表征和反应性能预测。],
  ),
)

#cv-section("奖项与资助")

#cv-honor(
  date: [2026],
  title: [浙江大学博士研究生求是新星培养计划资助项目],
  location: [资助],
)

#cv-honor(
  date: [研究生],
  title: [浙江大学优秀研究生；新和成创新奖学金],
  location: [奖项],
)

#cv-honor(
  date: [本科],
  title: [浙江大学校优秀毕业生；浙江大学校级优秀团员；美国大学生数学建模竞赛 Meritorious Winner 两次],
  location: [奖项],
)

#cv-honor(
  date: [本科],
  title: [浙江大学学业奖学金二等奖一次、三等奖两次；竺可桢学院拔尖学生奖学金；省级大学生科研训练计划项目；第二届全国大学生化学实验创新设计大赛三等奖],
  location: [奖学金],
)

#cv-section("项目经历")

#project-entry(
  title: [MolGR 分子图重建工具],
  outcome: [XYZ 坐标到 RDKit 分子图的高性能重建 Python 包],
  date: [2025.12 - 至今],
  role: [负责人],
  description: list(
    [开发基于 C++ 后端与 Python 参考实现的分子图重建工具，从 XYZ 文本、总电荷和自旋多重度生成带键级、三维构象、可选配位键和立体化学信息的 RDKit 分子对象。],
    [面向有机分子、金属配合物和不同自旋多重度体系优化候选态枚举、评分和后处理流程，单个有机分子图重建可达 1 ms 内，并在金属体系与自旋态处理准确性上优于 xyz2graph 等现有工具。],
  ),
)

#project-entry(
  title: [N,N′-dioxide/金属催化不对称 Michael 加成数据与建模平台],
  outcome: [一作论文：#text(style: "italic")[Angew. Chem., Int. Ed.] 2026],
  date: [2024.10 - 2025.08],
  role: [一作 / 负责人],
  description: list(
    [整理 N,N′-dioxide/金属催化 Michael 加成反应数据，建立机理感知图神经网络与相似性加权外推流程，用于催化剂选择和选择性预测。],
  ),
)

#project-entry(
  title: [RXNGraphormer 统一预训练反应建模框架],
  outcome: [合作论文：#text(style: "italic")[Nat. Mach. Intell.] 2025],
  date: [2024.07 - 2025.03],
  role: [算法贡献],
  description: list(
    [在上海科学智能研究院物质科学部门实习，负责虚构反应生成算法设计，参与支持反应嵌入、产率/选择性预测和合成规划的预训练框架。],
  ),
)

#project-entry(
  title: [高效分子计算日志数据提取工具 MolOP],
  outcome: [计算化学数据解析与自动化工具],
  date: [2023.10 - 至今],
  role: [负责人],
  description: list(
    [开发类型友好、带数值量纲、支持并行处理的分子计算日志解析与数据引擎，为量子化学数据生产和自动化流程提供工程基础。],
  ),
)

#project-entry(
  title: [天池首届世界科学智能大赛：分子属性预测竞赛],
  outcome: [千万量级有机小分子量子化学能量与受力预测任务],
  date: [2023.08 - 2023.10],
  role: [队员],
  description: list(
    [使用图神经网络模型预测有机小分子的量子化学能量与受力，并围绕模型架构和训练策略进行优化。],
  ),
)

#project-entry(
  title: [QM9star 分子数据集与 qm9star_query 查询平台],
  outcome: [一作论文：#text(style: "italic")[Sci. Data] 2024],
  date: [2023.03 - 2024.06],
  role: [一作 / 负责人],
  description: list(
    [面向离子、自由基和中性分子构建 DFT 优化结构数据集，并开发数据库查询、API 服务、图神经网络示例和教程。],
  ),
)

#project-entry(
  title: [基于谱图的分子表征与反应性能预测],
  outcome: [一作论文：#text(style: "italic")[Chem. Asian J.] 2023],
  date: [2022.04 - 2023.02],
  role: [一作 / 负责人],
  description: list(
    [使用图像识别解析分子 NMR 光谱图像，将谱图向量用于反应性能预测，验证谱图启发描述符的分子表征能力。],
  ),
)

#pagebreak()

#resume-repeat-header(
  name-zh,
  email,
  phone,
  political-status,
  english-level,
  photo,
  location: location,
  subtitle: [#role · #affiliation · 数据驱动化学 / 化学人工智能],
)

#cv-section("专业技能")

#skill-item(
  [机器学习],
  [熟练使用 Python 进行科研数据挖掘、脚本开发和模型实验；熟悉监督学习、图神经网络、Transformer/预训练模型及图像处理流程，能够基于 sklearn、PyTorch、OpenCV 等完成分子性质、反应选择性、合成规划和谱图表征任务。],
)

#skill-item(
  [计算化学],
  [掌握 Gaussian、xTB 等量子化学和半经验计算工具的使用，能够结合 Python 脚本与计算软件开展反应机理计算、批量结构优化、日志解析和数据生产；理解电子结构、过渡态、原子/键级性质与三维构象在分子表征和模型解释中的作用。],
)

#skill-item(
  [昇腾平台与算子优化],
  [具备华为昇腾（Ascend）平台使用和算子优化经验，能够开展模型部署与性能分析，定位性能瓶颈，并针对算子实现和数据流进行优化。],
)

#skill-item(
  [化学信息学],
  [熟悉 RDKit、OpenBabel 等分子工具包的使用和深度二次开发，具备从 XYZ/SMILES、计算日志、文献反应、谱图图像和量子化学结果构建分子与反应数据基础设施的经验。],
)

#skill-item(
  [科研工程],
  [具备化学数据库、API 服务、命令行工具和可复现数据管线开发经验；熟悉后端开发、Linux、CI/CD、容器和虚拟化运维，能够将算法原型整理为可维护的科研软件与自动化工作流。],
)

#skill-item(
  [GitHub],
  [#link(github-url)[#github-url]],
)

#skill-item(
  [Google Scholar],
  [#link(google-scholar-url)[#google-scholar-url]],
)

#skill-item(
  [ORCID],
  [#link(orcid-url)[#orcid-url]],
)

#cv-section("科研成果")

#compact-note([
  目前以第一作者发表 SCI 论文 3 篇，另合作发表论文 8 篇。以下按代表性工作优先列出。
])

#v(1.5pt)
#include "publications.zh.typ"
