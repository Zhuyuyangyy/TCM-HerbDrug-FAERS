# TCM-HerbDrug-FAERS

基于 FDA FAERS 真实不良事件数据的中西药相互作用信号挖掘系统

## 核心创新点

1. **真实 FAERS 数据验证** — 基于 FDA 公开季度数据（2004-至今），非合成数据
2. **多指标信号检测** — ROR / PRR / IC / BCPNN 四类不成比例分析
3. **EBGM 近似收缩评分** — 基于贝叶斯 Gamma-Poisson 模型的信号强度分级
4. **16 种草药标准化映射** — 支持英文/拉丁文/拼音多名称匹配 FAERS 药物名
5. **阳性对照验证** — 28 个文献已知相互作用对作为 positive controls
6. **三级风险排序** — signal_only / signal_plus_database / signal_plus_mechanism

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 下载 FAERS 数据

从 FDA 官网下载季度 ASCII 数据文件：
- 地址: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- 下载 `faers_ascii_YYYYQN.zip` 格式的文件
- 解压到 `data/faers_ascii/` 目录下

```
data/faers_ascii/
├── 2022Q1/
│   ├── DEMO22Q1.txt
│   ├── DRUG22Q1.txt
│   ├── REAC22Q1.txt
│   ├── OUTC22Q1.txt
│   ├── INDI22Q1.txt
│   └── THER22Q1.txt
├── 2022Q2/
│   └── ...
└── ...
```

### 3. 运行分析

```bash
# 分析所有草药
python scripts/run_faers_analysis.py

# 分析特定草药
python scripts/run_faers_analysis.py --herbs ginkgo danshen licorice

# 指定季度范围
python scripts/run_faers_analysis.py --quarters 2022Q1 2022Q2 2022Q3 2022Q4

# 指定数据目录
python scripts/run_faers_analysis.py --data-dir /path/to/faers_ascii
```

### 4. 启动 API 服务

```bash
cd backend && python main.py
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/signal/detect` | POST | 检测药物不良事件信号 |
| `/api/signal/batch` | POST | 批量信号检测 |
| `/api/risk/assess` | POST | 三级风险评估 |
| `/api/risk/chain` | GET | 证据链查询 |

## 支持的草药（16 种）

| 草药 | 英文名 | FAERS 匹配模式 |
|------|--------|---------------|
| 银杏 | Ginkgo biloba | GINKGO, EGb 761 |
| 人参 | Panax ginseng | GINSENG, PANAX |
| 贯叶连翘 | St. John's wort | ST. JOHN, HYPERICUM |
| 丹参 | Danshen | DANSHEN, SALVIA MILTIORRHIZA |
| 甘草 | Licorice | LICORICE, GLYCYRRHIZ |
| 麻黄 | Ma Huang | EPHEDRA, MA HUANG |
| 当归 | Dong Quai | DONG QUAI, ANGELICA SINENSIS |
| 大蒜 | Garlic | GARLIC, ALLIUM SATIVUM |
| 姜黄 | Turmeric | TURMERIC, CURCUMIN |
| 锯棕榈 | Saw Palmetto | SAW PALMETTO, SERENOA |
| 缬草 | Valerian | VALERIAN, VALERIANA |
| 紫锥菊 | Echinacea | ECHINACEA |
| 卡瓦 | Kava | KAVA, PIPER METHYSTICUM |
| 黑升麻 | Black Cohosh | BLACK COHOSH, CIMICIFUGA |
| 绿茶 | Green Tea | GREEN TEA, CAMELLIA SINENSIS |
| 山楂 | Hawthorn | HAWTHORN, CRATAEGUS |

## 信号检测方法

### 不成比例分析

| 方法 | 公式 | 信号判定 |
|------|------|---------|
| ROR | ad/bc | CI 下限 > 1 |
| PRR | [a/(a+b)] / [c/(c+d)] | CI 下限 > 1 |
| IC | log2(O/E) | CI 下限 > 0 |
| BCPNN | Bayesian IC posterior | CI 下限 > 0 |

### EBGM 近似收缩评分

基于 Gamma-Poisson 模型的贝叶斯收缩估计：
- `disproportionate_strong`: EBGM >= 5, EB05 >= 2
- `disproportionate`: EBGM >= 2, EB05 >= 1
- `weak_disproportionate`: EBGM >= 1.5, EB05 >= 0.5

## 项目结构

```
TCM-HerbDrug-FAERS/
├── backend/
│   ├── api/
│   │   ├── signal.py          # 信号检测 API
│   │   └── risk.py            # 风险评估 API
│   ├── data/
│   │   ├── faers_real_loader.py    # 真实 FAERS 数据加载器
│   │   ├── herb_name_normalizer.py # 药物名称标准化
│   │   ├── faers_loader.py         # 通用数据加载器
│   │   └── herb_kg.py              # 中药知识图谱
│   ├── analysis/
│   │   ├── faers_pipeline.py       # 完整分析 pipeline
│   │   ├── risk_scoring.py         # 三级风险评分
│   │   └── evidence_chain.py       # 证据链构建
│   ├── models/
│   │   ├── disproportionality.py   # ROR/PRR/IC/BCPNN
│   │   └── signal_detector.py      # 信号检测引擎
│   └── main.py
├── data/
│   ├── known_hdi_pairs.yaml        # 已知相互作用验证集
│   └── herb_drug_pairs.yaml
├── scripts/
│   └── run_faers_analysis.py       # 分析脚本
└── output/                         # 分析结果输出
```

## 数据来源

- **FDA FAERS** — 美国 FDA 不良事件报告系统（2004-至今）
- **MedDRA** — 医学术语集（不良事件标准化）
- **文献** — Natural Medscape, PubMed 已知相互作用

## 引用

如果使用本项目，请引用：
- FDA Adverse Event Reporting System (FAERS). U.S. Food and Drug Administration.
- MedDRA: the Medical Dictionary for Regulatory Activities.
