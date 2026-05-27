"""Evidence chain builder for herb-drug interaction mechanisms."""
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class EvidenceLink:
    source: str
    target: str
    relation: str
    confidence: float
    source_type: str  # "signal", "database", "mechanism", "literature"

@dataclass
class EvidenceChain:
    herb: str
    drug: str
    links: List[EvidenceLink]
    overall_confidence: float
    chain_type: str

class EvidenceChainBuilder:
    """证据链构建器 — 从信号到机制的完整证据路径"""

    def build_chain(self, herb: str, drug: str,
                    signal_data: Optional[Dict] = None,
                    db_data: Optional[Dict] = None,
                    mechanism_data: Optional[Dict] = None) -> EvidenceChain:
        links = []
        if signal_data:
            links.append(EvidenceLink(
                source=herb, target=drug,
                relation="co-occurrence_in_FAERS",
                confidence=signal_data.get("ror", 0),
                source_type="signal"
            ))
        if db_data:
            links.append(EvidenceLink(
                source=herb, target=drug,
                relation="known_HDI_in_database",
                confidence=db_data.get("support_score", 0.5),
                source_type="database"
            ))
        if mechanism_data:
            for step in mechanism_data.get("pathway", []):
                links.append(EvidenceLink(
                    source=step.get("from", ""), target=step.get("to", ""),
                    relation=step.get("relation", ""),
                    confidence=step.get("confidence", 0.5),
                    source_type="mechanism"
                ))
        confs = [l.confidence for l in links]
        overall = sum(confs) / len(confs) if confs else 0
        chain_type = "incomplete"
        if len(links) >= 3:
            chain_type = "full"
        elif len(links) >= 2:
            chain_type = "partial"
        return EvidenceChain(herb=herb, drug=drug, links=links,
                             overall_confidence=round(overall, 3),
                             chain_type=chain_type)
