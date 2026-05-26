<template>
  <div class="app">
    <nav class="navbar">
      <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
        <span class="nav-icon">🍽️</span>
        食堂场景
      </router-link>
      <router-link to="/simulation" class="nav-link" :class="{ active: $route.path === '/simulation' }">
        <span class="nav-icon">⚙️</span>
        运行仿真
      </router-link>
      <router-link to="/analysis" class="nav-link" :class="{ active: $route.path === '/analysis' }">
        <span class="nav-icon">📊</span>
        决策分析
      </router-link>
    </nav>

    <router-view />
  </div>
</template>

<script setup>
// App.vue 只是作为路由容器
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.app {
  min-height: 100vh;
}

.navbar {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  display: flex;
  gap: 1rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.nav-link {
  color: #4a5568;
  text-decoration: none;
  font-size: 1.1rem;
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.nav-link:hover {
  background: #f7fafc;
  color: #4299e1;
  transform: translateY(-2px);
}

.nav-link.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.nav-icon {
  font-size: 1.2rem;
}
</style>