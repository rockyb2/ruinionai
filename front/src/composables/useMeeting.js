import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { generateSummary, getMeeting } from '@/service/api'
import { isProcessing } from '@/utils/meeting'

export function useMeeting(meetingId) {
  const router = useRouter()
  const meeting = ref(null)
  const loading = ref(true)
  const error = ref('')
  const retrying = ref(false)
  let disposed = false
  let timer
  let controller

  async function refresh() {
    clearTimeout(timer)
    controller?.abort()
    const request = new AbortController()
    controller = request
    try {
      const value = await getMeeting(meetingId, { signal: request.signal })
      if (disposed || request.signal.aborted) return
      meeting.value = value
      error.value = ''
    } catch (failure) {
      if (disposed || request.signal.aborted) return
      if (failure.status === 401) router.push('/login')
      error.value = failure.message || 'Impossible d’actualiser la réunion.'
    } finally {
      if (!disposed && !request.signal.aborted) {
        loading.value = false
        if (isProcessing(meeting.value) || error.value || meeting.value?.processing_status === 'idle') {
          timer = setTimeout(refresh, isProcessing(meeting.value) ? 2000 : 10000)
        }
      }
    }
  }

  async function retry() {
    if (retrying.value || isProcessing(meeting.value)) return
    retrying.value = true
    clearTimeout(timer)
    controller?.abort()
    try {
      const value = await generateSummary(meetingId)
      if (disposed) return
      meeting.value = value
      error.value = ''
      window.dispatchEvent(new CustomEvent('meeting-created'))
    } catch (failure) {
      if (disposed) return
      error.value = failure.message || 'Impossible de relancer le traitement.'
      if (failure.status === 401) router.push('/login')
    } finally {
      retrying.value = false
      if (!disposed) timer = setTimeout(refresh, 1500)
    }
  }

  onMounted(refresh)
  onUnmounted(() => { disposed = true; clearTimeout(timer); controller?.abort() })
  return { meeting, loading, error, retrying, refresh, retry }
}
