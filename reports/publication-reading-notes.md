# 论文全文阅读笔记与研究画像

更新时间：2026-06-08

本文基于本仓库中已整理的 10 篇论文 PDF 全文提取文本撰写，重点阅读了摘要、引言、数据与方法、结果、讨论、结论、数据/代码可用性和作者贡献声明。本文不替代论文原文，而是用于维护个人主页、CV、研究陈述和代表工作介绍。

## 总体判断

你的研究画像不宜简单写成“机器学习用于化学”。更准确的主线是：

> 面向计算化学与有机合成的数据基础设施、机理感知反应建模和分子表征方法。

从论文全文看，反复出现的工作模式是：

1. 找到化学研究中重要但难以直接复用的信息来源，例如文献反应表格、补充信息中的低选择性数据、谱图图像、立体环境、量子化学输出、反应键变化或自由基/离子中间体。
2. 将这些信息整理为结构化、可查询、可建模的数据资源。
3. 基于化学知识设计描述符、模型输入、数据划分或训练策略，而不是只把通用模型直接套到化学数据上。
4. 用模型回答实际化学问题，例如选择性预测、催化剂选择、反应机制判定、键能预测或合成规划。
5. 尽可能把结果以数据库、Web 平台、API、GitHub 仓库、脚本或教程的形式沉淀为可复用工具。

因此，主页和 CV 中最应突出的不是某一个模型架构，而是“数据资源 + 机理知识 + 可复用软件 + 预测/解释”的组合能力。

## 研究方向的层次结构

### 1. 化学数据基础设施

最强证据来自 QM9star、AHO 数据库和 N,N'-dioxide/metal 催化 Michael 加成数据库。它们覆盖从量子化学计算数据到文献反应数据的不同层级。

- **QM9star** 解决的是反应中间体数据缺口。已有大型分子性质数据集多数集中在中性、闭壳层、符合八隅体规则的分子；QM9star 从 QM9 出发移除端位氢并生成阳离子、阴离子和自由基，最终提供约 191.6 万个拓扑结构和约 200.9 万个三维结构。
- **AHO 数据库** 解决的是不对称氢化文献数据难以用于模型训练的问题。论文整理了 2000-2020 年间 355 篇文献中的 12619 条不对称烯烃氢化反应，涉及 1686 个过渡金属催化剂和 2754 个烯烃底物。
- **N,N'-dioxide/metal Michael 加成平台** 进一步成熟化了文献数据基础设施路线。论文整理近二十年 37 篇文献中的 2176 条有效反应，保留底物、产物、金属盐、配体、溶剂、添加剂、计量、条件、产率、ee、de、DOI、原子映射和机理相关活化形式，并提供在线平台。

这一方向最适合在主页中表达为：

> I build structured molecular and reaction data resources that turn literature records, quantum-chemical calculations, and experimental artifacts into reusable computational infrastructure.

中文可写为：

> 我构建结构化的分子与反应数据资源，将文献记录、量子化学计算和实验表征信息转化为可查询、可建模、可复用的计算基础设施。

### 2. 机理感知反应建模与不对称催化

这条线从 AHO 的层次学习开始，发展到 N,N'-dioxide/metal Michael 加成的机理增强模型，并通过 RXNGraphormer 扩展到跨任务预训练反应建模。

- **AHO** 的核心不是简单预测 ee，而是为“目标底物只有几十个实验数据”的早期筛选场景设计层次学习。模型先从结构相关的大数据学习通用催化行为，再用更接近目标底物的数据做 delta learning，最后用目标底物的小数据校正。
- **N,N'-dioxide/metal Michael 加成** 把类似思想推进到更复杂的催化体系。论文先用二维可视化和统计分析理解金属/配体/底物适用性，再用 CGRNN 做 ee 建模，并针对 leave-one-reaction-out 的外推下降问题，引入反应中间体数据增强和相似性加权调参。
- **RXNGraphormer** 则把反应性能预测和正/逆合成规划放入同一个预训练框架，使用分子图编码器、Transformer 相互作用模块、虚构反应对比预训练和 delta-mol 图来捕捉键变化。

这一方向可表达为：

