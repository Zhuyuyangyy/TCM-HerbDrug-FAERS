"""Herb-Ingredient-Target-CYP-AE mechanism graph."""
import networkx as nx
from typing import List, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class MechanismPath:
    herb: str
    ingredient: str
    target: str
    cyp_enzyme: str
    adverse_event: str
    evidence_level: int  # 1=direct, 2=inferred, 3=putative
    confidence: float

class MechanismGraph:
    """中药-成分-靶点-CYP/转运体-AE 机制解释图谱"""

    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_default_graph()

    def _build_default_graph(self):
        default_edges = [
            ("丹参", "tanshinone_IIA", "herb_ingredient", 1.0),
            ("tanshinone_IIA", "CYP2C9", "ingredient_cyp", 0.9),
            ("tanshinone_IIA", "CYP3A4", "ingredient_cyp", 0.7),
            ("tanshinone_IIA", "CYP1A2", "ingredient_cyp", 0.5),
            ("CYP2C9", "warfarin_metabolism_inhibition", "cyp_interaction", 0.95),
            ("warfarin_metabolism_inhibition", "bleeding_risk", "interaction_ae", 0.9),
            ("甘草", "glycyrrhizin", "herb_ingredient", 1.0),
            ("glycyrrhizin", "11beta_HSD2_inhibition", "ingredient_target", 0.85),
            ("11beta_HSD2_inhibition", "hypokalemia", "target_ae", 0.8),
            ("当归", "ferulic_acid", "herb_ingredient", 1.0),
            ("ferulic_acid", "CYP2C19", "ingredient_cyp", 0.6),
            ("CYP2C19", "clopidogrel_metabolism", "cyp_interaction", 0.7),
            ("clopidogrel_metabolism", "reduced_antiplatelet", "interaction_ae", 0.65),
        ]
        for src, tgt, rel, conf in default_edges:
            self.graph.add_edge(src, tgt, relation=rel, confidence=conf)

    def find_mechanism_paths(self, herb: str, ae: str) -> List[MechanismPath]:
        paths = []
        if herb not in self.graph or ae not in self.graph:
            return paths
        try:
            for path in nx.all_simple_paths(self.graph, herb, ae, cutoff=5):
                if len(path) >= 3:
                    edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
                    confs = [self.graph[u][v].get("confidence", 0.5) for u, v in edges]
                    avg_conf = sum(confs) / len(confs)
                    ingredients = [n for n in path if self.graph.in_edges(n) and
                                   any(self.graph[u][v].get("relation") == "herb_ingredient"
                                       for u, v in self.graph.in_edges(n))]
                    targets = [n for n in path if "CYP" in n or "HSD" in n or "inhibition" in n]
                    paths.append(MechanismPath(
                        herb=herb,
                        ingredient=path[1] if len(path) > 1 else "",
                        target=targets[0] if targets else "",
                        cyp_enzyme=next((n for n in path if "CYP" in n), ""),
                        adverse_event=ae,
                        evidence_level=min(len(path) - 2, 3),
                        confidence=round(avg_conf, 3)
                    ))
        except nx.NetworkXNoPath:
            pass
        return sorted(paths, key=lambda p: p.confidence, reverse=True)

    def add_interaction(self, source: str, target: str, relation: str, confidence: float = 0.5):
        self.graph.add_edge(source, target, relation=relation, confidence=confidence)
