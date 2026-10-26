import { createRouter, createWebHistory } from 'vue-router'

import Dashlayouts from '../layouts/Dashlayouts.vue'
import ConditionsUtilisation from '../views/ConditionsUtilisation.vue'
import Equipe from '../views/Equipe.vue'
import Historique from '../views/Historique.vue'
import Invitation from '../views/Invitation.vue'
import Login from '../views/Login.vue'
import NotFound from '../views/NotFound.vue'
import PolitiqueConfidentialite from '../views/PolitiqueConfidentialite.vue'
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
        redirect: '/réunion',
      },
      {
        path: 'réunion',
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
        path: 'équipe',
        name: 'equipe',
        component: Equipe,
        meta: { title: 'Équipe' },
      },
      {
        path: 'paramètres',
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
    path: '/politique-de-confidentialité',
    name: 'politique-confidentialite',
    component: PolitiqueConfidentialite,
    meta: { title: 'Politique de confidentialité' },
  },
  {
    path: '/conditions-d-utilisation',
    name: 'conditions-utilisation',
    component: ConditionsUtilisation,
    meta: { title: 'Conditions d’utilisation' },
  },
  {
    path: '/connexion',
    name: 'login',
    component: Login,
    meta: { guestOnly: true, title: 'Connexion' },
  },
  {
    path: '/inscription',
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
        redirect: '/admin/tableau-de-bord',
      },
      {
        path: 'tableau-de-bord',
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
        path: 'utilisation-coûts',
        name: 'admin-usage',
        component: () => import('../views/admin/Usage.vue'),
        meta: { title: 'Usage & coûts', admin: true },
      },
      {
        path: 'réunions',
        name: 'admin-reunions',
        component: () => import('../views/admin/Reunions.vue'),
        meta: { title: 'Réunions', admin: true },
      },
      {
        path: 'audit-sécurité',
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
        path: 'configuration',
        name: 'admin-configurations',
        component: () => import('../views/admin/Configurations.vue'),
        meta: { title: 'Configuration', admin: true },
      },
      {
        path: 'ia-fournisseurs',
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
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFound,
    meta: { title: 'Page introuvable' },
  },
]

const FRENCH_PATHS = {
  '/reunion': '/réunion',
  '/equipe': '/équipe',
  '/parametres': '/paramètres',
  '/politique-de-confidentialite': '/politique-de-confidentialité',
  '/admin/reunions': '/admin/réunions',
  '/admin/audit-securite': '/admin/audit-sécurité',
  '/admin/utilisation-couts': '/admin/utilisation-coûts',
}

function normalizePath(path) {
  let decodedPath = path

  try {
    decodedPath = decodeURI(path)
  } catch {
    // Une URL mal encodée reste inchangée et aboutira à la page 404.
  }

  const normalizedPath = decodedPath.normalize('NFC')
  return FRENCH_PATHS[normalizedPath] || normalizedPath
}

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const normalizedPath = normalizePath(to.path)

  if (normalizedPath !== to.path) {
    return {
      path: normalizedPath,
      query: to.query,
      hash: to.hash,
      replace: true,
    }
  }

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
