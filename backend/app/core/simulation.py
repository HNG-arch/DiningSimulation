"""
仿真引擎核心类
北京交大食堂就餐仿真系统 - 仿真引擎

本模块实现了食堂就餐仿真的核心逻辑，包括：
1. 学生到达生成（时变泊松分布）
2. 窗口分配（最短队列优先策略）
3. 打饭服务（正态分布服务时间）
4. 座位分配（随机选择空座位）
5. 就餐过程（时间递减）
6. 统计计算（等待时间、吞吐量等）

仿真使用固定时间步长推进，每个时间步执行一次完整的状态更新。

时间单位说明：
- 仿真内部时间：分钟（current_time, arrive_time等）
- 服务/就餐时间：秒（serve_time_left, seat_matrix等）
- 转换关系：tick_seconds = tick_step × 60
"""
from typing import List, Tuple, Optional, Callable
import math
import time
import numpy as np
from .models import ConfigParams, WindowState, StudentRecord, Statistics, SeatMatrix
from .random_utils import poisson_arrivals, normal_time


class SimulationEngine:
    """食堂就餐仿真引擎类"""

    def __init__(self, config: ConfigParams):
        self.config = config
        self.rng = np.random.default_rng(config.random_seed)
        self.current_time = 0.0
        self.is_running = False
        self.is_finished = False
        self.force_stop = False  # 【修复】强制停止标识

        # ========== 窗口初始化 ==========
        self.windows = [
            WindowState(window_id=i, queue_length=0, serve_time_left=0.0, total_served=0)
            for i in range(config.window_count)
        ]
        self.window_queues: List[List[StudentRecord]] = [[] for _ in range(config.window_count)]

        # ========== 座位初始化 ==========
        self.seat_rows = int(math.sqrt(config.seat_count))
        self.seat_cols = (config.seat_count + self.seat_rows - 1) // self.seat_rows
        self.seat_matrix = [[0.0 for _ in range(self.seat_cols)] for _ in range(self.seat_rows)]

        # ========== 学生管理 ==========
        self.next_student_id = 0
        self.all_students: List[StudentRecord] = []
        self.waiting_for_seat: List[StudentRecord] = []
        self.eating_students: List[StudentRecord] = []

        # ========== 统计变量 ==========
        self.total_students = 0
        self.total_wait_time = 0.0
        self.completed_students = 0
        self.time_series = []

    def _time_varying_rate(self) -> float:
        if self.config.simulation_duration <= 0:
            return self.config.arrival_rate
        progress = self.current_time / self.config.simulation_duration
        peak_raw = self.config.arrival_rate
        floor_ratio = 0.1
        if self.config.student_count > 0:
            raw_area = self.config.simulation_duration * 0.73 * peak_raw
            scale = min(1.0, self.config.student_count / raw_area) if raw_area > 0 else 1.0
        else:
            scale = 1.0
        peak = peak_raw * scale
        floor = peak * floor_ratio

        if progress < 0.3:
            return floor + (peak - floor) * (progress / 0.3)
        elif progress < 0.7:
            return peak
        else:
            return peak - (peak - floor) * ((progress - 0.7) / 0.3)

    def _generate_arrivals(self) -> List[StudentRecord]:
        if self.config.student_count > 0 and self.total_students >= self.config.student_count:
            return []
        mean_rate = self._time_varying_rate()
        num = poisson_arrivals(mean_rate, self.config.tick_step, self.rng)
        max_per_tick = int(self.config.arrival_rate * self.config.tick_step)
        num = min(num, max_per_tick)

        if self.config.student_count > 0:
            remaining = self.config.student_count - self.total_students
            num = min(num, remaining)

        new_students = []
        for _ in range(num):
            student = StudentRecord(id=self.next_student_id, arrive_time=self.current_time)
            self.next_student_id += 1
            self.all_students.append(student)
            self.total_students += 1
            new_students.append(student)
        return new_students

    def _assign_windows(self, students: List[StudentRecord]):
        for student in students:
            queue_lens = [len(q) for q in self.window_queues]
            min_len = min(queue_lens)
            candidates = [i for i, l in enumerate(queue_lens) if l == min_len]
            chosen = self.rng.choice(candidates)
            self.window_queues[chosen].append(student)
            student.selected_window = chosen
            student.enter_queue_time = self.current_time
            self.windows[chosen].queue_length = len(self.window_queues[chosen])

    def _update_serving(self):
        tick_sec = self.config.tick_step * 60.0
        for i, window in enumerate(self.windows):
            if window.serve_time_left > 0:
                window.serve_time_left -= tick_sec
                if window.serve_time_left < 0:
                    window.serve_time_left = 0.0

            if window.serve_time_left == 0.0 and self.window_queues[i]:
                student = self.window_queues[i].pop(0)
                window.total_served += 1
                serve_std = self.config.serve_time_std or (self.config.avg_serve_time * 0.2)
                serve_sec = normal_time(self.config.avg_serve_time, serve_std, self.rng, min_val=1.0)
                window.serve_time_left = serve_sec
                self.waiting_for_seat.append(student)
                window.queue_length = len(self.window_queues[i])

    def _find_available_seat(self) -> Optional[Tuple[int, int]]:
        empty_seats = []
        for i in range(self.seat_rows):
            for j in range(self.seat_cols):
                if self.seat_matrix[i][j] == 0.0:
                    empty_seats.append((i, j))
        if empty_seats:
            choice = self.rng.choice(empty_seats)
            return tuple(choice) if isinstance(choice, np.ndarray) else choice
        return None

    def _allocate_seat(self, student: StudentRecord) -> bool:
        seat = self._find_available_seat()
        if seat:
            row, col = seat
            eat_std = self.config.eat_time_std or (self.config.avg_eat_time * 0.2)
            eat_sec = normal_time(self.config.avg_eat_time, eat_std, self.rng, min_val=1.0)
            self.seat_matrix[row][col] = eat_sec
            student.start_eat_time = self.current_time
            student.wait_time = student.start_eat_time - student.enter_queue_time
            self.total_wait_time += student.wait_time
            self.eating_students.append(student)
            return True
        return False

    def _process_seat_waiting_queue(self):
        still_waiting = []
        for student in self.waiting_for_seat:
            if not self._allocate_seat(student):
                still_waiting.append(student)
        self.waiting_for_seat = still_waiting

    def _update_eating(self):
        tick_sec = self.config.tick_step * 60.0
        for i in range(self.seat_rows):
            for j in range(self.seat_cols):
                if self.seat_matrix[i][j] > 0.0:
                    self.seat_matrix[i][j] -= tick_sec
                    if self.seat_matrix[i][j] <= 0.0:
                        self.seat_matrix[i][j] = 0.0
                        self.completed_students += 1

    def _record_statistics(self):
        avg_wait = self.total_wait_time / self.completed_students if self.completed_students else 0.0
        total_queue = sum(len(q) for q in self.window_queues)
        eating_count = sum(1 for row in self.seat_matrix for v in row if v > 0)
        waiting_seat = len(self.waiting_for_seat)
        self.time_series.append({
            "time": round(self.current_time, 2),
            "avg_wait": round(avg_wait, 2),
            "queue_length_sum": total_queue,
            "eating_count": eating_count,
            "waiting_seat": waiting_seat,
            "total_arrived": self.total_students,
            "total_completed": self.completed_students,
            "total_throughput": sum(w.total_served for w in self.windows)
        })

    def run(self, state_callback: Optional[Callable[[dict], None]] = None):
        """运行仿真主循环"""
        self.is_running = True
        self.is_finished = False
        self.force_stop = False  # 【修复】确保每次运行开始时标记为False
        
        num_ticks = int(self.config.simulation_duration / self.config.tick_step)

        for tick in range(num_ticks):
            # 【修复】如果被后端API叫停，立刻终止循环
            if self.force_stop:
                break

            self.current_time = tick * self.config.tick_step
            new_students = self._generate_arrivals()
            self._assign_windows(new_students)
            self._update_serving()
            self._process_seat_waiting_queue()
            self._update_eating()
            self._process_seat_waiting_queue()
            self._record_statistics()

            if state_callback:
                state_callback(self.get_state_snapshot())

            if self.config.tick_delay > 0:
                time.sleep(self.config.tick_delay)

        # 【修复】完美解决卡59/60的问题。只有自然运行结束，才把时间补满到总时长
        if not self.force_stop:
            self.current_time = float(self.config.simulation_duration)

        self.is_running = False
        self.is_finished = True

        # 最后推一次完成状态
        if state_callback:
            state_callback(self.get_state_snapshot())

    def get_state_snapshot(self) -> dict:
        avg_wait = self.total_wait_time / self.completed_students if self.completed_students else 0.0
        total_throughput = sum(w.total_served for w in self.windows)
        total_queue = sum(len(q) for q in self.window_queues)
        eating_count = sum(1 for row in self.seat_matrix for v in row if v > 0)
        if self.config.seat_count and self.config.simulation_duration:
            seat_turnover = self.completed_students / self.config.seat_count / (self.config.simulation_duration / 60.0)
        else:
            seat_turnover = 0.0
        return {
            "current_time": round(self.current_time, 2),
            "total_arrived": self.total_students,
            "total_completed": self.completed_students,
            "eating_count": eating_count,
            "total_queue": total_queue,
            "windows": [
                {
                    "window_id": w.window_id,
                    "queue_length": w.queue_length,
                    "serve_time_left": round(w.serve_time_left, 1),
                    "total_served": w.total_served
                }
                for w in self.windows
            ],
            "seats": {
                "rows": self.seat_rows,
                "cols": self.seat_cols,
                "data": [[round(v, 1) for v in row] for row in self.seat_matrix]
            },
            "statistics": {
                "avg_wait_time": round(avg_wait, 2),
                "throughput": total_throughput,
                "seat_turnover": round(seat_turnover, 2),
                "satisfaction": round(max(0.0, 1.0 - avg_wait / 15.0), 3)
            }
        }

    def get_statistics(self) -> Statistics:
        avg_wait = self.total_wait_time / self.completed_students if self.completed_students else 0.0
        throughput_per_window = [w.total_served for w in self.windows]
        if self.config.seat_count and self.config.simulation_duration:
            seat_turnover = self.completed_students / self.config.seat_count / (self.config.simulation_duration / 60.0)
        else:
            seat_turnover = 0.0
        satisfaction = max(0.0, 1.0 - avg_wait / 15.0)
        return Statistics(
            avg_wait_time=round(avg_wait, 2),
            throughput_per_window=throughput_per_window,
            seat_turnover=round(seat_turnover, 2),
            satisfaction_score=round(satisfaction, 3),
            time_series=self.time_series
        )