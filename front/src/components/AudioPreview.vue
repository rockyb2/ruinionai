<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Download, Pause, Play } from '@lucide/vue'
import { audioExtension, formatAudioTime, locateAudioPosition } from '../utils/audio'

const props = defineProps({ segments: { type: Array, required: true }, disabled: Boolean, downloadable: Boolean })
const player = ref(null)
const urls = ref([])
const index = ref(0)
const durations = ref([])
const position = ref(0)
const playing = ref(false)
const message = ref('')
const total = computed(() => durations.value.reduce((sum, value) => sum + value, 0))
const downloads = computed(() => props.segments.map((segment, part) => {
  const number = String(part + 1).padStart(2, '0')
  return {
    url: urls.value[part],
    name: `note-vocale${props.segments.length > 1 ? `-partie-${number}` : ''}.${audioExtension(segment.file.type)}`,
    label: `Partie ${number} — ${formatAudioTime(segment.duration)}`,
  }
}))
let pendingOffset = 0
let playWhenReady = false
let generation = 0

function stop() {
  generation += 1
  playWhenReady = false
  player.value?.pause()
  playing.value = false
}

function releaseUrls() {
  urls.value.forEach((url) => URL.revokeObjectURL(url))
}

watch(() => props.segments, (segments) => {
  stop()
  releaseUrls()
  index.value = 0
  position.value = 0
  pendingOffset = 0
  message.value = ''
  durations.value = segments.map((segment) => segment.duration || 0)
  urls.value = segments.map((segment) => URL.createObjectURL(segment.file))
}, { immediate: true })

watch(() => props.disabled, (disabled) => { if (disabled) stop() })

async function play() {
  if (props.disabled || !player.value) return
  const version = ++generation
  try {
    await player.value.play()
    if (version !== generation) return
    playing.value = true
    message.value = ''
  } catch (error) {
    if (version !== generation || error.name === 'AbortError') return
    playing.value = false
    message.value = 'Lecture impossible. Réessayez ou utilisez un autre format audio.'
  }
}

function toggle() {
  if (playing.value || playWhenReady) stop()
  else if (total.value > 0 && position.value >= total.value - 0.05) seekTo(0, true)
  else void play()
}

function seekTo(seconds, keepPlaying = playing.value) {
  const target = locateAudioPosition(durations.value, seconds)
  stop()
  position.value = seconds
  pendingOffset = target.offset
  if (target.index !== index.value) {
    playWhenReady = keepPlaying
    index.value = target.index
  } else if (player.value?.readyState >= 1) {
    player.value.currentTime = target.offset
    pendingOffset = 0
    if (keepPlaying) void play()
  } else {
    playWhenReady = keepPlaying
  }
}

function metadataLoaded() {
  const measured = player.value.duration
  if (Number.isFinite(measured) && measured > 0) durations.value[index.value] = measured
  if (pendingOffset > 0) player.value.currentTime = pendingOffset
  pendingOffset = 0
  if (playWhenReady && !props.disabled) {
    playWhenReady = false
    void play()
  }
}

function timeUpdated() {
  position.value = durations.value.slice(0, index.value).reduce((sum, value) => sum + value, 0)
    + (player.value?.currentTime || 0)
}

function ended() {
  const measured = player.value?.currentTime
  if (Number.isFinite(measured) && measured > 0) durations.value[index.value] = measured
  if (index.value + 1 < urls.value.length && !props.disabled) {
    pendingOffset = 0
    playWhenReady = true
    index.value += 1
  } else {
    position.value = total.value
    playing.value = false
  }
}

function playbackError() {
  stop()
  message.value = 'Ce navigateur ne peut pas lire cet audio. Essayez un fichier MP3 ou WAV.'
}

onBeforeUnmount(() => { stop(); releaseUrls() })
defineExpose({ stop })
</script>

<template>
  <div v-if="urls.length" class="w-full rounded-xl border border-blue-100 bg-white p-3">
    <audio
      ref="player"
      :src="urls[index]"
      preload="metadata"
      @loadedmetadata="metadataLoaded"
      @timeupdate="timeUpdated"
      @ended="ended"
      @error="playbackError"
      @pause="playing = false"
      @play="playing = true"
    />
    <div class="flex items-center gap-3">
      <button
        type="button"
        class="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-blue-600 text-white disabled:opacity-40"
        :disabled="disabled"
        :aria-label="playing ? 'Mettre la lecture en pause' : 'Écouter l’audio'"
        @click="toggle"
      >
        <Pause v-if="playing" class="h-5 w-5" />
        <Play v-else class="h-5 w-5" />
      </button>
      <div class="min-w-0 flex-1">
        <input
          type="range"
          class="w-full accent-blue-600"
          aria-label="Position dans l’audio"
          :min="0"
          :max="total || 1"
          :step="0.1"
          :value="Math.min(position, total)"
          :disabled="disabled || !total"
          @input="seekTo(Number($event.target.value))"
        />
        <p class="text-xs font-semibold tabular-nums text-slate-500">
          {{ formatAudioTime(position) }} / {{ total ? formatAudioTime(total) : 'Durée en cours de lecture' }}
        </p>
      </div>
    </div>
    <div v-if="downloadable" class="mt-3 border-t border-blue-50 pt-3 text-sm text-blue-700">
      <a v-if="downloads.length === 1" :href="downloads[0].url" :download="downloads[0].name" class="inline-flex items-center justify-center gap-2 font-bold underline underline-offset-2">
        <Download class="h-4 w-4" /> Télécharger l’audio
      </a>
      <details v-else class="text-left">
        <summary class="cursor-pointer font-bold">Télécharger les {{ downloads.length }} parties</summary>
        <p class="mt-2 text-xs text-slate-500">Téléchargez chaque partie pour conserver l’enregistrement complet. Les fichiers sont numérotés dans l’ordre.</p>
        <ul class="mt-2 flex max-h-48 flex-col gap-2 overflow-y-auto">
          <li v-for="file in downloads" :key="file.url">
            <a :href="file.url" :download="file.name" class="inline-flex items-center gap-2 underline underline-offset-2">
              <Download class="h-4 w-4 shrink-0" /> {{ file.label }}
            </a>
          </li>
        </ul>
      </details>
    </div>
    <p v-if="message" role="alert" class="mt-2 text-xs text-red-600">{{ message }}</p>
  </div>
</template>
