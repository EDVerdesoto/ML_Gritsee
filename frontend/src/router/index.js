import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'
// Layouts y Vistas
import MainLayout from '../layouts/MainLayout.vue'
import DashboardView from '../views/DashboardView.vue'
import UploadView from '../views/UploadView.vue'
import HistoryView from '../views/HistoryView.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // RUTA PÚBLICA: LOGIN
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { guest: true }
    },

    // RUTAS PROTEGIDAS (DASHBOARD, ETC)
    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'dashboard', component: DashboardView },
        { path: 'carga', name: 'upload', component: UploadView },
        { path: 'historial', name: 'history', component: HistoryView }
      ]
    }
  ]
})

// --- NAVIGATION GUARD ---
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  // Si la ruta requiere auth
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // Si hay usuario en localStorage, confiamos (la cookie se valida en cada request)
    if (userStore.user) {
      next()
      return
    }
    
    // Si no hay usuario en localStorage, verificamos con el backend
    const isAuthenticated = await userStore.checkAuth()
    if (!isAuthenticated) {
      next('/login')
      return
    }
  }

  // Si ya estamos logueados e intentamos ir al Login -> Dashboard
  if (to.matched.some(record => record.meta.guest)) {
    if (userStore.user) {
      next('/')
      return
    }
  }

  next()
})

export default router