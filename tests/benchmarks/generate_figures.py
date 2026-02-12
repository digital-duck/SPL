"""Generate paper figures from benchmark data.

Reads JSON results from docs/paper/data/ and produces PDF figures
in docs/paper/figures/ for LaTeX inclusion.

Run: python -m tests.benchmarks.generate_figures

Requires: matplotlib (pip install matplotlib)
"""

from __future__ import annotations
import json
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from tests.benchmarks.bench_utils import DATA_DIR, FIGURES_DIR


# Color palette
COLORS = {
    "spl": "#2563eb",       # Blue
    "python": "#f97316",    # Orange
    "system": "#6b7280",    # Gray
    "context": "#3b82f6",   # Blue
    "rag": "#10b981",       # Green
    "memory": "#8b5cf6",    # Purple
    "output": "#f59e0b",    # Amber
    "buffer": "#e5e7eb",    # Light gray
}


def figure1_loc_comparison():
    """Figure 1: Lines of Code — SPL vs Imperative Python (grouped bar chart)."""
    data = json.loads((DATA_DIR / "experiment1_developer_experience.json").read_text())

    labels = [d["label"] for d in data]
    spl_loc = [d["spl_loc"] for d in data]
    python_loc = [d["python_loc"] for d in data]

    fig, ax = plt.subplots(figsize=(10, 5))

    x = range(len(labels))
    width = 0.35

    bars1 = ax.bar([i - width/2 for i in x], spl_loc, width, label="SPL", color=COLORS["spl"])
    bars2 = ax.bar([i + width/2 for i in x], python_loc, width, label="Imperative Python", color=COLORS["python"])

    # Add value labels on bars
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=9)

    ax.set_ylabel("Lines of Code", fontsize=12)
    ax.set_title("Developer Experience: SPL vs Imperative Python", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha='right', fontsize=10)
    ax.legend(fontsize=11)
    ax.set_ylim(0, max(python_loc) * 1.15)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # Add reduction % annotations
    for i in x:
        reduction = data[i]["reduction_pct"]
        mid_y = (spl_loc[i] + python_loc[i]) / 2
        ax.annotate(f'-{reduction}%',
                    xy=(i, mid_y), fontsize=9, ha='center',
                    color='#dc2626', fontweight='bold')

    plt.tight_layout()
    path = FIGURES_DIR / "figure1_loc_comparison.pdf"
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")
    return path


def figure2_token_allocation():
    """Figure 2: Token Allocation Stacked Bar Chart across budgets."""
    data = json.loads((DATA_DIR / "experiment2_token_optimization.json").read_text())
    budgets_data = data["varying_budgets"]

    labels = [f"{d['budget']//1000}K" for d in budgets_data]
    system = [d["system"] for d in budgets_data]
    question = [d["question"] for d in budgets_data]
    docs = [d["docs"] for d in budgets_data]
    history = [d["history"] for d in budgets_data]
    output = [d["output"] for d in budgets_data]
    buffer = [d["buffer"] for d in budgets_data]

    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(len(labels))

    # Stacked bars
    bottom = [0] * len(labels)

    for values, label, color in [
        (system, "System Role", COLORS["system"]),
        (question, "Context (question)", COLORS["context"]),
        (docs, "RAG (docs)", COLORS["rag"]),
        (history, "Memory (history)", COLORS["memory"]),
        (output, "Output Budget", COLORS["output"]),
        (buffer, "Buffer (unused)", COLORS["buffer"]),
    ]:
        ax.bar(x, values, bottom=bottom, label=label, color=color, edgecolor='white', linewidth=0.5)
        bottom = [b + v for b, v in zip(bottom, values)]

    # Add utilization % on top
    for i in x:
        util = budgets_data[i]["utilization"]
        ax.text(i, bottom[i] + 100, f'{util}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_ylabel("Tokens", fontsize=12)
    ax.set_xlabel("Total Budget", fontsize=12)
    ax.set_title("Token Allocation Strategy Across Budget Levels", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.legend(loc='upper left', fontsize=9)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, p: f'{int(v):,}'))

    plt.tight_layout()
    path = FIGURES_DIR / "figure2_token_allocation.pdf"
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")
    return path


