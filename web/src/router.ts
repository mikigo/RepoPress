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
      path: '/editor/:repoId([a-zA-Z0-9-]+)?',
      name: 'editor',
      component: () => import('./views/Editor.vue'),
      meta: { auth: true },
    },
    {
      path: '/editor/:repoId([a-zA-Z0-9-]+)/:path(.*)',
      name: 'editor-file',
      component: () => import('./views/Editor.vue'),
      meta: { auth: true },
    },
    {
      path: '/user',
      name: 'user',
      component: () => import('./views/UserView.vue'),
      meta: { auth: true, admin: true },
    },
    {
      path: '/setting',
      name: 'setting',
      component: () => import('./views/SettingView.vue'),
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
