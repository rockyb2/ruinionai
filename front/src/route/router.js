import { createRouter, createWebHistory } from 'vue-router'

import Dashlayouts from '../layouts/Dashlayouts.vue'
import Equipe from '../views/Equipe.vue'
import Historique from '../views/Historique.vue'
import Invitation from '../views/Invitation.vue'
import Login from '../views/Login.vue'
import Reunion from '../views/Reunion.vue'
import Setting from '../views/Setting.vue'
import Signin from '../views/Signin.vue'
import { isAuthenticated } from '../service/api'

const routes = [
  {
    path: '/',
    component: Dashlayouts,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/reunion',
      },
      {
        path: 'reunion',
        name: 'reunion',
        component: Reunion,
      },
      {
        path: 'historique',
        name: 'historique',
        component: Historique,
      },
      {
        path: 'equipe',
        name: 'equipe',
        component: Equipe,
      },
      {
        path: 'setting',
        name: 'setting',
        component: Setting,
      },
    ],
  },
  {
    path: '/invitation',
    name: 'invitation',
    component: Invitation,
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: { guestOnly: true },
  },
  {
    path: '/signin',
    name: 'signin',
    component: Signin,
    meta: { guestOnly: true },
  },

  // route administration
  {
    path: '/admin',
    component: () => import('../layouts/DashAdminLayouts.vue'),
    // Prévisualisation publique contenant uniquement des données fictives.
    // Une autorisation serveur sera nécessaire avant de brancher des données réelles.
    meta: { adminDemo: true },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard',
      },
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: () => import('../views/admin/Dashboard.vue'),
      },
      {
        path: 'utilisateurs',
        name: 'admin-utilisateurs',
        component: () => import('../views/admin/Utilisateurs.vue'),
      },
      {
        path: 'usage',
        name: 'admin-usage',
        component: () => import('../views/admin/Usage.vue'),
      },
      {
        path: 'reunions',
        name: 'admin-reunions',
        component: () => import('../views/admin/Reunions.vue'),
      },
      {
        path: 'audit',
        name: 'admin-audit',
        component: () => import('../views/admin/Audit.vue'),
      },
      {
        path: 'abonnements',
        name: 'admin-abonnements',
        component: () => import('../views/admin/Abonnements.vue'),
      },
      {
        path: 'configurations',
        name: 'admin-configurations',
        component: () => import('../views/admin/Configurations.vue'),
      },
      {
        path: 'aifournisseurs',
        name: 'admin-aifournisseurs',
        component: () => import('../views/admin/AIfournisseurs.vue'),
      },
      {
        path: 'organisations',
        name: 'admin-organisations',
        component: () => import('../views/admin/Organisations.vue'),
      },
      {
        path: 'incidents',
        name: 'admin-incidents',
        component: () => import('../views/admin/Incidents.vue'),
      },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const loggedIn = isAuthenticated()

  if (to.matched.some((route) => route.meta.requiresAuth) && !loggedIn) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.guestOnly && loggedIn) {
    return { name: 'reunion' }
  }

  return true
})

export default router
