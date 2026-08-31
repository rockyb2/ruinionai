<template>
  <section class="min-h-full rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <header>
      <h1 class="text-2xl font-black text-slate-900">Bienvenue ! 👋</h1>
      <p class="mt-1 text-sm font-semibold text-slate-500">
        Enregistrez une nouvelle réunion ou importez un fichier audio pour obtenir le résumé intelligent.
      </p>
    </header>

    <div class="mt-5 rounded-2xl border border-slate-200 bg-white p-5">
      <div class="grid gap-6 lg:grid-cols-[1fr_1.35fr]">
        <div class="space-y-6 lg:border-r lg:border-slate-200 lg:pr-8">
          <h2 class="text-lg font-black text-slate-900">Créer une nouvelle réunion</h2>

          <label class="block">
            <span class="text-sm font-black text-slate-700">Titre de la réunion</span>
            <span class="mt-3 flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3">
              <SquarePen class="h-4 w-4 text-slate-400" />
              <input
                v-model="meetingTitle"
                class="w-full border-0 bg-transparent text-sm font-semibold text-slate-700 outline-none placeholder:text-slate-400"
                placeholder="Réunion commerciale"
                type="text"
              />
            </span>
          </label>

          <div>
            <p class="text-sm font-black text-slate-700">
              Participants <span class="font-semibold text-slate-400">(facultatif)</span>
            </p>

            <div class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="participant in participants"
                :key="participant"
                class="inline-flex items-center gap-2 rounded-lg bg-blue-50 px-4 py-2 text-sm font-black text-blue-600"
              >
                {{ participant }}
                <button
                  class="rounded-full text-blue-500 transition hover:text-blue-700"
                  type="button"
                  @click="removeParticipant(participant)"
                >
                  <X class="h-4 w-4" />
                </button>
              </span>

              <form class="flex gap-2" @submit.prevent="addParticipant">
                <input
                  v-model="newParticipant"
                  class="w-28 rounded-lg border border-dashed border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
                  placeholder="Nom"
                  type="text"
                />
                <button
                  class="inline-flex items-center gap-2 rounded-lg border border-dashed border-blue-300 px-4 py-2 text-sm font-black text-blue-600 transition hover:bg-blue-50"
                  type="submit"
                >
                  <Plus class="h-4 w-4" />
                  Ajouter
                </button>
              </form>
            </div>
          </div>
        </div>

        <div class="grid place-items-center py-2">
          <div class="w-full max-w-xl text-center">
            <p class="text-sm font-black text-slate-700">Enregistrer votre réunion</p>

            <div class="mt-4 flex items-center justify-center">
              <div class="hidden flex-1 items-center justify-end gap-1 sm:flex">
                <span
                  v-for="bar in leftWaveBars"
                  :key="`left-${bar.id}`"
                  class="w-1 rounded-full bg-blue-200"
                  :class="isRecording ? 'animate-pulse bg-blue-400' : ''"
                  :style="{ height: `${bar.height}px`, animationDelay: `${bar.delay}ms` }"
                />
              </div>

              <button
                class="mx-5 grid h-24 w-24 place-items-center rounded-full border-[10px] border-blue-50 bg-blue-600 text-white shadow-lg shadow-blue-100 transition hover:scale-105 hover:bg-blue-700"
                type="button"
                @click="toggleRecording"
              >
                <Mic v-if="!isRecording" class="h-9 w-9" />
                <Square v-else class="h-8 w-8 fill-white" />
              </button>

              <div class="hidden flex-1 items-center justify-start gap-1 sm:flex">
                <span
                  v-for="bar in rightWaveBars"
                  :key="`right-${bar.id}`"
                  class="w-1 rounded-full bg-blue-200"
                  :class="isRecording ? 'animate-pulse bg-blue-400' : ''"
                  :style="{ height: `${bar.height}px`, animationDelay: `${bar.delay}ms` }"
                />
              </div>
            </div>

            <p class="mt-2 text-2xl font-black text-slate-900">{{ formattedRecordingTime }}</p>
            <p class="mt-4 inline-flex items-center gap-2 text-xs font-semibold text-slate-500">
              <Lightbulb class="h-4 w-4 text-amber-400" />
              Parlez clairement et rapprochez-vous du micro
            </p>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-4 grid gap-4 lg:grid-cols-[1.25fr_0.9fr]">
      <div class="rounded-2xl border border-slate-200 bg-white p-5">
        <p class="text-sm font-black text-slate-800">Ou importer un fichier audio</p>

        <button
          class="mt-4 flex w-full items-center justify-center gap-5 rounded-xl border border-dashed border-blue-200 bg-white px-5 py-8 text-left transition hover:border-blue-400 hover:bg-blue-50/40"
          type="button"
          @click="openFilePicker"
          @dragover.prevent
          @drop.prevent="handleFileDrop"
        >
          <UploadCloud class="h-12 w-12 text-blue-400" />
          <span>
            <span class="block text-sm font-black text-slate-700">
              {{ selectedFile ? selectedFile.name : 'Glissez votre fichier ici ou cliquez pour parcourir' }}
            </span>
            <span class="mt-2 block text-xs font-semibold text-slate-500">
              MP3, WAV, M4A, WEBM · Max 500 Mo
            </span>
          </span>
        </button>

        <input
          ref="fileInput"
          class="hidden"
          accept="audio/*"
          type="file"
          @change="handleFileChange"
        />
      </div>

      <div class="rounded-2xl bg-gradient-to-br from-blue-50 via-white to-slate-50 p-5">
        <div class="flex gap-3">
          <span class="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-blue-600 text-white">
            <Info class="h-4 w-4" />
          </span>
          <p class="text-sm font-black text-blue-600">
            Nous prendrons en charge la transcription, l'analyse et le résumé.
          </p>
        </div>

        <div class="mt-4 space-y-3">
          <p
            v-for="step in steps"
            :key="step"
            class="flex items-center gap-3 text-sm font-semibold text-slate-700"
          >
            <Check class="h-4 w-4 text-emerald-500" />
            {{ step }}
          </p>
        </div>
      </div>
    </div>

    <div class="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p v-if="statusMessage" class="text-sm font-bold text-blue-600">{{ statusMessage }}</p>
        <p v-if="errorMessage" class="text-sm font-bold text-red-600">{{ errorMessage }}</p>
      </div>

      <button
        class="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-black text-white shadow-lg shadow-blue-100 transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
        :disabled="isSubmitting"
        type="button"
        @click="processMeeting"
      >
        <LoaderCircle v-if="isSubmitting" class="h-4 w-4 animate-spin" />
        <Sparkles v-else class="h-4 w-4" />
        Générer le résumé
      </button>
    </div>

    <div v-if="meetingResult" class="mt-5 grid gap-4 lg:grid-cols-2">
      <article class="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 class="text-sm font-black uppercase text-slate-400">Transcription</h3>
        <p class="mt-3 max-h-56 overflow-auto whitespace-pre-wrap text-sm font-semibold leading-6 text-slate-700">
          {{ meetingResult.transcription || 'Transcription non disponible.' }}
        </p>
      </article>

      <article class="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 class="text-sm font-black uppercase text-slate-400">Résumé</h3>
        <p class="mt-3 max-h-56 overflow-auto whitespace-pre-wrap text-sm font-semibold leading-6 text-slate-700">
          {{ meetingResult.summary || 'Résumé non disponible.' }}
        </p>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import {
  Check,
  Info,
  Lightbulb,
  LoaderCircle,
  Mic,
  Plus,
  Sparkles,
  Square,
  SquarePen,
  UploadCloud,
  X,
} from '@lucide/vue'
import { createMeeting, generate_Summary, uploadAudio } from '@/service/api'

