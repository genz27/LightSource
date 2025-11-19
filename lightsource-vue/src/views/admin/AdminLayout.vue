<template>
  <AppLayout>
    <div class="admin-wrap">
      <aside class="admin-sidebar">
        <h2 class="admin-title">Admin</h2>
        <nav class="admin-nav">
          <RouterLink to="/admin" class="nav-pill" :class="{ active: $route.name === 'admin-home' }">Overview</RouterLink>
          <RouterLink to="/admin/users" class="nav-pill" :class="{ active: $route.name === 'admin-users' }">Users</RouterLink>
          <RouterLink to="/admin/assets" class="nav-pill" :class="{ active: $route.name === 'admin-assets' }">Assets</RouterLink>
          <RouterLink to="/admin/jobs" class="nav-pill" :class="{ active: $route.name === 'admin-jobs' }">Jobs</RouterLink>
          <RouterLink to="/admin/providers" class="nav-pill" :class="{ active: $route.name === 'admin-providers' }">Providers</RouterLink>
          <RouterLink to="/admin/billing" class="nav-pill" :class="{ active: $route.name === 'admin-billing' }">Billing</RouterLink>
        </nav>
      </aside>
      <section class="admin-content">
        <RouterView />
      </section>
    </div>
  </AppLayout>
  
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
</script>

<style scoped>
.admin-wrap {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 24px;
  max-width: var(--container-width, 1200px);
  margin: 0 auto;
}

.admin-sidebar {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  position: sticky;
  top: calc(var(--header-height, 80px) + 24px);
  align-self: start;
}

.admin-title {
  margin: 0 0 12px;
  font-size: 18px;
}

.admin-nav {
  display: grid;
  gap: 8px;
}

.nav-pill {
  display: block;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--pill);
  color: var(--text);
  padding: 10px 16px;
  font-size: 14px;
  text-decoration: none;
}

.nav-pill.active {
  border-color: var(--accent);
  background: var(--accent);
  color: #111;
  font-weight: 700;
}

.admin-content {
  display: grid;
  gap: 16px;
  min-width: 0;
  max-width: var(--container-width, 1200px);
}

@media (max-width: 1024px) {
  .admin-wrap {
    grid-template-columns: 1fr;
  }
  .admin-sidebar {
    position: static;
  }
}
</style>