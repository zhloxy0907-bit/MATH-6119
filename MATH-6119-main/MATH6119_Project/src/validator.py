import csv
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)


input_files = {
    "data/intermediate/mapping.csv": ["head_type", "supported_components"],
    "data/intermediate/feeders.csv": ["component_type", "x_coord", "y_coord"],
    "data/intermediate/pcb_positions.csv": ["component_type", "x_coord", "y_coord"],
    "data/intermediate/assignment.csv": ["machine_id", "head_slot", "head_type"]
}

output_files = [
    "data/output/machine_1_log.csv",
    "data/output/machine_2_log.csv",
    "data/output/machine_3_log.csv"
]
output_cols = ['step_id', 'action', 'component', 'head_id', 'x_coord', 'y_coord']

def check_csv_columns(relative_path, required_cols):
    abs_path = os.path.join(project_root , relative_path)
    
    if not os.path.exists(abs_path):
        return f"File not found: {abs_path}"
    
    with open(abs_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            cols = next(reader) 
        except StopIteration:
            return f"{abs_path} is an empty file!"
            
    missing = [c for c in required_cols if c not in cols]
    if missing:
        return f"{abs_path} Missing column name: {missing}"
    return f"{relative_path} Listed correctly"

def check_final_results():
    """Check whether all 102 core components have been placed"""
    total_places = 0
    for relative_path in output_files:
        abs_path = os.path.join(project_root , relative_path)
        
        if not os.path.exists(abs_path):
            print(f" Cannot find the output file: {abs_path}")
            return False
            
        # Check the column names in the output file
        print(check_csv_columns(relative_path, output_cols))
        
        # Count the number of PLACE entries 
        with open(abs_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('action') == 'PLACE':
                    total_places += 1
                    
    print("-" * 30)
    print(f"Total Number of PLACE Actions: {total_places}")
    if total_places == 102:
        print("pass")
        return True
    else:
        print("fail")
        return False


if __name__ == "__main__":
    print("=== 1. Check the input file (P2/P3) ===")
    for path, cols in input_files.items():
        print(check_csv_columns(path, cols))
        
    print("\n=== 2. Check the output file (P4) ===")
    check_final_results()