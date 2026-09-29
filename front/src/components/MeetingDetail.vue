<script setup>
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { ArrowLeft, CalendarDays, Check, Copy, Download, FileText, Headphones, LoaderCircle, RefreshCw, Search, Users } from '@lucide/vue'
import { useMeeting } from '@/composables/useMeeting'
import { downloadMeetingReport, getMeetingAudio } from '@/service/api'
import { formatMeetingDate, formatTime, isProcessing, processingErrorMessage, statusLabel } from '@/utils/meeting'

const props = defineProps({ meetingId: { type: Number, required: true } })
const { meeting, loading, error, retrying, refresh, retry } = useMeeting(props.meetingId)
const tab = ref('transcript')
const search = ref('')
const audio = ref(null)
const audioUrl = ref('')
const audioLoading = ref(false)
const audioError = ref('')
const currentTime = ref(0)
const playing = ref(false)
const speed = ref(1)
const follow = ref(false)
const transcriptPanel = ref(null)
const actionError = ref('')
const downloading = ref(false)
const copied = ref(false)
let audioController
let disposed = false
let copiedTimer
const segments = computed(() => meeting.value?.transcription_segments || [])
const visibleSegments = computed(() => segments.value.map((segment, index) => ({ ...segment, index }))
  .filter(segment => segment.text.toLocaleLowerCase('fr').includes(search.value.toLocaleLowerCase('fr'))))
const paragraphs = computed(() => (meeting.value?.transcription || '').split(/\n\s*\n|\n/).filter(text => text.trim())
  .filter(text => text.toLocaleLowerCase('fr').includes(search.value.toLocaleLowerCase('fr'))))
const activeSegment = computed(() => segments.value.findIndex(segment => currentTime.value >= segment.start && currentTime.value < segment.end))
const participants = computed(() => (meeting.value?.participants || '').split(',').map(name => name.trim()).filter(Boolean))
const busy = computed(() => isProcessing(meeting.value))
const tabs = [{ id: 'transcript', label: 'Transcription' }, { id: 'summary', label: 'Résumé' }, { id: 'report', label: 'Compte rendu' }]

async function loadAudio() {
  if (!meeting.value?.audio_available || audioLoading.value) return
  audioController?.abort()
  audioController = new AbortController()
  audioLoading.value = true
  audioError.value = ''
  try {
    const blob = await getMeetingAudio(props.meetingId, audioController.signal)
    if (disposed) return
    if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
    audioUrl.value = URL.createObjectURL(blob)
  } catch (failure) {
    if (!disposed && failure.name !== 'AbortError') audioError.value = failure.message || 'Impossible de charger l’audio.'
  } finally {
    if (!disposed) audioLoading.value = false
  }
}

async function seek(seconds) {
  if (!audio.value || !Number.isFinite(audio.value.duration)) return
  audio.value.currentTime = Math.max(0, Math.min(seconds, audio.value.duration))
  currentTime.value = audio.value.currentTime
  try { await audio.value.play() }
  catch (failure) {
    if (!disposed && failure.name !== 'AbortError') audioError.value = 'Cliquez sur Lecture pour écouter ce passage.'
  }
}

async function downloadWord() {
  downloading.value = true
  actionError.value = ''
  try { await downloadMeetingReport(props.meetingId) }
  catch (failure) { actionError.value = failure.message }
  finally { downloading.value = false }
}

async function copyText() {
  const text = tab.value === 'transcript' ? meeting.value.transcription : tab.value === 'summary' ? meeting.value.summary_short : meeting.value.summary_long
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    clearTimeout(copiedTimer)
    copiedTimer = setTimeout(() => { copied.value = false }, 2000)
  } catch { actionError.value = 'La copie est indisponible dans ce navigateur.' }
}

