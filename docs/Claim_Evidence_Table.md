# Claim-Evidence Table: TCM-HerbDrug-FAERS

| # | Paper Claim | Evidence Type | Evidence File | Status |
|---|-------------|--------------|---------------|--------|
| C1 | ROR/PRR/IC可有效检测HDI信号 | 算法实现 | backend/models/disproportionality.py | verified |
| C2 | 多指标联合降低假阳性 | 模拟实验 | backend/models/signal_detector.py | pending |
| C3 | 已知HDI对可被正确检出 | 验证实验 | data/herb_drug_pairs.yaml | pending |
| C4 | 机制图谱覆盖主要CYP交互 | 知识库 | backend/models/mechanism_graph.py | verified |
| C5 | 三级风险排序与临床严重度一致 | 专家评估 | backend/analysis/risk_scoring.py | pending |
| C6 | 证据链提供可追溯的机制解释 | 系统实现 | backend/analysis/evidence_chain.py | verified |
| C7 | 系统可扩展至新药对 | 架构设计 | backend/data/herb_kg.py | verified |
| C8 | 外部验证与HDI数据库一致 | 交叉验证 | backend/analysis/validation.py | pending |
