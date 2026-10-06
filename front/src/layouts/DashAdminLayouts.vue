<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SideBar from '../components/admin/SideBar.vue'
import AdminIcon from '../components/admin/AdminIcon.vue'
import { navigation, toast } from '../admin/demo'
import { adminRequest } from '../service/admin'
import { logoutUser } from '../service/api'
import '../admin/admin.css'

const route = useRoute(), router = useRouter()
const current = computed(() => navigation.find(item => item.path === route.path) || navigation[0])
const connectedPages = ['/admin/organisations', '/admin/utilisateurs', '/admin/reunions']
const isDemo = computed(() => !connectedPages.includes(route.path))
const menuOpen = ref(false), profileOpen = ref(false), loading = ref(true), accessError = ref(''), admin = ref(null)
const adminName = computed(() => [admin.value?.first_name, admin.value?.last_name].filter(Boolean).join(' ') || admin.value?.email || 'Administration')
const initials = computed(() => adminName.value.split(/\s+/).slice(0, 2).map(value => value[0]).join('').toUpperCase())

async function verifyAccess() {
  loading.value = true
  try { admin.value = await adminRequest('/me'); accessError.value = '' }
  catch (error) {
    accessError.value = error.status === 403 ? 'Votre compte n’a pas les droits de super administrateur.' : error.message
    if (error.status === 401) router.replace({ name: 'login', query: { redirect: route.fullPath } })
  } finally { loading.value = false }
}
function logout() { logoutUser(); router.push({ name: 'login' }) }
watch(() => route.path, () => { menuOpen.value = false; profileOpen.value = false; document.title = `${current.value.label} · Administration Ruinion AI` }, { immediate: true })
onMounted(verifyAccess)
</script>

<template>
  <div class="admin-app" @keydown.esc="menuOpen = false; profileOpen = false">
    <a href="#admin-content" class="a-skip-link">Aller au contenu</a>
    <button v-if="menuOpen" class="a-menu-backdrop" aria-label="Fermer le menu" @click="menuOpen = false" />
    <div class="a-sidebar-container" :class="{ open: menuOpen }"><SideBar @navigate="menuOpen = false" /></div>
    <main id="admin-content" class="a-main">
      <header class="a-page-header"><div class="a-page-title"><button class="a-icon-button a-mobile-menu" aria-label="Ouvrir le menu administrateur" :aria-expanded="menuOpen" @click="menuOpen = !menuOpen"><AdminIcon name="menu" /></button><div><h1>{{ current.label }}</h1><p>{{ current.description }}</p></div></div>
        <div class="a-header-actions"><span v-if="isDemo" class="a-demo-badge"><span class="a-dot" />Interface de démonstration</span>
          <div v-if="admin" class="a-popover-anchor"><button class="a-profile" :aria-expanded="profileOpen" @click="profileOpen = !profileOpen"><span class="a-profile-avatar">{{ initials }}</span><span><strong>Super administrateur</strong><small>{{ adminName }}</small></span><AdminIcon name="down" :size="16" /></button><div v-if="profileOpen" class="a-popover"><p>{{ admin.email }}</p><RouterLink to="/reunion">Retour à l’application</RouterLink><button class="a-button a-spaced" @click="logout">Se déconnecter</button></div></div>
        </div></header>
      <section v-if="loading" class="a-card a-panel" role="status">Vérification des droits administrateur…</section>
      <section v-else-if="accessError" class="a-card a-panel"><h2>Accès refusé</h2><p class="a-danger-text a-spaced">{{ accessError }}</p><div class="a-actions a-spaced"><RouterLink class="a-button" to="/reunion">Retour à l’application</RouterLink><button class="a-button" @click="logout">Se connecter avec un autre compte</button></div></section>
      <RouterView v-else />
      <footer class="a-page-footer"><span>Ruinion AI · Espace administrateur sécurisé</span><span>{{ isDemo ? 'Données fictives sur cette page' : 'Données de la plateforme' }}</span></footer>
    </main>
    <Transition name="a-toast"><div v-if="toast" class="a-toast-message" role="status"><AdminIcon name="success" /><span>{{ toast }}</span><button aria-label="Fermer le message" @click="toast = ''"><AdminIcon name="x" :size="16" /></button></div></Transition>
  </div>
</template>
