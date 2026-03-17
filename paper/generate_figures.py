"""Generate supplementary figures for TruthCert PLOS ONE manuscript.

Usage: python paper/generate_figures.py
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)

# Load data from latest v2 run (auto-discover most recent)
_RUNS_DIR = Path(__file__).parent.parent / "outputs" / "runs_v2"
if _RUNS_DIR.exists():
    _candidates = sorted(_RUNS_DIR.iterdir(), key=lambda p: p.stat().st_mtime,
                         reverse=True)
    DATA_DIR = _candidates[0] if _candidates else _RUNS_DIR / "MISSING"
else:
    DATA_DIR = _RUNS_DIR / "MISSING"


def s1_fig_regret():
    """S1 Fig: Decision regret by topic and method (grouped bar chart)."""
    df = pd.read_csv(DATA_DIR / "topic_metrics.csv")

    topics = df["label"].values
    x = np.arange(len(topics))
    w = 0.25

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - w, df["regret_classic"], w, label="Classic RE", color="#4472C4")
    ax.bar(x,     df["regret_arb"],     w, label="Arbitrated", color="#ED7D31")
    ax.bar(x + w, df["regret_delta"],   w, label="Delta Engine", color="#A5A5A5")

    ax.set_ylabel("Decision Regret")
    ax.set_title("S1 Fig. Decision regret by topic and method (50 replications)")
    ax.set_xticks(x)
    ax.set_xticklabels(topics, rotation=45, ha="right", fontsize=8)
    ax.legend()
    ax.set_ylim(0, max(df["regret_classic"].max(), df["regret_arb"].max()) * 1.15)
    plt.tight_layout()
    fig.savefig(OUT / "S1_Fig_regret.png", dpi=300)
    fig.savefig(OUT / "S1_Fig_regret.pdf")
    plt.close(fig)
    print(f"  S1 Fig saved to {OUT / 'S1_Fig_regret.png'}")


def s2_fig_coverage():
    """S3 Fig: Coverage and width by method across topics."""
    df = pd.read_csv(DATA_DIR / "topic_metrics.csv")

    topics = df["label"].values
    x = np.arange(len(topics))
    w = 0.25

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Coverage
    ax1.bar(x - w, df["coverage_classic"], w, label="Classic RE", color="#4472C4")
    ax1.bar(x,     df["coverage_arb"],     w, label="Arbitrated", color="#ED7D31")
    ax1.bar(x + w, df["coverage_delta"],   w, label="Delta Engine", color="#A5A5A5")
    ax1.axhline(0.95, color="red", linestyle="--", alpha=0.5, label="95% target")
    ax1.set_ylabel("Coverage")
    ax1.set_title("S3 Fig. Coverage and interval width by topic and method")
    ax1.legend(fontsize=8)
    ax1.set_ylim(0.95, 1.005)

    # Width
    ax2.bar(x - w, df["width_classic"], w, label="Classic RE", color="#4472C4")
    ax2.bar(x,     df["width_arb"],     w, label="Arbitrated", color="#ED7D31")
    ax2.bar(x + w, df["width_delta"],   w, label="Delta Engine", color="#A5A5A5")
    ax2.set_ylabel("Mean Interval Width (logRR scale)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(topics, rotation=45, ha="right", fontsize=8)
    ax2.legend(fontsize=8)

    plt.tight_layout()
    fig.savefig(OUT / "S3_Fig_coverage_width.png", dpi=300)
    fig.savefig(OUT / "S3_Fig_coverage_width.pdf")
    plt.close(fig)
    print(f"  S3 Fig saved to {OUT / 'S3_Fig_coverage_width.png'}")


def s2_fig_witness_agreement():
    """S2 Fig: Witness agreement patterns (heatmap placeholder from capsules)."""
    import json

    capsule_path = DATA_DIR / "node_capsules.jsonl"
    if not capsule_path.exists():
        print("  S2 Fig: skipped (no capsules found)")
        return

    topics = []
    levels = {"low": 0, "mid": 1, "high": 2}
    topic_disagreements = {}

    with open(capsule_path) as f:
        for line in f:
            cap = json.loads(line)
            tid = cap["topic_id"]
            arb = cap.get("arbitration", {})
            level = arb.get("level", "low")
            if tid not in topic_disagreements:
                topic_disagreements[tid] = []
            topic_disagreements[tid].append(levels.get(level, 0))

    tids = sorted(topic_disagreements.keys())
    mean_levels = [np.mean(topic_disagreements[t]) for t in tids]

    fig, ax = plt.subplots(figsize=(10, 4))
    bars = ax.barh(range(len(tids)), mean_levels, color="#ED7D31")
    ax.set_yticks(range(len(tids)))
    ax.set_yticklabels(tids, fontsize=9)
    ax.set_xlabel("Mean Disagreement Level (0=low, 1=mid, 2=high)")
    ax.set_title("S2 Fig. Witness disagreement by topic (last replication)")
    ax.set_xlim(0, 2)
    ax.axvline(0.33, color="green", linestyle="--", alpha=0.5, label="Low threshold")
    ax.axvline(1.0, color="orange", linestyle="--", alpha=0.5, label="Mid threshold")
    ax.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(OUT / "S2_Fig_witness_agreement.png", dpi=300)
    fig.savefig(OUT / "S2_Fig_witness_agreement.pdf")
    plt.close(fig)
    print(f"  S2 Fig saved to {OUT / 'S2_Fig_witness_agreement.png'}")


def main():
    if not DATA_DIR.exists():
        print(f"ERROR: {DATA_DIR} not found. Run simulation first.")
        return

    print("Generating supplementary figures...")
    s1_fig_regret()
    s2_fig_witness_agreement()
    s2_fig_coverage()
    print("Done.")


if __name__ == "__main__":
    main()
