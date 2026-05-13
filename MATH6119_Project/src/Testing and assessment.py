# -*- coding: utf-8 -*-
"""Author: 37652435
Date: 2026-05-13

Part 5 testing and assessment script.

This script checks the project input files, assignment strategy files,
and final machine operation logs. It verifies that the required CSV files
exist, confirms that all files use the expected column names, validates the
six P3 assignment strategies, compares their estimated workload and feeder
travel performance, and checks that all 102 PCB components are placed.

The script uses:
- mapping.csv
- feeders.csv
- pcb_positions.csv
- assignment_baseline.csv
- assignment_balanced.csv
- assignment_feeder_friendly.csv
- assignment_size_clustered.csv
- assignment_throughput.csv
- assignment_redundant.csv
- machine_1_log.csv
- machine_2_log.csv
- machine_3_log.csv
"""

from collections import Counter
from pathlib import Path
import math
import pandas as pd




BASE_DIR = Path("/content")

# All P3 assignment strategy files
ASSIGNMENT_FILES = [
    BASE_DIR / "assignment_baseline.csv",
    BASE_DIR / "assignment_balanced.csv",
    BASE_DIR / "assignment_feeder_friendly.csv",
    BASE_DIR / "assignment_size_clustered.csv",
    BASE_DIR / "assignment_throughput.csv",
    BASE_DIR / "assignment_redundant.csv",
]

# Core input files
MAPPING_FILE = BASE_DIR / "mapping.csv"
FEEDERS_FILE = BASE_DIR / "feeders.csv"
PCB_POSITIONS_FILE = BASE_DIR / "pcb_positions.csv"

# P4 output files
MACHINE_LOG_FILES = [
    BASE_DIR / "machine_1_log.csv",
    BASE_DIR / "machine_2_log.csv",
    BASE_DIR / "machine_3_log.csv",
]

# Checking all files exist
ALL_FILES = ASSIGNMENT_FILES + [
    MAPPING_FILE,
    FEEDERS_FILE,
    PCB_POSITIONS_FILE,
] + MACHINE_LOG_FILES

print("Checking uploaded files...\n")

for file_path in ALL_FILES:
    if file_path.exists():
        print(f"PASS: {file_path.name}")
    else:
        print(f"FAIL: {file_path.name} is missing")

import pandas as pd
from pathlib import Path

BASE_DIR = Path("/content")

ASSIGNMENT_FILES = [
    "assignment_baseline.csv",
    "assignment_balanced.csv",
    "assignment_feeder_friendly.csv",
    "assignment_size_clustered.csv",
    "assignment_throughput.csv",
    "assignment_redundant.csv",
]

MACHINE_LOG_FILES = [
    "machine_1_log.csv",
    "machine_2_log.csv",
    "machine_3_log.csv",
]

REQUIRED_COLUMNS = {
    "mapping.csv": ["head_type", "supported_components"],
    "feeders.csv": ["component_type", "x_coord", "y_coord"],
    "pcb_positions.csv": ["component_type", "x_coord", "y_coord"],
    "assignment": ["machine_id", "head_slot", "head_type"],
    "machine_log": ["step_id", "action", "component", "head_id", "x_coord", "y_coord"],
}

def check_columns(file_name, required_columns):
    file_path = BASE_DIR / file_name
    df = pd.read_csv(file_path)

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        return {
            "file": file_name,
            "status": "FAIL",
            "message": f"Missing columns: {missing_columns}",
            "actual_columns": list(df.columns)
        }

    return {
        "file": file_name,
        "status": "PASS",
        "message": "Correct columns",
        "actual_columns": list(df.columns)
    }

column_results = []

for file_name in ["mapping.csv", "feeders.csv", "pcb_positions.csv"]:
    column_results.append(check_columns(file_name, REQUIRED_COLUMNS[file_name]))

for file_name in ASSIGNMENT_FILES:
    column_results.append(check_columns(file_name, REQUIRED_COLUMNS["assignment"]))

for file_name in MACHINE_LOG_FILES:
    column_results.append(check_columns(file_name, REQUIRED_COLUMNS["machine_log"]))

column_df = pd.DataFrame(column_results)
display(column_df)

mapping_df = pd.read_csv(BASE_DIR / "mapping.csv")

def check_assignment_validity(file_name):
    df = pd.read_csv(BASE_DIR / file_name)

    expected_heads = set(mapping_df["head_type"].astype(str))
    actual_heads = set(df["head_type"].astype(str))

    machine_counts = df.groupby("machine_id")["head_type"].count().to_dict()

    valid_rows = len(df) == 9
    valid_machine_count = df["machine_id"].nunique() == 3
    valid_unique_heads = df["head_type"].nunique() == 9
    valid_all_heads_used = actual_heads == expected_heads
    valid_three_heads_each = all(count == 3 for count in machine_counts.values())

    is_valid = all([
        valid_rows,
        valid_machine_count,
        valid_unique_heads,
        valid_all_heads_used,
        valid_three_heads_each,
    ])

    return {
        "strategy_file": file_name,
        "valid_assignment": is_valid,
        "rows": len(df),
        "machines": df["machine_id"].nunique(),
        "unique_heads": df["head_type"].nunique(),
        "three_heads_each_machine": valid_three_heads_each,
        "machine_head_counts": machine_counts,
    }