> My reaction-modeling work emphasizes extrapolation under realistic discovery settings: unseen substrates, sparse target data, catalyst transfer, and mechanistic changes.

中文可写为：

> 我的反应建模工作强调真实发现场景中的外推能力，包括新底物、小样本目标空间、催化剂迁移和机理变化。

### 3. 分子表征与描述符设计

SPMS、spectrum descriptor、QM9star 的局部量子性质、RXNGraphormer 的 delta-mol 图，以及 non-heme iron BDE 工作中的 2D/3D 描述符对比，都说明你长期关注“化学信息如何被机器表示”。

- **SPMS** 将分子 van der Waals 表面投影到球面并展开为矩阵/彩图，能够区分手性骨架、取代基和对映体，并可用于卷积神经网络预测不对称反应 ee。
- **Spectrum descriptor** 将谱图图像中的峰位和强度通过 OCR/图像处理转化为网格化描述符，用于 Buchwald-Hartwig 反应产率预测，并证明软件预测谱图也可作为自动化工作流中的特征来源。
- **RXNGraphormer** 的 delta-mol 图把反应物和产物之间的键变化编码为图结构，使模型在性能预测任务中接收更接近反应过程的信息。
- **non-heme iron BDE** 对 Morgan fingerprint、RDKit fingerprint、Topo fingerprint、atom pair fingerprint、SOAP、MBTR 和 Coulomb Matrix 做系统对比，说明 2D 与 3D 表征各自适用的化学边界。

这一方向可表达为：

> I design molecular and reaction representations from spectra, stereostructures, quantum-chemical outputs, graph topology, and bond-change patterns.

### 4. 物理有机和过渡金属反应机理图谱

Cu radical LFER 和 non-heme iron BDE 两篇论文说明你参与的不只是数据工程，也包括机制解释和物理有机模型。

- **Cu radical LFER** 建立了配体、自由基和亲核试剂对三种 Cu(II) 介导 C-C 成键路径的线性可加贡献，进而预测 132300 个组合的主导机理。论文显示你参与了数据分析。
- **non-heme iron BDE** 针对非血红素铁配合物构建了 652 个配合物、889 个 diabatic BDE 的专门数据集，并训练模型预测 Fe-X 和 Fe-OH 键能。作者贡献声明显示你参与模型训练。

这一方向适合在报告和 CV 中作为“机制与性质建模能力”的支撑，但不宜压过第一作者数据平台工作。

### 5. LLM 与自动化合成作为发展方向

LLM 综述表明你所在研究线正在关注更上层的自动化合成工作流。该综述将 LLM 在分子合成中的角色总结为知识库、非结构化数据抽取工具、性质/反应预测器和 agent 系统的中枢。这与前述“结构化数据资源、模型、工具链”的主线一致。

在主页中建议把它写成 emerging direction，而不是当前最核心身份：

> Emerging interests include LLM-assisted chemical data extraction and agentic synthesis workflows, grounded in reliable data and domain-specific tools.

## 逐篇论文细读摘要

### 10.1055/s-0040-1705977：SPMS 立体结构描述符

**研究问题。** 不对称催化机器学习需要描述分子立体环境。传统几何参数可解释但维度有限；SOAP、ACSF 等通用 3D 描述符未必能区分对映体；CoMFA 类网格描述符又依赖结构对齐。

**核心方法。** SPMS 将分子的 vdW 表面投影到自定义球面，再用 equirectangular projection 展开为矩阵或彩图。通过平移和旋转标准化，使描述符对整体运动不敏感，同时保留手性差异。

**关键结果。**

- 推荐分辨率为 40 x 80，能在精度与生成效率之间取得平衡。
- 可清楚区分手性磷酸、取代基变化和对映体。
- 在 Denmark 的 CPA 催化硫醇加成 N-acylimines 数据集上，使用 1075 个反应和 CNN 建模，十次随机划分平均 MAE 为 0.1624 kcal/mol。
- SPMS 图还能重现 Ru-BINAP 四象限立体环境，用于化学解释和教学。

**对研究画像的意义。** 这是你研究中“分子表征服务不对称催化建模”的早期基础。它不仅是描述符论文，也体现了一个重要偏好：表征需要兼顾机器可读性和化学解释性。

