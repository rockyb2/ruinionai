<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { ChevronRight, Clock3, FileText, LogOut, Plus, Settings } from '@lucide/vue'

import logo from '@/assets/logo.png'
import { getCurrentUser, listMeetings, logoutUser } from '@/service/api'

const router = useRouter()

const session = ref(null)
const recentMeetings = ref([])
const isLoading = ref(true)

const user = computed(() => session.value?.user)
const organization = computed(() => session.value?.organization)
const role = computed(() => session.value?.role)

const userName = computed(() => {
  if (!user.value) {
    return 'Utilisateur'
  }

  return `${user.value.first_name || ''} ${user.value.last_name || ''}`.trim()
})

const initials = computed(() => {
  const first = user.value?.first_name?.[0] || ''
  const last = user.value?.last_name?.[0] || ''
  return `${first}${last}`.toUpperCase() || 'UA'
})

const navItems = [
  {
    label: 'Historique',
    to: '/historique',
    icon: Clock3,
  },
  {
    label: 'Paramètres',
    to: '/setting',
    icon: Settings,
  },
]

function formatMeetingDate(value) {
  if (!value) {
    return 'Date non renseignée'
  }

  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function loadSidebarData() {
  try {
    isLoading.value = true
    const currentSession = await getCurrentUser()
    session.value = currentSession

    try {
      const meetings = await listMeetings()
      recentMeetings.value = meetings.slice(0, 4)
    } catch {
      recentMeetings.value = []
    }
  } catch {
    logoutUser()
    router.push('/login')
  } finally {
    isLoading.value = false
  }
}

function handleLogout() {
  logoutUser()
  router.push('/login')
}

onMounted(loadSidebarData)
</script>

<template>
  <aside class="flex w-full shrink-0 flex-col rounded-2xl border border-slate-200 bg-white px-5 py-5 shadow-sm lg:sticky lg:top-2 lg:h-[calc(100vh-1rem)] lg:w-72">
    <RouterLink class="mb-6 flex items-center justify-center" to="/reunion">
      <img :src="logo" alt="Ruinion AI" class="h-24 object-contain" />
    </RouterLink>

    <RouterLink
      to="/reunion"
      class="mb-5 flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-blue-700"
      active-class="bg-blue-700"
    >
      <Plus class="h-4 w-4" />
      Nouvelle réunion
    </RouterLink>

    <nav class="grid gap-2 sm:grid-cols-2 lg:block lg:space-y-2">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-bold text-slate-600 transition hover:bg-slate-50 hover:text-blue-600"
        active-class="bg-blue-50 text-blue-600"
      >
        <component :is="item.icon" class="h-4 w-4" />
        {{ item.label }}
      </RouterLink>
    </nav>

    <div class="my-5 border-t border-slate-100"></div>

    <section class="min-h-0">
      <div class="mb-3 flex items-center justify-between">
        <p class="text-xs font-black uppercase text-slate-400">Récentes</p>
        <RouterLink class="text-xs font-black text-blue-600 transition hover:text-blue-700" to="/historique">
          Voir
        </RouterLink>
      </div>

      <div v-if="isLoading" class="space-y-2">
        <div v-for="index in 3" :key="index" class="h-12 rounded-lg bg-slate-100"></div>
      </div>

      <div v-else-if="recentMeetings.length" class="space-y-2">
        <button
          v-for="meeting in recentMeetings"
          :key="meeting.id"
          class="flex w-full items-start gap-3 rounded-lg px-3 py-2 text-left transition hover:bg-blue-50"
          type="button"
        >
          <FileText class="mt-1 h-4 w-4 text-blue-600" />
          <div class="min-w-0 flex-1">
            <p class="truncate text-xs font-black text-slate-700">{{ meeting.title }}</p>
            <p class="text-xs text-slate-500">{{ formatMeetingDate(meeting.created_at || meeting.date) }}</p>
          </div>
        </button>
      </div>

      <p v-else class="rounded-lg bg-slate-50 px-3 py-3 text-xs font-semibold leading-5 text-slate-500">
        Aucune réunion pour le moment.
      </p>
    </section>

    <div class="mt-auto space-y-3">
      <div class="rounded-xl border border-slate-200 p-3">
        <div class="flex items-center gap-3">
          <div class="grid h-10 w-10 place-items-center rounded-full bg-blue-600 text-sm font-black text-white">
            {{ initials }}
          </div>

          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-black text-slate-800">{{ userName }}</p>
            <p class="truncate text-xs text-slate-500">{{ user?.email || 'Session active' }}</p>
          </div>

          <ChevronRight class="h-4 w-4 text-slate-400" />
        </div>

        <div class="mt-3 rounded-lg bg-slate-50 px-3 py-2">
          <p class="truncate text-xs font-black text-slate-700">
            {{ organization?.name || 'Organisation' }}
          </p>
          <p class="mt-1 text-[11px] font-bold uppercase text-blue-600">
            {{ role || 'member' }}
          </p>
        </div>
      </div>

      <button
        class="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 px-4 py-3 text-sm font-black text-slate-600 transition hover:border-red-100 hover:bg-red-50 hover:text-red-600"
        type="button"
        @click="handleLogout"
      >
        <LogOut class="h-4 w-4" />
        Se déconnecter
      </button>
    </div>
  </aside>
</template>
