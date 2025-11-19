<template>
  <div class="app">
    <header class="top-bar">
      <div class="top-bar-inner">
      <div class="brand">LightSource</div>
      <nav class="main-nav">
        <RouterLink 
          to="/" 
          class="pill" 
          :class="{ active: $route.path === '/' }"
        >
          Index
        </RouterLink>
        <RouterLink 
          v-if="authStore.isAuthenticated"
          to="/generator" 
          class="pill" 
          :class="{ active: $route.path === '/generator' }"
        >
          Generators
        </RouterLink>
      <RouterLink 
          v-if="authStore.isAuthenticated"
          to="/assets" 
          class="pill" 
          :class="{ active: $route.path === '/assets' }"
        >
          Library
        </RouterLink>
        <RouterLink 
          v-if="authStore.isAuthenticated && authStore.user?.role?.toLowerCase() === 'admin'"
          to="/admin" 
          class="pill" 
          :class="{ active: $route.path.startsWith('/admin') }"
        >
          Admin
        </RouterLink>
        <RouterLink 
          v-if="authStore.isAuthenticated"
          to="/settings" 
          class="pill" 
          :class="{ active: $route.path === '/settings' }"
        >
          Settings
        </RouterLink>
      </nav>
      <div class="actions">
        <template v-if="!authStore.isAuthenticated">
          <RouterLink to="/auth" class="ghost" aria-label="Register account">Register</RouterLink>
          <RouterLink to="/auth" class="pill accent">Login</RouterLink>
        </template>
        <template v-else>
          <RouterLink to="/settings" class="avatar" aria-label="User settings">
            {{ authStore.user?.username?.charAt(0).toUpperCase() || 'LS' }}
          </RouterLink>
          <button class="pill" @click="handleLogout">Logout</button>
        </template>
      </div>
      </div>
    </header>

    <main>
      <slot />
    </main>

    <footer class="site-footer">
      <div class="footer-links">
        <span>Docs</span><span>Status</span><span>Security</span><span>Contact</span>
      </div>
      <div class="footer-links">
        <span>(c) 2025 LightSource</span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { onMounted } from 'vue'

const authStore = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  authStore.logout()
  router.push('/auth')
}

onMounted(async () => {
  try {
    if (authStore.isAuthenticated && !authStore.user) {
      await authStore.fetchMe()
    }
  } catch {}
})
</script>

<style scoped>
.app {
  width: 100%;
  max-width: 100%;
  margin: 0;
  padding: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.top-bar {
  background: #0b0b0d;
  border-bottom: 1px solid var(--border);
  padding: 0 40px;
  height: var(--header-height, 80px);
  box-shadow: var(--shadow);
  position: sticky;
  top: 0;
  z-index: 100;
}

.top-bar-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: var(--container-width, 1200px);
  margin: 0 auto;
  width: 100%;
}

.brand {
  font-weight: 800;
  letter-spacing: 0.5px;
  font-size: 20px;
  color: var(--accent);
}

.main-nav,
.actions {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.pill {
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--pill);
  color: var(--text);
  padding: 10px 18px;
  font-size: 14px;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s ease;
}

.pill:hover {
  border-color: #2f2f33;
  background: #25252a;
}

.pill.active {
  border-color: var(--accent);
  background: var(--accent);
  color: #1a1a1a;
  font-weight: 700;
}

.pill.accent {
  background: var(--accent);
  color: #1a1a1a;
  border: none;
  font-weight: 700;
}

.ghost {
  color: var(--muted);
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 10px;
  background: transparent;
  border: 1px solid transparent;
  text-decoration: none;
  transition: all 0.2s ease;
}

.ghost:hover {
  border-color: var(--border);
  background: rgba(255, 255, 255, 0.05);
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--panel-soft);
  border: 1px solid var(--border);
  display: grid;
  place-items: center;
  font-size: 14px;
  color: var(--muted);
  font-weight: 700;
  text-decoration: none;
  transition: all 0.2s ease;
}

.avatar:hover {
  border-color: var(--accent);
}

main {
  flex: 1;
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  padding: var(--space-5, 40px) var(--space-5, 40px) var(--space-10, 80px);
}

.site-footer {
  margin-top: auto;
  padding: var(--space-4, 32px) var(--space-5, 40px);
  border-top: 1px solid var(--border);
  color: var(--muted);
  display: grid;
  gap: var(--space-2, 16px);
  font-size: var(--font-size-sm, 14px);
  width: 100%;
  max-width: var(--container-width, 1200px);
  margin: auto auto 0 auto;
}

.footer-links {
  display: flex;
  gap: var(--space-2, 16px);
  flex-wrap: wrap;
}

/* Desktop (1200px and up) */
@media (min-width: 1200px) {
  .top-bar {
    padding: var(--space-3, 24px) var(--space-6, 48px);
  }
  
  main {
    padding: var(--space-6, 48px) var(--space-6, 48px) var(--space-9, 72px);
    max-width: 100%;
  }
  
  .site-footer {
    padding: var(--space-5, 40px) var(--space-6, 48px);
    max-width: var(--container-width, 1200px);
  }
}

/* Tablet (768px to 1199px) */
@media (min-width: 768px) and (max-width: 1199px) {
  .top-bar {
    padding: var(--space-3, 24px) var(--space-5, 40px);
  }
  
  main {
    padding: var(--space-5, 40px) var(--space-5, 40px) var(--space-8, 64px);
    max-width: 100%;
  }
  
  .site-footer {
    padding: var(--space-4, 32px) var(--space-5, 40px);
    max-width: var(--container-width, 1200px);
  }
}

/* Mobile (767px and below) */
@media (max-width: 767px) {
  .top-bar {
    flex-direction: column;
    gap: var(--space-2, 16px);
    align-items: stretch;
    padding: var(--space-2, 16px) var(--space-2, 16px);
    position: relative;
  }
  
  .main-nav {
    justify-content: center;
    flex-wrap: wrap;
    gap: 20px;
  }
  
  .actions {
    justify-content: center;
    gap: 20px;
  }
  
  main {
    padding: var(--space-3, 24px) var(--space-2, 16px) var(--space-6, 48px);
    max-width: 100%;
  }
  
  .site-footer {
    padding: var(--space-3, 24px) var(--space-2, 16px);
    max-width: 100%;
  }
}
</style>