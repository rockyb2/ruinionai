<script setup>
import {
  Building2,
  ChevronRight,
  Clock3,
  FileText,
  Plus,
  Settings,
  Users,
  X,
} from '@lucide/vue'

import logo from '@/assets/logo.png'

defineProps({
  open: { type: Boolean, default: false },
  organization: { type: Object, default: null },
  recentMeetings: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

defineEmits(['close'])

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
        <img :src="logo" alt="Ruionin AI" class="h-20 w-auto object-contain" />
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

    <RouterLink
      :to="{ name: 'reunion' }"
      class="mt-6 flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 font-semibold text-white shadow-lg shadow-blue-600/20 transition hover:bg-blue-700"
      @click="$emit('close')"
    >
      <Plus class="h-5 w-5" />
      Nouvelle réunion
    </RouterLink>

    <nav class="mt-6 space-y-1" aria-label="Sections">
      <RouterLink
        v-for="item in navItems"
        :key="item.name"
        :to="{ name: item.name }"
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

    <RouterLink
      :to="{ name: 'setting' }"
      class="mt-5 flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 transition hover:border-blue-200 hover:bg-blue-50"
      @click="$emit('close')"
    >
      <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white">
        <Building2 class="h-5 w-5" />
      </span>
      <span class="min-w-0 flex-1">
        <span class="block truncate text-sm font-bold text-slate-900">
          {{ organization?.name || 'Mon organisation' }}
        </span>
        <span class="block text-xs text-slate-500">Organisation active</span>
      </span>
      <ChevronRight class="h-4 w-4 text-slate-400" />
    </RouterLink>
  </aside>
</template>
