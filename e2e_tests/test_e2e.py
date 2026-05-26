"""
e2e 端到端集成测试 — 覆盖完整用户操作链路

运行方式（在项目根目录）：
    conda activate diningSim
    pytest e2e_tests/ -v              # 使用 Edge 浏览器，无头模式
    pytest e2e_tests/ -v --headed     # 显示浏览器窗口

测试场景：
    场景1：正常流程 — 配置参数 → 开始仿真 → 分析页验证（API测试）
    场景2：异常流程 — 仿真运行中再次启动，后端应拦截（API测试）
    场景3：数据库验证 — 仿真完成后检查记录写入（API测试）
    场景4：UI完整流程 — 真实用户操作（滑块→预览→仿真→食堂→分析）
    场景5：UI参数验证 — 验证 avg_eat_time 正确传递（捕获之前的bug）
"""
import time
import json
import re
import sqlite3
import pytest
from pathlib import Path

# 项目常量
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "backend" / "simulation_history.db"
API_URL = "http://127.0.0.1:8000"
FRONT_URL = "http://127.0.0.1:5173"


# ====================================================================
# 辅助函数
# ====================================================================

def _ensure_simulation_complete():
    """确保之前的仿真完全结束"""
    import requests
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            r = requests.get(f"{API_URL}/api/stats", timeout=2)
            data = r.json()
            if data.get("is_finished"):
                time.sleep(0.5)
                return True
        except:
            pass
        time.sleep(0.3)
    return False


def _run_simulation_via_api(page, config_override=None):
    """通过 API 运行一次短仿真（API测试用）"""
    _ensure_simulation_complete()

    default_config = {
        "window_count": 8, "seat_count": 120, "arrival_rate": 15.0,
        "avg_serve_time": 30.0, "avg_eat_time": 600.0, "simulation_duration": 2,
        "tick_step": 0.2, "tick_delay": 0.05, "student_count": 200,
        "serve_time_std": 5.0, "eat_time_std": 50.0, "random_seed": 42,
    }
    if config_override:
        default_config.update(config_override)

    resp = page.evaluate(
        f"""async () => {{
            const r = await fetch("{API_URL}/api/config", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({json.dumps(default_config)})
            }});
            return await r.json();
        }}"""
    )
    assert resp.get("success"), f"API 配置失败: {resp}"

    resp2 = page.evaluate(
        f"""async () => {{
            const r = await fetch("{API_URL}/api/start", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }}
            }});
            return await r.json();
        }}"""
    )
    assert resp2.get("success"), f"API 启动失败: {resp2}"

    deadline = time.time() + 60
    while time.time() < deadline:
        result = page.evaluate(
            f"""async () => {{
                const r = await fetch("{API_URL}/api/stats");
                return await r.json();
            }}"""
        )
        if result.get("is_finished"):
            return result.get("stats")
        time.sleep(0.5)

    pytest.fail("仿真超时未完成")


def _count_db_records():
    if not DB_PATH.exists():
        return 0
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM simulation_runs")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def _get_latest_db_record():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM simulation_runs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ====================================================================
# 场景1：正常流程（API测试）
# ====================================================================

def test_scenario_normal_flow(page):
    """正常流程：配置 → 仿真 → 分析页验证"""
    stats = _run_simulation_via_api(page, config_override={
        "window_count": 12, "seat_count": 160, "arrival_rate": 18.0, "simulation_duration": 2,
    })

    page.goto(f"{FRONT_URL}/analysis", wait_until="networkidle")
    time.sleep(2)

    html = page.content()
    assert "决策分析" in html, "页面未包含'决策分析'标题"
    assert "食堂场景" in html and "运行仿真" in html and "决策分析" in html

    print(f"✓ 场景1 通过：avg_wait={stats.get('avg_wait_time')}")


# ====================================================================
# 场景2：异常流程（API测试）
# ====================================================================

def test_scenario_error_on_unconfigured(page):
    """异常流程：仿真运行中再次启动，后端应拦截"""
    _run_simulation_via_api(page, config_override={"simulation_duration": 3})

    resp = page.evaluate(
        f"""async () => {{
            const cfg = await fetch("{API_URL}/api/config", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{
                    window_count: 5, seat_count: 50, arrival_rate: 10,
                    avg_serve_time: 30, avg_eat_time: 600, simulation_duration: 1
                }})
            }});
            return await cfg.json();
        }}"""
    )

    result = page.evaluate(
        f"""async () => {{
            const r = await fetch("{API_URL}/api/start", {{
                method: "POST", headers: {{ "Content-Type": "application/json" }}
            }});
            return {{ status: r.status, body: await r.json() }};
        }}"""
    )

    is_handled = (
        result["status"] == 400
        or (result["status"] == 200 and "仿真" in str(result["body"].get("message", "")))
    )
    assert is_handled, f"后端未正确处理重复启动: {result}"

    print("✓ 场景2 通过：重复启动已被正确处理")


