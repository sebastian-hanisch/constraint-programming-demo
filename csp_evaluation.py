"""Kennzahlen aus einem Suchlauf, plus der Vergleich gegen csp_bnb_reference (B&B
ohne Kompatibilitäts-Propagation) und die echte OR-Tools-CP-SAT-Referenz."""

from collections import Counter

from csp_bnb_reference import solve_bnb_reference
from csp_constants import MAX_NODES_EXPLORED
from csp_ortools_reference import solve_with_ortools


def compute_stats(result):
    counts = Counter(node.status for node in result.nodes)
    nodes_explored = len(result.nodes)
    total_incompatibility_exclusions = sum(len(node.incompatibility_exclusions) for node in result.nodes)
    return {
        "nodes_explored": nodes_explored,
        "pruned_infeasible": counts["prune_infeasible"],
        "pruned_bound": counts["prune_bound"],
        "leaves_evaluated": counts["leaf_new_best"] + counts["leaf_not_best"],
        "incompatibility_exclusions": total_incompatibility_exclusions,
        "best_value": result.best_value,
        "truncated": result.truncated,
    }


def stats_up_to_step(result, step):
    visited = [node for node in result.nodes if node.id <= step]
    counts = Counter(node.status for node in visited)
    current_best = 0
    for nid, v in result.incumbent_history:
        if nid <= step:
            current_best = v
    return {
        "nodes_so_far": counts.total(),
        "pruned_infeasible": counts["prune_infeasible"],
        "pruned_bound": counts["prune_bound"],
        "incompatibility_exclusions": sum(len(node.incompatibility_exclusions) for node in visited),
        "current_best": current_best,
    }


def comparison(instance, csp_result, max_nodes=MAX_NODES_EXPLORED):
    bnb_value, _bnb_selection, bnb_nodes, bnb_truncated = solve_bnb_reference(instance, max_nodes=max_nodes)
    ortools_result = solve_with_ortools(instance)
    return {
        "csp_nodes": len(csp_result.nodes),
        "csp_best_value": csp_result.best_value,
        "bnb_nodes": bnb_nodes,
        "bnb_best_value": bnb_value,
        "bnb_truncated": bnb_truncated,
        "ortools_best_value": ortools_result["best_value"],
        "ortools_wall_time": ortools_result["wall_time"],
        "ortools_proven_optimal": ortools_result["proven_optimal"],
    }
