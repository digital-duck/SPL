"""SPL EXPLAIN: render execution plans in human-readable format."""

from spl.optimizer import ExecutionPlan


def explain_plan(plan: ExecutionPlan) -> str:
    """Render an execution plan as a formatted string (like SQL EXPLAIN)."""
    lines: list[str] = []

    # Header
    lines.append(f"Execution Plan for: {plan.prompt_name}")
    lines.append("=" * 60)

    budget_str = f"{plan.total_budget:,} tokens" if plan.total_budget else "unlimited"
    model_str = plan.model or "default"
    lines.append(f"Budget: {budget_str} | Model: {model_str}")
    lines.append("")

    # Token allocation tree
    lines.append("Token Allocation:")

    total_all = plan.total_input_tokens + plan.output_budget + plan.buffer_tokens
    if total_all == 0:
        total_all = 1  # prevent division by zero

    for i, step in enumerate(plan.steps):
        is_last_step = (i == len(plan.steps) - 1) and plan.output_budget == 0
        prefix = "+-- " if not is_last_step else "\\-- "

        pct = step.allocated_tokens / total_all * 100
        annotation = _step_annotation(step)

        line = (
            f"{prefix}{step.alias:<25s} "
            f"{step.allocated_tokens:>6,} tokens  "
            f"({pct:>5.1f}%)"
        )
        if annotation:
            line += f"  [{annotation}]"
        lines.append(line)

    # Output budget
    if plan.output_budget:
        pct = plan.output_budget / total_all * 100
        lines.append(f"+-- {'Output Budget':<25s} {plan.output_budget:>6,} tokens  ({pct:>5.1f}%)")

    # Buffer
    if plan.buffer_tokens > 0:
        pct = plan.buffer_tokens / total_all * 100
        lines.append(f"\\-- {'Buffer':<25s} {plan.buffer_tokens:>6,} tokens  ({pct:>5.1f}%)")

    lines.append(f"{'':>4s}{'':->36s}")

    # Total
    if plan.total_budget:
        usage_pct = (plan.total_input_tokens + plan.output_budget) / plan.total_budget * 100
        lines.append(
            f"{'Total':<29s} {plan.total_input_tokens + plan.output_budget:>6,} / "
            f"{plan.total_budget:,} tokens ({usage_pct:.1f}%)"
        )
    else:
        lines.append(
            f"{'Total':<29s} {plan.total_input_tokens + plan.output_budget:>6,} tokens"
        )

    lines.append("")

    # Estimated cost and latency
    if plan.estimated_cost is not None:
        lines.append(f"Estimated Cost: ${plan.estimated_cost:.4f}")

    # Optimizations applied
    if plan.optimizations:
        lines.append("")
        lines.append("Optimizations Applied:")
        for opt in plan.optimizations:
            lines.append(f"  * {opt}")

    # Warnings
    if plan.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warn in plan.warnings:
            lines.append(f"  ! {warn}")

    return '\n'.join(lines)


def explain_plans(plans: list[ExecutionPlan]) -> str:
    """Render multiple execution plans."""
    return '\n\n'.join(explain_plan(p) for p in plans)


def _step_annotation(step) -> str:
    """Generate annotation text for a step."""
    parts = []
    if step.compressed:
        ratio_pct = (1.0 - step.compression_ratio) * 100
        parts.append(f"compressed {ratio_pct:.0f}%")
    if step.cache_status == "hit":
        parts.append("cache HIT")
    elif step.cache_status == "miss":
        parts.append("cache MISS")
    if step.operation == "memory_get":
        parts.append("from memory")
    return ", ".join(parts)
