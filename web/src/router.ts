import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores.js'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('./views/Login.vue'),
      meta: { guest: true },
    },
    {
      path: '/editor/:repoId(\\d+)?',
      name: 'editor',
      component: () => import('./views/Editor.vue'),
      meta: { auth: true },
    },
    {
      path: '/editor/:repoId(\\d+)/:path(.*)',
      name: 'editor-file',
      component: () => import('./views/Editor.vue'),
      meta: { auth: true },
    },
    {
      path: '/admin/repos',
      name: 'admin-repos',
      component: () => import('./views/AdminRepos.vue'),
      meta: { auth: true, admin: true },
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('./views/AdminUsers.vue'),
      meta: { auth: true, admin: true },
    },
    {
      path: '/admin/permissions',
      name: 'admin-permissions',
      component: () => import('./views/AdminPerms.vue'),
      meta: { auth: true, admin: true },
    },
    {
      path: '/admin/settings',
      name: 'admin-settings',
      component: () => import('./views/AdminSettings.vue'),
      meta: { auth: true, admin: true },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/editor',
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  if (to.meta.auth) {
    if (!authStore.token) {
      return next('/login')
    }
    if (!authStore.user) {
      try {
        await authStore.fetchUser()
      } catch {
        authStore.logout()
        return next('/login')
      }
    }
    if (to.meta.admin && !authStore.isAdmin) {
      return next('/editor')
    }
  }

  if (to.meta.guest && authStore.token) {
    return next('/editor')
  }

  next()
})

export default router
