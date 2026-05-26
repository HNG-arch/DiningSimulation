"""
辅助工具：仿真过程观察脚本

独立启动一个短时仿真并在控制台打印每步的详细日志，
包括窗口排队状态、座位占用情况、实时统计指标。

用于开发和调试时观察仿真内部运行过程。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.models import ConfigParams
from app.core.simulation import SimulationEngine


def log_callback(snapshot: dict):
    """
    仿真每 tick 调用的状态回调函数

    在控制台打印当前仿真时刻的详细状态：
    - 各窗口的队列长度和剩余服务时间
    - 座位占用情况
    - 实时平均等待时间和吞吐量

    参数：
    - snapshot: 仿真引擎返回的状态快照字典
    """
    print(f"时间: {snapshot['current_time']:.2f} 分钟")
    print("窗口状态:")
    for w in snapshot['windows']:
        print(f"  窗口{w['window_id']}: 队列长度={w['queue_length']}, 剩余服务时间={w['serve_time_left']:.1f}秒")

    seats = snapshot['seats']
    # 统计已占用的座位数
    occupied = sum(1 for row in seats['data'] for val in row if val > 0)
    total_seats = seats['rows'] * seats['cols']
    print(f"座位占用: {occupied}/{total_seats}")

    # 打印实时统计
    print(f"实时统计: 平均等待={snapshot['statistics']['avg_wait_time']}分钟, 吞吐量={snapshot['statistics']['throughput']}")
    print("-" * 40)


# ==================== 仿真配置 ====================

# 创建一个小规模短时仿真配置用于观察
config = ConfigParams(
    window_count=2,           # 2个打饭窗口
    seat_count=10,            # 10个就餐座位
    arrival_rate=30,          # 到达率30人/分钟
    avg_serve_time=20,        # 平均打饭20秒
    avg_eat_time=120,         # 平均就餐2分钟（快速演示）
    simulation_duration=10,   # 仿真10分钟
    random_seed=42            # 固定随机种子，确保可复现
)

# 创建仿真引擎并注册日志回调
engine = SimulationEngine(config)
engine.run(state_callback=log_callback)

# 打印最终统计结果
print("\n=== 最终统计 ===")
stats = engine.get_statistics()
print(stats)