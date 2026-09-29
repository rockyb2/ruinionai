<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowUpRight, CalendarDays, FileText, Headphones, LoaderCircle, Plus, Search, Users } from '@lucide/vue'
import { listMeetings } from '@/service/api'
import MeetingDetail from '@/components/MeetingDetail.vue'
import { formatMeetingDate, formatTime, isProcessing, statusLabel } from '@/utils/meeting'

const route = useRoute()
const router = useRouter()
const meetings = ref([])
const searchQuery = ref(typeof route.query.q === 'string' ? route.query.q : '')
const filter = ref('all')
const sort = ref('recent')
const loading = ref(true)
const error = ref('')
let timer
let disposed = false
let requestNumber = 0
const selectedMeetingId = computed(() => {
  const id = Number(route.query.meeting)
  return Number.isSafeInteger(id) && id > 0 ? id : null
})
const filters = [
  { id: 'all', label: 'Toutes les réunions' }, { id: 'completed', label: 'Terminées' },
  { id: 'processing', label: 'En cours' }, { id: 'failed', label: 'À relancer' },
]
const matchesFilter = (meeting, value) => value === 'all'
  || (value === 'completed' && statusLabel(meeting) === 'Terminé')
  || (value === 'processing' && isProcessing(meeting))
  || (value === 'failed' && meeting.processing_status === 'failed')
const filteredMeetings = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase('fr')
  return meetings.value.filter(meeting => matchesFilter(meeting, filter.value)
    && [meeting.title, meeting.participants, meeting.summary_short, meeting.summary_long, meeting.transcription]
      .some(text => (text || '').toLocaleLowerCase('fr').includes(query)))
    .sort((a, b) => {
      if (sort.value === 'title') return a.title.localeCompare(b.title, 'fr')
      const difference = new Date(a.date || a.created_at || 0) - new Date(b.date || b.created_at || 0) || a.id - b.id
      return sort.value === 'oldest' ? difference : -difference
    })
})
function names(meeting) { return (meeting.participants || '').split(',').map(name => name.trim()).filter(Boolean) }
async function loadMeetings() {
  clearTimeout(timer)
  const request = ++requestNumber
  try {
    const result = await listMeetings()
    if (disposed || request !== requestNumber) return
    meetings.value = result
    error.value = ''
  } catch (failure) {
    if (disposed || request !== requestNumber) return
    if (failure.status === 401) router.push('/login')
    error.value = failure.message || 'Impossible de charger les réunions.'
  } finally {
    if (!disposed && request === requestNumber) {
      loading.value = false
      if (!selectedMeetingId.value) timer = setTimeout(loadMeetings, meetings.value.some(isProcessing) ? 3000 : 15000)
    }
  }
}
watch(() => route.query.q, value => { searchQuery.value = typeof value === 'string' ? value : '' })
watch(selectedMeetingId, value => { clearTimeout(timer); if (!value) loadMeetings() })
onMounted(() => { if (!selectedMeetingId.value) loadMeetings() })
onUnmounted(() => { disposed = true; clearTimeout(timer) })
</script>

