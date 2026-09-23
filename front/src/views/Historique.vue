<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  CalendarDays,
  Download,
  FileText,
  LoaderCircle,
  Search,
  Sparkles,
} from '@lucide/vue'

import { downloadMeetingReport, listMeetings } from '@/service/api'



const route = useRoute()
const router = useRouter()

const meetings = ref([])
const searchQuery = ref(typeof route.query.q === 'string' ? route.query.q : '')
const isLoading = ref(true)
const errorMessage = ref('')
const downloadingMeetingId = ref(null)
const downloadError = ref('')

const filteredMeetings = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  if (!query) {
    return meetings.value
  }

  return meetings.value.filter((meeting) => {
    return [
      meeting.title,
      meeting.participants,
      meeting.summary_short,
      meeting.summary_long,
    ]
      .filter(Boolean)
      .some((value) => value.toLowerCase().includes(query))
  })
})

function formatDate(value) {
  if (!value) {
    return 'Date non renseignée'
  }

  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function downloadReport(meeting) {
  if (!meeting?.id || !meeting.report_path) {
    return
  }

  try {
    downloadingMeetingId.value = meeting.id
    downloadError.value = ''

    await downloadMeetingReport(meeting.id)
  } catch (error) {
    if (error.status === 401) {
      router.push('/login')
      return
    }

    downloadError.value =
      error.message || 'Impossible de télécharger le compte rendu Word.'
  } finally {
    downloadingMeetingId.value = null
  }
}


async function loadMeetings() {
  try {
    isLoading.value = true
    errorMessage.value = ''
    meetings.value = await listMeetings()
  } catch (error) {
    if (error.status === 401) {
      router.push('/login')
      return
    }

    errorMessage.value = error.message || 'Impossible de charger les réunions.'
  } finally {
    isLoading.value = false
  }
}

watch(
  () => route.query.q,
  value => {
    searchQuery.value = typeof value === 'string' ? value : ''
  },
)

onMounted(loadMeetings)
</script>

<template>
  <section class="min-h-full rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
    <header class="flex flex-col gap-4 border-b border-slate-100 pb-5 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <p class="text-xs font-black uppercase tracking-normal text-blue-600">Mémoire d'équipe</p>
        <h1 class="mt-2 text-2xl font-black text-slate-900">Historique des réunions</h1>
        <p class="mt-1 max-w-2xl text-sm font-semibold leading-6 text-slate-500">
          Retrouvez les transcriptions, résumés courts et comptes rendus générés dans votre organisation.
        </p>
      </div>

      <RouterLink
        class="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-black text-white shadow-lg shadow-blue-100 transition hover:bg-blue-700"
        to="/reunion">
        <Sparkles class="h-4 w-4" />
        Nouvelle réunion
      </RouterLink>
    </header>

    <div class="mt-5 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <label class="relative block w-full lg:max-w-md">
        <Search class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input v-model="searchQuery"
          class="h-12 w-full rounded-lg border border-slate-200 bg-white pl-11 pr-4 text-sm font-semibold text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
          type="search" placeholder="Rechercher une réunion, un participant, une décision..." />
      </label>

      <p class="text-sm font-bold text-slate-500">
        {{ filteredMeetings.length }} réunion{{ filteredMeetings.length > 1 ? 's' : '' }}
      </p>
    </div>

    <p v-if="downloadError"
      class="mt-5 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold text-red-600">
      {{ downloadError }}
    </p>

    <div v-if="isLoading" class="mt-6 grid gap-3">
      <div v-for="index in 5" :key="index" class="h-24 rounded-xl bg-slate-100"></div>
    </div>

    <p v-else-if="errorMessage"
      class="mt-6 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold text-red-600">
      {{ errorMessage }}
    </p>

    <div v-else-if="filteredMeetings.length" class="mt-6 overflow-hidden rounded-xl border border-slate-200">
      <div
        class="grid grid-cols-[1.2fr_0.9fr_0.9fr_auto] gap-4 border-b border-slate-200 bg-slate-50 px-5 py-3 text-xs font-black uppercase text-slate-400">
        <span>Réunion</span>
        <span>Participants</span>
        <span>Date</span>
        <span class="text-right">Document</span>
      </div>

      <article v-for="meeting in filteredMeetings" :key="meeting.id"
        class="grid grid-cols-[1.2fr_0.9fr_0.9fr_auto] overflow-y items-center gap-4 border-b border-slate-100 px-5 py-4 last:border-b-0">
        <div class="min-w-0">
          <div class="flex items-center gap-3">
            <span class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-blue-50 text-blue-600">
              <FileText class="h-5 w-5" />
            </span>
            <div class="min-w-0">
              <h2 class="truncate text-sm font-black text-slate-900">{{ meeting.title }}</h2>
              <p class="mt-1 line-clamp-1 text-xs font-semibold text-slate-500">
                {{ meeting.summary_short || meeting.summary_long || 'Résumé non généré.' }}
              </p>
            </div>
          </div>
        </div>

        <p class="truncate text-sm font-semibold text-slate-600">
          {{ meeting.participants || 'Non renseignés' }}
        </p>

        <p class="flex items-center gap-2 text-sm font-semibold text-slate-500">
          <CalendarDays class="h-4 w-4 text-slate-400" />
          {{ formatDate(meeting.created_at || meeting.date) }}
        </p>

        <div class="flex min-w-36 justify-end">
          <button v-if="meeting.report_path"
            class="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-black text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            :disabled="downloadingMeetingId !== null" type="button" @click="downloadReport(meeting)">
            <LoaderCircle v-if="downloadingMeetingId === meeting.id" class="h-4 w-4 animate-spin" />
            <Download v-else class="h-4 w-4" />

            {{
              downloadingMeetingId === meeting.id
                ? 'Téléchargement...'
                : 'Télécharger'
            }}
          </button>

          <span v-else class="rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold text-slate-400">
            Indisponible
          </span>
        </div>
      </article>
    </div>

    <div v-else
      class="mt-8 grid place-items-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 py-14 text-center">
      <div class="grid h-14 w-14 place-items-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-100">
        <FileText class="h-7 w-7" />
      </div>
      <h2 class="mt-5 text-lg font-black text-slate-900">Aucune réunion enregistrée</h2>
      <p class="mt-2 max-w-md text-sm font-semibold leading-6 text-slate-500">
        Lancez votre première transcription pour construire la mémoire de votre organisation.
      </p>
      <RouterLink
        class="mt-6 inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-black text-white shadow-lg shadow-blue-100 transition hover:bg-blue-700"
        to="/reunion">
        <Sparkles class="h-4 w-4" />
        Créer une réunion
      </RouterLink>
    </div>
  </section>
</template>
