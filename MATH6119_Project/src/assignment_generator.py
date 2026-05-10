"""
Author: 36938912
Date: 2026-05-10

PCB placement machine assignment generator.
Reads mapping.csv and generates multiple assignment plans.
"""

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTERMEDIATE_DIR = PROJECT_ROOT / "data" / "intermediate"
MAPPING_PATH = INTERMEDIATE_DIR / "mapping.csv"
DEFAULT_OUTPUT_PATH = INTERMEDIATE_DIR / "assignment.csv"
OUTPUT_COLUMNS = ["machine_id", "head_slot", "head_type"]

# Head order in mapping.csv:
# 0=α1, 1=α2, 2=α3, 3=α4, 4=α5, 5=α6, 6=α7, 7=α8, 8=α9
ASSIGNMENT_PLANS = {
    "assignment_baseline.csv": {
        "M1": [5, 7, 8],  # α6 α8 α9
        "M2": [0, 4, 2],  # α1 α5 α3
        "M3": [1, 3, 6],  # α2 α4 α7
    },
    "assignment_balanced.csv": {
        "M1": [0, 4, 2],  # α1 α5 α3
        "M2": [1, 3, 6],  # α2 α4 α7
        "M3": [5, 7, 8],  # α6 α8 α9
    },
    "assignment_feeder_friendly.csv": {
        "M1": [5, 7, 8],  # α6 α8 α9
        "M2": [2, 0, 4],  # α3 α1 α5
        "M3": [3, 1, 6],  # α4 α2 α7
    },
}


def load_available_heads(path=MAPPING_PATH):
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [row["head_type"] for row in reader]


def build_assignment_rows(machine_layout, available_heads):
    available_head_set = set(available_heads)
    used_heads = set()
    rows = []

    for machine_id, indices in machine_layout.items():
        heads = [available_heads[index] for index in indices]
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


def write_assignment(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def generate_all_assignments():
    available_heads = load_available_heads()

    for filename, machine_layout in ASSIGNMENT_PLANS.items():
        rows = build_assignment_rows(machine_layout, available_heads)
        write_assignment(INTERMEDIATE_DIR / filename, rows)

    baseline_rows = build_assignment_rows(
        ASSIGNMENT_PLANS["assignment_baseline.csv"], available_heads
    )
    write_assignment(DEFAULT_OUTPUT_PATH, baseline_rows)


if __name__ == "__main__":
    generate_all_assignments()
    print(f"Generated assignment plans in {INTERMEDIATE_DIR}")