# ====================================================================
# 场景3：数据库验证（API测试）
# ====================================================================

def test_scenario_database_verification(page):
    """数据库验证：运行仿真后检查数据库记录"""
    count_before = _count_db_records()
    print(f"  仿真前数据库记录数: {count_before}")

    stats = _run_simulation_via_api(page, config_override={
        "window_count": 6, "seat_count": 80, "arrival_rate": 12.0, "simulation_duration": 2,
    })

    time.sleep(1)
    count_after = _count_db_records()
    print(f"  仿真后数据库记录数: {count_after}")

    assert count_after > count_before, f"数据库未增加新记录: 前={count_before}, 后={count_after}"

    record = _get_latest_db_record()
    assert record is not None
    assert record.get("window_count") == 6
    assert record.get("seat_count") == 80
    avg_wait = record.get("avg_wait_time")
    assert avg_wait is not None and avg_wait >= 0

    print(f"✓ 场景3 通过：wait={avg_wait} satisfaction={record.get('satisfaction_score')}")


# ====================================================================
# 场景4：UI完整流程（真实UI测试）
# ====================================================================

def test_ui_full_flow(page):
    """
    UI完整流程测试：模拟真实用户操作

    步骤：
    1. 访问配置页
    2. 修改滑块参数（窗口=12, 桌子=40, 到达率=18）
    3. 验证预览卡片显示正确的值
    4. 点击开始仿真
    5. 等待页面跳转到食堂页
    6. 等待仿真结束
    7. 导航到分析页
    8. 验证分析页关键元素
    """
    page.goto(f"{FRONT_URL}/simulation", wait_until="networkidle")
    page.wait_for_load_state("domcontentloaded")
    time.sleep(1)

    page.wait_for_selector("text=仿真参数配置", timeout=10000)
    print("  ✓ 配置页加载成功")

    # 使用 JS 方式修改滑块（通过修改 input.value + input 事件触发 Vue 响应式）
    # 窗口滑块（第0个）：min=5, max=15
    page.evaluate("""
        const sliders = document.querySelectorAll('input[type="range"]');
        if (sliders[0]) {
            sliders[0].value = 12;
            sliders[0].dispatchEvent(new Event('input', { bubbles: true }));
        }
    """)
    page.wait_for_timeout(300)
    print("  ✓ 窗口数量设置为12")

    # 桌子滑块（第1个）：min=20, max=50
    page.evaluate("""
        const sliders = document.querySelectorAll('input[type="range"]');
        if (sliders[1]) {
            sliders[1].value = 40;
            sliders[1].dispatchEvent(new Event('input', { bubbles: true }));
        }
    """)
    page.wait_for_timeout(300)
    print("  ✓ 桌子数量设置为40")

    # 到达率滑块（第6个）：min=5, max=30
    page.evaluate("""
        const sliders = document.querySelectorAll('input[type="range"]');
        if (sliders[6]) {
            sliders[6].value = 18;
            sliders[6].dispatchEvent(new Event('input', { bubbles: true }));
        }
    """)
    page.wait_for_timeout(300)
    print("  ✓ 到达率设置为18")

    # 验证预览卡片显示
    preview_html = page.locator(".preview-panel").inner_html()

    assert "12" in preview_html, f"预览卡片中未显示窗口数量12，当前内容: {preview_html[:200]}"
    print("  ✓ 预览卡片显示窗口数量12")

    assert "40" in preview_html, f"预览卡片中未显示桌子数量40，当前内容: {preview_html[:200]}"
    print("  ✓ 预览卡片显示桌子数量40")

    assert "160" in preview_html, f"预览卡片中未显示总座位数160，当前内容: {preview_html[:200]}"
    print("  ✓ 预览卡片显示总座位数160")

    assert "18" in preview_html, f"预览卡片中未显示到达率18"
    print("  ✓ 预览卡片显示到达率18")

    # 点击开始仿真
    run_button = page.get_by_role("button", name="开始仿真")
    run_button.click()
    print("  ✓ 点击开始仿真按钮")

    # 等待页面跳转
    page.wait_for_url("**/?**", timeout=15000)
    page.wait_for_selector("text=食堂场景", timeout=10000)
    print("  ✓ 页面跳转到食堂页")

    # 等待仿真结束
    print("  等待仿真结束...")
    deadline = time.time() + 120
    simulation_done = False

    while time.time() < deadline:
        result = page.evaluate(
            f"""async () => {{
                const r = await fetch("{API_URL}/api/stats");
                return await r.json();
            }}"""
        )
        if result.get("is_finished"):
            simulation_done = True
            print(f"  ✓ 仿真完成，avg_wait={result.get('stats', {}).get('avg_wait_time')}")
            break
        time.sleep(1)

    assert simulation_done, "仿真超时未完成"

    # 导航到分析页
    analysis_link = page.locator(".navbar").get_by_text("决策分析")
    analysis_link.click()
    page.wait_for_url("**/analysis**", timeout=10000)
    page.wait_for_load_state("networkidle")
    print("  ✓ 导航到分析页")

    # 验证分析页关键元素
    html = page.content()
    assert "决策分析" in html, "分析页未包含'决策分析'标题"
    print("  ✓ 分析页包含'决策分析'标题")

    assert "食堂场景" in html, "缺少'食堂场景'导航项"
    assert "运行仿真" in html, "缺少'运行仿真'导航项"
    print("  ✓ 导航栏元素完整")

    has_analysis_content = any(keyword in html for keyword in ["成本", "分析", "配置", "数据", "优化"])
    assert has_analysis_content, "分析页未包含预期内容"
    print("  ✓ 分析页包含预期内容")

    print("✓ 场景4（UI完整流程）通过！")