**个人贡献边界。** 论文没有列出详细作者贡献声明，你是共同作者。主页中可以把它作为早期代表工作或方法基础，不应写成单独主导项目。

### 10.1002/anie.202106880：不对称烯烃氢化数据库与层次学习

**研究问题。** 不对称氢化催化剂筛选仍依赖经验。现实中，新底物开发早期只有少量实验数据，直接训练目标模型不可靠；简单把所有相关文献数据混合训练也会让目标空间数据被淹没。

**数据资源。**

- 人工整理 355 篇文献。
- 形成 12619 条反应记录、1686 个过渡金属催化剂、2754 个烯烃底物。
- 记录反应物、催化剂、条件、性能和 DOI。
- 统一 SMILES，清洗 RDKit 无法识别的结构。
- 为催化剂生成配体-金属复合结构，并提供 xTB 优化三维几何。

**模型策略。** 层次学习将相关数据按化学接近程度分层。基础模型学习远相关数据中的通用规律；delta model 逐层学习更接近目标底物的数据与上一层预测之间的残差；最后用目标底物几十个数据做校正。

**关键结果。**

- 对 methyl (Z)-2-acetamido-3-phenylacrylate，43 个训练数据配合层次学习可达 R2 = 0.852、MAE = 0.387 kcal/mol。
- 随机打乱层次或加入无化学相关性数据会显著降低性能，说明提升来自化学相关性而不是形式上的分层。
- 对 dimethyl itaconate，用 Morgan fingerprint 距离选择相关数据也能提升性能，说明该策略可迁移到不同相似性定义。

**对研究画像的意义。** 这是“文献反应数据库 + 小样本外推建模 + 化学启发数据选择”的早期代表。它为后续 N,N'-dioxide 平台和反应建模工作提供了思想基础。

**个人贡献边界。** 论文未提供详细作者贡献声明，你是共同作者。可强调参与该研究线和数据平台方向，但不宜把数据库整体建设完全归为个人贡献。

### 10.1002/asia.202300011：基于谱图的分子描述符

**研究问题。** 谱图是分子结构和物性的重要实验表征，但机器学习中常只用局部化学位移或少数人工选取特征，图像或曲线中大量信息没有被系统利用。

**核心方法。**

- 使用 OCR/图像处理从谱图图片中提取峰位和强度。
- 将峰信息归一化为 peak vector，再投影到固定网格得到描述符。
- 不只支持图像谱图，也支持 JCAMP 曲线格式。
- 以 Pd 催化 Buchwald-Hartwig 偶联中 15 个 aryl halides 的谱图作为关键输入。

**关键结果。**

- 数据集包含 4140 个 Buchwald-Hartwig 反应。
- 反应编码包含 26 维谱图描述符和 93 维物理有机参数。
- 随机森林模型达到 R2 = 0.929、Pearson R = 0.965、MAE = 4.99%、RMSE = 7.28%。
- Top 10 重要特征中有 7 个是谱图描述符。
- NMRDB 预测谱图可以替代实验谱图，说明该方法可进入全自动虚拟筛选工作流。

**对研究画像的意义。** 这是一作工作，体现了你把“实验表征图像”转化为机器可读特征的能力。它与 SPMS 的共同点是：不是只选择已有标准描述符，而是从化学实际数据形态出发设计表征。

**个人贡献边界。** 你为第一作者，可以在主页和 CV 中作为分子表征方向的代表工作。

### 10.1038/s41597-024-03933-6：QM9star

**研究问题。** 主流大规模分子数据集多集中于中性、闭壳层、稳定分子，难以覆盖阳离子、阴离子和自由基等有机反应关键中间体。

**数据构建。**

- 从 QM9 三维结构出发，移除非等价端位氢。
- 生成自由基、阳离子、阴离子的初始结构。
- 初始猜测数量为 2194899。
- 使用 B3LYP-D3(BJ)/6-311+G(d,p) 优化，并做 NBO 计算。
- 过滤未收敛、NBO 失败、力异常和虚频结构。
- 最终包含 1915870 个拓扑结构和 2008806 个三维结构。

**数据内容。** 每条记录包含 39 类字段，覆盖原子、键、坐标、力、NBO 键级、NPA 电荷、Mulliken 电荷/自旋密度、能量、热力学校正、频率、偶极/四极/八极/十六极矩、HOMO/LUMO 等。

