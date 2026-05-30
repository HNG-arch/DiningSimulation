<template>
  <div class="app">
    <nav class="navbar">
      <div class="nav-brand">
        <div class="brand-mark">仿</div>
        <span class="brand-name">BJTU 食堂仿真系统</span>
      </div>
      <div class="nav-links">
        <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
          食堂场景
        </router-link>
        <router-link to="/simulation" class="nav-link" :class="{ active: $route.path === '/simulation' }">
          运行仿真
        </router-link>
        <router-link to="/analysis" class="nav-link" :class="{ active: $route.path === '/analysis' }">
          决策分析
        </router-link>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #F8FAFC;
  min-height: 100vh;
  color: #0F172A;
}
.app { min-height: 100vh; display: flex; flex-direction: column; }

.navbar {
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid #E2E8F0;
  padding: 0 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 54px;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-mark {
  width: 30px;
  height: 30px;
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35);
}

.brand-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #0F172A;
  letter-spacing: -0.2px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 2px;
}

.nav-link {
  color: #64748B;
  text-decoration: none;
  font-size: 0.865rem;
  padding: 6px 14px;
  border-radius: 6px;
  transition: color 0.15s, background 0.15s;
  font-weight: 500;
}

.nav-link:hover {
  color: #4F46E5;
  background: #EEF2FF;
}

.nav-link.active {
  color: #4F46E5;
  background: #EEF2FF;
  font-weight: 600;
}
</style>
