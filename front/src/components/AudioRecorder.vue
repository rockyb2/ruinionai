<script setup>
import { computed, ref, watch } from 'vue'
import { LoaderCircle, Mic, Pause, Square, Trash2 } from '@lucide/vue'
import AudioPreview from './AudioPreview.vue'
import { useAudioRecorder } from '../composables/useAudioRecorder'
import { audioDraftKey } from '../service/audioDraft'
import { getAuthToken } from '../service/api'
import { formatAudioTime } from '../utils/audio'

const props = defineProps({ disabled: Boolean })
const emit = defineEmits(['update:files', 'update:ready', 'update:active', 'update:hasAudio'])
const preview = ref(null)
const confirmingDelete = ref(false)
const { state, segments, duration, level, error, draftMessage, busy, active,
  start, pause, finish, discard, reopen, clearDraft } = useAudioRecorder({ draftKey: audioDraftKey(getAuthToken()) })

const labels = {
  idle: 'Enregistrer depuis le micro', requesting: 'Autorisation du micro…', recording: 'Enregistrement en cours',
  stopping: 'Préparation de l’audio…', paused: 'En pause — écoutez puis reprenez', ready: 'Votre audio est prêt',
}
const buttonLabel = computed(() => state.value === 'recording' ? 'Mettre en pause' : state.value === 'idle' ? 'Enregistrer' : 'Reprendre')

watch([segments, state, busy], () => {
  emit('update:files', segments.value.map((segment) => segment.file))
  emit('update:ready', state.value === 'ready' && !busy.value)
  emit('update:active', active.value || busy.value)
  emit('update:hasAudio', segments.value.length > 0)
}, { immediate: true })

async function toggleRecording() {
  if (props.disabled || busy.value) return
  preview.value?.stop()
  confirmingDelete.value = false
  if (state.value === 'recording') await pause()
  else { reopen(); await start() }
}

async function removeRecording() {
  preview.value?.stop()
  await discard()
  confirmingDelete.value = false
}

defineExpose({ clearDraft, stopPlayback: () => preview.value?.stop() })
</script>

<template>
  <div class="flex min-w-0 flex-col items-center rounded-xl bg-slate-50 px-4 py-6 text-center">
    <p class="text-sm font-black text-slate-700" aria-live="polite">{{ labels[state] }}</p>
    <button
      type="button"
      class="mt-4 grid h-24 w-24 place-items-center rounded-full border-[10px] border-blue-50 bg-blue-600 text-white shadow-lg shadow-blue-100 transition hover:bg-blue-700 disabled:opacity-50"
      :disabled="disabled || busy"
      :aria-label="buttonLabel"
      @click="toggleRecording"
    >
      <LoaderCircle v-if="busy" class="h-8 w-8 animate-spin" />
      <Pause v-else-if="state === 'recording'" class="h-8 w-8" />
      <Mic v-else class="h-9 w-9" />
    </button>
    <p class="mt-2 text-xs font-bold text-blue-600">{{ buttonLabel }}</p>
    <p class="mt-2 text-2xl font-black tabular-nums text-slate-900">{{ formatAudioTime(duration) }}</p>

    <div v-if="state === 'recording'" class="mt-3 w-full">
      <div role="meter" aria-label="Niveau du micro" :aria-valuenow="Math.round(level * 100)" :aria-valuemin="0" :aria-valuemax="100" class="h-2 overflow-hidden rounded-full bg-slate-200">
        <div class="h-full rounded-full bg-emerald-500 transition-[width] duration-75" :style="{ width: `${level * 100}%` }" />
      </div>
      <p class="mt-2 text-xs text-slate-500">Mettez en pause pour écouter et vérifier votre voix.</p>
    </div>

    <AudioPreview v-if="segments.length && !active" ref="preview" class="mt-4" :segments="segments" :disabled="disabled || busy" downloadable />

    <div class="mt-4 flex flex-wrap justify-center gap-2">
      <button
        v-if="state === 'recording' || state === 'paused'"
        type="button"
        :disabled="disabled || busy"
        class="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-bold text-white disabled:opacity-50"
        @click="finish"
      >
        <Square class="h-4 w-4" /> Terminer
      </button>
      <button
        v-if="segments.length && !active && !confirmingDelete"
        type="button"
        :disabled="disabled || busy"
        class="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold text-red-600 disabled:opacity-50"
        @click="confirmingDelete = true"
      >
        <Trash2 class="h-4 w-4" /> Supprimer
      </button>
    </div>
    <div v-if="confirmingDelete" class="mt-2 rounded-lg bg-red-50 p-3 text-sm">
      <p>Supprimer cet enregistrement et son brouillon ?</p>
      <div class="mt-2 flex justify-center gap-4">
        <button type="button" class="font-bold text-red-600" :disabled="disabled" @click="removeRecording">Supprimer</button>
        <button type="button" class="font-bold text-slate-600" @click="confirmingDelete = false">Conserver</button>
      </div>
    </div>
    <p v-if="state === 'ready'" class="mt-3 text-xs font-semibold text-blue-600">Lancez la génération lorsque vous avez vérifié votre audio.</p>
    <p v-if="draftMessage" role="status" class="mt-3 text-xs text-slate-500">{{ draftMessage }}</p>
    <p v-if="error" role="alert" class="mt-3 text-sm font-semibold text-red-600">{{ error }}</p>
  </div>
</template>
