<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import {
  Bell,
  CheckCheck,
  LoaderCircle,
  Menu,
  X,
} from '@lucide/vue'

import SideBar from '../components/SideBar.vue'
import { useOnboardingStore } from '@/stores/onboarding'
import {
  getCurrentUser,
  listMeetings,
  listOrganizationNotifications,
  logoutUser,
  markAllOrganizationNotificationsRead,
  markOrganizationNotificationRead,
  syncOrganizationNotifications,
} from '@/service/api'

const router = useRouter()
const route = useRoute()
const onboarding = useOnboardingStore()
const session = ref(null)
const recentMeetings = ref([])
const isLoading = ref(true)
const mobileMenuOpen = ref(false)
const notificationDialog = ref(null)
const notifications = ref([])
const notificationTotal = ref(0)
const unreadNotifications = ref(0)
const notificationsLoading = ref(false)
const notificationsError = ref('')

const user = computed(() => session.value?.user)
const organization = computed(() => session.value?.organization)
const role = computed(() => session.value?.role)
const canSeeNotifications = computed(() => Boolean(organization.value))
const canSyncTeamInvitations = computed(() => ['owner', 'admin'].includes(role.value))
let notificationTimer

function formatNotificationDate(value) {
  if (!value) return ''
  const normalized = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : value + 'Z'
  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(normalized))
}

function notificationLabel(kind) {
  return {
    invitation_expiring: 'Bientôt expirée',
    invitation_expired: 'Expirée',
    invitation_accepted: 'Acceptée',
    meeting_invitation: 'Réunion',
  }[kind] || 'Invitation'
}

async function loadNotifications({ sync = false, quiet = false } = {}) {
  if (!canSeeNotifications.value || notificationsLoading.value) return
  if (!quiet) {
    notificationsLoading.value = true
    notificationsError.value = ''
  }
  try {
    if (sync && canSyncTeamInvitations.value) await syncOrganizationNotifications()
    const result = await listOrganizationNotifications({ limit: 20 })
    notifications.value = result.items
    notificationTotal.value = result.total
    unreadNotifications.value = result.unread_count
  } catch (error) {
    if (!quiet) notificationsError.value = error.message || 'Impossible de charger les notifications.'
  } finally {
    notificationsLoading.value = false
  }
}

async function openNotifications() {
  notificationDialog.value?.showModal()
  await loadNotifications({ sync: true })
}

async function readNotification(notification) {
  try {
    if (!notification.is_read) {
      const updated = await markOrganizationNotificationRead(notification.id)
      notifications.value = notifications.value.map((item) =>
        item.id === updated.id ? updated : item,
      )
      unreadNotifications.value = Math.max(0, unreadNotifications.value - 1)
    }
    if (notification.meeting_id) {
      notificationDialog.value?.close()
      await router.push({ name: 'historique', query: { meeting: notification.meeting_id } })
    }
  } catch (error) {
    notificationsError.value = error.message || 'Impossible de mettre à jour la notification.'
  }
}

async function readAllNotifications() {
  if (!unreadNotifications.value) return
  try {
    await markAllOrganizationNotificationsRead()
    notifications.value = notifications.value.map((item) => ({
      ...item,
      is_read: true,
      read_at: item.read_at || new Date().toISOString(),
    }))
    unreadNotifications.value = 0
  } catch (error) {
    notificationsError.value = error.message || 'Impossible de mettre à jour les notifications.'
  }
}

async function handleLogout() {
  await logoutUser()
  await router.push('/connexion')
}

async function restartOnboarding(event) {
  event.currentTarget.closest('details')?.removeAttribute('open')
  await onboarding.reset()
}

function handleOrganizationUpdated(event) {
  if (!session.value?.organization || !event.detail) return
  session.value = {
    ...session.value,
    organization: {
      ...session.value.organization,
      ...event.detail,
    },
  }
}

function refreshNotifications() {
  if (document.visibilityState === 'visible') loadNotifications({ quiet: true })
}

async function refreshMeetings() {
  try { recentMeetings.value = await listMeetings({ limit: 4 }) } catch { /* Keep the current list on a temporary failure. */ }
}

async function loadLayout() {
  isLoading.value = true
  try {
    session.value = await getCurrentUser()
  } catch {
    await logoutUser()
    await router.push('/connexion')
    return
  }

  const meetingsResult = await Promise.allSettled([
    listMeetings({ limit: 4 }),
    loadNotifications({ sync: true }),
  ])
  recentMeetings.value = meetingsResult[0].status === 'fulfilled'
    ? meetingsResult[0].value.slice(0, 4)
    : []
  isLoading.value = false
}