const meetingTitle = ref('Réunion commerciale')
const participants = ref(['Awa', 'Koffi', 'Sarah'])
const newParticipant = ref('')
const selectedFile = ref(null)
const fileInput = ref(null)
const isRecording = ref(false)
const recordingSeconds = ref(0)
const mediaRecorder = ref(null)
const mediaStream = ref(null)
const audioChunks = ref([])
const isSubmitting = ref(false)
const statusMessage = ref('')
const errorMessage = ref('')
const meetingResult = ref(null)

let recordingTimer = null

const steps = [
  'Transcription précise',
  'Résumé intelligent',
  'Points clés et actions',
  'Export facile',
]

const waveBars = Array.from({ length: 44 }, (_, index) => ({
  id: index,
  height: 10 + ((index * 9) % 34),
  delay: index * 35,
}))

const leftWaveBars = waveBars.slice(0, 22)
const rightWaveBars = waveBars.slice(22)

const formattedRecordingTime = computed(() => {
  const minutes = String(Math.floor(recordingSeconds.value / 60)).padStart(2, '0')
  const seconds = String(recordingSeconds.value % 60).padStart(2, '0')
  return `00:${minutes}:${seconds}`
})

function addParticipant() {
  const value = newParticipant.value.trim()

  if (!value || participants.value.includes(value)) {
    newParticipant.value = ''
    return
  }

  participants.value.push(value)
  newParticipant.value = ''
}

