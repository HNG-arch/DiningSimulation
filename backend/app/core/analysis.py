
"""
决策分析模块
基于历史仿真数据进行成本分析、机器学习预测和参数寻优。

本模块从 analysis_data/analyze_results.py 集成：
- 随机森林预测模型 (RandomForestRegressor)
- 基于排队论的网格搜索优化
- 模型评估指标 (MAE, R²)
- U型曲线和热力图数据生成

所有成本计算函数、数据常量和加载函数均引用自 models 模块。
"""
import sqlite3
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from .models import (
    DB_PATH, COST_PER_WINDOW, COST_PER_SEAT, PENALTY_PER_MINUTE,
    load_all_results, calculate_cost, calculate_cost_tuple
)


# 随机森林模型实例（全局单例），训练后保存在内存中
_ml_model = None
# ML模型的特征列名，对应数据库中哪些字段用于训练
_ml_features = ['window_count', 'seat_count', 'arrival_rate', 'avg_serve_time', 'avg_eat_time']
# 模型是否已完成训练的标记
_model_trained = False
# 模型评估指标缓存（R², MAE, 样本数等）
_model_metrics = None


def load_dataframe() -> pd.DataFrame:
    """
    从 SQLite 数据库加载仿真数据为 pandas DataFrame

    用于机器学习模型的特征工程和训练。

    返回：
    - pd.DataFrame: 包含所有仿真记录的DataFrame
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM simulation_runs", conn)
    conn.close()
    return df


def train_model():
    """
    训练随机森林回归模型，预测平均等待时间

    使用 80/20 训练测试分割，评估指标包括：
    - R² (决定系数): 越接近1越好
    - MAE (平均绝对误差): 越小越好

    返回：
    - (metrics, error): 成功返回 (指标字典, None)，失败返回 (None, 错误信息)
    """
    global _ml_model, _model_trained, _model_metrics

    df = load_dataframe()
    if len(df) < 10:
        return None, "数据量不足（需至少10条记录）"

    # 提取特征矩阵和目标变量
    X = df[_ml_features]
    y = df['avg_wait_time'].fillna(0)

    # 按8:2划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 创建并训练随机森林回归器
    _ml_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    _ml_model.fit(X_train, y_train)

    # 在测试集上评估模型性能
    preds = _ml_model.predict(X_test)
    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)

    _model_metrics = {
        "r2_score": round(float(r2), 4),
        "mae": round(float(mae), 2),
        "sample_count": len(df),
        "train_count": len(X_train),
        "test_count": len(X_test)
    }
    _model_trained = True
    return _model_metrics, None


def get_model_status() -> dict:
    """
    查询当前ML模型的状态

    返回：
    - dict: 包含 trained/metics/features 三项
    """
    return {
        "trained": _model_trained,
        "metrics": _model_metrics,
        "features": _ml_features
    }


def predict_wait_time(window_count: int, seat_count: int, arrival_rate: float,
                      avg_serve_time: float, avg_eat_time: float) -> float:
    """
    使用训练好的ML模型预测指定配置的等待时间

    参数：
    - window_count: 窗口数量
    - seat_count: 座位数量
    - arrival_rate: 到达率（人/分钟）
    - avg_serve_time: 平均打饭时间（秒）
    - avg_eat_time: 平均就餐时间（秒）

    返回：
    - float: 预测的等待时间（分钟），模型未训练返回 None
    """
    if not _model_trained or _ml_model is None:
        return None
    input_data = pd.DataFrame([[
        window_count, seat_count, arrival_rate, avg_serve_time, avg_eat_time
    ]], columns=_ml_features)
    return round(float(_ml_model.predict(input_data)[0]), 2)


def optimize_config(arrival_rate=None, serve_time=None, eat_time=None):
    """
    寻找全局最优配置（最低综合成本）

    策略：
    - 如果ML模型已训练，使用网格搜索+ML预测进行精确寻优
    - 否则，从历史记录中直接查找最低成本配置

    返回：
    - dict: 最优配置及成本明细，无数据返回 None
    """
    results = load_all_results()
    if not results:
        return None

    # 优先使用ML模型进行精确网格搜索
    if _model_trained and _ml_model is not None:
        return _ml_optimize_config(arrival_rate, serve_time, eat_time)

    # 回退：从历史记录中查找
    best = None
    best_cost = float('inf')
    for r in results:
        cost = calculate_cost(r['window_count'], r['seat_count'], r['avg_wait_time'] or 0)
        if cost['total'] < best_cost:
            best_cost = cost['total']
            best = {
                "window_count": r['window_count'],
                "seat_count": r['seat_count'],
                "arrival_rate": r['arrival_rate'],
                "avg_serve_time": r['avg_serve_time'],
                "avg_eat_time": r['avg_eat_time'],
                "avg_wait_time": r['avg_wait_time'],
                "throughput_total": r['throughput_total'],
                "satisfaction_score": r['satisfaction_score'],
                "cost": cost
            }
    return best


def _ml_optimize_config(target_arrival=None, serve_time=None, eat_time=None) -> dict:
    """
    基于ML模型的网格搜索优化配置（内部函数）

    在合理的参数空间内穷举搜索：
    - 窗口数: 5~29
    - 座位数: 100~580（步长20）
    对每个组合用ML模型预测等待时间，计算综合成本，取最低者。

    返回：
    - dict: 最优配置及其成本明细
    """
    results = load_all_results()
    if not results:
        return None

    # 使用最新的历史记录作为默认参数
    target_arrival = target_arrival or results[0].get('arrival_rate', 30.0)
    serve_time = serve_time or results[0].get('avg_serve_time', 30.0)
    eat_time = eat_time or results[0].get('avg_eat_time', 600.0)

    best_cost = float('inf')
    best_config = {}

    # 构建搜索网格
    test_cases = []
    for w in range(5, 30):
        for s in range(100, 600, 20):
            test_cases.append([w, s, target_arrival, serve_time, eat_time])

    test_df = pd.DataFrame(test_cases, columns=_ml_features)
    preds = _ml_model.predict(test_df)

    # 遍历所有组合寻找最优
    for i, row in enumerate(test_cases):
        w, s = row[0], row[1]
        wait = preds[i]
        total_cost, op, pen = calculate_cost_tuple(w, s, wait)
        if total_cost < best_cost:
            best_cost = total_cost
            best_config = {
                "window_count": w,
                "seat_count": s,
                "arrival_rate": target_arrival,
                "avg_serve_time": serve_time,
                "avg_eat_time": eat_time,
                "avg_wait_time": round(float(wait), 2),
                "throughput_total": 0,
                "satisfaction_score": round(max(0.0, 1.0 - wait / 15.0), 3),
                "cost": {
                    "total": round(float(total_cost), 0),
                    "operating": round(float(op), 0),
                    "penalty": round(float(pen), 0),
                    "window_cost": int(w * COST_PER_WINDOW),
                    "seat_cost": int(s * COST_PER_SEAT)
                }
            }
    return best_config


def get_u_curve_data(fixed_seat=None, fixed_arrival=None, fixed_serve=None, fixed_eat=None) -> dict:
    """
    生成U型成本曲线数据

    固定座位数和其他参数，遍历窗口数5~29，
    用ML模型预测每个窗口数下的等待时间和综合成本。
    验证"窗口数并非越多越好"的经济学原理。

    返回：
    - dict: windows/costs/wait_times/best_window等，模型未训练返回 None
    """
    if not _model_trained or _ml_model is None:
        return None

    results = load_all_results()
    if not results:
        return None

    # 固定参数默认从历史数据中取
    fixed_seat = fixed_seat or 300
    fixed_arrival = fixed_arrival or results[0].get('arrival_rate', 45.0)
    fixed_serve = fixed_serve or results[0].get('avg_serve_time', 30.0)
    fixed_eat = fixed_eat or results[0].get('avg_eat_time', 800.0)

    windows_range = list(range(5, 30))
    costs = []        # 各窗口数下的综合成本
    wait_times = []   # 各窗口数下的预计等待时间
    operatings = []   # 各窗口数下的运营成本
    penalties = []    # 各窗口数下的惩罚成本

    for w in windows_range:
        test_data = pd.DataFrame(
            [[w, fixed_seat, fixed_arrival, fixed_serve, fixed_eat]],
            columns=_ml_features
        )
        wait = _ml_model.predict(test_data)[0]
        total_cost, op, pen = calculate_cost_tuple(w, fixed_seat, wait)
        costs.append(round(float(total_cost), 0))
        wait_times.append(round(float(wait), 2))
        operatings.append(round(float(op), 0))
        penalties.append(round(float(pen), 0))

    # U型曲线的最低点就是最优窗口数
    best_idx = int(np.argmin(costs))

    return {
        "windows": windows_range,
        "costs": costs,
        "wait_times": wait_times,
        "operatings": operatings,
        "penalties": penalties,
        "best_window": windows_range[best_idx],
        "best_cost": costs[best_idx],
        "fixed_params": {
            "seat": fixed_seat,
            "arrival_rate": fixed_arrival,
            "serve_time": fixed_serve,
            "eat_time": fixed_eat
        }
    }


def get_heatmap_data(fixed_arrival=None, fixed_serve=None, fixed_eat=None) -> dict:
    """
    生成窗口×座位等待时间热力图数据

    固定到达率和服务时间，遍历窗口(10~24)和座位(100~500)的组合，
    用ML模型预测每个组合的等待时间，展示木桶效应：
    - 窗口少座位多 → 窗口瓶颈
    - 窗口多座位少 → 座位瓶颈

    返回：
    - dict: windows/seats/matrix/fixed_params，模型未训练返回 None
    """
    if not _model_trained or _ml_model is None:
        return None

    results = load_all_results()
    if not results:
        return None

    fixed_arrival = fixed_arrival or results[0].get('arrival_rate', 50.0)
    fixed_serve = fixed_serve or results[0].get('avg_serve_time', 30.0)
    fixed_eat = fixed_eat or results[0].get('avg_eat_time', 600.0)

    w_range = list(range(10, 26, 2))
    s_range = list(range(100, 501, 50))

    # 遍历所有窗口×座位组合
    matrix = []
    for si, seat in enumerate(s_range):
        row = []
        for wi, win in enumerate(w_range):
            test_data = pd.DataFrame(
                [[win, seat, fixed_arrival, fixed_serve, fixed_eat]],
                columns=_ml_features
            )
            wait = _ml_model.predict(test_data)[0]
            row.append(round(float(wait), 2))
        matrix.append(row)

    return {
        "windows": w_range,
        "seats": s_range,
        "matrix": matrix,
        "fixed_params": {
            "arrival_rate": fixed_arrival,
            "serve_time": fixed_serve,
            "eat_time": fixed_eat
        }
    }


def get_analysis_summary() -> dict:
    """
    生成综合分析摘要

    汇总内容：
    - 最新仿真记录与成本分析
    - ML模型状态与指标
    - 全局最优配置推荐
    - 所有历史数据的统计摘要

    返回：
    - dict: 全面分析摘要，无数据返回 None
    """
    results = load_all_results()
    if not results:
        return None

    latest = results[0]
    latest_cost = calculate_cost(
        latest['window_count'], latest['seat_count'], latest['avg_wait_time'] or 0
    )
    optimum = optimize_config()

    all_wait_times = [r['avg_wait_time'] for r in results if r['avg_wait_time'] is not None]
    all_satisfaction = [r['satisfaction_score'] for r in results if r['satisfaction_score'] is not None]

    model_info = get_model_status()

    return {
        "total_runs": len(results),
        "model_info": model_info,
        "latest": {
            "id": latest['id'],
            "config": {
                "window_count": latest['window_count'],
                "seat_count": latest['seat_count'],
                "arrival_rate": latest['arrival_rate'],
                "simulation_duration": latest['simulation_duration']
            },
            "statistics": {
                "avg_wait_time": latest['avg_wait_time'],
                "throughput_total": latest['throughput_total'],
                "satisfaction_score": latest['satisfaction_score']
            },
            "cost": latest_cost
        },
        "optimum": optimum,
        "stats_summary": {
            "avg_wait_all": round(float(np.mean(all_wait_times)), 2) if all_wait_times else 0,
            "min_wait": round(float(np.min(all_wait_times)), 2) if all_wait_times else 0,
            "max_wait": round(float(np.max(all_wait_times)), 2) if all_wait_times else 0,
            "avg_satisfaction": round(float(np.mean(all_satisfaction)), 3) if all_satisfaction else 0
        },
        "cost_params": {
            "per_window": COST_PER_WINDOW,
            "per_seat": COST_PER_SEAT,
            "penalty_per_minute": PENALTY_PER_MINUTE
        }
    }