**可用性。**

- 数据以 PostgreSQL dump 形式发布。
- 提供 `gentle1999/qm9star_query` 仓库，包含部署、查询、PyTorch Geometric 数据集类和深度学习使用示例。
- DimeNet++ 验证模型加入 formal charge 和 radical embedding，形成能量 MAE 达 0.235 kcal/mol。

**作者贡献。** 作者贡献声明明确写明你负责 Data Curation and Clean、Investigation、Software、Writing - Original Draft。该论文是个人主页中最强的“数据基础设施 + 软件 + 原始写作”证据。

**对研究画像的意义。** 这是当前最适合作为“分子数据基础设施”方向代表作的论文。它不只是数据量大，更重要的是把反应中间体的量子化学数据、数据库模式、访问工具和模型验证连接起来。

### 10.1360/tb-2024-0812：有机分子理化性质预测综述

**文章定位。** 这是中文综述，梳理数据驱动有机分子理化性质预测的发展，包括数据库、机器学习流程、分子编码、模型架构和代表性性质预测任务。

**覆盖内容。**

- 数据库与数据集：NIST、PubChemQC、SDBS、iBonD、FreeSolv、QM9、PubChemQC PM6、Frag20、MoleculeNet。
- 方法流程：数据集建立、分子编码、模型训练、测试集划分和应用分析。
- 分子编码：SMILES、分子指纹、二维图、三维结构、等变模型。
- 代表性任务：光谱性质、HOMO/LUMO、pKa、BDE、氧化还原电势、Mayr 参数。

**核心观点。**

- 机器学习能在许多性质预测任务中接近量子化学计算精度，并显著提高效率。
- 公开实验数据不足、数据标准化不足、模型外推和可解释性仍是主要瓶颈。
- 未来方向包括更全面标准化数据库、化学原理驱动的模型框架、与实验化学家更紧密互动。

**对研究画像的意义。** 这篇综述支撑你对“分子性质预测与数据集生态”的系统理解。它适合放在 publication list 中，但不应作为主页代表工作优先级最高的条目。

### 10.1039/d5ob00007f：非血红素铁配合物 diabatic BDE 预测

**研究问题。** 非血红素铁催化卤化/羟化选择性与 Fe-X 和 Fe-OH 的 diabatic BDE 密切相关。传统实验和量子化学计算成本高，且已有 BDE 机器学习数据多集中于非金属有机键。

**数据与方法。**

- 从 374 篇文献和实验数据中构建非血红素铁配合物结构。
- 最终得到 652 个配合物和 889 个 diabatic BDE。
- 使用 DFT 优化完整配合物，并对键裂解后的片段做单点能计算。
- 用 SMARTS 分割分子与两个片段，将整体和片段指纹拼接。
- 比较 Morgan、RDKit、Topo、Atom pair 指纹，以及 SOAP、MBTR、Coulomb Matrix 三维描述符。

**关键结果。**

- Morgan fingerprint + Gradient Boosting Regressor 表现最好，R2 = 0.791、MAE = 10.23 kcal/mol。
- SOAP 等 3D 描述符能提升 RDKit/Topo/Atom pair 指纹模型，但与 Morgan 结合时整体提升有限。
- 对 BDE 差异大的异构体，SOAP 等 3D 描述符仍有优势。

**作者贡献。** 作者贡献声明显示你参与模型训练。

**对研究画像的意义。** 这篇工作说明你的建模经验延伸到过渡金属配合物性质预测，尤其是 2D/3D 表征的适用边界判断。它适合在 CV 中作为合作研究或技能证据。

### 10.1038/s41467-025-67770-w：Cu 催化自由基成键机理 LFER

**研究问题。** Cu 催化自由基转化中，C-C 成键可通过 Cu(III) reductive elimination、outer-sphere radical substitution 或 ion-pair/radical-polar crossover 等路径。已有 DFT 研究多是事后分析单个体系，缺少能跨配体、自由基和亲核试剂预测机理偏好的定量规则。

**核心方法。**

