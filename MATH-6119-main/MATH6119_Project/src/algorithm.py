"""
Author: 36842427
Date: 2026-05-11

PCB placement machine workplan generator.
Reads the input CSV files, including mapping.csv, feeders.csv,
pcb_positions.csv, and assignment.csv.

This script assigns each PCB component to a valid machine head based on the
attachment capability mapping and generates the final machine operation logs:

- data/output/machine_1_log.csv
- data/output/machine_2_log.csv
- data/output/machine_3_log.csv
"""

import csv
import math
from itertools import permutations
from pathlib import Path


project_root = Path(__file__).resolve().parent.parent
intermediate_dir = project_root / "data" / "intermediate"
output_dir = project_root / "data" / "output"

mapping_path = intermediate_dir / "mapping.csv"
feeders_path = intermediate_dir / "feeders.csv"
pcb_positions_path = intermediate_dir / "pcb_positions.csv"
assignment_path = intermediate_dir / "assignment.csv"

output_columns = ["step_id", "action", "component", "head_id", "x_coord", "y_coord"]
machine_order = ["M1", "M2", "M3"]
head_order = [1, 2, 3]
origin_point = (0.0, 0.0)


def read_csv_file(file_path):
    """Read a CSV file and return a list of dictionaries."""
    with Path(file_path).open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def load_mapping():
    """Load the attachment-to-component capability mapping."""
    mapping = {}

    for row in read_csv_file(mapping_path):
        head_type = row["head_type"].strip()
        supported_components = {
            component.strip()
            for component in row["supported_components"].split(";")
            if component.strip()
        }
        mapping[head_type] = supported_components

    return mapping


def load_feeders():
    """Load feeder coordinates for each component type."""
    feeders = {}

    for row in read_csv_file(feeders_path):
        component = row["component_type"].strip()
        x_coord = float(row["x_coord"])
        y_coord = float(row["y_coord"])
        feeders[component] = (x_coord, y_coord)

    return feeders


def load_pcb_positions():
    """Load every component position on the PCB."""
    pcb_positions = []

    for task_id, row in enumerate(read_csv_file(pcb_positions_path), start=1):
        pcb_positions.append(
            {
                "task_id": task_id,
                "component": row["component_type"].strip(),
                "x_coord": float(row["x_coord"]),
                "y_coord": float(row["y_coord"]),
            }
        )

    return pcb_positions


def load_assignment():
    """Load the P3 assignment of attachment heads to machines."""
    assignment = {machine_id: [] for machine_id in machine_order}

    for row in read_csv_file(assignment_path):
        machine_id = row["machine_id"].strip()
        head_slot = int(row["head_slot"])
        head_type = row["head_type"].strip()

        assignment.setdefault(machine_id, []).append(
            {
                "head_slot": head_slot,
                "head_type": head_type,
            }
        )

    for machine_id, heads in assignment.items():
        assignment[machine_id] = sorted(heads, key=lambda item: item["head_slot"])

    return assignment


def build_machine_heads(mapping, assignment):
    """Combine mapping and assignment into machine/head capabilities."""
    machine_heads = {}

    for machine_id, heads in assignment.items():
        machine_heads[machine_id] = []

        for head in heads:
            head_type = head["head_type"]

            if head_type not in mapping:
                raise ValueError(f"Unknown head_type in assignment.csv: {head_type}")

            machine_heads[machine_id].append(
                {
                    "machine_id": machine_id,
                    "head_slot": head["head_slot"],
                    "head_type": head_type,
                    "supported_components": mapping[head_type],
                }
            )

    return machine_heads


def estimate_single_task_cost(task, feeders):
    """Estimate a simple travel cost for workload balancing."""
    component = task["component"]
    feeder_point = feeders[component]
    pcb_point = (task["x_coord"], task["y_coord"])

    return (
        math.dist(origin_point, feeder_point)
        + math.dist(feeder_point, pcb_point)
        + math.dist(pcb_point, origin_point)
    )


def find_candidate_heads(component, machine_heads):
    """Find all machine heads that can process a component."""
    candidate_heads = []

    for machine_id in machine_order:
        for head in machine_heads[machine_id]:
            if component in head["supported_components"]:
                candidate_heads.append(head)

    return candidate_heads


def assign_tasks_to_heads(pcb_positions, feeders, machine_heads):
    """Assign every PCB component to a feasible machine head."""
    machine_load = {machine_id: 0.0 for machine_id in machine_order}
    head_load = {
        (head["machine_id"], head["head_slot"]): 0.0
        for machine_id in machine_order
        for head in machine_heads[machine_id]
    }

    def count_candidate_heads(task):
        return len(find_candidate_heads(task["component"], machine_heads))

    ordered_positions = sorted(
        pcb_positions,
        key=lambda task: (
            count_candidate_heads(task),
            -estimate_single_task_cost(task, feeders),
        ),
    )

    assigned_tasks = []

    for task in ordered_positions:
        component = task["component"]
        candidate_heads = find_candidate_heads(component, machine_heads)

        if not candidate_heads:
            raise ValueError(f"No feasible machine head for component: {component}")

        task_cost = estimate_single_task_cost(task, feeders)

        chosen_head = min(
            candidate_heads,
            key=lambda head: (
                machine_load[head["machine_id"]],
                head_load[(head["machine_id"], head["head_slot"])],
            ),
        )

        machine_id = chosen_head["machine_id"]
        head_id = chosen_head["head_slot"]

        machine_load[machine_id] += task_cost
        head_load[(machine_id, head_id)] += task_cost

        assigned_tasks.append(
            {
                "task_id": task["task_id"],
                "machine_id": machine_id,
                "head_id": head_id,
                "component": component,
                "x_coord": task["x_coord"],
                "y_coord": task["y_coord"],
            }
        )

    return assigned_tasks, machine_load, head_load


