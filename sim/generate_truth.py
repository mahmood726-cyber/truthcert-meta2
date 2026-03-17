"""Generate ground-truth node-level parameters (mu, tau, p_control)."""

from typing import Dict, List

import numpy as np
from numpy.random import Generator

from .config_schema import TopicConfig


def build_node_ids(cfg: TopicConfig) -> List[str]:
    """Build all node_id strings as PHENOTYPE|CLASS|ENDPOINT."""
    nodes = []
    for p in cfg.node_grid.phenotypes:
        for c in cfg.node_grid.classes:
            for e in cfg.node_grid.endpoints:
                nodes.append(f"{p}|{c}|{e}")
    return nodes


def generate_truth(cfg: TopicConfig, rng: Generator) -> Dict[str, dict]:
    """Generate true mu, tau, p_control for each node.

    Returns dict mapping node_id -> {"mu", "tau", "p_control"}.

    Effect structures:
      block:          phenotype + class blocks + small noise
      smooth:         global + attenuated phenotype/class + small noise
      discontinuous:  smooth baseline then flip selected nodes
    """
    node_ids = build_node_ids(cfg)
    truth = cfg.truth
    n_nodes = len(node_ids)

    phenotypes = cfg.node_grid.phenotypes
    classes = cfg.node_grid.classes
    endpoints = cfg.node_grid.endpoints

    # ── Generate mu per node ──────────────────────────────────────────
    if truth.node_effect_structure == "block":
        pheno_eff = {p: rng.normal(0, truth.mu_node_sd) for p in phenotypes}
        class_eff = {c: rng.normal(0, truth.mu_node_sd) for c in classes}
        mu_nodes = {}
        for nid in node_ids:
            p, c, _e = nid.split("|")
            mu_nodes[nid] = (truth.mu_global
                             + pheno_eff[p]
                             + class_eff[c]
                             + rng.normal(0, truth.mu_node_sd * 0.3))

    elif truth.node_effect_structure == "smooth":
        pheno_eff = {p: rng.normal(0, truth.mu_node_sd * 0.5) for p in phenotypes}
        class_eff = {c: rng.normal(0, truth.mu_node_sd * 0.5) for c in classes}
        mu_nodes = {}
        for nid in node_ids:
            p, c, _e = nid.split("|")
            mu_nodes[nid] = (truth.mu_global
                             + pheno_eff[p]
                             + class_eff[c]
                             + rng.normal(0, truth.mu_node_sd * 0.2))

    elif truth.node_effect_structure == "discontinuous":
        # Start with smooth baseline
        pheno_eff = {p: rng.normal(0, truth.mu_node_sd * 0.5) for p in phenotypes}
        class_eff = {c: rng.normal(0, truth.mu_node_sd * 0.5) for c in classes}
        mu_nodes = {}
        for nid in node_ids:
            p, c, _e = nid.split("|")
            mu_nodes[nid] = (truth.mu_global
                             + pheno_eff[p]
                             + class_eff[c]
                             + rng.normal(0, truth.mu_node_sd * 0.2))
        # Apply discontinuity
        disc = truth.discontinuity
        if disc.enabled:
            if disc.type == "phenotype_flip":
                flip_pheno = phenotypes[0]
                for nid in node_ids:
                    if nid.split("|")[0] == flip_pheno:
                        mu_nodes[nid] += disc.magnitude
            elif disc.type == "node_flip":
                n_flip = max(1, n_nodes // 4)
                flip_idx = rng.choice(n_nodes, size=n_flip, replace=False)
                for i in flip_idx:
                    mu_nodes[node_ids[i]] += disc.magnitude
    else:
        raise ValueError(f"Unknown node_effect_structure: {truth.node_effect_structure}")

    # ── Generate tau per node ─────────────────────────────────────────
    tau_nodes = {}
    for nid in node_ids:
        tau_nodes[nid] = max(0.01, truth.tau_base + rng.normal(0, truth.tau_sd))

    # ── Generate p_control per endpoint ───────────────────────────────
    p_control = {}
    for e in endpoints:
        lo, hi = cfg.baseline_risk.control_event_rate[e]
        p_control[e] = float(rng.uniform(lo, hi))

    # ── Assemble ──────────────────────────────────────────────────────
    result = {}
    for nid in node_ids:
        e = nid.split("|")[2]
        result[nid] = {
            "mu": float(mu_nodes[nid]),
            "tau": float(tau_nodes[nid]),
            "p_control": p_control[e],
        }
    return result
