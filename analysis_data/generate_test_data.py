"""
generate_test_data.py --- 测试数据生成脚本
生成符合真实排队论非线性特征的多维度仿真测试数据。

用途：
  1. 为 ML 模型训练提供充足、高质量的模拟数据
  2. 模拟不同配置组合（窗口×座位×到达率）下的等待时间
  3. 嵌入符合二维（M/M/c 排队论近似）的非线性拥堵特征

数据维度：窗口 × 座位 × 到达率 = 1830 条记录
保存位置：simulation_history.db 的 simulation_runs 表
"""
import sqlite3
import math
import random
import numpy as np
import os



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ==================== 常量定义 ====================

# 数据库文件路径（与仿真系统共用）
DB_PATH = os.path.join(BASE_DIR, "backend", "simulation_history.db")

# 遍历参数范围
WINDOWS = [2, 3, 4, 5, 6, 8, 10, 12, 14, 15, 16, 18, 20, 24, 30]  # 15种窗口配置
SEATS   = list(range(50, 401, 25))                                    # 15种座位配置
ARRIVAL_RATES = [15, 20, 25, 30, 35, 40, 45, 50]                     #  8种到达率配置

# 固定仿真参数
SERVE_TIME = 30.0     # 固定打饭时间（秒）
EAT_TIME = 600.0      # 固定就餐时间（秒）
DURATION = 60         # 仿真时长（分钟）
SEED_BASE = 42        # 随机种子基础值


def init_db():
    """
    初始化数据库，创建仿真记录表

    如果表已存在则跳过，确保和仿真系统的表结构一致。
    表结构与 backend/app/main.py 中 init_db() 完全对齐。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT NOT NULL,
            random_seed INTEGER,
            window_count INTEGER,
            seat_count INTEGER,
            arrival_rate REAL,
            avg_serve_time REAL,
            avg_eat_time REAL,
            simulation_duration INTEGER,
            tick_step REAL,
            avg_wait_time REAL,
            throughput_total INTEGER,
            seat_turnover REAL,
            satisfaction_score REAL
        )
    ''')
    conn.commit()
    conn.close()


def simulate_nonlinear_wait(window: int, seat: int, arrival_rate: float) -> float:
    """
    用排队论近似公式模拟不同配置下的平均等待时间

    核心思路（M/M/c 排队论 + 非线性扰动）：
    1. 计算瓶颈荷载因子 ρ ：
       ρ = 到达率 / (窗口数 × 窗口服务速率)
       其中窗口服务速率 = 60秒/分 ÷ 打饭时间 = 60 ÷ 30 = 2人/分钟
    2. 当 ρ < 0.7 时，排队较轻松
    3. 当 ρ ≥ 0.85 时，系统接近饱和，等待时间非线性爆炸
    4. 座位压力：到达率越高，找座位越困难

    参数：
    - window:        窗口数量（个）
    - seat:          座位数量（个）
    - arrival_rate:  学生到达率（人/分钟）

    返回：
    - float: 模拟的平均等待时间（分钟）
    """
    # 窗口处理速率：2 人/分钟/窗口
    serve_rate_per_window = 60.0 / SERVE_TIME

    # === 1. 排队阶段（窗口瓶颈）===
    total_serve_rate = window * serve_rate_per_window  # 总服务速率
    rho = arrival_rate / total_serve_rate if total_serve_rate > 0 else 2.0  # 荷载因子

    # 排队冗余时间（M/M/c 近似）
    if rho < 0.85:
        # 低负载：温和线性增长
        queue_wait = max(0, rho * 3 + (arrival_rate / max(window, 1)) * 0.4)
    else:
        # 高负载：非线性爆炸增长（排队理论中当 ρ→1 时排队长度 →∞）
        queue_wait = max(0, 12 + (arrival_rate / max(window, 1)) * 3.5 + (rho - 0.85) * 30)

    # === 2. 座位瓶颈 ===
    # 座位上人速率：每小时每座接待 (3600/EAT_TIME) 人
    seat_serve_rate = 3600.0 / EAT_TIME           # 每人每小时
    max_eating_capacity = seat * seat_serve_rate   # 总就餐容量
    seat_pressure = max(0, (arrival_rate * 60) / max(max_eating_capacity, 1))

    # 座位排队：压力超过0.8时非线性增长
    if seat_pressure < 0.8:
        seat_wait = max(0, seat_pressure * 2 + (arrival_rate / max(seat, 1)) * 6)
    else:
        seat_wait = max(0, 8 + (arrival_rate / max(seat, 1)) * 12 + (seat_pressure - 0.8) * 20)

    # === 3. 综合等待时间 ===
    # 主要瓶颈取大，加上 15% 的交互效应
    base_wait = max(queue_wait, seat_wait) + 0.15 * min(queue_wait, seat_wait)

    # 添加符合现实的随机扰动（噪声标准差为基值的8%）
    noise = np.random.normal(0, max(0.5, base_wait * 0.08))
    final_wait = max(0, base_wait + noise)

    return round(final_wait, 2)


def generate_test_data():
    """
    生成测试数据并写入数据库

    遍历窗口数 × 座位数 × 到达率的所有组合，
    用排队论模型模拟每种配置下的等待时间，
    计算相关统计指标，写入 simulation_runs 表。
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    seed = SEED_BASE
    total_combinations = len(WINDOWS) * len(SEATS) * len(ARRIVAL_RATES)
    written = 0

    print(f"正在生成 {total_combinations} 条测试数据...")

    for window in WINDOWS:
        for seat in SEATS:
            for arrival_rate in ARRIVAL_RATES:
                # 跳过明显不合理的极端参数组合
                if seat < window * 3 or arrival_rate < 1:
                    continue

                # 模拟等待时间
                wait = simulate_nonlinear_wait(window, seat, arrival_rate)

                # 估算吞吐量 = 到达率 × 仿真时长（未拥挤时）
                potential_throughput = arrival_rate * DURATION
                throughput = int(min(potential_throughput, window * (60.0 / SERVE_TIME) * DURATION))

                # 座位周转率 = 完成人数 / (座位数 × 仿真小时数)
                seat_turnover = throughput / seat / (DURATION / 60.0) if seat > 0 else 0
                seat_turnover = round(seat_turnover, 2)

                # 满意度 = 1 - 等待/15，限制在 [0, 1] 范围内
                satisfaction = round(max(0.0, 1.0 - wait / 15.0), 3)

                # 写入数据库
                cursor.execute("""
                    INSERT INTO simulation_runs
                    (run_timestamp, random_seed, window_count, seat_count,
                     arrival_rate, avg_serve_time, avg_eat_time,
                     simulation_duration, tick_step, avg_wait_time,
                     throughput_total, seat_turnover, satisfaction_score)
                    VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, 0.1, ?, ?, ?, ?)
                """, (
                    seed, window, seat, arrival_rate,
                    SERVE_TIME, EAT_TIME, DURATION,
                    wait, throughput, seat_turnover, satisfaction
                ))
                seed += 1
                written += 1

    conn.commit()
    conn.close()
    print(f"数据生成完成，共写入 {written} 条记录到 {DB_PATH}")


# 命令行入口：直接运行此脚本即可生成测试数据
if __name__ == "__main__":
    generate_test_data()