def choose_place_order(picked_tasks, last_pick_point):
    """Choose the shortest place order for up to three picked components."""
    if len(picked_tasks) <= 1:
        return picked_tasks

    best_order = None
    best_distance = None

    for place_order in permutations(picked_tasks):
        current_point = last_pick_point
        total_distance = 0.0

        for task in place_order:
            next_point = (task["x_coord"], task["y_coord"])
            total_distance += math.dist(current_point, next_point)
            current_point = next_point

        total_distance += math.dist(current_point, origin_point)

        if best_distance is None or total_distance < best_distance:
            best_distance = total_distance
            best_order = place_order

    return list(best_order)


def format_coord(value):
    """Write integer-looking coordinates without a decimal point."""
    numeric_value = float(value)

    if numeric_value.is_integer():
        return int(numeric_value)

    return round(numeric_value, 4)


def build_machine_log(machine_tasks, feeders):
    """Build PICK and PLACE rows for one machine."""
    tasks_by_head = {head_id: [] for head_id in head_order}

    for task in machine_tasks:
        tasks_by_head[task["head_id"]].append(task)

    for head_id in head_order:
        tasks_by_head[head_id].sort(key=lambda task: (task["y_coord"], task["x_coord"]))

    rows = []
    step_id = 1

    while any(tasks_by_head[head_id] for head_id in head_order):
        picked_tasks = []
        last_pick_point = origin_point

        for head_id in head_order:
            if tasks_by_head[head_id]:
                task = tasks_by_head[head_id].pop(0)
                component = task["component"]
                feeder_x, feeder_y = feeders[component]
                last_pick_point = (feeder_x, feeder_y)

                rows.append(
                    {
                        "step_id": step_id,
                        "action": "PICK",
                        "component": component,
                        "head_id": head_id,
                        "x_coord": format_coord(feeder_x),
                        "y_coord": format_coord(feeder_y),
                    }
                )
                step_id += 1
                picked_tasks.append(task)

        for task in choose_place_order(picked_tasks, last_pick_point):
            rows.append(
                {
                    "step_id": step_id,
                    "action": "PLACE",
                    "component": task["component"],
                    "head_id": task["head_id"],
                    "x_coord": format_coord(task["x_coord"]),
                    "y_coord": format_coord(task["y_coord"]),
                }
            )
            step_id += 1

    return rows


def write_machine_logs(assigned_tasks, feeders):
    """Write the three final P4 output files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks_by_machine = {machine_id: [] for machine_id in machine_order}

    for task in assigned_tasks:
        tasks_by_machine[task["machine_id"]].append(task)

    total_places = 0

    for machine_id in machine_order:
        machine_number = machine_id.replace("M", "")
        output_path = output_dir / f"machine_{machine_number}_log.csv"
        rows = build_machine_log(tasks_by_machine[machine_id], feeders)
        total_places += sum(1 for row in rows if row["action"] == "PLACE")

        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=output_columns)
            writer.writeheader()
            writer.writerows(rows)

        relative_path = output_path.relative_to(project_root)
        print(f"Generated {relative_path} with {len(rows)} rows")

    print(f"Total PLACE actions: {total_places}")


def print_summary(machine_heads, assigned_tasks, machine_load):
    """Print a short summary for checking and reporting."""
    print("\nMachine capabilities:")

    for machine_id in machine_order:
        supported_components = sorted(
            {
                component
                for head in machine_heads[machine_id]
                for component in head["supported_components"]
            }
        )
        print(f"{machine_id}: {supported_components}")

    print("\nAssigned task counts:")

    for machine_id in machine_order:
        task_count = sum(1 for task in assigned_tasks if task["machine_id"] == machine_id)
        estimated_load = machine_load[machine_id]
        print(f"{machine_id}: {task_count} tasks, estimated load = {estimated_load:.2f}")


def main():
    """Run the P4 baseline algorithm."""
    mapping = load_mapping()
    feeders = load_feeders()
    pcb_positions = load_pcb_positions()
    assignment = load_assignment()
    machine_heads = build_machine_heads(mapping, assignment)

    assigned_tasks, machine_load, head_load = assign_tasks_to_heads(
        pcb_positions=pcb_positions,
        feeders=feeders,
        machine_heads=machine_heads,
    )

    write_machine_logs(assigned_tasks, feeders)
    print_summary(machine_heads, assigned_tasks, machine_load)

    # Keep this variable referenced for readability during debugging.
    _ = head_load


if __name__ == "__main__":
    main()