watch(() => meeting.value?.audio_available, available => { if (available && !audioUrl.value) loadAudio() })
watch(speed, value => { if (audio.value) audio.value.playbackRate = Number(value) })
watch(activeSegment, async index => {
  if (!follow.value || !playing.value || tab.value !== 'transcript' || index < 0) return
  await nextTick()
  const panel = transcriptPanel.value
  const item = panel?.querySelector(`[data-segment="${index}"]`)
  if (panel && item) panel.scrollTo({ top: item.offsetTop - 30, behavior: 'smooth' })
})
onUnmounted(() => {
  disposed = true
  audioController?.abort()
  audio.value?.pause()
  if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
  clearTimeout(copiedTimer)
})
</script>

<template>
  <section class="min-w-0 space-y-5">
    <RouterLink :to="{ name: 'historique' }" class="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-blue-600">
      <ArrowLeft class="h-4 w-4" /> Toutes les réunions
    </RouterLink>
    <div v-if="loading" class="h-96 animate-pulse rounded-2xl bg-white" aria-label="Chargement de la réunion"></div>
    <div v-if="error" role="alert" class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
      {{ error }} <button class="font-bold underline" @click="refresh">Actualiser</button>
    </div>
    <template v-if="meeting">
      <header class="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between">
        <div class="min-w-0 flex-1">
          <h1 class="break-words text-2xl font-black tracking-tight text-slate-900">{{ meeting.title }}</h1>
          <div class="mt-3 flex flex-wrap items-center gap-4 text-xs font-medium text-slate-500">
            <span class="flex items-center gap-1.5"><CalendarDays class="h-4 w-4" /> {{ formatMeetingDate(meeting.date || meeting.created_at) }}</span>
            <span v-if="meeting.audio_duration" class="flex items-center gap-1.5"><Headphones class="h-4 w-4" /> {{ formatTime(meeting.audio_duration) }}</span>
            <span class="rounded-full px-3 py-1 font-bold" :class="meeting.processing_status === 'failed' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'">{{ statusLabel(meeting) }}</span>
          </div>
        </div>
        <button v-if="meeting.report_path" :disabled="downloading" @click="downloadWord" class="inline-flex w-fit items-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50">
          <LoaderCircle v-if="downloading" class="h-4 w-4 animate-spin" /><Download v-else class="h-4 w-4" /> Télécharger le Word
        </button>
      </header>
      <div v-if="busy" role="status" class="flex items-center gap-3 rounded-xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-700">
        <LoaderCircle class="h-5 w-5 shrink-0 animate-spin" />
        <div><p class="font-bold">{{ statusLabel(meeting) }}…</p><p class="mt-1 text-xs">Vous pouvez quitter cette page. Le traitement continue et les résultats apparaîtront ici.</p></div>
      </div>
      <div v-else-if="meeting.processing_status === 'failed' || (!meeting.report_path && (meeting.has_source_audio || meeting.transcription))" class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p class="min-w-0 flex-1">{{ meeting.processing_status === 'failed' ? processingErrorMessage(meeting) : 'Cette réunion est prête à être traitée.' }}</p>
        <button :disabled="retrying" @click="retry" class="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 font-bold shadow-sm disabled:opacity-50">
          <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': retrying }" /> {{ meeting.summary_short && meeting.summary_long ? 'Recréer le Word' : 'Relancer le traitement' }}
        </button>
      </div>
      <p v-if="actionError" role="alert" class="text-sm text-red-600">{{ actionError }}</p>

      <div class="grid min-w-0 items-start gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <article class="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm" data-testid="transcript-panel">
          <div class="flex items-center justify-between gap-2 border-b border-slate-100 p-3 sm:p-4">
            <div class="flex min-w-0 flex-wrap gap-1" role="tablist" aria-label="Contenu de la réunion">
              <button v-for="item in tabs" :id="`tab-${item.id}`" :key="item.id" role="tab" :aria-selected="tab === item.id" aria-controls="meeting-text" @click="tab = item.id"
                class="rounded-lg px-3 py-2.5 text-sm font-bold transition" :class="tab === item.id ? 'bg-blue-50 text-blue-600' : 'text-slate-500 hover:bg-slate-50'">{{ item.label }}</button>
            </div>
            <button @click="copyText" aria-label="Copier le texte" class="shrink-0 rounded-lg p-2 text-slate-400 hover:bg-slate-50 hover:text-blue-600"><Check v-if="copied" class="h-4 w-4" /><Copy v-else class="h-4 w-4" /></button>
          </div>
          <div v-if="tab === 'transcript'" class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-3">
            <label class="flex min-w-0 flex-1 items-center gap-2"><Search class="h-4 w-4 shrink-0 text-slate-400" /><input v-model="search" type="search" aria-label="Rechercher dans la transcription" placeholder="Rechercher dans la transcription" class="min-w-0 w-full bg-transparent py-1 text-sm text-slate-600 outline-none" /></label>
            <label v-if="segments.length" class="flex items-center gap-2 text-xs text-slate-500"><input v-model="follow" type="checkbox" class="accent-blue-600" /> Suivre la lecture</label>
          </div>
          <div id="meeting-text" ref="transcriptPanel" role="tabpanel" :aria-labelledby="`tab-${tab}`" class="relative min-h-80 max-h-[65vh] overflow-y-auto overscroll-contain px-5 py-6 sm:px-7 xl:h-[calc(100vh-22rem)] xl:min-h-96">
            <template v-if="tab === 'transcript'">
              <div v-if="segments.length" class="space-y-2">
                <div v-for="segment in visibleSegments" :key="segment.index" :data-segment="segment.index" class="flex gap-3 rounded-xl px-3 py-4 transition-colors" :class="activeSegment === segment.index ? 'bg-blue-50' : 'hover:bg-slate-50'">
                  <button @click="seek(segment.start)" :disabled="!audioUrl || audioLoading" :aria-label="`Écouter à ${formatTime(segment.start)}`" class="h-fit shrink-0 rounded-md bg-blue-50 px-2 py-1 text-xs font-bold tabular-nums text-blue-600 hover:bg-blue-100 disabled:opacity-40">{{ formatTime(segment.start) }}</button>
                  <p class="min-w-0 whitespace-pre-wrap break-words text-sm leading-7 text-slate-700">{{ segment.text }}</p>
                </div>
              </div>
              <div v-else-if="meeting.transcription" class="space-y-5"><p v-for="(paragraph, index) in paragraphs" :key="index" class="whitespace-pre-wrap break-words text-sm leading-8 text-slate-700">{{ paragraph }}</p></div>
              <p v-else class="py-14 text-center text-sm leading-7 text-slate-400">{{ busy ? 'La transcription apparaîtra ici dès qu’elle sera prête.' : 'Aucune transcription disponible pour cette réunion.' }}</p>
              <p v-if="search && !(segments.length ? visibleSegments.length : paragraphs.length)" class="py-12 text-center text-sm text-slate-400">Aucun passage ne correspond à votre recherche.</p>
            </template>
            <p v-else class="whitespace-pre-wrap break-words text-sm leading-8 text-slate-700">{{ (tab === 'summary' ? meeting.summary_short : meeting.summary_long) || 'Ce contenu n’est pas encore disponible.' }}</p>
          </div>
        </article>

        <aside class="min-w-0 space-y-5" data-testid="audio-panel">
          <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div class="flex items-center gap-2 border-b border-slate-100 px-5 py-4 text-sm font-bold text-slate-800"><Headphones class="h-4 w-4 text-blue-600" /> Enregistrement audio</div>
            <div class="m-3 flex min-h-52 flex-col items-center justify-center rounded-xl bg-gradient-to-br from-blue-50 via-slate-50 to-blue-100 px-5 py-8 sm:min-h-64">
              <span class="grid h-16 w-16 place-items-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-200"><Headphones class="h-8 w-8" /></span>
              <div aria-hidden="true" class="mt-7 flex h-10 items-center gap-1.5"><span v-for="(height, index) in [12,22,16,32,24,40,28,16,36,24,40,18,30,14,22,10,18]" :key="index" class="w-1 rounded-full bg-blue-400/60" :style="{height: `${height}px`}" /></div>
              <p class="mt-5 text-xs font-semibold text-slate-500">{{ meeting.audio_duration ? formatTime(meeting.audio_duration) + ' d’enregistrement' : meeting.audio_available ? 'Audio de la réunion' : 'Enregistrement' }}</p>
            </div>
            <div class="space-y-4 p-5 pt-2">
              <p v-if="audioLoading" role="status" class="flex items-center gap-2 text-sm text-blue-600"><LoaderCircle class="h-4 w-4 animate-spin" /> Chargement de l’audio…</p>
              <template v-if="audioUrl">
                <audio ref="audio" :src="audioUrl" controls preload="metadata" class="w-full" aria-label="Lecteur de la réunion"
                  @timeupdate="currentTime = $event.target.currentTime" @play="playing = true; audioError = ''" @pause="playing = false" @ended="playing = false"
                  @loadedmetadata="$event.target.playbackRate = Number(speed)" @error="audioError = 'Cet enregistrement ne peut pas être lu. Réessayez de le charger.'" />
                <div class="flex items-center justify-between gap-3 text-xs font-semibold text-slate-500">
                  <div class="flex gap-2"><button class="rounded-lg bg-slate-50 px-3 py-2 hover:bg-blue-50" @click="seek(currentTime - 15)" aria-label="Reculer de 15 secondes">−15 s</button><button class="rounded-lg bg-slate-50 px-3 py-2 hover:bg-blue-50" @click="seek(currentTime + 15)" aria-label="Avancer de 15 secondes">+15 s</button></div>
                  <label>Vitesse <select v-model="speed" aria-label="Vitesse de lecture" class="ml-1 rounded-lg border border-slate-200 bg-white p-2"><option v-for="rate in [0.75, 1, 1.25, 1.5, 2]" :key="rate" :value="rate">{{ rate }}×</option></select></label>
                  <a :href="audioUrl" :download="`reunion-${meeting.id}.mp3`" aria-label="Télécharger l’audio" class="rounded-lg p-2 hover:bg-blue-50 hover:text-blue-600"><Download class="h-4 w-4" /></a>
                </div>
              </template>
              <div v-if="audioError" role="alert" class="text-sm text-red-600">{{ audioError }} <button class="font-bold underline" @click="loadAudio">Réessayer</button></div>
              <p v-else-if="!meeting.audio_available" class="text-center text-sm leading-6 text-slate-500">{{ meeting.has_source_audio ? 'L’audio sera disponible après sa préparation.' : 'L’audio de cette réunion n’a pas été conservé. Les nouveaux enregistrements restent disponibles ici.' }}</p>
            </div>
          </section>
          <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 class="flex items-center gap-2 text-sm font-bold text-slate-800"><Users class="h-4 w-4 text-blue-600" /> Participants <span class="ml-auto text-xs font-medium text-slate-400">{{ participants.length }}</span></h2>
            <div v-if="participants.length" class="mt-4 flex flex-wrap gap-2"><span v-for="(name, index) in participants" :key="index" class="inline-flex max-w-full items-center gap-2 rounded-full bg-slate-50 py-1.5 pl-1.5 pr-3 text-xs font-semibold text-slate-600"><span class="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-blue-100 font-bold text-blue-600">{{ name[0]?.toUpperCase() }}</span><span class="truncate">{{ name }}</span></span></div>
            <p v-else class="mt-3 text-sm text-slate-400">Participants non renseignés.</p>
          </section>
        </aside>
      </div>
    </template>
  </section>
</template>