validity_results = [
    check_assignment_validity(file_name)
    for file_name in ASSIGNMENT_FILES
]

validity_df = pd.DataFrame(validity_results)
display(validity_df)

from collections import Counter
import pandas as pd

# Loading core files
mapping_df = pd.read_csv(BASE_DIR / "mapping.csv")
feeders_df = pd.read_csv(BASE_DIR / "feeders.csv")
pcb_df = pd.read_csv(BASE_DIR / "pcb_positions.csv")

# Converting mapping into dictionary:
mapping = {
    row["head_type"]: [
        component.strip()
        for component in str(row["supported_components"]).split(";")
        if component.strip()
    ]
    for _, row in mapping_df.iterrows()
}

# Converting feeder x-coordinates into dictionary:
feeders = {
    row["component_type"]: float(row["x_coord"])
    for _, row in feeders_df.iterrows()
}

# Counting how many times each component appears on the PCB
component_counts = Counter(pcb_df["component_type"])


def average_feeder_x(head_type):
    """
    Estimate the average feeder x-position for one attachment head.
    """
    supported_components = mapping[head_type]
    x_values = [
        feeders[component]
        for component in supported_components
        if component in feeders
    ]

    return sum(x_values) / len(x_values)


def estimate_workload(machine_heads):
    """
    Estimate workload by summing the PCB frequencies of all components
    that the machine's attachment heads can process.
    """
    total = 0

    for head in machine_heads:
        for component in mapping[head]:
            total += component_counts.get(component, 0)

    return total


def estimate_pick_travel(machine_heads):
    """
    Estimate feeder-pick travel using the fixed head order:
    head 1 -> head 2 -> head 3.

    The machine begins at x = 0 and visits the average feeder location
    associated with each attachment.
    """
    x_positions = [average_feeder_x(head) for head in machine_heads]

    travel = abs(x_positions[0] - 0)
    travel += abs(x_positions[1] - x_positions[0])
    travel += abs(x_positions[2] - x_positions[1])

    return travel


def assess_strategy(file_name):
    df = pd.read_csv(BASE_DIR / file_name)

    machine_workloads = {}
    machine_pick_travel = {}

    for machine_id in sorted(df["machine_id"].unique()):
        machine_df = df[df["machine_id"] == machine_id].sort_values("head_slot")
        machine_heads = list(machine_df["head_type"])

        machine_workloads[machine_id] = estimate_workload(machine_heads)
        machine_pick_travel[machine_id] = estimate_pick_travel(machine_heads)

    workload_gap = max(machine_workloads.values()) - min(machine_workloads.values())
    total_pick_travel = sum(machine_pick_travel.values())

    # Lower estimated score is better.
    estimated_score = workload_gap + total_pick_travel

    return {
        "strategy_file": file_name,
        "M1_workload": machine_workloads.get("M1", 0),
        "M2_workload": machine_workloads.get("M2", 0),
        "M3_workload": machine_workloads.get("M3", 0),
        "workload_gap": workload_gap,
        "M1_pick_travel": round(machine_pick_travel.get("M1", 0), 2),
        "M2_pick_travel": round(machine_pick_travel.get("M2", 0), 2),
        "M3_pick_travel": round(machine_pick_travel.get("M3", 0), 2),
        "total_pick_travel": round(total_pick_travel, 2),
        "estimated_score": round(estimated_score, 2),
    }


strategy_results = [
    assess_strategy(file_name)
    for file_name in ASSIGNMENT_FILES
]

strategy_df = pd.DataFrame(strategy_results)
strategy_df = strategy_df.sort_values("estimated_score").reset_index(drop=True)

display(strategy_df)

print("Recommended strategy:")
print(strategy_df.iloc[0]["strategy_file"])
print("Estimated score:", strategy_df.iloc[0]["estimated_score"])

MACHINE_LOG_FILES = [
    "machine_1_log.csv",
    "machine_2_log.csv",
    "machine_3_log.csv",
]

def check_machine_logs():
    results = []
    total_pick = 0
    total_place = 0

    for file_name in MACHINE_LOG_FILES:
        df = pd.read_csv(BASE_DIR / file_name)

        pick_count = len(df[df["action"] == "PICK"])
        place_count = len(df[df["action"] == "PLACE"])
        invalid_actions = set(df["action"]) - {"PICK", "PLACE"}

        total_pick += pick_count
        total_place += place_count

        if invalid_actions:
            status = "FAIL"
            message = f"Invalid actions found: {invalid_actions}"
        else:
            status = "PASS"
            message = "Only PICK and PLACE actions used"

        results.append({
            "file": file_name,
            "status": status,
            "pick_count": pick_count,
            "place_count": place_count,
            "message": message,
        })

    return pd.DataFrame(results), total_pick, total_place


log_df, total_pick, total_place = check_machine_logs()

display(log_df)

print("Total PICK actions:", total_pick)
print("Total PLACE actions:", total_place)
print("Expected PLACE actions:", len(pcb_df))

if total_place == len(pcb_df):
    print("PASS: Every PCB component has been placed.")
else:
    print("FAIL: PLACE count does not match PCB component count.")