onMounted(() => {
  loadLayout()
  window.addEventListener('organization-updated', handleOrganizationUpdated)
  window.addEventListener('meeting-created', refreshMeetings)
  window.addEventListener('focus', refreshNotifications)
  notificationTimer = window.setInterval(refreshNotifications, 30000)
})
onBeforeUnmount(() => {
  window.removeEventListener('organization-updated', handleOrganizationUpdated)
  window.removeEventListener('meeting-created', refreshMeetings)
  window.removeEventListener('focus', refreshNotifications)
  window.clearInterval(notificationTimer)
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <div
      v-if="mobileMenuOpen"
      class="fixed inset-0 z-40 bg-slate-950/40 lg:hidden"
      @click="mobileMenuOpen = false"
    ></div>

    <SideBar
      :open="mobileMenuOpen"
      :user="user"
      :role="role"
      :recent-meetings="recentMeetings"
      :loading="isLoading"
      @close="mobileMenuOpen = false"
      @logout="handleLogout"
      @restart-onboarding="restartOnboarding"
    />

    <div class="min-h-screen lg:pl-72">
      <header class="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-6">
        <button
          class="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-slate-200 text-slate-600 lg:hidden"
          type="button"
          aria-label="Ouvrir la navigation"
          @click="mobileMenuOpen = true"
        >
          <Menu class="h-5 w-5" />
        </button>

        <div class="ml-auto flex shrink-0 items-center gap-2 sm:gap-3">
          <button
            v-if="canSeeNotifications"
            data-tour="notifications"
            class="relative grid h-11 w-11 place-items-center rounded-xl border border-slate-200 text-slate-600 transition hover:bg-blue-50 hover:text-blue-600"
            type="button"
            aria-label="Notifications"
            @click="openNotifications"
          >
            <Bell class="h-5 w-5" />
            <span
              v-if="unreadNotifications"
              class="absolute right-1.5 top-1.5 min-w-4 rounded-full bg-red-500 px-1 text-center text-[10px] leading-4 text-white"
            >
              {{ unreadNotifications > 9 ? '9+' : unreadNotifications }}
            </span>
          </button>

        </div>
      </header>

      <main class="min-w-0 p-4 sm:p-6">
        <div class="mx-auto w-full max-w-[1600px]">
          <RouterView :key="route.fullPath" />
        </div>
      </main>
    </div>

    <dialog
      ref="notificationDialog"
      class="m-auto w-[min(520px,calc(100vw-32px))] rounded-2xl border border-slate-200 bg-white p-0 text-slate-900 shadow-2xl backdrop:bg-slate-950/40"
    >
      <header class="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5">
        <div>
          <h2 class="text-lg font-black">Notifications</h2>
          <p class="mt-1 text-sm font-semibold text-slate-500">Activité récente des invitations.</p>
        </div>
        <button class="grid h-9 w-9 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700" type="button" aria-label="Fermer" @click="notificationDialog.close()">
          <X class="h-5 w-5" />
        </button>
      </header>

      <div class="max-h-[60vh] overflow-y-auto p-4">
        <div v-if="notificationsLoading" class="flex items-center justify-center gap-3 py-12 text-sm font-bold text-slate-500">
          <LoaderCircle class="h-5 w-5 animate-spin text-blue-600" />
          Chargement…
        </div>
        <p v-else-if="notificationsError" class="rounded-xl bg-red-50 p-4 text-sm font-bold text-red-700" role="alert">
          {{ notificationsError }}
        </p>
        <p v-else-if="!notifications.length" class="rounded-xl bg-slate-50 p-8 text-center text-sm font-semibold text-slate-500">
          Aucune notification pour le moment.
        </p>
        <template v-else>
          <button
            v-for="notification in notifications"
            :key="notification.id"
            class="mb-2 flex w-full gap-3 rounded-xl border p-4 text-left transition hover:border-blue-200 hover:bg-blue-50/50"
            :class="notification.is_read ? 'border-slate-100 bg-white' : 'border-blue-100 bg-blue-50/40'"
            type="button"
            @click="readNotification(notification)"
          >
            <span class="mt-1 h-2.5 w-2.5 shrink-0 rounded-full" :class="notification.is_read ? 'bg-slate-300' : 'bg-blue-600'"></span>
            <span class="min-w-0 flex-1">
              <span class="flex flex-wrap items-center justify-between gap-2">
                <strong class="text-sm">{{ notification.title }}</strong>
                <span class="text-[11px] font-bold text-blue-600">{{ notificationLabel(notification.kind) }}</span>
              </span>
              <span class="mt-1 block text-xs font-semibold leading-5 text-slate-500">{{ notification.message }}</span>
              <span v-if="notification.meeting_id" class="mt-2 block text-xs font-bold text-blue-600">Voir la réunion →</span>
              <span class="mt-2 block text-[11px] font-semibold text-slate-400">{{ formatNotificationDate(notification.created_at) }}</span>
            </span>
          </button>
        </template>
      </div>

      <footer class="flex items-center justify-between gap-4 border-t border-slate-100 px-6 py-4">
        <span class="text-xs font-bold text-slate-500">{{ unreadNotifications }} non lue(s)</span>
        <button class="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-black text-blue-600 hover:bg-blue-50 disabled:text-slate-300" type="button" :disabled="!unreadNotifications" @click="readAllNotifications">
          <CheckCheck class="h-4 w-4" />
          Tout marquer comme lu
        </button>
      </footer>
    </dialog>
  </div>
</template>
