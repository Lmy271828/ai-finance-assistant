<script setup lang="ts">
/**
 * App.vue —— 只是路由出口，不是主页
 *
 * 全局壳子（导航栏）放这里，三个页面共享的部分放这里。
 * 具体业务内容全在 views/ 里。
 */
</script>

<template>
  <div class="app">
    <header class="app-header">
      <nav class="nav">
        <RouterLink to="/bill" class="nav-item">账单</RouterLink>
        <RouterLink to="/import" class="nav-item">导入</RouterLink>
      </nav>
      <div class="brand">AI 财务助手</div>
    </header>

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-2) var(--space-4);
  background: var(--color-card);
  border-bottom: 1px solid var(--color-border);
}
.nav {
  display: flex;
  gap: var(--space-3);
}
.nav-item {
  color: var(--color-muted);
  text-decoration: none;
  padding: var(--space-1) var(--space-2);
}
.nav-item.router-link-active {
  color: var(--color-text);
  font-weight: 600;
}
.brand {
  margin-left: auto;
  color: var(--color-muted);
}
.app-main {
  max-width: 960px;
  margin: 0 auto;
  padding: var(--space-4);
}
</style>