- 定义目标化学空间：126 个自由基、75 个亲核试剂、14 个配体，共 132300 种组合。
- 选取 250 个代表性组合，计算三种成键路径的过渡态。
- 构建三元 LFER：每个反应组分对过渡态稳定化的贡献线性可加。
- 为配体、自由基和亲核试剂建立 RE、RS、IP 三种路径的量化尺度。

**关键结果。**

- RE、RS、IP 三种路径的 LFER R2 约为 0.983-0.992，MAE 小于 1.8 kcal/mol。
- 机理预测准确率在构建集上约 93.9%，外推测试集约 92.3%。
- 132300 个组合中，82.9% 具有单一主导机理；RE 是最常见主导路径。
- 配体对机理的影响最大，其次为亲核试剂，自由基影响较小。
- 发现 RS 路径在既有机理研究中可能被低估。

**作者贡献。** 作者贡献声明显示你参与数据分析。

**对研究画像的意义。** 这是“物理有机模型 + 大规模机理图谱 + 数据分析”的合作证据。它与纯机器学习不同，但与整体研究方向一致：通过结构化计算结果建立可预测、可解释、可查询的化学规则。

### 10.1038/s42256-025-01098-4：RXNGraphormer

**研究问题。** 反应性能预测通常是数值回归，合成规划通常是序列生成，两类任务长期由不同模型框架处理。论文试图用统一预训练框架连接 reactivity/selectivity prediction、forward synthesis 和 retrosynthesis。

**核心方法。**

- 汇总开源反应数据和 WIPO 数据，清洗后得到约 680 万高质量真实反应。
- 通过 fragment-exchange 生成结构相近但键变化错误的虚构反应，总预训练数据超过 1300 万条。
- 使用 real/fictitious reaction binary classification 作为对比式预训练任务，让模型学习反应位点和键变化模式。
- 架构由 GNN 分子编码器、Transformer 分子间相互作用模块、分类/回归/序列解码模块组成。
- 对反应性能预测任务额外引入 delta-link method 生成 delta-mol graphs，以编码反应物和产物之间的键变化。

**关键结果。**

- 预训练 embedding 无需显式反应类型监督，即能按反应类型形成有意义聚类。
- 在 Buchwald-Hartwig、Suzuki-Miyaura、自由基 C-H functionalization、asymmetric thiol addition 等数据集上获得强性能。
- 在 USPTO-50k、USPTO-full、USPTO-480k、USPTO-STEREO 上同时支持正/逆合成任务。
- 在 AHO 外部数据集上取得与原层次学习接近的性能，说明模型可服务真实文献数据场景。

**作者贡献。** 作者贡献声明明确写明你参与实现 fictitious reaction generation algorithm。这是预训练任务能否有效学习键变化模式的关键组成部分。

**对研究画像的意义。** RXNGraphormer 是你“跨任务反应智能”方向的代表合作工作。主页中应强调参与点与整体框架意义：大型反应预训练、虚构反应构造、反应 embedding、性能预测和合成规划统一。

### 10.1002/anie.202518560：N,N'-dioxide/metal 催化 Michael 加成数据平台

**研究问题。** N,N'-dioxide/metal 催化体系应用广、选择性高，但金属、配体骨架、取代基、底物几何和非共价作用共同控制选择性，使催化剂设计很难靠单变量经验完成。

**数据资源。**

- 从 2007 年以来近二十年的 37 篇文献中整理数据。
- 获得 2176 条有效 Michael 加成反应。
- 记录 Michael acceptor、donor、product、metal salt、ligand、solvent、additive、温度、时间、yield、ee、de、DOI。
- 加入原子映射和机理活化形式，以更准确反映真实反应步骤。
- 建立在线平台，支持反应检索、结构可视化、统计分析、数据导出和模型预测/催化剂推荐。

**统计分析。**

- 对 ee >= 80% 的 1487 条高选择性反应做 metal/ligand/substrate applicability mapping。
- rare-earth 与 non-rare-earth metal 的底物兼容性互补。
- Sc、La、Yb 等金属的高选择性适用区域不同。
- Pr、Pi、Ra 配体骨架覆盖不同底物区域，取代基小变化也能造成非连续的适用性变化。

**建模策略。**

