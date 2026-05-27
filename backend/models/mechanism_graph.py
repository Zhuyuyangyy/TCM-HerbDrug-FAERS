"""Herb-Ingredient-Target-CYP-AE mechanism graph with 20+ known HDI edges."""
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

@dataclass
class SearchPathResult:
    """Result from search_path: a full path with human-readable explanation."""
    path: List[str]
    edges: List[Dict]
    explanation: str
    overall_confidence: float

class MechanismGraph:
    """中药-成分-靶点-CYP/转运体-AE 机制解释图谱

    Comprehensive herb-drug interaction mechanism knowledge graph
    covering CYP1A2, CYP2C9, CYP2C19, CYP2D6, CYP3A4, P-gp
    with 20+ documented HDI mechanism edges.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_default_graph()

    def _build_default_graph(self):
        default_edges = [
            # ── 丹参 (Danshen / Salvia miltiorrhiza) ──────────────────────
            ("丹参", "tanshinone_IIA", "herb_ingredient", 1.0),
            ("丹参", "salvianolic_acid_B", "herb_ingredient", 1.0),
            ("tanshinone_IIA", "CYP2C9", "ingredient_cyp", 0.9),
            ("tanshinone_IIA", "CYP3A4", "ingredient_cyp", 0.7),
            ("tanshinone_IIA", "CYP1A2", "ingredient_cyp", 0.5),
            ("salvianolic_acid_B", "CYP2C9", "ingredient_cyp", 0.85),
            ("salvianolic_acid_B", "antiplatelet_effect", "ingredient_target", 0.8),
            ("CYP2C9", "warfarin_metabolism_inhibition", "cyp_interaction", 0.95),
            ("warfarin_metabolism_inhibition", "bleeding_risk", "interaction_ae", 0.9),
            ("antiplatelet_effect", "bleeding_risk", "pharmacodynamic_additive", 0.75),

            # ── 甘草 (Licorice / Glycyrrhiza) ─────────────────────────────
            ("甘草", "glycyrrhizin", "herb_ingredient", 1.0),
            ("glycyrrhizin", "11beta_HSD2_inhibition", "ingredient_target", 0.85),
            ("11beta_HSD2_inhibition", "hypokalemia", "target_ae", 0.8),
            ("hypokalemia", "cardiac_arrhythmia_risk", "ae_cascade", 0.7),
            ("glycyrrhizin", "CYP3A4", "ingredient_cyp", 0.6),
            ("glycyrrhizin", "CYP2B6", "ingredient_cyp", 0.5),

            # ── 当归 (Dong Quai / Angelica sinensis) ──────────────────────
            ("当归", "ferulic_acid", "herb_ingredient", 1.0),
            ("当归", "ligustilide", "herb_ingredient", 1.0),
            ("ferulic_acid", "CYP2C19", "ingredient_cyp", 0.6),
            ("ligustilide", "CYP3A4", "ingredient_cyp", 0.55),
            ("CYP2C19", "clopidogrel_metabolism", "cyp_interaction", 0.7),
            ("clopidogrel_metabolism", "reduced_antiplatelet", "interaction_ae", 0.65),
            ("ligustilide", "antiplatelet_effect", "ingredient_target", 0.7),
            ("antiplatelet_effect", "increased_INR", "pharmacodynamic_additive", 0.6),

            # ── 黄芩 (Scutellaria / Baical Skullcap) ──────────────────────
            ("黄芩", "baicalin", "herb_ingredient", 1.0),
            ("黄芩", "wogonin", "herb_ingredient", 1.0),
            ("baicalin", "CYP2C9", "ingredient_cyp", 0.7),
            ("baicalin", "CYP1A2", "ingredient_cyp", 0.8),
            ("wogonin", "CYP3A4", "ingredient_cyp", 0.75),
            ("CYP3A4", "cyclosporine_metabolism_inhibition", "cyp_interaction", 0.9),
            ("cyclosporine_metabolism_inhibition", "nephrotoxicity_risk", "interaction_ae", 0.85),

            # ── 大黄 (Rhubarb / Rhei Radix) ───────────────────────────────
            ("大黄", "emodin", "herb_ingredient", 1.0),
            ("大黄", "rhein", "herb_ingredient", 1.0),
            ("emodin", "CYP3A4", "ingredient_cyp", 0.8),
            ("emodin", "CYP2C9", "ingredient_cyp", 0.5),
            ("rhein", "CYP1A2", "ingredient_cyp", 0.45),
            ("大黄", "gi_motility_increase", "herb_effect", 0.7),
            ("gi_motility_increase", "reduced_drug_absorption", "effect_ae", 0.6),

            # ── 圣约翰草 (St. John's Wort / Hypericum perforatum) ─────────
            ("圣约翰草", "hypericin", "herb_ingredient", 1.0),
            ("圣约翰草", "hyperforin", "herb_ingredient", 1.0),
            ("hyperforin", "CYP3A4_induction", "ingredient_cyp", 0.95),
            ("hyperforin", "P_gp_induction", "ingredient_transporter", 0.95),
            ("hyperforin", "CYP2C9_induction", "ingredient_cyp", 0.7),
            ("hyperforin", "CYP1A2_induction", "ingredient_cyp", 0.6),
            ("CYP3A4_induction", "cyclosporine_level_decrease", "cyp_interaction", 0.95),
            ("cyclosporine_level_decrease", "transplant_rejection_risk", "interaction_ae", 0.9),
            ("P_gp_induction", "digoxin_level_decrease", "transporter_interaction", 0.9),
            ("digoxin_level_decrease", "heart_failure_exacerbation", "interaction_ae", 0.85),
            ("CYP3A4_induction", "oral_contraceptive_failure", "cyp_interaction", 0.9),
            ("oral_contraceptive_failure", "unintended_pregnancy", "interaction_ae", 0.85),
            ("CYP3A4_induction", "warfarin_level_decrease", "cyp_interaction", 0.8),
            ("warfarin_level_decrease", "thromboembolism_risk", "interaction_ae", 0.75),

            # ── 红曲 (Red Yeast Rice / Monascus purpureus) ────────────────
            ("红曲", "monacolin_K", "herb_ingredient", 1.0),
            ("monacolin_K", "HMG_CoA_reductase_inhibition", "ingredient_target", 0.95),
            ("monacolin_K", "CYP3A4", "ingredient_cyp", 0.8),
            ("HMG_CoA_reductase_inhibition", "myopathy_risk", "target_ae", 0.7),
            ("CYP3A4", "statin_metabolism_inhibition", "cyp_interaction", 0.85),
            ("statin_metabolism_inhibition", "rhabdomyolysis_risk", "interaction_ae", 0.8),

            # ── 银杏 (Ginkgo biloba) ──────────────────────────────────────
            ("银杏", "ginkgolide_B", "herb_ingredient", 1.0),
            ("银杏", "bilobalide", "herb_ingredient", 1.0),
            ("ginkgolide_B", "PAF_antagonism", "ingredient_target", 0.9),
            ("PAF_antagonism", "bleeding_risk", "pharmacodynamic_additive", 0.8),
            ("bilobalide", "CYP2C9", "ingredient_cyp", 0.5),
            ("bilobalide", "CYP3A4", "ingredient_cyp", 0.45),
            ("CYP2C9", "warfarin_metabolism_inhibition", "cyp_interaction", 0.95),
            ("ginkgolide_B", "antiplatelet_effect", "ingredient_target", 0.85),
            ("antiplatelet_effect", "bleeding_risk", "pharmacodynamic_additive", 0.75),

            # ── 人参 (Ginseng / Panax ginseng) ────────────────────────────
            ("人参", "ginsenoside_Rb1", "herb_ingredient", 1.0),
            ("人参", "ginsenoside_Rg1", "herb_ingredient", 1.0),
            ("ginsenoside_Rb1", "CYP2D6", "ingredient_cyp", 0.55),
            ("ginsenoside_Rb1", "CYP3A4", "ingredient_cyp", 0.5),
            ("ginsenoside_Rg1", "CYP2C9", "ingredient_cyp", 0.45),
            ("ginsenoside_Rb1", "hypoglycemic_effect", "ingredient_target", 0.7),
            ("hypoglycemic_effect", "hypoglycemia_risk", "pharmacodynamic_additive", 0.65),
            ("ginsenoside_Rb1", "warfarin_antagonism", "ingredient_target", 0.6),
            ("warfarin_antagonism", "reduced_anticoagulation", "interaction_ae", 0.55),

            # ── 麻黄 (Ephedra / Ma Huang) ─────────────────────────────────
            ("麻黄", "ephedrine", "herb_ingredient", 1.0),
            ("麻黄", "pseudoephedrine", "herb_ingredient", 1.0),
            ("ephedrine", "alpha_adrenergic_agonism", "ingredient_target", 0.9),
            ("ephedrine", "beta_adrenergic_agonism", "ingredient_target", 0.85),
            ("alpha_adrenergic_agonism", "hypertensive_crisis", "target_ae", 0.7),
            ("beta_adrenergic_agonism", "tachycardia", "target_ae", 0.8),
            ("ephedrine", "CYP1A2", "ingredient_cyp", 0.4),
            ("CYP1A2", "theophylline_metabolism_alteration", "cyp_interaction", 0.6),
            ("theophylline_metabolism_alteration", "theophylline_toxicity", "interaction_ae", 0.7),
            ("麻黄", "sympathomimetic_effect", "herb_effect", 0.9),
            ("sympathomimetic_effect", "antihypertensive_antagonism", "effect_interaction", 0.8),

            # ── 半夏 (Pinellia ternata) ────────────────────────────────────
            ("半夏", "pinelline", "herb_ingredient", 1.0),
            ("半夏", "beta_sitosterol", "herb_ingredient", 0.9),
            ("pinelline", "CYP2D6", "ingredient_cyp", 0.5),
            ("pinelline", "CYP3A4", "ingredient_cyp", 0.45),
            ("beta_sitosterol", "antiemetic_effect", "ingredient_target", 0.7),
            ("CYP2D6", "metoprolol_metabolism_alteration", "cyp_interaction", 0.55),
            ("metoprolol_metabolism_alteration", "bradycardia_risk", "interaction_ae", 0.5),

            # ── 附子 (Aconitum / Fuzi) ────────────────────────────────────
            ("附子", "aconitine", "herb_ingredient", 1.0),
            ("附子", "mesaconitine", "herb_ingredient", 0.9),
            ("aconitine", "sodium_channel_activation", "ingredient_target", 0.95),
            ("sodium_channel_activation", "cardiac_arrhythmia_risk", "target_ae", 0.9),
            ("mesaconitine", "CYP3A4", "ingredient_cyp", 0.4),
            ("CYP3A4", "antiarrhythmic_metabolism", "cyp_interaction", 0.5),
            ("antiarrhythmic_metabolism", "proarrhythmic_risk", "interaction_ae", 0.6),
            ("aconitine", "neurotoxicity", "ingredient_target", 0.85),
            ("neurotoxicity", "CNS_depression_additive", "ae_cascade", 0.6),

            # ── Shared P-gp interactions ───────────────────────────────────
            ("P_gp_induction", "reduced_bioavailability_Pgp_substrates", "transporter_interaction", 0.85),
            ("reduced_bioavailability_Pgp_substrates", "treatment_failure", "interaction_ae", 0.7),
        ]

        for src, tgt, rel, conf in default_edges:
            self.graph.add_edge(src, tgt, relation=rel, confidence=conf)

    def find_mechanism_paths(self, herb: str, ae: str) -> List[MechanismPath]:
        """Find all mechanism paths from herb to adverse event."""
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
                    targets = [n for n in path if "CYP" in n or "HSD" in n or "inhibition" in n
                               or "effect" in n.lower()]
                    paths.append(MechanismPath(
                        herb=herb,
                        ingredient=path[1] if len(path) > 1 else "",
                        target=targets[0] if targets else "",
                        cyp_enzyme=next((n for n in path if "CYP" in n), ""),
                        adverse_event=ae,
                        evidence_level=min(len(path) - 2, 3),
                        confidence=round(avg_conf, 3)
                    ))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass
        return sorted(paths, key=lambda p: p.confidence, reverse=True)

    def search_path(self, source: str, target: str, max_depth: int = 6) -> List[SearchPathResult]:
        """Search for all paths between source and target with explanations.

        Returns a list of SearchPathResult objects, each containing:
        - path: list of node names in the path
        - edges: list of dicts with {from, to, relation, confidence}
        - explanation: human-readable chain explanation
        - overall_confidence: geometric mean of edge confidences

        Works for any two nodes in the graph (herbs, ingredients, CYPs, AEs, etc.)
        """
        results = []
        # Normalize: try exact match first, then fuzzy
        src = self._resolve_node(source)
        tgt = self._resolve_node(target)
        if src is None or tgt is None:
            return results
        try:
            for path in nx.all_simple_paths(self.graph, src, tgt, cutoff=max_depth):
                edges_info = []
                confs = []
                for i in range(len(path) - 1):
                    edge_data = self.graph[path[i]][path[i+1]]
                    edges_info.append({
                        "from": path[i],
                        "to": path[i+1],
                        "relation": edge_data.get("relation", "unknown"),
                        "confidence": edge_data.get("confidence", 0.5),
                    })
                    confs.append(edge_data.get("confidence", 0.5))

                # Geometric mean of confidences
                import math
                if confs:
                    log_sum = sum(math.log(max(c, 0.01)) for c in confs)
                    overall_conf = round(math.exp(log_sum / len(confs)), 3)
                else:
                    overall_conf = 0.0

                explanation = self._generate_explanation(path, edges_info)

                results.append(SearchPathResult(
                    path=path,
                    edges=edges_info,
                    explanation=explanation,
                    overall_confidence=overall_conf,
                ))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass
        return sorted(results, key=lambda r: r.overall_confidence, reverse=True)

    def _resolve_node(self, name: str) -> Optional[str]:
        """Resolve a node name, supporting fuzzy matching."""
        if name in self.graph:
            return name
        # Case-insensitive search
        lower = name.lower()
        for node in self.graph.nodes():
            if node.lower() == lower:
                return node
        # Partial match
        for node in self.graph.nodes():
            if lower in node.lower() or node.lower() in lower:
                return node
        return None

    def _generate_explanation(self, path: List[str], edges: List[Dict]) -> str:
        """Generate a human-readable explanation for a mechanism path."""
        RELATION_TEMPLATES = {
            "herb_ingredient": "{src} contains active ingredient {tgt}",
            "ingredient_cyp": "{src} inhibits/metabolizes via {tgt}",
            "ingredient_target": "{src} acts on target {tgt}",
            "ingredient_transporter": "{src} affects transporter {tgt}",
            "cyp_interaction": "{src} leads to altered drug metabolism → {tgt}",
            "transporter_interaction": "{src} leads to altered drug transport → {tgt}",
            "interaction_ae": "{src} increases risk of {tgt}",
            "target_ae": "{src} can cause {tgt}",
            "ae_cascade": "{src} may cascade to {tgt}",
            "herb_effect": "{src} produces effect {tgt}",
            "effect_ae": "{src} may result in {tgt}",
            "effect_interaction": "{src} may interfere with {tgt}",
            "pharmacodynamic_additive": "{src} additively increases risk of {tgt}",
        }
        parts = []
        for edge in edges:
            rel = edge["relation"]
            tmpl = RELATION_TEMPLATES.get(rel, "{src} → {tgt}")
            parts.append(tmpl.format(src=edge["from"], tgt=edge["to"]))
        if not parts:
            return f"Path from {path[0]} to {path[-1]} (no edge details)"
        return " → ".join(parts)

    def get_all_herbs(self) -> List[str]:
        """Return all herb nodes (nodes with outgoing herb_ingredient edges)."""
        herbs = set()
        for u, v, data in self.graph.edges(data=True):
            if data.get("relation") == "herb_ingredient":
                herbs.add(u)
        return sorted(herbs)

    def get_all_cyps(self) -> List[str]:
        """Return all CYP enzyme nodes."""
        return sorted([n for n in self.graph.nodes() if "CYP" in n or "P_gp" in n])

    def add_interaction(self, source: str, target: str, relation: str, confidence: float = 0.5):
        """Add an interaction edge to the mechanism graph."""
        self.graph.add_edge(source, target, relation=relation, confidence=confidence)
