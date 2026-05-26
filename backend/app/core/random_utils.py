"""
随机数生成工具模块
北京交大食堂就餐仿真系统 - 随机数生成器

本模块提供了仿真系统中使用的随机数生成函数，主要用于：
1. 模拟学生到达过程（泊松分布）
2. 生成服务时间和就餐时间（正态分布）

所有函数都使用 NumPy 的随机生成器，支持设置随机种子以确保结果可复现。
"""
import numpy as np


def poisson_arrivals(rate_per_min: float, tick_min: float, rng: np.random.Generator) -> int:
    """
    根据泊松分布生成本时间步内的到达人数

    泊松分布用于模拟单位时间内随机事件发生的次数，
    是离散事件仿真的基础。在某段时间内到达人数服从
    参数λ = 到达率 × 时间步长的泊松分布。

    参数：
    - rate_per_min: 到达率（人/分钟）
    - tick_min: 时间步长（分钟）
    - rng: NumPy 随机数生成器实例

    返回：
    - int: 本时间步内的到达人数（非负整数）
    """
    mu = rate_per_min * tick_min
    return rng.poisson(mu)


def normal_time(mean: float, std: float, rng: np.random.Generator, min_val: float = 1.0) -> float:
    """
    生成正态分布时间（秒），并截断至最小值

    正态分布用于模拟服务时间和就餐时间，
    这些时间通常围绕平均值波动，满足自然世界的中心极限定理。
    为防止时间过小甚至为负，添加最小值截断保护。

    参数：
    - mean: 均值（秒）
    - std: 标准差（秒）
    - rng: NumPy 随机数生成器实例
    - min_val: 最小值下限（秒），默认1.0秒

    返回：
    - float: 生成的时间值（秒），保证不小于 min_val
    """
    t = rng.normal(mean, std)
    return max(min_val, t)