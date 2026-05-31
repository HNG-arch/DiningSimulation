# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Beijing Jiaotong University Cafeteria Dining Simulation System (北京交通大学食堂就餐仿真系统). A discrete-event simulation that models student dining behavior — Poisson arrivals with time-varying rate, shortest-queue-first window assignment, random seat allocation, and normal-distributed serve/eat times. Includes a Random Forest ML model for optimizing cafeteria configuration (minimizing operating cost + waiting penalty).

Frontend-backend separation: FastAPI (Python) backend + Vue 3/Vite frontend, communicating via REST. SQLite for persistence. Playwright for E2E tests.

## Commands

### Backend (Python/FastAPI)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Or: python backend/app/main.py
```

### Frontend (Vue 3/Vite)
```bash
cd frontend
npm install
npm run dev       # Dev server on http://0.0.0.0:5173
npm run build     # Production build to frontend/dist/
```

### E2E tests
```bash
pytest backend/tests/e2e/ -v                # Headless (Edge Chromium)
pytest backend/tests/e2e/ -v --headed       # Show browser
```

The E2E `conftest.py` auto-manages backend + frontend process lifecycles — no need to start them manually.

## Architecture

### Backend (`backend/`)

**Entry point:** `app/main.py` — FastAPI app, CORS all origins, global `simulation_engine` singleton.

The simulation runs in a **daemon thread**. State is shared via `state_lock`/`engine_lock` threading locks. The `force_stop` flag is checked each tick for clean termination.

**`app/core/simulation.py`** — `SimulationEngine` class. Main loop per tick: generate Poisson arrivals → assign to shortest queue → update serving timers → allocate seats to waiting students → update eating timers → record stats → call `state_callback` (which frontend polls). Time units: simulation clock is minutes, serve/eat times are seconds.

**`app/core/models.py`** — Pydantic models (`ConfigParams`, `WindowState`, `Statistics`, `CostBreakdown`, etc.) + cost constants (`COST_PER_WINDOW=300`, `COST_PER_SEAT=5`, `PENALTY_PER_MINUTE=80`) + DB helpers (`load_all_results`, `calculate_cost`).

**`app/core/analysis.py`** — ML and optimization. Global `_ml_model` (RandomForestRegressor, 100 estimators, max_depth=10). `train_model()` requires >=10 DB records. `optimize_config()` does grid search over windows×seats to find lowest cost. U-curve and heatmap generators. Falls back to best historical record if model untrained.

**`app/core/random_utils.py`** — `poisson_arrivals()` and `normal_time()` wrappers using NumPy RNG.

**Database** (`backend/data/simulation_history.db`): Two tables — `simulation_runs` (14 cols including config params, metrics, time_series JSON) and `window_throughput` (run_id FK, window_id, served_count). DB path: `backend/app/main.py` computes it as `os.path.join(backend_dir, "data", "simulation_history.db")`.

### Frontend (`frontend/`)

Three Vue routes: `/` (CafeteriaView), `/simulation` (SimulationView), `/analysis` (AnalysisView) — all in `frontend/src/views/`.

**Data passing between pages is via `localStorage`** (not Pinia/Vuex). SimulationView saves config → CafeteriaView reads it → AnalysisView reads `lastSimulationId`.

**CafeteriaView** polls `GET /api/state` every `max(400, 2000/speed)` ms for real-time visualization of windows, queues, seats, and student flow.

**API base URL** is hardcoded to `http://127.0.0.1:8000` in all components.

**Vite** binds to `0.0.0.0:5173`, allows `localhost` and `*.ngrok-free.app` hosts.

### Key API endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/config` | Set simulation parameters |
| `POST /api/start` | Start simulation (daemon thread) |
| `POST /api/stop` | Force-stop |
| `GET /api/state` | Real-time snapshot (polled by frontend) |
| `GET /api/stats` | Final statistics |
| `POST /api/analysis/train` | Train Random Forest ML model |
| `GET /api/analysis/optimize` | Get optimal config (lowest cost) |
| `GET /api/analysis/u-curve` | U-shaped cost curve data |
| `GET /api/analysis/heatmap` | Window × Seat wait-time heatmap |

## Tests

`backend/tests/unit/` — for future unit tests (currently empty).

All current test coverage is via E2E Playwright tests in `backend/tests/e2e/test_e2e.py` (5 scenarios: normal flow, duplicate-start rejection, DB verification, UI full flow, parameter verification).