<template>
  <MeetingDetail v-if="selectedMeetingId" :key="selectedMeetingId" :meeting-id="selectedMeetingId" />
  <section v-else class="min-h-full min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
    <header class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <p class="text-xs font-bold uppercase tracking-wider text-blue-600">Mémoire d’équipe</p>
        <h1 class="mt-2 text-2xl font-black tracking-tight text-slate-900">Historique des réunions</h1>
        <p class="mt-2 text-sm text-slate-500">Vos échanges, vos décisions et vos enregistrements, au même endroit.</p>
      </div>
      <RouterLink to="/reunion" class="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-blue-100 hover:bg-blue-700"><Plus class="h-4 w-4" /> Nouvelle réunion</RouterLink>
    </header>

    <div class="mt-7 flex flex-col justify-between gap-4 border-b border-slate-100 pb-5 2xl:flex-row 2xl:items-center">
      <div class="flex flex-wrap gap-2" aria-label="Filtrer les réunions">
        <button v-for="item in filters" :key="item.id" @click="filter = item.id" :aria-pressed="filter === item.id"
          class="flex items-center gap-2 rounded-lg px-3 py-2.5 text-xs font-bold transition sm:text-sm"
          :class="filter === item.id ? 'bg-blue-50 text-blue-600' : 'text-slate-500 hover:bg-slate-50'">
          {{ item.label }} <span class="rounded-md px-1.5 py-0.5 text-[10px]" :class="filter === item.id ? 'bg-blue-100' : 'bg-slate-100'">{{ meetings.filter(meeting => matchesFilter(meeting, item.id)).length }}</span>
        </button>
      </div>
      <label class="relative block w-full 2xl:max-w-sm">
        <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input v-model="searchQuery" type="search" aria-label="Rechercher une réunion" placeholder="Titre, participant ou mot-clé…"
          class="h-11 w-full rounded-lg border border-slate-200 bg-slate-50/50 pl-10 pr-4 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-50" />
      </label>
    </div>
    <div class="my-5 flex items-center justify-between gap-3 text-xs text-slate-500">
      <p>{{ filteredMeetings.length }} réunion{{ filteredMeetings.length > 1 ? 's' : '' }}</p>
      <select v-model="sort" aria-label="Trier les réunions" class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold">
        <option value="recent">Les plus récentes</option><option value="oldest">Les plus anciennes</option><option value="title">Par titre</option>
      </select>
    </div>
    <div v-if="error" role="alert" class="mb-5 flex items-center justify-between gap-3 rounded-xl bg-red-50 p-4 text-sm text-red-600">{{ error }} <button @click="loadMeetings" class="font-bold underline">Réessayer</button></div>
    <div v-if="loading" class="grid gap-5 md:grid-cols-2 xl:grid-cols-3"><div v-for="index in 6" :key="index" class="h-72 animate-pulse rounded-2xl bg-slate-100" /></div>
    <div v-else-if="filteredMeetings.length" class="grid gap-5 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
      <RouterLink v-for="meeting in filteredMeetings" :key="meeting.id" :to="{ name: 'historique', query: { meeting: meeting.id } }"
        class="group min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-lg hover:shadow-blue-100/50 focus-visible:outline-2 focus-visible:outline-blue-500"
        :aria-label="'Ouvrir la réunion ' + meeting.title" data-testid="meeting-card">
        <div class="relative flex h-32 items-center justify-center overflow-hidden bg-gradient-to-br from-blue-50 via-slate-50 to-blue-100">
          <div aria-hidden="true" class="absolute -right-8 -top-16 h-44 w-44 rounded-full border-[24px] border-white/30" />
          <span class="grid h-12 w-12 place-items-center rounded-2xl bg-white/90 text-blue-600 shadow-sm"><Headphones v-if="meeting.has_source_audio" class="h-6 w-6" /><FileText v-else class="h-6 w-6" /></span>
          <span v-if="meeting.audio_duration" class="absolute bottom-3 right-3 rounded-md bg-white/90 px-2 py-1 text-[10px] font-bold tabular-nums text-blue-700">{{ formatTime(meeting.audio_duration) }}</span>
          <span class="absolute left-3 top-3 inline-flex max-w-[90%] items-center gap-1.5 rounded-full bg-white/95 px-2.5 py-1 text-[10px] font-bold" :class="meeting.processing_status === 'failed' ? 'text-red-600' : 'text-blue-600'"><LoaderCircle v-if="isProcessing(meeting)" class="h-3 w-3 animate-spin" />{{ statusLabel(meeting) }}</span>
        </div>
        <div class="p-4">
          <div class="flex items-start justify-between gap-2"><h2 class="line-clamp-2 text-sm font-bold leading-6 text-slate-900 group-hover:text-blue-700">{{ meeting.title }}</h2><ArrowUpRight class="mt-1 h-4 w-4 shrink-0 text-slate-300 group-hover:text-blue-500" /></div>
          <p class="mt-2 flex items-center gap-1.5 text-[11px] text-slate-400"><CalendarDays class="h-3.5 w-3.5" />{{ formatMeetingDate(meeting.date || meeting.created_at) }}</p>
          <p class="mt-3 line-clamp-2 min-h-10 text-xs leading-5 text-slate-500">{{ meeting.summary_short || (isProcessing(meeting) ? 'La réunion est en cours de traitement…' : 'Ouvrez la réunion pour retrouver son contenu.') }}</p>
          <div class="mt-4 flex items-center gap-2 border-t border-slate-100 pt-3">
            <div v-if="names(meeting).length" class="flex -space-x-1.5"><span v-for="(name, index) in names(meeting).slice(0, 3)" :key="index" :title="name" class="grid h-6 w-6 place-items-center rounded-full border-2 border-white bg-blue-100 text-[9px] font-bold text-blue-600">{{ name[0]?.toUpperCase() }}</span></div>
            <Users v-else class="h-4 w-4 text-slate-300" />
            <p class="truncate text-[11px] text-slate-400">{{ names(meeting).length ? names(meeting).length + ' participant(s)' : 'Participants non renseignés' }}</p>
          </div>
        </div>
      </RouterLink>
    </div>
    <div v-else-if="!error" class="grid place-items-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 px-5 py-20 text-center">
      <span class="grid h-14 w-14 place-items-center rounded-2xl bg-blue-50 text-blue-600"><Headphones class="h-7 w-7" /></span>
      <h2 class="mt-5 text-lg font-bold text-slate-900">{{ meetings.length ? 'Aucune réunion ne correspond' : 'Votre historique commence ici' }}</h2>
      <p class="mt-2 text-sm text-slate-500">{{ meetings.length ? 'Essayez un autre mot-clé ou un autre filtre.' : 'Enregistrez une réunion pour retrouver son audio, sa transcription et ses décisions.' }}</p>
      <button v-if="meetings.length" @click="filter = 'all'; searchQuery = ''" class="mt-5 text-sm font-bold text-blue-600">Effacer les filtres</button>
      <RouterLink v-else to="/reunion" class="mt-5 text-sm font-bold text-blue-600">Créer une réunion →</RouterLink>
    </div>
  </section>
</template>
