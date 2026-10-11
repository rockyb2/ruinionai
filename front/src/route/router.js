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
    meta: { requiresAuth: true, title: 'Ruinion AI' },
    children: [
      {
        path: '',
        redirect: '/reunion',
      },
      {
        path: 'reunion',
        name: 'reunion',
        component: Reunion,
        meta: { title: 'Nouvelle réunion' },
      },
      {
        path: 'historique',
        name: 'historique',
        component: Historique,
        meta: { title: 'Historique' },
      },
      {
        path: 'equipe',
        name: 'equipe',
        component: Equipe,
        meta: { title: 'Équipe' },
      },
      {
        path: 'setting',
        name: 'setting',
        component: Setting,
        meta: { title: 'Paramètres' },
      },
    ],
  },
  {
    path: '/invitation',
    name: 'invitation',
    component: Invitation,
    meta: { title: 'Invitation' },
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: { guestOnly: true, title: 'Connexion' },
  },
  {
    path: '/signin',
    name: 'signin',
    component: Signin,
    meta: { guestOnly: true, title: 'Créer un compte' },
  },

  // route administration
  {
    path: '/admin',
    component: () => import('../layouts/DashAdminLayouts.vue'),
    // Le layout vérifie /admin/me avant de monter les vues. Les routes API
    // appliquent également l'autorisation, indépendamment du navigateur.
    meta: { requiresAuth: true, admin: true, title: 'Administration' },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard',
      },
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: () => import('../views/admin/Dashboard.vue'),
        meta: { title: 'Vue d’ensemble', admin: true },
      },
      {
        path: 'utilisateurs',
        name: 'admin-utilisateurs',
        component: () => import('../views/admin/Utilisateurs.vue'),
        meta: { title: 'Utilisateurs', admin: true },
      },
      {
        path: 'usage',
        name: 'admin-usage',
        component: () => import('../views/admin/Usage.vue'),
        meta: { title: 'Usage & coûts', admin: true },
      },
      {
        path: 'reunions',
        name: 'admin-reunions',
        component: () => import('../views/admin/Reunions.vue'),
        meta: { title: 'Réunions', admin: true },
      },
      {
        path: 'audit',
        name: 'admin-audit',
        component: () => import('../views/admin/Audit.vue'),
        meta: { title: 'Audit & sécurité', admin: true },
      },
      {
        path: 'abonnements',
        name: 'admin-abonnements',
        component: () => import('../views/admin/Abonnements.vue'),
        meta: { title: 'Abonnements', admin: true },
      },
      {
        path: 'configurations',
        name: 'admin-configurations',
        component: () => import('../views/admin/Configurations.vue'),
        meta: { title: 'Configuration', admin: true },
      },
      {
        path: 'aifournisseurs',
        name: 'admin-aifournisseurs',
        component: () => import('../views/admin/AIfournisseurs.vue'),
        meta: { title: 'IA & fournisseurs', admin: true },
      },
      {
        path: 'organisations',
        name: 'admin-organisations',
        component: () => import('../views/admin/Organisations.vue'),
        meta: { title: 'Organisations', admin: true },
      },
      {
        path: 'incidents',
        name: 'admin-incidents',
        component: () => import('../views/admin/Incidents.vue'),
        meta: { title: 'Incidents', admin: true },
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

router.afterEach((to) => {
  const title = to.meta.title || 'Ruinion AI'
  document.title = to.meta.admin
    ? `${title} · Administration Ruinion AI`
    : title === 'Ruinion AI'
      ? title
      : `${title} · Ruinion AI`
})

export default router