- 系统比较 Autocorr、ECFP、VSA、PhysChem 等描述符和多种回归算法。
- CGRNN 在常规交叉验证中表现较好，Pearson R = 0.865、MAE = 0.314 kcal/mol。
- Leave-one-reaction-out 外推测试中，naive CGRNN 明显下降，平均 Pearson R = 0.428、MAE = 0.571 kcal/mol。
- 引入机理中间体数据增强和相似性加权调参，组合策略将平均 Pearson R 提高到 0.549。

**实验验证。**

- 对一个含硫 donor 与 alpha,beta-unsaturated acylpyrazole acceptor 的挑战性新反应，模型推荐 La-based catalyst。
- 实验验证中 L3-PrPr2/La 等组合给出较好产率和 ee。
- 8 个扩展实验验证中，预测与实验 ee 的 Pearson R = 0.916、MAE = 0.276 kcal/mol。

**作者贡献边界。** 你是共同第一作者。论文没有在提取文本中列出详细作者贡献声明，但从署名和内容看，这是当前反应建模方向最适合作为核心代表的一作工作。

**对研究画像的意义。** 这是最完整的“文献数据平台 + 机理知识 + 外推模型 + 实验验证”闭环。主页与 CV 应把它排在反应建模方向的第一梯队。

### 10.1002/chem.71074：LLM 与分子合成综述

**文章定位。** 综述 LLM 在分子合成中的角色，不是简单宣称 LLM 替代传统模型，而是讨论其在知识管理、数据结构化、预测和 agent 编排中的位置。

**核心结构。**

- LLM 作为交互式领域知识库：通过化学数据微调和 RAG 支持合成知识问答。
- LLM 辅助结构化数据抽取：从文献、专利、图像和多模态材料中抽取反应数据。
- LLM 用于性质和反应预测：包括生成式回归、embedding 表征、retro planning 等，但强调数据分布和外推限制。
- LLM-based agent：作为工具调用和自动化实验/计算工作流的协调者。

**关键判断。**

- LLM 的价值在于语言理解、信息整合、计划和工具编排。
- 独立 LLM 在真实化学发现中仍受幻觉、训练数据偏差、表示瓶颈和外推能力限制。
- 更可靠的路线是 LLM 与专门化学工具、数据库、实验平台和人类验证结合。

**对研究画像的意义。** 这篇综述可作为未来方向：LLM-assisted chemical data extraction、tool orchestration、agentic synthesis workflow。它与已有数据基础设施和软件工具路线自然衔接。

## 建议的主页/简历表述

### 英文研究简介

I develop data resources, molecular representations, and scientific software for data-driven computational chemistry. My work turns literature reaction records, spectra, stereostructures, quantum-chemical calculations, and reaction bond changes into structured resources for mechanism-aware prediction, catalyst selection, and reusable chemical data infrastructure.

### 中文研究简介

我的研究围绕数据驱动的计算化学展开，重点构建分子与反应数据资源、分子表征方法和科研软件。我关注如何将文献反应记录、谱图、立体结构、量子化学计算和反应键变化转化为结构化资源，用于机理感知预测、催化剂选择和可复用化学数据基础设施。

### 代表方向排序

1. N,N'-dioxide/metal asymmetric Michael addition platform：最完整的一作反应建模闭环。
2. QM9star / qm9star_query：最强的数据基础设施和软件证据。
3. RXNGraphormer：跨任务预训练反应建模和合成规划代表合作。
4. Spectrum descriptor / SPMS：分子表征方法基础。
5. Cu radical LFER / non-heme iron BDE：机制图谱和过渡金属性质建模合作。
6. LLM synthesis review：未来自动化与 agent 方向。

### 需要避免的表述

- 不建议把整体研究概括为“AI for chemistry”或“large language models for chemistry”。这会削弱你在数据基础设施和机理建模上的真实特色。
- 不建议把所有合作论文都写成个人主导。对 RXNGraphormer、Cu LFER、non-heme iron BDE，应写清具体贡献。
- 不建议只强调模型指标。更有辨识度的是数据建设、化学信息结构化、外推设置和可复用工具。
- 不建议把 Google Scholar 或自动抓取数据作为核心稳定依赖。ORCID、Crossref、本地 PDF 与手动 overrides 更适合长期维护。
