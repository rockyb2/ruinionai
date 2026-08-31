<template>
  <aside class="flex rounded-2xl border h-[90] w-72 flex-col  border-slate-200 bg-white px-6 py-5 shadow-sm">
    <div class="mb-6 flex items-center justify-center gap-3">
      <img :src="logo" alt="Reunion AI" class="h-30 " />
      
    </div>

    <RouterLink
      to="/reunion"
      class="mb-5 flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-3 text-sm font-bold text-white shadow-sm hover:bg-blue-700"
    >
      <Plus class="h-4 w-4" />
      Nouvelle réunion
    </RouterLink>

    <nav class="space-y-2">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-bold text-slate-600 hover:bg-slate-50 hover:text-blue-600"
        active-class="bg-blue-50 text-blue-600"
      >
        <component :is="item.icon" class="h-4 w-4" />
        {{ item.label }}
      </RouterLink>
    </nav>

    <div class="my-5 border-t border-slate-100"></div>

    <div>
      <p class="mb-3 text-xs font-black uppercase text-slate-400">Récentes</p>

      <div class="space-y-2">
        <button
          v-for="meeting in recentMeetings"
          :key="meeting.title"
          class="flex w-full items-start gap-3 rounded-lg px-3 py-2 text-left hover:bg-blue-50"
        >
          <FileText class="mt-1 h-4 w-4 text-blue-600" />
          <div class="min-w-0 flex-1">
            <p class="truncate text-xs font-black text-slate-700">{{ meeting.title }}</p>
            <p class="text-xs text-slate-500">{{ meeting.date }}</p>
          </div>
        </button>
      </div>
    </div>

    <div class="mt-auto rounded-xl border border-slate-200 p-3">
      <div class="flex items-center gap-3">
        <div class="grid h-10 w-10 place-items-center rounded-full bg-blue-600 text-sm font-black text-white">
          AD
        </div>

        <div class="min-w-0 flex-1">
          <p class="text-sm font-black text-slate-800">Admin</p>
          <p class="truncate text-xs text-slate-500">admin@reunionai.com</p>
        </div>

        <ChevronDown class="h-4 w-4 text-slate-500" />
      </div>
    </div>
  </aside>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import { ChevronDown, Clock3, FileText, Home, Plus, Settings } from '@lucide/vue'
import logo from '@/assets/logo.png'

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

const recentMeetings = [
  {
    title: 'Réunion commerciale',
    date: '29 août, 10:30',
  },
  {
    title: 'Réunion direction',
    date: '28 août, 15:45',
  },
  {
    title: 'Projet CRM - Point hebdo',
    date: '27 août, 11:00',
  },
  {
    title: 'Brainstorming produit',
    date: '26 août, 09:15',
  },
]
</script>