function removeParticipant(participant) {
  participants.value = participants.value.filter((item) => item !== participant)
}

function openFilePicker() {
  fileInput.value?.click()
}

function handleFileChange(event) {
  const [file] = event.target.files || []

  if (file) {
    selectedFile.value = file
    errorMessage.value = ''
  }
}

function handleFileDrop(event) {
  const [file] = event.dataTransfer.files || []

  if (file) {
    selectedFile.value = file
    errorMessage.value = ''
  }
}

async function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
    return
  }

  await startRecording()
}

async function startRecording() {
  try {
    errorMessage.value = ''
    mediaStream.value = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioChunks.value = []

    const recorder = new MediaRecorder(mediaStream.value)
    mediaRecorder.value = recorder

    recorder.addEventListener('dataavailable', (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
      }
    })

    recorder.addEventListener('stop', () => {
      const audioBlob = new Blob(audioChunks.value, { type: recorder.mimeType || 'audio/webm' })
      selectedFile.value = new File([audioBlob], `note-vocale-${Date.now()}.webm`, {
        type: audioBlob.type,
      })
      stopStream()
    })

    recorder.start()
    isRecording.value = true
    recordingSeconds.value = 0
    recordingTimer = window.setInterval(() => {
      recordingSeconds.value += 1
    }, 1000)
  } catch {
    errorMessage.value = "Impossible d'accéder au micro."
    stopStream()
  }
}

function stopRecording() {
  if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop()
  }

  isRecording.value = false
  clearRecordingTimer()
}

function stopStream() {
  mediaStream.value?.getTracks().forEach((track) => track.stop())
  mediaStream.value = null
}

function clearRecordingTimer() {
  if (recordingTimer) {
    window.clearInterval(recordingTimer)
    recordingTimer = null
  }
}

async function processMeeting() {
  const title = meetingTitle.value.trim()

  if (!title) {
    errorMessage.value = 'Ajoutez un titre de réunion.'
    return
  }

  if (!selectedFile.value) {
    errorMessage.value = 'Enregistrez une note vocale ou importez un fichier audio.'
    return
  }

  try {
    isSubmitting.value = true
    errorMessage.value = ''
    meetingResult.value = null

    statusMessage.value = 'Création de la réunion...'
    const meeting = await createMeeting({
      title,
      participants: participants.value,
    })

    statusMessage.value = 'Transcription audio en cours...'
    await uploadAudio(meeting.id, selectedFile.value)

    statusMessage.value = 'Génération du résumé intelligent...'
    meetingResult.value = await generate_Summary(meeting.id)

    statusMessage.value = 'Résumé généré avec succès.'
  } catch (error) {
    errorMessage.value = error.message || 'Une erreur est survenue pendant le traitement.'
    statusMessage.value = ''
  } finally {
    isSubmitting.value = false
  }
}

onBeforeUnmount(() => {
  if (isRecording.value) {
    stopRecording()
  }

  clearRecordingTimer()
  stopStream()
})
</script>
