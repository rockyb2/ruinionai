import { computed, onScopeDispose, ref, shallowRef } from 'vue'
import { deleteAudioDraft, readAudioDraft, saveAudioDraft } from '../service/audioDraft.js'
import { audioExtension, MAX_AUDIO_BYTES, MAX_AUDIO_SEGMENTS } from '../utils/audio.js'

export function useAudioRecorder({ draftKey, storage = { readAudioDraft, saveAudioDraft, deleteAudioDraft } }) {
  const state = ref('idle')
  const segments = shallowRef([])
  const duration = ref(0)
  const level = ref(0)
  const error = ref('')
  const draftMessage = ref('')
  const restoring = ref(true)
  const busy = computed(() => restoring.value || ['requesting', 'stopping'].includes(state.value))
  const active = computed(() => ['requesting', 'recording', 'stopping'].includes(state.value))

  let recorder = null
  let stream = null
  let audioContext = null
  let animation = null
  let timer = null
  let startedAt = 0
  let savedDuration = 0
  let stopping = null
  let disposed = false
  let draftQueue = Promise.resolve()

  function persist(remove = false) {
    // Serialize writes so a late save cannot resurrect a deleted draft.
    const draft = { segments: [...segments.value], ready: state.value === 'ready' }
    draftQueue = draftQueue.then(async () => {
      if (!draftKey) throw new Error('Compte indisponible.')
      if (remove) await storage.deleteAudioDraft(draftKey)
      else await storage.saveAudioDraft(draftKey, draft)
      draftMessage.value = remove ? '' : 'Brouillon sauvegardé sur cet appareil à la dernière pause.'
    }).catch(() => {
      draftMessage.value = 'Sauvegarde locale indisponible. Gardez cette page ouverte pour conserver votre audio.'
    })
    return draftQueue
  }

  async function restore() {
    try {
      const draft = draftKey ? await storage.readAudioDraft(draftKey) : null
      if (disposed || !draft?.segments?.length) return
      segments.value = draft.segments.filter((segment) => segment.file?.size > 0)
      savedDuration = segments.value.reduce((sum, segment) => sum + segment.duration, 0)
      duration.value = savedDuration
      state.value = segments.value.length ? (draft.ready ? 'ready' : 'paused') : 'idle'
      draftMessage.value = 'Brouillon restauré. Vous pouvez l’écouter ou reprendre l’enregistrement.'
    } catch {
      draftMessage.value = 'Sauvegarde locale indisponible. Gardez cette page ouverte pour conserver votre audio.'
    } finally {
      restoring.value = false
    }
  }

  function releaseMicrophone() {
    stream?.getTracks().forEach((track) => track.stop())
    stream = null
    if (timer !== null) clearInterval(timer)
    if (animation !== null) cancelAnimationFrame(animation)
    timer = null
    animation = null
    level.value = 0
    audioContext?.close().catch(() => {})
    audioContext = null
  }

  function startMeter() {
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext
      audioContext = new AudioContextClass()
      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      // Never connect the microphone to the speakers (avoids feedback).
      const values = new Uint8Array(analyser.fftSize)
      const update = () => {
        analyser.getByteTimeDomainData(values)
        const power = values.reduce((sum, value) => sum + ((value - 128) / 128) ** 2, 0) / values.length
        level.value = Math.min(1, Math.sqrt(power) * 5)
        animation = requestAnimationFrame(update)
      }
      audioContext.resume().catch(() => {})
      update()
    } catch {
      // Meter support must not prevent recording.
      audioContext?.close().catch(() => {})
      audioContext = null
    }
  }

  async function start() {
    if (disposed || busy.value || !['idle', 'paused'].includes(state.value)) return
    if (segments.value.length >= MAX_AUDIO_SEGMENTS) {
      error.value = 'La limite de 100 parties est atteinte. Terminez cet enregistrement.'
      return
    }
    if (!navigator.mediaDevices?.getUserMedia || !globalThis.MediaRecorder) {
      error.value = 'L’enregistrement nécessite un navigateur compatible et une connexion HTTPS (ou localhost).'
      return
    }

    const previousState = state.value
    state.value = 'requesting'
    error.value = ''
    try {
      const acquiredStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      if (disposed) {
        acquiredStream.getTracks().forEach((track) => track.stop())
        return
      }
      stream = acquiredStream
      const mimeType = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus']
        .find((type) => MediaRecorder.isTypeSupported(type))
      recorder = new MediaRecorder(stream, { ...(mimeType ? { mimeType } : {}), audioBitsPerSecond: 64000 })
      const currentRecorder = recorder
      const chunks = []
      let bytes = segments.value.reduce((sum, segment) => sum + segment.file.size, 0)
      let nextState = 'paused'
      let segmentDuration = null
      let resolveStop
      stopping = new Promise((resolve) => { resolveStop = resolve })

      currentRecorder.addEventListener('dataavailable', (event) => {
        if (!event.data.size) return
        chunks.push(event.data)
        bytes += event.data.size
        if (bytes >= MAX_AUDIO_BYTES && state.value === 'recording') {
          error.value = 'Enregistrement trop volumineux (500 Mo maximum).'
          void stop('ready')
        }
      })
      currentRecorder.addEventListener('error', () => {
        error.value = 'L’enregistrement a été interrompu. Les parties déjà capturées sont conservées.'
      })
      currentRecorder.addEventListener('stop', () => {
        const seconds = segmentDuration ?? Math.max(0, (performance.now() - startedAt) / 1000)
        if (chunks.length) {
          const type = currentRecorder.mimeType || chunks[0].type || 'audio/webm'
          const file = new File(chunks, `note-vocale-${Date.now()}.${audioExtension(type)}`, { type })
          segments.value = [...segments.value, { id: crypto.randomUUID(), file, duration: seconds }]
          savedDuration += seconds
        } else {
          error.value = 'Aucun son n’a été enregistré. Vérifiez le micro puis réessayez.'
        }
        duration.value = savedDuration
        state.value = segments.value.length ? nextState : 'idle'
        // Persist the final state as well as the bytes.
        if (segments.value.length) void persist()
        releaseMicrophone()
        recorder = null
        resolveStop()
      }, { once: true })
      // Finalize a playable file at every pause, then create a fresh recorder on resume.
      currentRecorder.finishSegment = (targetState) => {
        nextState = targetState
        segmentDuration = Math.max(0, (performance.now() - startedAt) / 1000)
        currentRecorder.stop()
      }
      stream.getAudioTracks().forEach((track) => track.addEventListener('ended', () => {
        if (state.value === 'recording') {
          error.value = 'Le micro a été déconnecté. Vous pouvez écouter les parties conservées.'
          void stop('paused')
        }
      }, { once: true }))
      currentRecorder.start(1000)
      startedAt = performance.now()
      state.value = 'recording'
      timer = setInterval(() => {
        duration.value = savedDuration + (performance.now() - startedAt) / 1000
        if (duration.value >= 4 * 60 * 60) {
          error.value = 'La durée maximale de 4 heures est atteinte.'
          void stop('ready')
        }
      }, 200)
      startMeter()
    } catch (cause) {
      releaseMicrophone()
      recorder = null
      state.value = previousState
      error.value = cause.name === 'NotAllowedError'
        ? 'Autorisez l’accès au micro dans votre navigateur pour enregistrer.'
        : 'Impossible de démarrer le micro. Vérifiez qu’il est disponible.'
    }
  }

  async function stop(targetState = 'paused') {
    if (state.value === 'stopping') return stopping
    if (state.value !== 'recording') return
    state.value = 'stopping'
    if (timer !== null) clearInterval(timer)
    timer = null
    if (recorder?.state !== 'inactive') recorder.finishSegment(targetState)
    return stopping
  }

  async function finish() {
    if (busy.value) return
    if (state.value === 'recording') await stop('ready')
    else if (segments.value.length) {
      state.value = 'ready'
      await persist()
    }
  }

  async function discard() {
    if (active.value || busy.value) return
    segments.value = []
    savedDuration = 0
    duration.value = 0
    state.value = 'idle'
    error.value = ''
    await persist(true)
  }

  function reopen() {
    if (state.value === 'ready') state.value = 'paused'
  }

  function beforeUnload(event) {
    if (active.value) {
      event.preventDefault()
      event.returnValue = ''
    }
  }
  window.addEventListener('beforeunload', beforeUnload)
  onScopeDispose(() => {
    disposed = true
    window.removeEventListener('beforeunload', beforeUnload)
    if (state.value === 'recording') void stop('paused')
    releaseMicrophone()
  })

  const restored = restore()
  return { state, segments, duration, level, error, draftMessage, busy, active, restored,
    start, pause: () => stop('paused'), finish, discard, reopen, clearDraft: () => persist(true) }
}
