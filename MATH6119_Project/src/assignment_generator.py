"""
P3 assignment generator and evaluator.

Generates candidate attachment assignments, scores them, and exports the
top plans for downstream planning and report writing.
"""

import csv
from itertools import permutations
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTERMEDIATE_DIR = PROJECT_ROOT / "data" / "intermediate"
MAPPING_PATH = INTERMEDIATE_DIR / "mapping.csv"
FEEDERS_PATH = INTERMEDIATE_DIR / "feeders.csv"
PCB_PATH = INTERMEDIATE_DIR / "pcb_positions.csv"

DEFAULT_ASSIGNMENT_PATH = INTERMEDIATE_DIR / "assignment.csv"
OUTPUT_COLUMNS = ["machine_id", "head_slot", "head_type"]
EVAL_COLUMNS = [
    "plan_name",
    "source_template",
    "selection_rule",
    "total_score",
    "coverage_score",
    "e_balance_score",
    "workload_balance_score",
    "feeder_order_score",
    "specialization_score",
    "estimated_workload_range",
    "average_feeder_span",
    "average_head_jump",
    "notes",
]
CATALOG_COLUMNS = [
    "candidate_id",
    "source_template",
    "total_score",
    "coverage_score",
    "e_balance_score",
    "workload_balance_score",
    "feeder_order_score",
    "specialization_score",
    "estimated_workload_range",
    "average_feeder_span",
    "average_head_jump",
]

MACHINE_IDS = ["M1", "M2", "M3"]

# Head order in mapping.csv:
# 0=alpha1, 1=alpha2, 2=alpha3, 3=alpha4, 4=alpha5, 5=alpha6, 6=alpha7, 7=alpha8, 8=alpha9
BASE_GROUP_TEMPLATES = {
    "distributed_e": [
        [5, 7, 8],  # alpha6 alpha8 alpha9
        [0, 4, 2],  # alpha1 alpha5 alpha3
        [1, 3, 6],  # alpha2 alpha4 alpha7
    ],
    "high_frequency_pair": [
        [0, 4, 2],  # alpha1 alpha5 alpha3
        [1, 3, 6],  # alpha2 alpha4 alpha7
        [5, 7, 8],  # alpha6 alpha8 alpha9
    ],
    "specialized_machine": [
        [4, 0, 1],  # alpha5 alpha1 alpha2
        [5, 7, 8],  # alpha6 alpha8 alpha9
        [2, 3, 6],  # alpha3 alpha4 alpha7
    ],
}

PLAN_OUTPUTS = {
    "assignment_baseline.csv": {
        "selection_rule": "highest total score",
        "notes": "Primary candidate selected by weighted evaluation score.",
    },
    "assignment_balanced.csv": {
        "selection_rule": "best workload balance",
        "notes": "Chosen to minimize workload imbalance while keeping full component coverage.",
    },
    "assignment_feeder_friendly.csv": {
        "selection_rule": "best feeder continuity",
        "notes": "Chosen to minimize head-order feeder travel under fixed pick order.",
    },
}


def load_mapping(path=MAPPING_PATH):
    rows = []
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            components = [item.strip() for item in row["supported_components"].split(";") if item.strip()]
            rows.append({"head_type": row["head_type"], "components": components})
    return rows


def load_component_counts(path=PCB_PATH):
    counts = {}
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            component = row["component_type"]
            counts[component] = counts.get(component, 0) + 1
    return counts


def load_feeder_positions(path=FEEDERS_PATH):
    positions = {}
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            positions[row["component_type"]] = float(row["x_coord"])
    return positions


def mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def write_csv(path, fieldnames, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_assignment_rows(machine_layout, available_heads):
    available_head_set = set(available_heads)
    used_heads = set()
    rows = []

    for machine_id in MACHINE_IDS:
        heads = [available_heads[index] for index in machine_layout[machine_id]]
        for slot_index, head_type in enumerate(heads, start=1):
            if head_type not in available_head_set:
                raise ValueError(f"Unknown head_type in assignment: {head_type}")
            if head_type in used_heads:
                raise ValueError(f"Duplicate head_type in assignment: {head_type}")

            used_heads.add(head_type)
            rows.append(
                {
                    "machine_id": machine_id,
                    "head_slot": slot_index,
                    "head_type": head_type,
                }
            )

    if used_heads != available_head_set:
        missing_heads = sorted(available_head_set - used_heads)
        extra_heads = sorted(used_heads - available_head_set)
        raise ValueError(
            f"Assignment does not match mapping heads. Missing: {missing_heads}, Extra: {extra_heads}"
        )

    return rows


def estimate_head_center(components, feeder_positions, component_counts):
    weighted_sum = 0.0
    total_weight = 0.0
    for component in components:
        weight = component_counts.get(component, 0)
        weighted_sum += feeder_positions[component] * weight
        total_weight += weight

    if total_weight == 0:
        return mean([feeder_positions[component] for component in components])
    return weighted_sum / total_weight


def evaluate_plan(candidate_id, source_template, machine_layout, mapping_rows, feeder_positions, component_counts):
    head_by_index = {index: row for index, row in enumerate(mapping_rows)}
    machine_components = {}
    machine_workloads = {}
    machine_spans = []
    feeder_gaps = []
    e_head_counts = []
    specialization_counts = []

    for machine_id in MACHINE_IDS:
        indices = machine_layout[machine_id]
        head_rows = [head_by_index[index] for index in indices]
        covered_components = sorted(
            {component for head_row in head_rows for component in head_row["components"]}
        )
        machine_components[machine_id] = covered_components
        machine_workloads[machine_id] = sum(component_counts.get(component, 0) for component in covered_components)

        feeder_xs = [feeder_positions[component] for component in covered_components]
        machine_spans.append(max(feeder_xs) - min(feeder_xs))

        head_centers = [
            estimate_head_center(head_row["components"], feeder_positions, component_counts)
            for head_row in head_rows
        ]
        feeder_gaps.extend(
            abs(head_centers[position + 1] - head_centers[position])
            for position in range(len(head_centers) - 1)
        )

        e_head_counts.append(sum(1 for head_row in head_rows if "E" in head_row["components"]))
        specialization_counts.append(sum(1 for head_row in head_rows if len(head_row["components"]) <= 2))

    all_covered_components = {
        component for covered_components in machine_components.values() for component in covered_components
    }
    workload_values = list(machine_workloads.values())
    workload_range = max(workload_values) - min(workload_values)
    average_span = mean(machine_spans)
    average_gap = mean(feeder_gaps)
    e_balance_penalty = max(e_head_counts) - min(e_head_counts)
    specialization_bonus = max(specialization_counts)

    coverage_score = 100.0 if len(all_covered_components) == len(component_counts) else 0.0
    e_balance_score = clamp(100.0 - 30.0 * e_balance_penalty)
    workload_balance_score = clamp(100.0 - 2.0 * workload_range)
    feeder_order_score = clamp(100.0 - 12.0 * average_gap - 4.0 * average_span)
    specialization_score = clamp(55.0 + 15.0 * specialization_bonus)

    total_score = round(
        0.25 * coverage_score
        + 0.20 * e_balance_score
        + 0.25 * workload_balance_score
        + 0.20 * feeder_order_score
        + 0.10 * specialization_score,
        2,
    )

    return {
        "candidate_id": candidate_id,
        "source_template": source_template,
        "total_score": total_score,
        "coverage_score": round(coverage_score, 2),
        "e_balance_score": round(e_balance_score, 2),
        "workload_balance_score": round(workload_balance_score, 2),
        "feeder_order_score": round(feeder_order_score, 2),
        "specialization_score": round(specialization_score, 2),
        "estimated_workload_range": workload_range,
        "average_feeder_span": round(average_span, 2),
        "average_head_jump": round(average_gap, 2),
    }


def layout_signature(machine_layout):
    ordered = []
    for machine_id in MACHINE_IDS:
        ordered.append(tuple(machine_layout[machine_id]))
    return tuple(ordered)


def generate_candidate_layouts():
    candidates = []
    seen = set()

    for template_name, groups in BASE_GROUP_TEMPLATES.items():
        for machine_group_order in permutations(range(len(groups))):
            ordered_groups = [groups[index] for index in machine_group_order]
            for slot_orders in permutations(range(3)):
                machine_layout = {}
                for machine_id, group in zip(MACHINE_IDS, ordered_groups):
                    machine_layout[machine_id] = [group[index] for index in slot_orders]

                signature = layout_signature(machine_layout)
                if signature in seen:
                    continue

                seen.add(signature)
                candidates.append(
                    {
                        "source_template": template_name,
                        "machine_layout": machine_layout,
                    }
                )

    return candidates


def select_distinct_candidate(scored_candidates, key_name, used_signatures):
    for candidate in sorted(
        scored_candidates,
        key=lambda item: (
            item["metrics"][key_name],
            item["metrics"]["total_score"],
            -item["metrics"]["estimated_workload_range"],
        ),
        reverse=True,
    ):
        signature = layout_signature(candidate["machine_layout"])
        if signature not in used_signatures:
            used_signatures.add(signature)
            return candidate
    raise ValueError("Unable to find a distinct candidate for selection.")


def export_selected_plan(filename, selected_candidate, available_heads):
    rows = build_assignment_rows(selected_candidate["machine_layout"], available_heads)
    write_csv(INTERMEDIATE_DIR / filename, OUTPUT_COLUMNS, rows)
    return rows


def generate_all_assignments():
    mapping_rows = load_mapping()
    available_heads = [row["head_type"] for row in mapping_rows]
    feeder_positions = load_feeder_positions()
    component_counts = load_component_counts()

    raw_candidates = generate_candidate_layouts()
    scored_candidates = []

    for candidate_index, candidate in enumerate(raw_candidates, start=1):
        metrics = evaluate_plan(
            candidate_id=f"C{candidate_index:03d}",
            source_template=candidate["source_template"],
            machine_layout=candidate["machine_layout"],
            mapping_rows=mapping_rows,
            feeder_positions=feeder_positions,
            component_counts=component_counts,
        )
        scored_candidates.append(
            {
                "candidate_id": metrics["candidate_id"],
                "source_template": candidate["source_template"],
                "machine_layout": candidate["machine_layout"],
                "metrics": metrics,
            }
        )

    catalog_rows = [candidate["metrics"] for candidate in scored_candidates]
    catalog_rows.sort(key=lambda row: row["total_score"], reverse=True)
    write_csv(INTERMEDIATE_DIR / "assignment_candidate_catalog.csv", CATALOG_COLUMNS, catalog_rows)

    used_signatures = set()
    selections = {
        "assignment_baseline.csv": select_distinct_candidate(scored_candidates, "total_score", used_signatures),
        "assignment_balanced.csv": select_distinct_candidate(
            scored_candidates, "workload_balance_score", used_signatures
        ),
        "assignment_feeder_friendly.csv": select_distinct_candidate(
            scored_candidates, "feeder_order_score", used_signatures
        ),
    }

    baseline_rows = None
    evaluation_rows = []
    for filename, config in PLAN_OUTPUTS.items():
        selected_candidate = selections[filename]
        rows = export_selected_plan(filename, selected_candidate, available_heads)
        if filename == "assignment_baseline.csv":
            baseline_rows = rows

        metric_row = {
            "plan_name": filename,
            "source_template": selected_candidate["source_template"],
            "selection_rule": config["selection_rule"],
            "total_score": selected_candidate["metrics"]["total_score"],
            "coverage_score": selected_candidate["metrics"]["coverage_score"],
            "e_balance_score": selected_candidate["metrics"]["e_balance_score"],
            "workload_balance_score": selected_candidate["metrics"]["workload_balance_score"],
            "feeder_order_score": selected_candidate["metrics"]["feeder_order_score"],
            "specialization_score": selected_candidate["metrics"]["specialization_score"],
            "estimated_workload_range": selected_candidate["metrics"]["estimated_workload_range"],
            "average_feeder_span": selected_candidate["metrics"]["average_feeder_span"],
            "average_head_jump": selected_candidate["metrics"]["average_head_jump"],
            "notes": config["notes"],
        }
        evaluation_rows.append(metric_row)

    write_csv(DEFAULT_ASSIGNMENT_PATH, OUTPUT_COLUMNS, baseline_rows)
    evaluation_rows.sort(key=lambda row: row["total_score"], reverse=True)
    write_csv(INTERMEDIATE_DIR / "assignment_evaluation.csv", EVAL_COLUMNS, evaluation_rows)


if __name__ == "__main__":
    generate_all_assignments()
    print(f"Generated assignment plans and evaluation in {INTERMEDIATE_DIR}")
