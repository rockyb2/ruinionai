<script setup>
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import SideBar from "../components/admin/SideBar.vue";
import AdminIcon from "../components/admin/AdminIcon.vue";
import { navigation, toast, alerts } from "../admin/demo";
import "../admin/admin.css";
const route = useRoute();
const current = computed(
  () => navigation.find((item) => item.path === route.path) || navigation[0],
);
const menuOpen = ref(false),
  notificationsOpen = ref(false),
  profileOpen = ref(false);
watch(
  () => route.path,
  () => {
    menuOpen.value = false;
    notificationsOpen.value = false;
    profileOpen.value = false;
    document.title = `${current.value.label} · Administration Ruinion AI`;
  },
  { immediate: true },
);
</script>
<template>
  <div
    class="admin-app"
    @keydown.esc="
      menuOpen = false;
      notificationsOpen = false;
      profileOpen = false;
    "
  >
    <a href="#admin-content" class="a-skip-link">Aller au contenu</a>
    <button
      v-if="menuOpen"
      class="a-menu-backdrop"
      aria-label="Fermer le menu"
      @click="menuOpen = false"
    />
    <div class="a-sidebar-container" :class="{ open: menuOpen }">
      <SideBar @navigate="menuOpen = false" />
    </div>
    <main id="admin-content" class="a-main">
      <header class="a-page-header">
        <div class="a-page-title">
          <button
            class="a-icon-button a-mobile-menu"
            aria-label="Ouvrir le menu administrateur"
            :aria-expanded="menuOpen"
            @click="menuOpen = !menuOpen"
          >
            <AdminIcon name="menu" />
          </button>
          <div>
            <h1>{{ current.label }}</h1>
            <p>{{ current.description }}</p>
          </div>
        </div>
        <div class="a-header-actions">
          <span class="a-demo-badge"
            ><span class="a-dot" />Données de démonstration</span
          >
          <div class="a-popover-anchor">
            <button
              class="a-icon-button a-notification-button"
              aria-label="Afficher les notifications"
              :aria-expanded="notificationsOpen"
              @click="
                notificationsOpen = !notificationsOpen;
                profileOpen = false;
              "
            >
              <AdminIcon name="bell" :size="22" /><b>3</b>
            </button>
            <section v-if="notificationsOpen" class="a-popover">
              <h3>Notifications de démonstration</h3>
              <RouterLink
                v-for="alert in alerts"
                :key="alert.title"
                to="/admin/incidents"
                ><strong>{{ alert.title }}</strong
                ><span>{{ alert.text }}</span
                ><small>{{ alert.time }}</small></RouterLink
              >
            </section>
          </div>
          <div class="a-popover-anchor">
            <button
              class="a-profile"
              :aria-expanded="profileOpen"
              @click="
                profileOpen = !profileOpen;
                notificationsOpen = false;
              "
            >
              <span class="a-profile-avatar">CA</span
              ><span
                ><strong>Super administrateur</strong
                ><small>Charles · Démonstration</small></span
              ><AdminIcon name="down" :size="16" />
            </button>
            <div v-if="profileOpen" class="a-popover">
              <p>Profil fictif pour la prévisualisation des interfaces.</p>
              <RouterLink to="/admin/configurations"
                >Paramètres de la plateforme</RouterLink
              ><RouterLink to="/reunion">Retour à l’application</RouterLink>
            </div>
          </div>
        </div>
      </header>
      <RouterView />
      <footer class="a-page-footer">
        <span>Ruinion AI · Espace administrateur</span
        ><span>Maquette interactive · Septembre 2026</span>
      </footer>
    </main>
    <Transition name="a-toast"
      ><div v-if="toast" class="a-toast-message" role="status">
        <AdminIcon name="success" /><span>{{ toast }}</span
        ><button aria-label="Fermer le message" @click="toast = ''">
          <AdminIcon name="x" :size="16" />
        </button></div
    ></Transition>
  </div>
</template>
