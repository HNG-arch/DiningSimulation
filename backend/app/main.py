"""
FastAPI后端API模块
北京交大食堂就餐仿真系统 - API服务器
"""
import sqlite3
from datetime import datetime
import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any , List
import threading
import time

from app.core.models import ConfigParams, Statistics
from app.core.simulation import SimulationEngine
from app.core.analysis import (
    get_analysis_summary, calculate_cost, optimize_config,
    train_model, get_model_status, predict_wait_time,
    get_u_curve_data, get_heatmap_data
)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "simulation_history.db")
DB_PATH = os.path.abspath(DB_PATH)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def init_db():
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
            satisfaction_score REAL,
            time_series TEXT DEFAULT '[]'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS window_throughput (
            run_id INTEGER,
            window_id INTEGER,
            served_count INTEGER,
            FOREIGN KEY (run_id) REFERENCES simulation_runs(id)
        )
    ''')
    conn.commit()
    try:
        cursor.execute('ALTER TABLE simulation_runs ADD COLUMN time_series TEXT DEFAULT \'[]\'')
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

def save_simulation_result(config: ConfigParams, stats: Statistics, run_id: int = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    time_series_json = json.dumps(stats.time_series, ensure_ascii=False)
    cursor.execute('''
        INSERT INTO simulation_runs (
            run_timestamp, random_seed, window_count, seat_count,
            arrival_rate, avg_serve_time, avg_eat_time, simulation_duration,
            tick_step, avg_wait_time, throughput_total, seat_turnover, satisfaction_score,
            time_series
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        config.random_seed,
        config.window_count,
        config.seat_count,
        config.arrival_rate,
        config.avg_serve_time,
        config.avg_eat_time,
        config.simulation_duration,
        config.tick_step,
        stats.avg_wait_time,
        sum(stats.throughput_per_window),
        stats.seat_turnover,
        stats.satisfaction_score,
        time_series_json
    ))
    run_id = cursor.lastrowid
    for window_id, served in enumerate(stats.throughput_per_window):
        cursor.execute('''
            INSERT INTO window_throughput (run_id, window_id, served_count)
            VALUES (?, ?, ?)
        ''', (run_id, window_id, served))
    conn.commit()
    conn.close()
    return run_id


app = FastAPI(
    title="北京交大食堂就餐仿真系统",
    description="提供食堂就餐流程仿真的配置、运行、状态查询和统计接口"
)

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


simulation_engine: Optional[SimulationEngine] = None
engine_lock = threading.Lock()
is_engine_running = False
simulation_thread: Optional[threading.Thread] = None
current_state: Dict[str, Any] = {}
state_lock = threading.Lock()


def update_state(snapshot: dict):
    global current_state
    with state_lock:
        current_state = snapshot


def run_simulation_thread():
    global simulation_engine, is_engine_running, current_state
    with engine_lock:
        if simulation_engine is None:
            return
        is_engine_running = True
    try:
        simulation_engine.run(state_callback=update_state)
        if simulation_engine.is_finished and not simulation_engine.force_stop:
            stats = simulation_engine.get_statistics()
            save_simulation_result(simulation_engine.config, stats)
    finally:
        with engine_lock:
            is_engine_running = False


class ConfigRequest(BaseModel):
    window_count: int = Field(ge=1)
    seat_count: int = Field(ge=1)
    arrival_rate: float = Field(gt=0)
    avg_serve_time: float = Field(gt=0)
    avg_eat_time: float = Field(gt=0)
    simulation_duration: int = Field(gt=0)
    serve_time_std: Optional[float] = Field(default=None)
    eat_time_std: Optional[float] = Field(default=None)
    random_seed: Optional[int] = Field(default=None)
    tick_step: float = Field(default=1.0, gt=0)
    tick_delay: float = Field(default=0.1, ge=0)
    student_count: int = Field(default=0, ge=0)


@app.options("/api/config")
async def options_config():
    return {"success": True}


@app.post("/api/config")
async def configure_simulation(config_req: ConfigRequest):
    global simulation_engine, is_engine_running, simulation_thread, current_state
    with engine_lock:
        # 如果仿真正在运行，自动停止
        if is_engine_running and simulation_engine is not None:
            simulation_engine.force_stop = True
            is_engine_running = False
        # 清空状态
        with state_lock:
            current_state = {}
        # 创建新引擎
        config = ConfigParams(**config_req.model_dump())
        simulation_engine = SimulationEngine(config)
    return {"success": True, "message": "配置成功"}


@app.post("/api/start")
async def start_simulation():
    global simulation_engine, is_engine_running, simulation_thread
    with engine_lock:
        if simulation_engine is None:
            raise HTTPException(status_code=400, detail="请先配置参数")
        if is_engine_running:
            return {"success": True, "message": "仿真已在运行"}
        is_engine_running = True
        simulation_thread = threading.Thread(target=run_simulation_thread, daemon=True)
        simulation_thread.start()
    return {"success": True, "message": "仿真已启动"}


