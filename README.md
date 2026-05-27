# TCM-HerbDrug-FAERS

基于FAERS/VigiBase与中药知识图谱的中西药相互作用风险信号挖掘研究

## 核心创新点
1. 不成比例分析 (ROR/PRR/IC) 信号发现
2. 中药-成分-靶点-CYP/转运体-AE 机制图谱
3. 三级风险排序 (信号级/信号+数据库/信号+机制)

## API端点
- GET  /health              - 健康检查
- POST /api/signal/detect   - 检测药物不良事件信号
- GET  /api/signal/query    - 查询已知信号
- POST /api/risk/assess     - 三级风险评估
- GET  /api/risk/chain      - 证据链查询

## 数据来源
- FDA FAERS (2004-至今)
- WHO VigiBase
- InterPAD (成分-抗癌药交互)
- HDI数据库

## 快速开始
pip install -e .
cd backend && python main.py
