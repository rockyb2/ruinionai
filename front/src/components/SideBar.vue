<script setup>
import { computed } from 'vue'
import {
  ChevronDown,
  ChevronRight,
  Clock3,
  FileText,
  Plus,
  Settings,
  Users,
  X,
} from '@lucide/vue'

import logo from '@/assets/logo.png'
import { useStartNewMeeting } from '@/composables/useStartNewMeeting'
import OnboardingChecklist from '@/components/OnboardingChecklist.vue'

const startNewMeeting = useStartNewMeeting()

const props = defineProps({
  open: { type: Boolean, default: false },
  user: { type: Object, default: null },
  role: { type: String, default: 'member' },
  recentMeetings: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'logout', 'restart-onboarding'])

const userName = computed(() =>
  [props.user?.first_name, props.user?.last_name].filter(Boolean).join(' ') || 'Utilisateur',
)
const initials = computed(() => {
  const first = props.user?.first_name?.[0] || ''
  const last = props.user?.last_name?.[0] || ''
  return `${first}${last}`.toUpperCase() || 'UA'
})
const roleLabel = computed(() => ({
  owner: 'Propriétaire',
  admin: 'Administrateur',
  member: 'Membre',
})[props.role?.toLowerCase()] || 'Membre')

async function handleNewMeeting() {
  emit('close')
  await startNewMeeting()
}

const navItems = [
  { name: 'historique', label: 'Historique', icon: Clock3 },
  { name: 'equipe', label: 'Équipe', icon: Users },
  { name: 'setting', label: 'Paramètres', icon: Settings },
]

function formatMeetingDate(value) {
  if (!value) return ''

  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <aside
    class="fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-200 bg-white px-5 py-6 shadow-xl transition-transform duration-200 lg:translate-x-0 lg:shadow-none"
    :class="open ? 'translate-x-0' : '-translate-x-full'"
    aria-label="Navigation principale"
  >
    <div class="flex items-center justify-between px-2">
      <RouterLink :to="{ name: 'reunion' }" @click="$emit('close')">
        <img :src="logo" alt="Ruinion AI" class="h-16 w-auto object-contain" />
      </RouterLink>

      <button
        type="button"
        class="rounded-xl p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
        aria-label="Fermer le menu"
        @click="$emit('close')"
      >
        <X class="h-5 w-5" />
      </button>
    </div>

    <button
      data-tour="sidebar-new-meeting"
      type="button"
      class="mt-4 flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 font-semibold text-white shadow-lg shadow-blue-600/20 transition hover:bg-blue-700"
      @click="handleNewMeeting"
    >
      <Plus class="h-5 w-5" />
      Nouvelle réunion
    </button>

    <nav class="mt-4 space-y-1" aria-label="Sections">
      <RouterLink
        v-for="item in navItems"
        :key="item.name"
        :to="{ name: item.name }"
        :data-tour="`sidebar-${item.name === 'equipe' ? 'team' : item.name === 'historique' ? 'history' : 'settings'}`"
        class="flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
        active-class="bg-blue-50 text-blue-700"
        @click="$emit('close')"
      >
        <component :is="item.icon" class="h-5 w-5" />
        {{ item.label }}
      </RouterLink>
    </nav>

    <div class="my-5 border-t border-slate-200" />

    <section class="min-h-0 flex-1 overflow-y-auto px-1">
      <div class="mb-3 flex items-center justify-between px-2">
        <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Récentes</p>
        <RouterLink
          :to="{ name: 'historique' }"
          class="text-xs font-semibold text-blue-600 hover:text-blue-700"
          @click="$emit('close')"
        >
          Voir
        </RouterLink>
      </div>

      <div v-if="loading" class="space-y-2 px-2">
        <div v-for="index in 4" :key="index" class="h-12 animate-pulse rounded-xl bg-slate-100" />
      </div>

      <div v-else-if="recentMeetings.length" class="space-y-1">
        <RouterLink
          v-for="meeting in recentMeetings"
          :key="meeting.id"
          :to="{ name: 'historique', query: { meeting: meeting.id } }"
          class="flex items-start gap-3 rounded-xl px-3 py-2.5 transition hover:bg-slate-100"
          @click="$emit('close')"
        >
          <FileText class="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
          <span class="min-w-0">
            <span class="block truncate text-sm font-semibold text-slate-700">{{ meeting.title }}</span>
            <span class="block text-xs text-slate-400">{{ formatMeetingDate(meeting.date || meeting.created_at) }}</span>
          </span>
        </RouterLink>
      </div>

      <p v-else class="px-3 py-4 text-sm text-slate-400">Aucune réunion récente.</p>
    </section>

    <OnboardingChecklist v-if="user" :key="user.id" :user="user" :role="role" class="mt-3" />

    <details v-if="user" data-tour="profile-menu" class="group relative mt-3 shrink-0 border-t border-slate-200 pt-3">
      <summary class="flex list-none items-center gap-3 rounded-xl px-2 py-2 transition hover:bg-slate-100">
        <span class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-blue-600 text-sm font-black text-white">
          {{ initials }}
        </span>
        <span class="min-w-0 flex-1 text-left">
          <strong class="block truncate text-sm text-slate-800">{{ userName }}</strong>
          <span class="block truncate text-[11px] font-medium text-slate-400">{{ user.email }}</span>
        </span>
        <ChevronRight class="h-4 w-4 text-slate-400 transition group-open:rotate-90" />
      </summary>

      <div class="absolute bottom-full left-0 right-0 z-20 mb-2 rounded-xl border border-slate-200 bg-white p-2 shadow-xl">
        <div class="flex items-start justify-between gap-2 px-2 py-2">
          <div class="min-w-0">
            <p class="truncate text-xs font-black text-slate-800">{{ userName }}</p>
            <p class="mt-0.5 text-[10px] font-black uppercase tracking-wide text-blue-600">{{ roleLabel }}</p>
          </div>
          <ChevronDown class="h-4 w-4 text-slate-400" />
        </div>
        <RouterLink class="block rounded-lg px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" :to="{ name: 'setting' }" @click="$emit('close')">
          Paramètres
        </RouterLink>
        <button class="mt-0.5 w-full rounded-lg px-3 py-2 text-left text-xs font-bold text-blue-600 hover:bg-blue-50" type="button" @click="$emit('restart-onboarding', $event)">
          Revoir le tutoriel
        </button>
        <button class="mt-0.5 w-full rounded-lg px-3 py-2 text-left text-xs font-bold text-red-600 hover:bg-red-50" type="button" @click="$emit('logout')">
          Se déconnecter
        </button>
      </div>
    </details>
  </aside>
</template>