@app.post("/api/stop")
async def stop_simulation_api():
    global simulation_engine, is_engine_running, current_state
    with engine_lock:
        if simulation_engine is not None:
            simulation_engine.force_stop = True
        is_engine_running = False
    with state_lock:
        current_state = {}
    return {"success": True, "message": "已终止仿真"}


@app.get("/api/state")
async def get_state():
    with state_lock:
        if current_state:
            return {"success": True, "state": current_state}
    if simulation_engine is None:
        return {"success": False, "state": None}
    return {"success": True, "state": None}


@app.get("/api/stats")
async def get_stats():
    if simulation_engine is None:
        raise HTTPException(status_code=400, detail="未初始化")
    stats = simulation_engine.get_statistics()
    return {
        "success": True,
        "is_finished": simulation_engine.is_finished,
        "stats": stats.dict()
    }


class SimulationRunRequest(BaseModel):
    window_count: int = Field(ge=1)
    seat_count: int = Field(ge=1)
    arrival_rate: float = Field(gt=0)
    avg_serve_time: float = Field(gt=0)
    avg_eat_time: float = Field(gt=0)
    simulation_duration: int = Field(gt=0)
    tick_step: float = Field(default=1.0, gt=0)
    tick_delay: float = Field(default=0.1, ge=0)
    serve_time_std: Optional[float] = Field(default=None)
    eat_time_std: Optional[float] = Field(default=None)
    random_seed: Optional[int] = Field(default=None)
    student_count: int = Field(default=0, ge=0)


@app.get("/api/simulation/config")
async def get_default_config():
    return {
        "window_count": 10, "table_count": 30, "serving_speed": 1,
        "student_count": 500, "simulation_duration": 120, "arrival_rate": 15,
        "avg_serve_time": 1.0, "avg_eat_time": 600, "tick_step": 1.0
    }

@app.get("/api/simulation/config/recommended")
async def get_recommended_config():
    return {
        "window_count": 15, "table_count": 50, "serving_speed": 1,
        "student_count": 1000, "simulation_duration": 120, "arrival_rate": 20,
        "avg_serve_time": 1.0, "avg_eat_time": 600, "tick_step": 1.0
    }

@app.post("/api/simulation/run")
async def run_simulation(request: SimulationRunRequest):
    global simulation_engine, is_engine_running
    if is_engine_running:
        raise HTTPException(status_code=400, detail="仿真运行中")
    config = ConfigParams(
        window_count=request.window_count, seat_count=request.seat_count,
        arrival_rate=request.arrival_rate, avg_serve_time=request.avg_serve_time * 60,
        avg_eat_time=request.avg_eat_time * 60, simulation_duration=request.simulation_duration,
        tick_step=request.tick_step, tick_delay=request.tick_delay,
        serve_time_std=request.serve_time_std, eat_time_std=request.eat_time_std,
        random_seed=request.random_seed, student_count=request.student_count
    )
    simulation_engine = SimulationEngine(config)
    simulation_engine.run()
    stats = simulation_engine.get_statistics()
    run_id = save_simulation_result(config, stats)
    return {
        "id": str(run_id), "config": config.dict(), "statistics": stats.dict(),
        "time_series": stats.time_series, "created_at": datetime.now().isoformat()
    }


