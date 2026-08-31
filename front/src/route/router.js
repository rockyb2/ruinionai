import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Signin from '../views/Signin.vue'
import Historique from '../views/Historique.vue'
import Reunion from '../views/Reunion.vue'
import Setting from '../views/Setting.vue'
import Dashlayouts from '../layouts/Dashlayouts.vue'

const routes = [
  {
    path: '/',
    component: Dashlayouts,
    children: [
      {
        path: 'reunion',
        name: 'reunion',
        component: Reunion
      },
      {
        path: 'historique',
        name: 'historique',
        component: Historique
      },
      
      {
        path: 'setting',
        name: 'setting',
        component: Setting
      }
    ]

  },
  {
    path: '/login',
    name: 'login',
    component: Login,
  },
  {
    path: '/signin',
    name: 'signin',
    component: Signin,
  },

]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
