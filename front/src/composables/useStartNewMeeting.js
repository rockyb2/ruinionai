import { useRouter } from 'vue-router'

import { useMeetingDraftStore } from '@/stores/meetingDraft'
import { audioDraftKey, deleteAudioDraft } from '@/service/audioDraft'
import { getAuthToken } from '@/service/api'

/**
 * Démarre un formulaire réellement vierge, même si l'utilisateur se trouve
 * déjà sur la page de création.
 */
export function useStartNewMeeting() {
  const router = useRouter()
  const meetingDraft = useMeetingDraftStore()

  return async function startNewMeeting() {
    meetingDraft.clear()

    const draftKey = audioDraftKey(getAuthToken())
    if (draftKey) {
      try {
        await deleteAudioDraft(draftKey)
      } catch {
        // Le formulaire doit rester utilisable si IndexedDB est indisponible.
      }
    }

    await router.push({
      name: 'reunion',
      query: { nouveau: Date.now().toString() },
    })
  }
}
