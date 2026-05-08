# MATH-6119

## 1. 项目目录结构规范 (请大家严格遵守)
所有代码请**统一使用相对路径**读取和保存文件


MATH6119_Group_Project/
│
├── data/                      # 存放所有CSV数据
│   ├── raw/                   # 原始数据 (老师发的最原始文件：MATH6119-PCB Component Layout.csv)
│   │
│   ├── intermediate/          # 核心中间数据枢纽 (供读取和交接)
│   │   ├── mapping.csv        # P2 产出: 附件与元件的对应关系
│   │   ├── feeders.csv        # P2 产出: 料盘（喂料器）的物理坐标
│   │   ├── pcb_positions.csv  # P2 产出: PCB 上每个元件的具体位置
│   │   └── assignment.csv     # P3 产出: 9个附件分配到3台机的方案
│   │
│   └── output/                # 最终交付物
│       ├── machine_1_log.csv  # P4 产出: 机器1的操作序列
│       ├── machine_2_log.csv  # P4 产出: 机器2的操作序列
│       └── machine_3_log.csv  # P4 产出: 机器3的操作序列
│
├── src/                       # 核心业务源代码
│   ├── data_processing.py     # P2 的代码
│   ├── algorithm.py           # P3, P4 的代码
│   └── validator.py           # P1 的一键检查脚本
│
├── tests/                     # 测试代码大本营
│   ├── test_data_processing.py # P5 测试 P2 脚本
│   └── test_algorithm.py       # P5 测试 P3/P4 脚本
│
├── docs/                      # 存放报告(Report)和会议纪要(Minutes)
├── README.md                  # 项目说明文档与规范清单
├── requirements.txt           # Python依赖包列表 (如 pandas, pytest)


## 2. CSV 文件与列名规范（重点！）

为了保证各模块代码能无缝对接，请所有人严格遵守以下文件命名和列名规范：

###  A. 中间数据 (P2 & P3 产出，供 P4 读取)
统一存放在 `data/intermediate/` 目录下：

1. **`mapping.csv` (附件与元件对应关系)**
   - **列名必须为**: `head_type`, `supported_components`
2. **`feeders.csv` (料盘物理坐标)**
   - **列名必须为**: `component_type`, `x_coord`, `y_coord`
3. **`pcb_positions.csv` (PCB 上每个元件的位置)**
   - **列名必须为**: `component_type`, `x_coord`, `y_coord`
4. **`assignment.csv` (9个附件分配到3台机的方案)**
   - **列名必须为**: `machine_id`, `head_slot`, `head_type`

B. 最终机器日志 (P4 产出，最终交付物)
统一存放在 `data/output/` 目录下，文件必须严格命名为 `machine_1_log.csv`, `machine_2_log.csv`, `machine_3_log.csv`。
**列名必须严格为**: `step_id`, `action`, `component`, `head_id`, `x_coord`, `y_coord`
- **字段说明**:
  - `step_id`: 操作序号（1, 2, 3...）
  - `action`: 必须是大写的 `PICK` (拾取) 或 `PLACE` (放置)
  - `component`: 元件类型 (A-J)
  - `head_id`: 使用的安装头编号 (1-9)
  - `x_coord` / `y_coord`: 机器移动的目标坐标

3. Python 代码与开发规范 

为了保证大家的代码能够顺利合并并让老师/助教看懂，请所有人遵守以下 Python 编写规范：

### A. 命名规范 
- **禁止使用拼音**：所有变量、函数、文件名**必须使用英文**（严禁出现 `jisuan_juli` 这种命名）。
- **变量与函数名**：统一使用小写字母加下划线）。
  - 正确：`calculate_distance()`, `head_type`
  - 错误：`CalculateDistance()`, `headType`
- **类名 **：如果有用到面向对象编程，类名统一使用大驼峰式。
  - 正确：`MachineOptimizer`, `ComponentTask`

###  B. 如果用到了除了 Python 自带库以外的第三方包（如 pandas, numpy, pytest），必须告诉 p1，p1会统一把这些包写进 requirements.txt 文件里，保证大家运行的环境是一致的。如果有新包，每人第一件事是在终端里运行 pip install -r requirements.txt。这样咱们所有人的 pandas 版本就统一了。

### C. 所有组员可根据validator.py脚本确认是否符合csv文件规范，当结果是：
=== 1. Check the input file (P2/P3) ===  #缺少列名或拼写错误---->Missing column name. 缺少文件-------->File not found
data/intermediate/mapping.csv Listed correctly
data/intermediate/feeders.csv Listed correctly
data/intermediate/pcb_positions.csv Listed correctly
data/intermediate/assignment.csv Listed correctly

=== 2. Check the output file (P4) ===.   #方案有问题----->fail
data/output/machine_1_log.csv Listed correctly
data/output/machine_2_log.csv Listed correctly
data/output/machine_3_log.csv Listed correctly
------------------------------
Total Number of PLACE Actions: 102
pass

说明是正确。



