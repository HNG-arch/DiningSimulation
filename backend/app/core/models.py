
"""
数据模型模块
北京交大食堂就餐仿真系统 - 数据模型定义与共享常量

本模块定义了仿真系统中使用的所有数据结构，包括：
1. 仿真配置参数模型 (ConfigParams)
2. 窗口状态模型 (WindowState)
3. 座位矩阵模型 (SeatMatrix)
4. 学生记录模型 (StudentRecord)
5. 统计结果模型 (Statistics)
6. 成本分析模型 (CostBreakdown)
7. 成本参数常量 (COST_PER_WINDOW 等)
8. 数据库路径与数据加载工具函数
9. 成本计算工具函数 (calculate_cost / calculate_cost_tuple)

所有模型类均使用 Pydantic V2 进行数据验证和序列化。
"""
import sqlite3
import os
from typing import List, Optional
from pydantic import BaseModel, Field

# ==================== 数据库与成本常量 ====================

# 数据库文件路径，位于 backend/data/simulation_history.db
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "simulation_history.db")
DB_PATH = os.path.abspath(DB_PATH)

# 每个窗口的每日运营成本（元/天），含人工、水电、设备折旧
COST_PER_WINDOW = 300
# 每个座位的每日摊销成本（元/天），含桌椅折旧、清洁维护
COST_PER_SEAT = 5
# 学生每等待1分钟的隐性口碑惩罚成本（元/分钟）
PENALTY_PER_MINUTE = 80


def load_all_results() -> list:
    """
    从 SQLite 数据库加载所有仿真运行记录

    查询 simulation_runs 表，按 id 倒序排列，
    返回最近运行在最前面的列表。

    返回：
    - list[dict]: 每条记录是一个字典，包含所有仿真字段
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM simulation_runs ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def calculate_cost(window_count: int, seat_count: int, avg_wait_time: float) -> dict:
    """
    计算食堂配置的综合运营成本

    总成本 = 运营硬件成本 + 学生等待惩罚成本
    - 运营硬件成本 = 窗口数 × 窗口单价 + 座位数 × 座位单价
    - 惩罚成本 = 平均等待时间 × 每分钟惩罚系数

    参数：
    - window_count: 窗口数量（个）
    - seat_count: 座位数量（个）
    - avg_wait_time: 平均等待时间（分钟），可为 None

    返回：
    - dict: 包含 total/operating/penalty/window_cost/seat_cost 五项
    """
    op_cost = (window_count * COST_PER_WINDOW) + (seat_count * COST_PER_SEAT)
    penalty = (avg_wait_time or 0) * PENALTY_PER_MINUTE
    total = op_cost + penalty
    return {
        "total": round(float(total), 0),
        "operating": round(float(op_cost), 0),
        "penalty": round(float(penalty), 0),
        "window_cost": int(window_count * COST_PER_WINDOW),
        "seat_cost": int(seat_count * COST_PER_SEAT)
    }


def calculate_cost_tuple(window: int, seat: int, wait_time: float) -> tuple:
    """
    计算综合成本（元组形式返回）

    与 calculate_cost() 功能相同，但返回三元组，
    便于机器学习网格搜索时的数值比较。

    参数：
    - window: 窗口数量（个）
    - seat: 座位数量（个）
    - wait_time: 预计等待时间（分钟）

    返回：
    - tuple: (总成本, 运营成本, 惩罚成本)
    """
    op_cost = (window * COST_PER_WINDOW) + (seat * COST_PER_SEAT)
    penalty = (wait_time or 0) * PENALTY_PER_MINUTE
    return op_cost + penalty, op_cost, penalty


# ==================== 仿真配置模型 ====================

class ConfigParams(BaseModel):
    """仿真配置参数类，定义一次仿真运行的所有输入参数"""
    window_count: int = Field(default=5, description="打饭窗口数量（个）", ge=1)
    seat_count: int = Field(default=100, description="就餐座位数量（个）", ge=1)
    arrival_rate: float = Field(default=20.0, description="学生到达率（人/分钟）", gt=0)
    avg_serve_time: float = Field(default=30.0, description="平均打饭时间（秒）", gt=0)
    avg_eat_time: float = Field(default=600.0, description="平均就餐时间（秒）", gt=0)
    simulation_duration: int = Field(default=60, description="仿真总时长（分钟）", gt=0)
    serve_time_std: Optional[float] = Field(default=None, description="打饭时间标准差（秒），默认使用均值的20%")
    eat_time_std: Optional[float] = Field(default=None, description="就餐时间标准差（秒），默认使用均值的20%")
    random_seed: Optional[int] = Field(default=None, description="随机种子，None每次不同，指定整数可复现结果")
    tick_step: float = Field(default=0.1, description="仿真时间步长（分钟）", gt=0)
    tick_delay: float = Field(default=0.1, description="每步实际延迟（秒），用于前端可视化动画", ge=0)
    student_count: int = Field(default=0, description="学生总数上限，0表示不限制", ge=0)


# ==================== 仿真运行时状态模型 ====================

class WindowState(BaseModel):
    """打饭窗口实时状态模型，记录每个窗口的当前服务情况"""
    window_id: int = Field(description="窗口唯一编号，从0开始")
    queue_length: int = Field(default=0, description="当前排在窗口前的学生数")
    serve_time_left: float = Field(default=0.0, description="当前学生剩余打饭时间（秒），0表示空闲")
    total_served: int = Field(default=0, description="累计完成服务的学生数")


class SeatMatrix(BaseModel):
    """座位矩阵模型，二维网格表示食堂座位占用情况"""
    rows: int = Field(description="座位矩阵行数")
    cols: int = Field(description="座位矩阵列数")
    data: List[List[int]] = Field(description="每个座位的剩余就餐秒数，0为空座位")


class StudentRecord(BaseModel):
    """学生就餐全流程记录模型，追踪每个学生的完整动线"""
    id: int = Field(description="学生唯一编号")
    arrive_time: float = Field(description="到达食堂的时间（分钟）")
    enter_queue_time: float = Field(default=0.0, description="开始排队的时间（分钟）")
    start_eat_time: float = Field(default=0.0, description="找到座位开始就餐的时间（分钟）")
    leave_time: float = Field(default=0.0, description="完成就餐离开的时间（分钟）")
    selected_window: int = Field(default=-1, description="选择的窗口编号，-1表示未分配")
    wait_time: float = Field(default=0.0, description="总等待时间（分钟），排队+等座")


# ==================== 统计与成本结果模型 ====================

class Statistics(BaseModel):
    """仿真统计结果模型，汇总一次仿真运行的核心指标"""
    avg_wait_time: float = Field(description="学生平均等待时间（分钟）")
    throughput_per_window: List[int] = Field(description="每个窗口的累计服务人数")
    seat_turnover: float = Field(description="座位周转率（次/小时）")
    satisfaction_score: float = Field(description="学生满意度评分（0~1），基于等待时间计算")
    time_series: List[dict] = Field(description="时间序列数据，每个时间步的统计快照")


class CostBreakdown(BaseModel):
    """成本分析明细模型，将综合成本拆分为运营成本和惩罚成本"""
    total: float = Field(description="综合总成本（元/天）= 运营成本 + 惩罚成本")
    operating: float = Field(description="运营硬件成本（元/天）= 窗口成本 + 座位成本")
    penalty: float = Field(description="学生等待惩罚成本（元/天）")
    window_cost: int = Field(description="窗口运营成本细项（元/天）")
    seat_cost: int = Field(description="座位摊销成本细项（元/天）")
