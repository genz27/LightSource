import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/auth',
      name: 'auth',
      component: () => import('../components/AuthForm.vue'),
    },
    
    {
      path: '/generator',
      name: 'generator',
      component: () => import('../views/GeneratorView.vue'),
    },
    {
      path: '/assets',
      name: 'assets',
      component: () => import('../views/AssetsView.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/admin/AdminLayout.vue'),
      children: [
        {
          path: '',
          name: 'admin-home',
          component: () => import('../views/admin/AdminLanding.vue'),
        },
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('../views/admin/AdminUsers.vue'),
        },
        {
          path: 'assets',
          name: 'admin-assets',
          component: () => import('../views/admin/AdminAssets.vue'),
        },
        {
          path: 'jobs',
          name: 'admin-jobs',
          component: () => import('../views/admin/AdminJobs.vue'),
        },
        {
          path: 'providers',
          name: 'admin-providers',
          component: () => import('../views/admin/AdminProviders.vue'),
        },
        {
          path: 'insights',
          name: 'admin-insights',
          component: () => import('../views/admin/AdminInsights.vue'),
        },
        {
          path: 'billing',
          name: 'admin-billing',
          component: () => import('../views/admin/AdminBilling.vue'),
        }
      ]
    },
  ],
})

  // Navigation guards
  router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()
    const protectedRoutes = ['/generator', '/assets', '/settings']
    const requiresAuth = protectedRoutes.includes(to.path)
    const isAdminRoute = to.path.startsWith('/admin')

    if (requiresAuth || isAdminRoute) {
      if (!authStore.isAuthenticated) {
        next('/auth')
        return
      }
      if (!authStore.user) {
        try { await authStore.rotateTokens() } catch {}
        try { await authStore.fetchMe() } catch {}
      }
    }

    if (isAdminRoute) {
      const role = authStore.user?.role?.toLowerCase()
      if (role !== 'admin') {
        next('/settings')
        return
      }
    }

    if (to.path === '/auth' && authStore.isAuthenticated) {
      const role = authStore.user?.role?.toLowerCase()
      next(role === 'admin' ? '/admin' : '/settings')
      return
    }

    next()
  })

export default router
