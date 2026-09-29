<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Check,
  FileAudio,
  Info,
  LoaderCircle,
  Send,
  Sparkles,
  SquarePen,
  UploadCloud,
  X,
} from '@lucide/vue'

import { createMeeting, generateSummary, uploadAudio } from '@/service/api'
import AudioRecorder from '@/components/AudioRecorder.vue'
import AudioPreview from '@/components/AudioPreview.vue'
import MeetingInvitees from '@/components/MeetingInvitees.vue'
import { MAX_AUDIO_BYTES } from '@/utils/audio'

const router = useRouter()

const meetingTitle = ref('Réunion commerciale')
const selectedMembers = ref([])
const createdMeeting = ref(null)
const isInviting = ref(false)
const invitationMessage = ref('')
const selectedFile = ref(null)
const fileInput = ref(null)
const audioRecorder = ref(null)
const importedPreview = ref(null)
const recordedFiles = ref([])
const recordingReady = ref(false)
const recordingActive = ref(false)
const hasRecording = ref(false)
const isSubmitting = ref(false)
const statusMessage = ref('')
const errorMessage = ref('')

const importDisabled = computed(() => isSubmitting.value || recordingActive.value || hasRecording.value || Boolean(createdMeeting.value?.has_source_audio))
const canSubmit = computed(() => !isSubmitting.value && !isInviting.value && !recordingActive.value
  && (createdMeeting.value?.has_source_audio || Boolean(selectedFile.value) || (recordingReady.value && recordedFiles.value.length > 0)))
const importedSegments = computed(() => selectedFile.value ? [{ file: selectedFile.value, duration: 0 }] : [])
const audioName = computed(() => selectedFile.value?.name
  || (hasRecording.value ? 'Note vocale enregistrée depuis le micro' : 'Ajoutez un fichier ou lancez un enregistrement.'))

const steps = [
  'Transcription de l’audio',
  'Résumé court pour lecture rapide',
  'Compte rendu détaillé',
  'Actions et décisions identifiées',
  'Document Word pret a telecharger',
]

const selectedFileName = computed(() => {
  return selectedFile.value?.name || 'Glissez votre fichier ici ou cliquez pour parcourir'
})

async function ensureMeeting() {
  if (createdMeeting.value) return createdMeeting.value
  createdMeeting.value = await createMeeting({
    title: meetingTitle.value.trim(),
    participant_member_ids: selectedMembers.value.map(member => member.member_id),
  })
  if (selectedMembers.value.length) {
    invitationMessage.value = `Invitation envoyée à ${selectedMembers.value.length} membre(s) dans l’application.`
  }
  window.dispatchEvent(new CustomEvent('meeting-created'))
  return createdMeeting.value
}

async function inviteMembers() {
  if (isInviting.value || isSubmitting.value || createdMeeting.value) return
  if (!meetingTitle.value.trim() || !selectedMembers.value.length) return
  isInviting.value = true
  errorMessage.value = ''
  try {
    await ensureMeeting()
  } catch (error) {
    if (error.status === 401) router.push('/login')
    errorMessage.value = error.message || 'Impossible d’envoyer les invitations.'
  } finally {
    isInviting.value = false
  }
}

function openFilePicker() {
  if (importDisabled.value) return
  fileInput.value?.click()
}

function setAudioFile(file) {
  if (importDisabled.value) return
  if (!file.size || file.size > MAX_AUDIO_BYTES) {
    errorMessage.value = 'Choisissez un fichier audio non vide de 500 Mo maximum.'
    return
  }
  if (!file.type.startsWith('audio/') && !/\.(mp3|wav|m4a|mp4|webm|ogg|flac|aac)$/i.test(file.name)) {
    errorMessage.value = 'Choisissez un fichier audio compatible.'
    return
  }
  selectedFile.value = file
  errorMessage.value = ''
}

