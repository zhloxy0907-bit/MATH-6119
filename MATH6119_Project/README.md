# MATH-6119

## 1. Project Directory Structure Guidelines (Please adhere strictly to these guidelines)
Please ensure that all code **uses relative paths** when reading and saving files.


MATH6119_Group_Project/
│
├── data/                      # Store all CSV data
│   ├── raw/                   # Raw data (MATH6119-PCB Component Layout.csv)
│   │
│   ├── intermediate/          # Core data hub (for reading and handover)
│   │   ├── mapping.csv        # P2 Output: Correspondence between attachments and components
│   │   ├── feeders.csv        # P2 Output: Physical coordinates of the feed tray (feeder)
│   │   ├── pcb_positions.csv  # P2 Output: The specific location of each component on the PCB
│   │   └── assignment.csv   # P3 Output:A plan for distributing 9 attachments across 3 machines
│   │
│   └── output/                # Final deliverables
│       ├── machine_1_log.csv  # P4 Output: Operation sequence for Machine 1
│       ├── machine_2_log.csv  # P4 Output: Operation sequence for Machine 2
│       └── machine_3_log.csv  # P4 Output: Operation sequence for Machine 3
│
├── src/                       # Core business source code
│   ├── data_processing.py     # The code for P2
│   ├── algorithm.py           # The code for P3 and P4
│   └── validator.py           # P1's one-click check script
│
├── tests/                     # The Hub for Test Code
│   ├── test_data_processing.py # P5 Testing the P2 script
│   └── test_algorithm.py       # P5 Testing the P3/P4 script
│
├── docs/                      # Archive reports and minutes
├── README.md                  # Project Description Document and Specification List
├── requirements.txt           # List of Python dependency packages (e.g. pandas, pytest)


## 2. CSV files and column name conventions (Important!)

To ensure that code from different modules integrates seamlessly, everyone is requested to strictly adhere to the following file and column naming conventions:

###  A.Intermediate data (outputs from P2 and P3, for reading by P4)
Stored centrally in the `data/intermediate/` directory:

1. **`mapping.csv` (Mapping of attachments to components)**
   - **The list must be**: `head_type`, `supported_components`

2. **`feeders.csv` (Physical coordinates of the material tray)**
   - **The list must be**: `component_type`, `x_coord`, `y_coord`

3. **`pcb_positions.csv` (The position of each component on the PCB)**
   - **The list must be**: `component_type`, `x_coord`, `y_coord`

4. **`assignment.csv` (A plan for distributing 9 attachments across 3 machines)**
   - **The list must be**: `machine_id`, `head_slot`, `head_type`

B. Final machine logs (P4 deliverables, final deliverables)
stored in one place `data/output/` Within the directory, files must be named exactly as follows: `machine_1_log.csv`, `machine_2_log.csv`, `machine_3_log.csv`。
**The list must strictly consist of**: `step_id`, `action`, `component`, `head_id`, `x_coord`, `y_coord`
- **Field descriptions**:
  - `step_id`: Operation number（1, 2, 3...）
  - `action`: It must be `PICK` (pick) or `PLACE` (place) in uppercase
  - `component`: Component type (A-J)
  - `head_id`: Installation head number used (1-9)
  - `x_coord` / `y_coord`: The target coordinates for the machine’s movement

3. Python Code and Development Guidelines

To ensure that everyone’s code can be merged smoothly and is understandable to the lecturer and teaching assistants, please adhere to the following Python coding conventions:

### A. Naming conventions 
- **The use of Pinyin is prohibited**：All variables, functions and filenames **must be in English** (names such as `jisuan_juli` are strictly prohibited).
- **Variable and function names**: Use lowercase letters followed by an underscore.
  - Correct：`calculate_distance()`, `head_type`
  - Error：`CalculateDistance()`, `headType`

- **Class names**: If object-oriented programming is used, class names should consistently follow the camelCase convention.
  - Correct：`MachineOptimizer`, `ComponentTask`

###  B. If you use any third-party packages other than Python’s built-in libraries (such as pandas, numpy or pytest), you must inform p1. p1 will then add these packages to the requirements.txt file, ensuring that everyone’s environment is consistent. If a new package is introduced, the first thing everyone should do is run `pip install -r requirements.txt` in the terminal. This will ensure that everyone is using the same version of pandas.

### C. All team members can use the `validator.py` script to check whether the file complies with the CSV specifications. If the result is:
=== 1. Check the input file (P2/P3) ===  #Missing column name or spelling error---->Missing column name. File missing-------->File not found
data/intermediate/mapping.csv Listed correctly
data/intermediate/feeders.csv Listed correctly
data/intermediate/pcb_positions.csv Listed correctly
data/intermediate/assignment.csv Listed correctly

=== 2. Check the output file (P4) ===.   #There is a problem with the plan----->fail
data/output/machine_1_log.csv Listed correctly
data/output/machine_2_log.csv Listed correctly
data/output/machine_3_log.csv Listed correctly
------------------------------
Total Number of PLACE Actions: 102
pass

The explanation is correct.