@app.get("/api/simulation/results")
async def get_all_results():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, run_timestamp as created_at, window_count, seat_count,
               arrival_rate, simulation_duration, avg_wait_time, throughput_total, satisfaction_score
        FROM simulation_runs ORDER BY id DESC LIMIT 50
    ''')
    results = [
        {
            "id": str(row["id"]), "createdAt": row["created_at"],
            "windowCount": row["window_count"], "seatCount": row["seat_count"],
            "arrivalRate": row["arrival_rate"], "duration": row["simulation_duration"],
            "avgWaitTime": row["avg_wait_time"], "throughput": row["throughput_total"],
            "satisfaction": row["satisfaction_score"]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return results

@app.get("/api/simulation/results/{result_id}")
async def get_result(result_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM simulation_runs WHERE id = ?', (result_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="不存在")
    cursor.execute('SELECT window_id, served_count FROM window_throughput WHERE run_id = ?', (result_id,))
    windows = cursor.fetchall()
    conn.close()

    time_series_data = json.loads(row["time_series"] or "[]") if row["time_series"] else []
    return {
        "id": str(result_id),
        "config": {
            "window_count": row["window_count"], "seat_count": row["seat_count"],
            "arrival_rate": row["arrival_rate"], "avg_serve_time": row["avg_serve_time"],
            "avg_eat_time": row["avg_eat_time"], "simulation_duration": row["simulation_duration"],
            "tick_step": row["tick_step"], "random_seed": row["random_seed"]
        },
        "statistics": {
            "avg_wait_time": row["avg_wait_time"],
            "throughput_per_window": [w["served_count"] for w in windows],
            "throughput_total": row["throughput_total"],
            "seat_turnover": row["seat_turnover"],
            "satisfaction_score": row["satisfaction_score"],
            "time_series": time_series_data
        },
        "time_series": time_series_data,
        "created_at": row["run_timestamp"]
    }

@app.delete("/api/simulation/results/{result_id}")
async def delete_result(result_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM window_throughput WHERE run_id = ?', (result_id,))
    cursor.execute('DELETE FROM simulation_runs WHERE id = ?', (result_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="不存在")
    conn.commit()
    conn.close()
    return {"success": True, "message": "删除成功"}


@app.get("/api/analysis/summary")
async def get_analysis_summary_endpoint():
    summary = get_analysis_summary()
    if summary is None:
        raise HTTPException(status_code=404, detail="无数据")
    return {"success": True, "data": summary}

@app.get("/api/analysis/cost/{result_id}")
async def get_cost_analysis(result_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM simulation_runs WHERE id = ?', (result_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="不存在")
    cost = calculate_cost(row["window_count"], row["seat_count"], row["avg_wait_time"] or 0)
    return {
        "success": True, "result_id": result_id,
        "config": {"window_count": row["window_count"], "seat_count": row["seat_count"],
                   "arrival_rate": row["arrival_rate"], "simulation_duration": row["simulation_duration"]},
        "statistics": {"avg_wait_time": row["avg_wait_time"], "throughput_total": row["throughput_total"],
                       "satisfaction_score": row["satisfaction_score"]},
        "cost": cost
    }

@app.get("/api/analysis/optimize")
async def get_optimization():
    optimum = optimize_config()
    if optimum is None:
        raise HTTPException(status_code=404, detail="无数据")
    return {"success": True, "data": optimum}

@app.post("/api/analysis/train")
async def train_ml_model():
    metrics, error = train_model()
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "metrics": metrics}

@app.get("/api/analysis/model")
async def get_model_info():
    return {"success": True, "data": get_model_status()}

@app.get("/api/analysis/predict")
async def predict_wait(window_count: int, seat_count: int, arrival_rate: float, avg_serve_time: float, avg_eat_time: float):
    result = predict_wait_time(window_count, seat_count, arrival_rate, avg_serve_time, avg_eat_time)
    if result is None:
        raise HTTPException(status_code=400, detail="未训练")
    return {"success": True, "predicted_wait": result}

@app.get("/api/analysis/u-curve")
async def get_ucurve(seat: int = None, arrival: float = None, serve: float = None, eat: float = None):
    data = get_u_curve_data(fixed_seat=seat, fixed_arrival=arrival, fixed_serve=serve, fixed_eat=eat)
    if data is None:
        raise HTTPException(status_code=400, detail="未训练或数据不足")
    return {"success": True, "data": data}

@app.get("/api/analysis/heatmap")
async def get_heatmap(arrival: float = None, serve: float = None, eat: float = None):
    data = get_heatmap_data(fixed_arrival=arrival, fixed_serve=serve, fixed_eat=eat)
    if data is None:
        raise HTTPException(status_code=400, detail="未训练或数据不足")
    return {"success": True, "data": data}

@app.get("/api/analysis/explain")
async def get_analysis_explanation():
    return {
        "success": True,
        "html": """
        <h2 style="color: #667eea; margin-bottom: 16px;">📊 系统决策模型解读</h2>
        <h3 style="color: #333; margin-top: 20px;">1. 为什么会有 U 型曲线？</h3>
        <p style="color: #555; line-height: 1.8;">食堂运营存在两种博弈：<b>运营成本</b>（窗口/座位越多越贵）与<b>惩罚成本</b>（排队越长口碑越差）。<br/>
        随着窗口数量增加，排队惩罚成本下降，但运营成本持续上升。U型曲线的最低点即是两者的平衡点——最优窗口配置。</p>
        <h3 style="color: #333; margin-top: 20px;">2. 什么是木桶效应热力图？</h3>
        <p style="color: #555; line-height: 1.8;">系统效率由当前的最短板决定：<br/>
        • <b>窗口少 + 座位多</b> → 窗口瓶颈（排队区拥堵）<br/>
        • <b>窗口多 + 座位少</b> → 座位瓶颈（找不到座位）<br/>
        颜色最深区域代表"窗口与座位严重不匹配"的灾难区。</p>
        <h3 style="color: #333; margin-top: 20px;">3. 如何使用 ML 优化建议？</h3>
        <p style="color: #555; line-height: 1.8;">系统基于历史仿真数据训练随机森林模型，预测不同配置的等待时间和综合成本。<br/>
        推荐配置综合考虑了运营效率和成本效益，可作为食堂扩容或优化的参考依据。</p>
        <div style="background: #f0f0f0; padding: 15px; border-radius: 8px; margin-top: 20px;">
            <p style="margin: 0; color: #666;"><b>💡 小提示：</b>实际运营中还需考虑人员排班、高峰时段差异等因素，模型建议仅供参考。</p>
        </div>
        """
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")