function removeImportedFile() {
  if (isSubmitting.value || createdMeeting.value?.has_source_audio) return
  importedPreview.value?.stop()
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
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

async function processMeeting() {
  if (isSubmitting.value || isInviting.value) return
  const title = meetingTitle.value.trim()

  if (!title) {
    errorMessage.value = 'Ajoutez un titre de réunion.'
    return
  }

  if (!canSubmit.value) {
    errorMessage.value = 'Terminez votre enregistrement ou importez un fichier audio avant de continuer.'
    return
  }

  try {
    isSubmitting.value = true
    audioRecorder.value?.stopPlayback()
    importedPreview.value?.stop()
    errorMessage.value = ''

    statusMessage.value = 'Création de la réunion...'
    const meeting = await ensureMeeting()

    statusMessage.value = 'Envoi et sauvegarde de l’audio…'
    if (!createdMeeting.value.has_source_audio) {
      createdMeeting.value = await uploadAudio(meeting.id, selectedFile.value || recordedFiles.value)
    }

    statusMessage.value = 'Mise en attente du traitement…'
    await generateSummary(meeting.id)
    if (!selectedFile.value) await audioRecorder.value?.clearDraft()

    statusMessage.value = 'Traitement lancé. Vous pouvez suivre son avancement dans l’historique.'
    window.dispatchEvent(new CustomEvent('meeting-created'))
    await router.push({ name: 'historique', query: { meeting: meeting.id } })
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
              :disabled="Boolean(createdMeeting) || isSubmitting || isInviting"
              maxlength="250"
              class="w-full border-0 bg-transparent text-sm font-semibold text-slate-700 outline-none placeholder:text-slate-400"
              placeholder="Réunion commerciale"
              type="text"
            />
          </span>
        </label>

        <MeetingInvitees v-model="selectedMembers" :disabled="Boolean(createdMeeting) || isSubmitting || isInviting" />
        <button v-if="!createdMeeting" type="button" class="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300" :disabled="isSubmitting || isInviting || !meetingTitle.trim() || !selectedMembers.length" @click="inviteMembers">
          <LoaderCircle v-if="isInviting" class="h-4 w-4 animate-spin" /><Send v-else class="h-4 w-4" />
          {{ isInviting ? 'Envoi des invitations…' : 'Inviter à la réunion' }}
        </button>
        <p v-if="invitationMessage" class="mt-3 rounded-lg bg-emerald-50 p-3 text-sm font-semibold text-emerald-700" role="status">{{ invitationMessage }}</p>
        <p v-else-if="!createdMeeting" class="mt-2 text-xs leading-5 text-slate-500">Vous pouvez inviter votre équipe avant l’enregistrement. Les membres sélectionnés seront aussi invités si vous lancez directement la génération.</p>
        <p v-if="createdMeeting" class="mt-3 text-xs leading-5 text-slate-500">Réunion créée. Vous pouvez maintenant enregistrer ou importer l’audio pour cette réunion.</p>
      </section>

      <section class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="grid gap-6 lg:grid-cols-[1fr_1fr]">
          <AudioRecorder
            ref="audioRecorder"
            v-model:files="recordedFiles"
            v-model:ready="recordingReady"
            v-model:active="recordingActive"
            v-model:has-audio="hasRecording"
            :disabled="isSubmitting || Boolean(selectedFile) || Boolean(createdMeeting?.has_source_audio)"
          />

          <div class="min-w-0">
            <p class="text-sm font-black text-slate-800">Importer un fichier audio</p>

            <button
              class="mt-4 flex min-h-44 w-full flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-blue-200 bg-white px-5 py-8 text-center transition hover:border-blue-400 hover:bg-blue-50/40 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              :disabled="importDisabled"
              @click="openFilePicker"
              @dragover.prevent
              @drop.prevent="handleFileDrop"
            >
              <UploadCloud class="h-12 w-12 text-blue-400" />
              <span class="w-full min-w-0">
                <span class="block break-words whitespace-normal text-sm font-black text-slate-700">
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
              :disabled="importDisabled"
              @change="handleFileChange"
            />
            <p v-if="hasRecording || recordingActive" class="mt-3 text-xs text-slate-500">
              Supprimez la note vocale avant d’importer un autre audio.
            </p>
            <template v-if="selectedFile">
              <AudioPreview ref="importedPreview" class="mt-4" :segments="importedSegments" :disabled="isSubmitting" />
              <button type="button" :disabled="isSubmitting || Boolean(createdMeeting?.has_source_audio)" class="mt-3 text-sm font-bold text-red-600 disabled:opacity-50" @click="removeImportedFile">
                Retirer le fichier
              </button>
            </template>
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
              {{ selectedFile || recordingReady ? 'Audio prêt' : hasRecording || recordingActive ? 'Enregistrement à terminer' : 'Aucun audio sélectionné' }}
            </p>
            <p class="mt-1 break-all text-xs font-semibold text-slate-500">
              {{ audioName }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <div class="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p v-if="statusMessage" class="text-sm font-bold text-blue-600">{{ statusMessage }}</p>
        <p v-if="errorMessage" class="text-sm font-bold text-red-600">{{ errorMessage }}</p>
        <RouterLink v-if="createdMeeting?.has_source_audio" :to="{ name: 'historique', query: { meeting: createdMeeting.id } }" class="mt-2 inline-block text-sm font-bold text-blue-600 underline">Suivre le traitement dans l’historique</RouterLink>
      </div>

      <button
        class="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-black text-white shadow-lg shadow-blue-100 transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
        :disabled="!canSubmit"
        type="button"
        @click="processMeeting"
      >
        <LoaderCircle v-if="isSubmitting" class="h-4 w-4 animate-spin" />
        <Sparkles v-else class="h-4 w-4" />
        Générer les résumés
      </button>
    </div>

  </section>
</template>
