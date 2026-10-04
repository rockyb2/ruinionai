import { createRouter, createWebHistory } from 'vue-router'

import Dashlayouts from '../layouts/Dashlayouts.vue'
import Equipe from '../views/Equipe.vue'
import Historique from '../views/Historique.vue'
import Invitation from '../views/Invitation.vue'
import Login from '../views/Login.vue'
import Reunion from '../views/Reunion.vue'
import Setting from '../views/Setting.vue'
import Signin from '../views/Signin.vue'
import DashAdminLayouts from '../layouts/DashAdminLayouts.vue'
import Dashboard from '../views/admin/Dashboard.vue'
import Utilisateurs from '../views/admin/Utilisateurs.vue'
import Usage from '../views/admin/Usage.vue'
import Reunions from '../views/admin/Reunions.vue'
import Audit from '../views/admin/Audit.vue'
import Abonnements from '../views/admin/Abonnements.vue'
import Configurations from '../views/admin/Configurations.vue'
import AIfournisseurs from '../views/admin/AIfournisseurs.vue'
import Organisations from '../views/admin/Organisations.vue'
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
    component: DashAdminLayouts,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard',
      },
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: Dashboard,
      },
      {
        path: 'utilisateurs',
        name: 'admin-utilisateurs',
        component: Utilisateurs,
      },
      {
        path: 'usage',
        name: 'admin-usage',
        component: Usage,
      },
      {
        path: 'reunions',
        name: 'admin-reunions',
        component: Reunions,
      },
      {
        path: 'audit',
        name: 'admin-audit',
        component: Audit,
      },
      {
        path: 'abonnements',
        name: 'admin-abonnements',
        component: Abonnements,
      },
      {
        path: 'configurations',
        name: 'admin-configurations',
        component: Configurations,
      },
      {
        path: 'aifournisseurs',
        name: 'admin-aifournisseurs',
        component: AIfournisseurs,
      },
      {
        path: 'organisations',
        name: 'admin-organisations',
        component: Organisations,
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
