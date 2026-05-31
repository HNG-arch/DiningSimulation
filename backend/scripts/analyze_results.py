"""
analyze_results.py --- 离散事件仿真分析脚本
基于随机森林构建预测模型，并结合运筹学进行最低成本网格搜索寻优。

用途：独立于 Web API 运行的离线分析工具，适合在命令行下进行批量实验。
与 backend/app/core/analysis.py 的关系：
  - 本文件是独立的本地脚本，定义了自己的成本常量和计算函数
  - 后端 API 中对应的逻辑位于 backend/app/core/analysis.py
  - 两者功能等价但运行环境不同，本脚本不需要启动 FastAPI
"""
import os
import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# 数据库文件路径，指向 backend/data/
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "simulation_history.db")

# ==================== 决策核心成本参数 ====================

# 每个窗口的每日运营成本（元/天），含人工、水电、设备折旧
COST_PER_WINDOW = 300
# 每个座位的每日摊销成本（元/天），含桌椅折旧、清洁维护
COST_PER_SEAT = 5
# 学生每等待 1 分钟的隐性口碑惩罚成本（元/分钟）
# 数值越高说明对排队拥挤越敏感
PENALTY_PER_MINUTE = 80


def load_data() -> pd.DataFrame:
    """
    从 SQLite 数据库加载所有仿真运行记录

    读取 simulation_runs 表的所有行，
    返回包含全部字段的 pandas DataFrame。

    返回：
    - pd.DataFrame: 仿真历史数据
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM simulation_runs", conn)
    conn.close()
    return df


def train_model() -> tuple:
    """
    训练随机森林回归模型，用于预测平均等待时间

    从数据库中读取所有仿真记录作为训练数据，
    用5个关键特征预测 avg_wait_time 目标变量。

    特征列：
    - window_count:  窗口数量
    - seat_count:    座位数量
    - arrival_rate:  学生到达率（人/分钟）
    - avg_serve_time: 平均打饭时间（秒）
    - avg_eat_time:   平均就餐时间（秒）

    返回：
    - tuple: (训练好的模型对象, 特征列名列表)
    """
    df = load_data()
    # 训练用特征列
    features = ['window_count', 'seat_count', 'arrival_rate', 'avg_serve_time', 'avg_eat_time']
    X = df[features]                # 特征矩阵
    y = df['avg_wait_time']         # 目标变量：平均等待时间

    # 创建随机森林回归器：100棵决策树，最大深度10，固定随机种子42确保可复现
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X, y)
    return model, features


def calculate_cost(window: int, seat: int, wait_time: float) -> tuple:
    """
    计算指定配置的综合运营成本

    总成本 = 运营硬件成本 + 学生等待惩罚成本
    - 运营硬件成本 = 窗口数 × 窗口单价 + 座位数 × 座位单价
    - 等待惩罚成本 = 平均等待时间 × 每分钟惩罚系数

    参数：
    - window:    窗口数量（个）
    - seat:      座位数量（个）
    - wait_time: 预计平均等待时间（分钟）

    返回：
    - tuple: (总成本, 运营成本, 惩罚成本)
    """
    op_cost = (window * COST_PER_WINDOW) + (seat * COST_PER_SEAT)
    penalty = wait_time * PENALTY_PER_MINUTE
    return op_cost + penalty, op_cost, penalty


def optimize_config(model, features: list, target_arrival: float,
                    serve_time: float, eat_time: float) -> dict:
    """
    网格搜索寻找最优配置（最低综合成本）

    在合理的参数空间内穷举搜索：
    - 窗口数: 5 ~ 29（25个取值）
    - 座位数: 100 ~ 580, 步长20（25个取值）
    对每个 (窗口, 座位) 组合用模型预测等待时间，计算综合成本。

    参数：
    - model:          训练好的随机森林模型
    - features:       特征列名列表
    - target_arrival: 目标到达率（人/分钟）
    - serve_time:     打饭时间（秒）
    - eat_time:       就餐时间（秒）

    返回：
    - dict: 最优配置 {window, seat, wait, total_cost, op_cost, penalty}
    """
    # 初始化最优值为无穷大
    best_cost = float('inf')
    best_config = {}

    # 构建搜索网格：25 × 25 = 625 个组合
    test_cases = []
    for w in range(5, 30):            # 窗口数从 5 到 29
        for s in range(100, 600, 20):  # 座位数从 100 到 580
            test_cases.append([w, s, target_arrival, serve_time, eat_time])

    # 批量预测所有组合的等待时间
    test_df = pd.DataFrame(test_cases, columns=features)
    preds = model.predict(test_df)

    # 遍历所有组合，寻找最低成本
    for i, row in enumerate(test_cases):
        w, s = row[0], row[1]          # 当前组合的窗口数和座位数
        wait = preds[i]                # 模型预测的等待时间
        total_cost, op, pen = calculate_cost(w, s, wait)

        if total_cost < best_cost:
            best_cost = total_cost
            best_config = {
                'window': w, 'seat': s, 'wait': wait,
                'total_cost': total_cost, 'op_cost': op, 'penalty': pen
            }

    # 打印最优结果
    print(f"\n智能决策结果 (设定人流:{target_arrival}人/分):")
    print(f"建议开启窗口: {best_config['window']} 个")
    print(f"建议开放座位: {best_config['seat']} 个")
    print(f"预计平均等待: {best_config['wait']:.2f} 分钟")
    print(f"预计硬件成本: {best_config['op_cost']} 元/天")
    print(f"预计拥堵代价: {best_config['penalty']:.0f} 元/天")
    print(f"综合最低成本: {best_config['total_cost']:.0f}")

    return best_config


# 命令行入口：直接运行此脚本即可执行完整分析流程
if __name__ == "__main__":
    model, features = train_model()
    optimize_config(model, features, target_arrival=40.0, serve_time=30.0, eat_time=600.0)