def figure3_compression():
    """Figure 3: Compression Behavior Under Budget Pressure."""
    data = json.loads((DATA_DIR / "experiment2_token_optimization.json").read_text())
    over_budget = data["over_budget"]

    multipliers = [d["multiplier"] for d in over_budget]
    requested = [d["requested_tokens"] for d in over_budget]
    allocated = [d["allocated_tokens"] for d in over_budget]
    input_budget = over_budget[0]["input_budget"]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    # Requested vs allocated tokens
    ax1.plot(multipliers, requested, 'o-', color=COLORS["python"], label="Requested Tokens", linewidth=2, markersize=8)
    ax1.plot(multipliers, allocated, 's-', color=COLORS["spl"], label="Allocated Tokens", linewidth=2, markersize=8)
    ax1.axhline(y=input_budget, color='#dc2626', linestyle='--', linewidth=1.5, label=f"Input Budget ({input_budget:,})")

    ax1.set_xlabel("Context-to-Budget Ratio", fontsize=12)
    ax1.set_ylabel("Tokens", fontsize=12)
    ax1.set_title("Graceful Degradation: Compression Under Budget Pressure", fontsize=14)
    ax1.legend(fontsize=10)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, p: f'{int(v):,}'))

    # Add compression count as annotations
    for i, d in enumerate(over_budget):
        if d["num_compressed"] > 0:
            ax1.annotate(f'{d["num_compressed"]} compressed',
                        xy=(multipliers[i], allocated[i]),
                        xytext=(10, -15), textcoords='offset points',
                        fontsize=8, color='#6b7280')

    plt.tight_layout()
    path = FIGURES_DIR / "figure3_compression.pdf"
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")
    return path


def figure4_cost_comparison():
    """Figure 4: Cost Comparison Across Models (horizontal bar chart)."""
    data = json.loads((DATA_DIR / "experiment3_cost_estimation.json").read_text())

    # Filter to models with cost data
    data = [d for d in data if d["estimated_cost"] is not None]

    models = [d["model_name"] for d in data]
    costs = [d["estimated_cost"] for d in data]
    tiers = [d["tier"] for d in data]

    tier_colors = {
        "Premium": "#dc2626",
        "Legacy Premium": "#ea580c",
        "Balanced": "#2563eb",
        "Flagship": "#7c3aed",
        "Economy": "#16a34a",
        "Budget": "#059669",
    }

    fig, ax = plt.subplots(figsize=(9, 5))

    colors = [tier_colors.get(t, "#6b7280") for t in tiers]
    bars = ax.barh(models, costs, color=colors, edgecolor='white', linewidth=0.5)

    # Add cost labels
    for bar, cost in zip(bars, costs):
        ax.text(bar.get_width() + max(costs) * 0.02, bar.get_y() + bar.get_height()/2,
                f'${cost:.4f}', va='center', fontsize=10)

    ax.set_xlabel("Estimated Cost (USD)", fontsize=12)
    ax.set_title("Pre-Execution Cost Visibility: Same Query, Different Models", fontsize=14)
    ax.invert_yaxis()

    # Add insight text
    if len(costs) >= 2:
        ratio = max(costs) / min(costs)
        ax.text(0.95, 0.05, f'{ratio:.0f}x cost difference\nvisible before execution',
                transform=ax.transAxes, ha='right', va='bottom',
                fontsize=10, style='italic', color='#6b7280',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    path = FIGURES_DIR / "figure4_cost_comparison.pdf"
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {path}")
    return path


def run():
    if not HAS_MATPLOTLIB:
        print("ERROR: matplotlib not installed. Run: pip install matplotlib")
        return

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating paper figures...")
    print()

    # Check which data files exist
    available = []
    for name in ["experiment1_developer_experience",
                 "experiment2_token_optimization",
                 "experiment3_cost_estimation"]:
        path = DATA_DIR / f"{name}.json"
        if path.exists():
            available.append(name)
        else:
            print(f"  SKIP: {path} not found (run benchmark first)")

    if "experiment1_developer_experience" in available:
        figure1_loc_comparison()

    if "experiment2_token_optimization" in available:
        figure2_token_allocation()
        figure3_compression()

    if "experiment3_cost_estimation" in available:
        figure4_cost_comparison()

    print()
    print("Done! Figures saved to docs/paper/figures/")


if __name__ == "__main__":
    run()
