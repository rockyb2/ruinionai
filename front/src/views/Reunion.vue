<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Check,
  Download,
  FileAudio,
  FileText,
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

import { createMeeting, downloadMeetingReport, generateSummary, uploadAudio } from '@/service/api'

const router = useRouter()

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
const isDownloadingReport = ref(false)
const statusMessage = ref('')
const errorMessage = ref('')
const meetingResult = ref(null)

let recordingTimer = null

const steps = [
  'Transcription de l’audio',
  'Résumé court pour lecture rapide',
  'Compte rendu détaillé',
  'Actions et décisions identifiées',
  'Document Word pret a telecharger',
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

const selectedFileName = computed(() => {
  return selectedFile.value?.name || 'Glissez votre fichier ici ou cliquez pour parcourir'
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

function setAudioFile(file) {
  selectedFile.value = file
  errorMessage.value = ''
}

function handleFileChange(event) {
  const [file] = event.target.files || []

  if (file) {
    setAudioFile(file)
  }
}

function handleFileDrop(event) {
  const [file] = event.dataTransfer.files || []

  if (file) {
    setAudioFile(file)
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
      setAudioFile(
        new File([audioBlob], `note-vocale-${Date.now()}.webm`, {
          type: audioBlob.type,
        }),
      )
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

    statusMessage.value = 'Génération des résumés court et détaillé...'
    meetingResult.value = await generateSummary(meeting.id)

    statusMessage.value = 'Résumés et document Word générés avec succès.'
  } catch (error) {
    if (error.status === 401) {
      router.push('/login')
      return
    }

    errorMessage.value = error.message || 'Une erreur est survenue pendant le traitement.'
    statusMessage.value = ''
  } finally {
    isSubmitting.value = false
  }
}

async function downloadReport() {
  if (!meetingResult.value?.id) {
    return
  }

  try {
    isDownloadingReport.value = true
    errorMessage.value = ''
    await downloadMeetingReport(meetingResult.value.id)
  } catch (error) {
    if (error.status === 401) {
      router.push('/login')
      return
    }

    errorMessage.value = error.message || 'Impossible de telecharger le compte rendu Word.'
  } finally {
    isDownloadingReport.value = false
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

<template>
  <section class="min-h-full rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
    <header class="flex flex-col gap-4 border-b border-slate-100 pb-5 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <p class="text-xs font-black uppercase tracking-normal text-blue-600">Compte rendu IA</p>
        <h1 class="mt-2 text-2xl font-black text-slate-900">Nouvelle réunion</h1>
        <p class="mt-1 max-w-2xl text-sm font-semibold leading-6 text-slate-500">
          Capturez l'audio, obtenez une transcription, puis générez un résumé court et un compte rendu détaillé.
        </p>
      </div>

      <div class="flex items-center gap-3 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3">
        <Sparkles class="h-5 w-5 text-blue-600" />
        <div>
          <p class="text-xs font-black uppercase text-blue-600">Workspace sécurisé</p>
          <p class="text-xs font-semibold text-slate-500">Toutes les réunions restent dans votre organisation.</p>
        </div>
      </div>
    </header>

    <div class="mt-5 grid gap-5 xl:grid-cols-[1fr_1.15fr]">
      <section class="rounded-2xl border border-slate-200 bg-white p-5">
        <h2 class="text-lg font-black text-slate-900">Informations</h2>

        <label class="mt-5 block">
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

        <div class="mt-6">
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
                :aria-label="`Retirer ${participant}`"
                @click="removeParticipant(participant)"
              >
                <X class="h-4 w-4" />
              </button>
            </span>

            <form class="flex min-w-[220px] flex-1 gap-2" @submit.prevent="addParticipant">
              <input
                v-model="newParticipant"
                class="min-w-0 flex-1 rounded-lg border border-dashed border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-400"
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
      </section>

      <section class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="grid gap-6 lg:grid-cols-[1fr_1fr]">
          <div class="grid place-items-center rounded-xl bg-slate-50 px-4 py-6 text-center">
            <p class="text-sm font-black text-slate-700">Enregistrer depuis le micro</p>

            <div class="mt-4 flex w-full items-center justify-center">
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
                :aria-label="isRecording ? 'Arrêter l’enregistrement' : 'Démarrer l’enregistrement'"
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

          <div>
            <p class="text-sm font-black text-slate-800">Importer un fichier audio</p>

            <button
              class="mt-4 flex min-h-44 w-full flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-blue-200 bg-white px-5 py-8 text-center transition hover:border-blue-400 hover:bg-blue-50/40"
              type="button"
              @click="openFilePicker"
              @dragover.prevent
              @drop.prevent="handleFileDrop"
            >
              <UploadCloud class="h-12 w-12 text-blue-400" />
              <span>
                <span class="block break-all text-sm font-black text-slate-700">
                  {{ selectedFileName }}
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
        </div>
      </section>
    </div>

    <section class="mt-5 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
      <div class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="flex gap-3">
          <span class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-blue-600 text-white">
            <Info class="h-4 w-4" />
          </span>
          <div>
            <p class="text-sm font-black text-slate-800">Pipeline de traitement</p>
            <div class="mt-4 grid gap-3 sm:grid-cols-2">
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
      </div>

      <div class="rounded-2xl border border-blue-100 bg-blue-50/70 p-5">
        <div class="flex items-center gap-3">
          <FileAudio class="h-8 w-8 text-blue-600" />
          <div>
            <p class="text-sm font-black text-blue-700">
              {{ selectedFile ? 'Audio prêt' : 'Aucun audio sélectionné' }}
            </p>
            <p class="mt-1 break-all text-xs font-semibold text-slate-500">
              {{ selectedFile ? selectedFile.name : 'Ajoutez un fichier ou lancez un enregistrement.' }}
            </p>
          </div>
        </div>
      </div>
    </section>

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
        Générer les résumés
      </button>
    </div>

    <div
      v-if="meetingResult?.report_path"
      class="mt-5 flex flex-col gap-4 rounded-2xl border border-emerald-100 bg-emerald-50/70 p-5 sm:flex-row sm:items-center sm:justify-between"
    >
      <div class="flex items-center gap-3">
        <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white text-emerald-600 shadow-sm">
          <FileText class="h-5 w-5" />
        </span>
        <div>
          <p class="text-sm font-black text-emerald-700">Compte rendu Word prêt</p>
          <p class="mt-1 text-xs font-semibold text-slate-500">
            Le document est enregistré dans l'espace sécurisé de votre organisation.
          </p>
        </div>
      </div>

      <button
        class="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-black text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        :disabled="isDownloadingReport"
        type="button"
        @click="downloadReport"
      >
        <LoaderCircle v-if="isDownloadingReport" class="h-4 w-4 animate-spin" />
        <Download v-else class="h-4 w-4" />
        Télécharger le Word
      </button>
    </div>

    <div v-if="meetingResult" class="mt-5 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
      <article class="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 class="text-sm font-black uppercase text-slate-400">Transcription</h3>
        <p class="mt-3 max-h-80 overflow-auto whitespace-pre-wrap text-sm font-semibold leading-6 text-slate-700">
          {{ meetingResult.transcription || 'Transcription non disponible.' }}
        </p>
      </article>

      <div class="grid gap-4">
        <article class="rounded-2xl border border-blue-100 bg-blue-50/60 p-5">
          <h3 class="text-sm font-black uppercase text-blue-500">Résumé court</h3>
          <p class="mt-3 max-h-44 overflow-auto whitespace-pre-wrap text-sm font-semibold leading-6 text-slate-700">
            {{ meetingResult.summary_short || meetingResult.summary || 'Résumé court non disponible.' }}
          </p>
        </article>

        <article class="rounded-2xl border border-slate-200 bg-white p-5">
          <h3 class="text-sm font-black uppercase text-slate-400">Compte rendu détaillé</h3>
          <p class="mt-3 max-h-64 overflow-auto whitespace-pre-wrap text-sm font-semibold leading-6 text-slate-700">
            {{ meetingResult.summary_long || meetingResult.summary || 'Compte rendu non disponible.' }}
          </p>
        </article>
      </div>
    </div>
  </section>
</template>
