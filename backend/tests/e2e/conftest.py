"""
e2e 集成测试 conftest — 自动管理后端和前端进程生命周期

运行方式（在项目根目录）：
    pytest backend/tests/e2e/ -v              # 使用 Edge 浏览器，无头模式
    pytest backend/tests/e2e/ -v --headed     # 显示浏览器窗口
"""
import os
import sys
import time
import json
import socket
import subprocess
import pytest
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# ========================== 常量 ==========================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

BACKEND_PORT = 8000
FRONTEND_PORT = 5173
BASE_URL = f"http://127.0.0.1:{FRONTEND_PORT}"
API_URL = f"http://127.0.0.1:{BACKEND_PORT}"


def _is_port_open(port: int) -> bool:
    """检测指定端口是否已被占用（服务已启动）"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _wait_for_service(url: str, timeout: int = 60) -> bool:
    """轮询等待服务 URL 可访问（返回200），支持较长的超时"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code < 500:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


# ========================== Session 级 fixtures ==========================

@pytest.fixture(scope="session")
def backend_process():
    """启动 FastAPI 后端服务"""
    print(f"\n[conftest] 启动后端服务 (端口 {BACKEND_PORT})...")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(BACKEND_PORT), "--log-level", "warning"],
        cwd=str(BACKEND_DIR), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    print("[conftest] 等待后端就绪...")
    ready = _wait_for_service(f"http://127.0.0.1:{BACKEND_PORT}/api/state")
    if not ready:
        proc.terminate()
        proc.wait()
        pytest.fail(f"后端启动超时")

    print("[conftest] 后端已就绪 ✓")
    yield proc

    print("\n[conftest] 关闭后端服务...")
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def frontend_process(backend_process):
    """启动 Vue 前端开发服务器"""
    print(f"\n[conftest] 启动前端服务 (端口 {FRONTEND_PORT})...")

    cmd = "npx.cmd" if sys.platform == "win32" else "npx"
    proc = subprocess.Popen(
        [cmd, "vite", "--port", str(FRONTEND_PORT), "--host", "127.0.0.1"],
        cwd=str(FRONTEND_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    print("[conftest] 等待前端就绪...")
    ready = _wait_for_service(f"http://127.0.0.1:{FRONTEND_PORT}")
    if not ready:
        proc.terminate()
        proc.wait()
        pytest.fail(f"前端启动超时")

    print("[conftest] 前端已就绪 ✓")
    yield proc

    print("\n[conftest] 关闭前端服务...")
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def browser(pytestconfig):
    """创建 Edge 浏览器实例（自定义配置）"""
    headless = not pytestconfig.getoption("--headed", False)
    slow_mo = pytestconfig.getoption("--slowmo", 0)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=headless,
            slow_mo=slow_mo,
        )
        yield browser
        browser.close()


@pytest.fixture
def context(browser):
    """创建浏览器上下文"""
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    yield ctx
    ctx.close()


@pytest.fixture
def page(context, frontend_process):
    """每个测试用例获取独立的页面"""
    pg = context.new_page()
    yield pg
    pg.close()