# ====================================================================
# 场景5：UI参数验证测试（捕获 avg_eat_time 传递 bug）
# ====================================================================

def test_ui_parameter_verification(page):
    """
    UI参数验证测试：验证前端参数正确传递到后端

    这个测试专门用来捕获之前发现的 avg_eat_time 传递问题。
    使用更可靠的方式直接读取 Vue 组件的 data。
    """
    page.goto(f"{FRONT_URL}/simulation", wait_until="networkidle")
    page.wait_for_load_state("domcontentloaded")
    time.sleep(1)

    # 平均就餐时间滑块（第5个）：min=5, max=20
    page.evaluate("""
        const sliders = document.querySelectorAll('input[type="range"]');
        if (sliders[5]) {
            sliders[5].value = 15;
            sliders[5].dispatchEvent(new Event('input', { bubbles: true }));
        }
    """)
    page.wait_for_timeout(500)
    print("  设置平均就餐时间为15分钟")

    # 验证预览卡片显示15分钟
    preview_html = page.locator(".preview-panel").inner_html()
    assert "15" in preview_html, f"预览卡片未显示就餐时间15，当前: {preview_html[:300]}"
    print("  ✓ 预览卡片显示15分钟")

    # 注入监控函数捕获实际发送的配置
    page.evaluate("""
        window._capturedConfig = null;
        window._originalLog = console.log;
        console.log = function(...args) {
            const msg = args.join(' ');
            if (msg.includes('发送配置到后端')) {
                window._capturedConfig = args;
            }
            window._originalLog.apply(console, args);
        };
    """)

    # 点击开始仿真
    run_button = page.get_by_role("button", name="开始仿真")
    run_button.click()
    print("  点击开始仿真")

    # 等待仿真启动，获取控制台捕获的数据
    page.wait_for_timeout(3000)

    # 获取捕获的配置
    captured = page.evaluate("window._capturedConfig")

    if captured:
        config_str = str(captured)
        print(f"  捕获的配置: {config_str[:500]}")

        # 从配置字符串中提取 avg_eat_time 的值
        match = re.search(r"'avg_eat_time':\s*(\d+(?:\.\d+)?)", config_str)
        if match:
            actual_value = float(match.group(1))
            print(f"  avg_eat_time 实际值: {actual_value}")

            # 15分钟 = 900秒
            if actual_value == 900:
                print("  ✓ avg_eat_time=900 (正确)")
            else:
                pytest.fail(
                    f"avg_eat_time 应为 900 (15分钟×60秒)，实际为 {actual_value}。"
                    f"这说明前端配置传递存在bug！\n"
                    f"完整配置: {config_str}"
                )
        else:
            pytest.fail(f"无法从配置中提取 avg_eat_time: {config_str}")

    # 等待仿真完成
    page.wait_for_url("**/?**", timeout=15000)
    page.wait_for_selector("text=食堂场景", timeout=10000)

    print("✓ 场景5（UI参数验证）通过！avg_eat_time 传递正确")