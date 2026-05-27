"""Mechanism explanation API endpoints.

POST /api/mechanism/explain: Given herb+drug, return full mechanism chain
GET  /api/mechanism/search?q=: Search mechanism graph
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from ..models.mechanism_graph import MechanismGraph
from ..data.herb_kg import HerbKnowledgeGraph

router = APIRouter(prefix="/api/mechanism", tags=["mechanism"])

# Shared singletons
_mech_graph = MechanismGraph()
_herb_kg = HerbKnowledgeGraph()


class MechanismExplainRequest(BaseModel):
    herb: str
    drug: str
    adverse_event: Optional[str] = None  # if None, try all known AEs


class PathEdge(BaseModel):
    source: str
    target: str
    relation: str
    confidence: float


class MechanismExplanation(BaseModel):
    herb: str
    drug: str
    paths: List[Dict]
    cyp_profile: Dict
    summary: str


def _get_drug_cyps(drug: str) -> List[str]:
    """Map known drugs to their primary CYP metabolism pathways."""
    DRUG_CYP_MAP = {
        "warfarin": ["CYP2C9", "CYP3A4", "CYP1A2"],
        "clopidogrel": ["CYP2C19", "CYP3A4"],
        "cyclosporine": ["CYP3A4"],
        "tacrolimus": ["CYP3A4"],
        "simvastatin": ["CYP3A4"],
        "atorvastatin": ["CYP3A4"],
        "lovastatin": ["CYP3A4"],
        "digoxin": [],  # P-gp substrate, not CYP
        "metoprolol": ["CYP2D6"],
        "codeine": ["CYP2D6"],
        "tramadol": ["CYP2D6"],
        "omeprazole": ["CYP2C19", "CYP3A4"],
        "diazepam": ["CYP2C19", "CYP3A4"],
        "theophylline": ["CYP1A2"],
        "clozapine": ["CYP1A2", "CYP3A4"],
        "fluoxetine": ["CYP2D6", "CYP2C9"],
        "phenytoin": ["CYP2C9", "CYP2C19"],
        "irinotecan": ["CYP3A4"],
        "saquinavir": ["CYP3A4"],
        "midazolam": ["CYP3A4"],
        "losartan": ["CYP2C9"],
    }
    return DRUG_CYP_MAP.get(drug.lower(), [])


DRUG_PGP_SUBSTRATES = {"digoxin", "cyclosporine", "tacrolimus", "saquinavir",
                        "irinotecan", "diltiazem", "verapamil", "amiodarone"}


@router.post("/explain")
async def explain_mechanism(req: MechanismExplainRequest):
    """Explain the full mechanism chain for a herb-drug interaction.

    Returns all mechanism paths from the herb to known adverse events
    that are relevant to the specified drug, including:
    - Active ingredients in the herb
    - CYP enzyme / transporter interactions
    - Downstream adverse events
    - The herb's CYP inhibition/induction profile
    """
    herb = req.herb
    drug = req.drug

    # Get the herb's CYP profile
    cyp_profile = _herb_kg.get_full_cyp_profile(herb)

    # Determine which CYP enzymes the drug uses
    drug_cyps = _get_drug_cyps(drug)

    # Find overlap: herb CYP interactions that affect the drug
    herb_inhib = cyp_profile.get("inhibition", {})
    herb_induc = cyp_profile.get("induction", {})
    pgp_info = cyp_profile.get("pgp", {})

    affected_cyps = []
    for cyp in drug_cyps:
        if cyp in herb_inhib:
            affected_cyps.append({"enzyme": cyp, "effect": "inhibition",
                                  "potency": herb_inhib[cyp]})
        if cyp in herb_induc:
            affected_cyps.append({"enzyme": cyp, "effect": "induction",
                                  "potency": herb_induc[cyp]})

    # P-gp effects
    pgp_affected = (pgp_info.get("effect") != "none" and
                    drug.lower() in DRUG_PGP_SUBSTRATES)

    # Search for mechanism paths
    # Try to find paths from herb to any AE that's relevant to the drug
    ALL_AES = [
        "bleeding_risk", "hypokalemia", "reduced_antiplatelet",
        "nephrotoxicity_risk", "cardiac_arrhythmia_risk", "myopathy_risk",
        "rhabdomyolysis_risk", "increased_INR", "transplant_rejection_risk",
        "heart_failure_exacerbation", "oral_contraceptive_failure",
        "thromboembolism_risk", "hypoglycemia_risk", "reduced_anticoagulation",
        "tachycardia", "hypertensive_crisis", "bradycardia_risk",
        "theophylline_toxicity", "neurotoxicity", "proarrhythmic_risk",
        "reduced_drug_absorption", "treatment_failure",
    ]

    if req.adverse_event:
        target_aes = [req.adverse_event]
    else:
        target_aes = ALL_AES

    all_paths = []
    for ae in target_aes:
        paths = _mech_graph.find_mechanism_paths(herb, ae)
        for p in paths:
            all_paths.append({
                "herb": p.herb,
                "ingredient": p.ingredient,
                "target": p.target,
                "cyp_enzyme": p.cyp_enzyme,
                "adverse_event": p.adverse_event,
                "evidence_level": p.evidence_level,
                "confidence": p.confidence,
            })

    # Also do search_path for direct herb->drug relevance
    search_results = []
    for cyp_info in affected_cyps:
        cyp = cyp_info["enzyme"]
        cyp_node = cyp + ("_induction" if cyp_info["effect"] == "induction" else "")
        paths = _mech_graph.search_path(herb, cyp_node)
        for sp in paths:
            search_results.append({
                "path": sp.path,
                "edges": sp.edges,
                "explanation": sp.explanation,
                "confidence": sp.overall_confidence,
            })
        # Also try without suffix
        paths2 = _mech_graph.search_path(herb, cyp)
        for sp in paths2:
            search_results.append({
                "path": sp.path,
                "edges": sp.edges,
                "explanation": sp.explanation,
                "confidence": sp.overall_confidence,
            })

    # Build summary
    summary_parts = [f"Interaction mechanism for {herb} + {drug}:"]
    if affected_cyps:
        for ca in affected_cyps:
            summary_parts.append(
                f"  - {herb} {ca['effect']} {ca['enzyme']} (potency={ca['potency']:.0%}), "
                f"which is a primary metabolic pathway for {drug}."
            )
    if pgp_affected:
        summary_parts.append(
            f"  - {herb} affects P-glycoprotein ({pgp_info['effect']}), "
            f"and {drug} is a P-gp substrate."
        )
    if all_paths:
        summary_parts.append(f"  - Found {len(all_paths)} mechanism pathway(s) to known adverse events.")
    else:
        summary_parts.append("  - No direct mechanism pathways found in knowledge graph. "
                             "Interaction may be pharmacodynamic or not yet characterized.")

    return {
        "herb": herb,
        "drug": drug,
        "affected_cyp_enzymes": affected_cyps,
        "pgp_affected": pgp_affected,
        "mechanism_paths": all_paths,
        "search_paths": search_results,
        "cyp_profile": cyp_profile,
        "summary": " ".join(summary_parts),
    }


@router.get("/search")
async def search_mechanism(q: str = Query(..., description="Search query for mechanism graph")):
    """Search the mechanism graph for nodes and paths matching the query.

    Returns matching nodes, their connections, and any paths between them.
    """
    graph = _mech_graph.graph
    q_lower = q.lower()

    # Find matching nodes
    matching_nodes = [n for n in graph.nodes() if q_lower in n.lower()]

    # Get edges for matching nodes
    node_details = []
    for node in matching_nodes:
        neighbors = []
        for _, tgt, data in graph.out_edges(node, data=True):
            neighbors.append({
                "target": tgt,
                "relation": data.get("relation", "unknown"),
                "confidence": data.get("confidence", 0.5),
                "direction": "outgoing",
            })
        for src, _, data in graph.in_edges(node, data=True):
            neighbors.append({
                "target": src,
                "relation": data.get("relation", "unknown"),
                "confidence": data.get("confidence", 0.5),
                "direction": "incoming",
            })
        node_details.append({"node": node, "connections": neighbors})

    # Also search herbs in KG
    herb_matches = _herb_kg.search_herbs(q)
    herb_details = []
    for h in herb_matches:
        profile = _herb_kg.get_full_cyp_profile(h)
        herb_details.append({
            "herb": h,
            "latin": _herb_kg.herbs.get(h, {}).get("latin", ""),
            "english": _herb_kg.herbs.get(h, {}).get("english", ""),
            "cyp_profile": profile,
        })

    # Find paths between matched nodes (if 2+ matches)
    inter_paths = []
    if len(matching_nodes) >= 2:
        for i in range(len(matching_nodes)):
            for j in range(i + 1, len(matching_nodes)):
                paths = _mech_graph.search_path(matching_nodes[i], matching_nodes[j])
                for sp in paths:
                    inter_paths.append({
                        "path": sp.path,
                        "explanation": sp.explanation,
                        "confidence": sp.overall_confidence,
                    })

    return {
        "query": q,
        "matching_nodes": node_details,
        "herb_matches": herb_details,
        "inter_paths": inter_paths,
        "total_graph_nodes": graph.number_of_nodes(),
        "total_graph_edges": graph.number_of_edges(),
    }


@router.get("/herbs")
async def list_herbs():
    """List all herbs in the mechanism graph with their CYP profiles."""
    herbs = _mech_graph.get_all_herbs()
    herb_data = []
    for h in herbs:
        kg_info = _herb_kg.herbs.get(h, {})
        cyp = _herb_kg.get_full_cyp_profile(h)
        herb_data.append({
            "name": h,
            "latin": kg_info.get("latin", ""),
            "english": kg_info.get("english", ""),
            "pinyin": kg_info.get("pinyin", ""),
            "cyp_profile": cyp,
        })
    return {"herbs": herb_data, "count": len(herb_data)}


@router.get("/cyps")
async def list_cyps():
    """List all CYP enzymes and transporters in the mechanism graph."""
    cyps = _mech_graph.get_all_cyps()
    cyp_data = []
    for c in cyps:
        inhibiting_herbs = _herb_kg.get_herbs_inhibiting_cyp(c)
        inducing_herbs = _herb_kg.get_herbs_inducing_cyp(c)
        cyp_data.append({
            "enzyme": c,
            "inhibiting_herbs": inhibiting_herbs,
            "inducing_herbs": inducing_herbs,
        })
    return {"cyps": cyp_data, "count": len(cyp_data)}
