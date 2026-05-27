# 基于FAERS/VigiBase与中药知识图谱的中西药相互作用风险信号挖掘研究

# Signal Detection and Mechanism Elucidation of Herb-Drug Interactions via FAERS and Knowledge Graph

## Abstract

### Background
中西药联用在全球日益普遍，但草药-药物相互作用(HDI)信息高度分散，缺乏系统性的信号发现和机制解释框架。

### Methods
本研究构建"信号发现-机制解释-风险排序"三位一体框架：(1) 基于FDA FAERS数据库的不成比例分析(ROR/PRR/IC)进行信号检测；(2) 构建中药-成分-靶点-CYP/转运体-不良事件机制图谱；(3) 设计三级风险排序体系。

### Results (placeholder)
在合成FAERS数据上，预期检出率>80%，与已知HDI数据库的一致性>70%。

### Conclusion
本框架为中西药安全联用提供了可扩展、可解释的风险评估工具。

**Keywords**: Herb-Drug Interaction, FAERS, Pharmacovigilance, Signal Detection, Knowledge Graph, Traditional Chinese Medicine

---

## 1. Introduction

### 1.1 中西药相互作用的安全挑战
全球约80%的人口使用草药产品，中西药联用在肿瘤、慢性病管理中尤为常见。然而，HDI信息高度分散(Zhang et al., 2022)，基层筛查工具不足(Puthiyedath et al., 2025)。

### 1.2 不良事件报告系统的机会
FDA FAERS覆盖2004年至今的上市后药物安全监测数据，WHO VigiBase是全球最大的不良反应数据库。不成比例分析(Disproportionality Analysis)是信号发现的标准方法。

### 1.3 本研究贡献
1. 基于FAERS的ROR/PRR/IC多指标信号检测
2. 中药-成分-靶点-CYP/转运体-AE机制图谱
3. 三级风险排序(信号级/信号+数据库/信号+机制)

---

## 2. Related Work

### 2.1 HDI数据库现状
Zhang et al. (2022) 综述了10个主要HDI数据库。InterPAD (Zhang et al., 2025) 提供成分-抗癌药交互资源。

### 2.2 不成比例分析方法
ROR(Reporting Odds Ratio)、PRR(Proportional Reporting Ratio)和IC(Information Component)是药物警戒中最常用的信号检测指标。

### 2.3 FAERS/VigiBase挖掘
Pochet et al. (2022) 基于VigiBase展示了草药-抗癌药相互作用的真实世界信号挖掘路径。

---

## 3. Method

### 3.1 不成比例分析
构建2×2列联表，计算ROR=ad/bc, PRR=[a/(a+b)]/[c/(c+d)], IC=log2(a/n_exp)。

### 3.2 信号检测引擎
多指标联合判定：ROR>2且PRR>2为信号，ROR>5且IC>2为强信号。

### 3.3 机制图谱
构建Herb→Ingredient→Target→CYP/Transporter→AE有向图，用网络路径搜索生成机制解释。

### 3.4 三级风险排序
- Level 1 (signal_only): 仅FAERS信号
- Level 2 (signal+database): 信号+HDI数据库支持
- Level 3 (signal+mechanism): 信号+数据库+机制路径

---

## 4. Experimental Setup

### 4.1 数据源
- FDA FAERS (2004-至今, 季度更新)
- WHO VigiBase
- InterPAD (成分-抗癌药交互)
- 已知HDI对(EMA/FDA/Literature)

### 4.2 验证策略
以已知HDI对(如丹参-warfarin, 甘草-digoxin)为金标准，评估信号检测的灵敏度和特异度。

### 4.3 评价指标
- Sensitivity, Specificity, PPV (vs known HDI)
- Risk level agreement with clinical severity
- Mechanism coverage proportion

---

## 5. References

1. Zhang Y, et al. Overview of Current Herb-Drug Interaction Databases. Drug Metab Dispos, 2022.
2. Puthiyedath R, et al. Drug-herb interactions in primary healthcare. Front Med, 2025.
3. FDA. FDA Adverse Event Reporting System Database.
4. Pochet S, et al. Herb-anticancer drug interactions via VigiBase. Sci Rep, 2022.
5. Zhang A, et al. InterPAD database. Sci Rep, 2025.
6. Yang B, et al. TCM DDI prediction via dual graph attention. Sci Rep, 2025.
7. Spanakis M, et al. AI Models for Herb-Drug Interaction Assessment, 2025.
8. Gamil NM, et al. Herb interactions: PK, PD and clinical implications, 2025.
9. Li P, et al. Real-World Evidence in TCM regulatory decisions. TIRS, 2024.
10. Gao K, et al. HERB 2.0 database. Nucleic Acids Res, 2025.
11. Kong X, et al. BATMAN-TCM 2.0 database. Nucleic Acids Res, 2024.
12. Zhou E, et al. AI in TCM modernization. Front Pharmacol, 2024.
13. Qu X, et al. Knowledge Graph in TCM Review, 2024.
14. Zhao M, et al. Multi-omics in TCM. Front Pharmacol, 2024.
15. Hubbard RA, et al. Target Trial Emulation. NEJM, 2024.
