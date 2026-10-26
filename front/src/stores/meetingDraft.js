import { defineStore } from 'pinia'

import { getAuthToken } from '@/service/api'

const STORAGE_PREFIX = 'ruinionai.meeting-draft.'
const DRAFT_MAX_AGE = 7 * 24 * 60 * 60 * 1000

/**
 * Récupère l'identifiant de l'utilisateur depuis son jeton.
 *
 * Le jeton complet n'est jamais utilisé comme clé de stockage.
 * Cela évite également de mélanger les brouillons de deux comptes.
 */
function getDraftStorageKey() {
  const token = getAuthToken()

  if (!token) return null

  try {
    const encodedPayload = token
      .split('.')[1]
      .replace(/-/g, '+')
      .replace(/_/g, '/')

    const paddedPayload = encodedPayload.padEnd(
      Math.ceil(encodedPayload.length / 4) * 4,
      '=',
    )

    const payload = JSON.parse(atob(paddedPayload))

    if (!payload.sub) return null

    return `${STORAGE_PREFIX}${encodeURIComponent(String(payload.sub))}`
  } catch {
    return null
  }
}

/**
 * On conserve uniquement les informations nécessaires.
 *
 * Il ne faut pas placer toute la réponse API dans localStorage,
 * car une réunion complète pourrait contenir une longue transcription.
 */
function normalizeCreatedMeeting(meeting) {
  if (!meeting) return null

  const id = Number(meeting.id)

  if (!Number.isSafeInteger(id) || id <= 0) return null

  return {
    id,
    title: typeof meeting.title === 'string' ? meeting.title : '',
    has_source_audio: Boolean(meeting.has_source_audio),
    audio_available: Boolean(meeting.audio_available),
  }
}

function normalizeMembers(members) {
  if (!Array.isArray(members)) return []

  return members
    .filter((member) => {
      const memberId = Number(member?.member_id)
      return Number.isSafeInteger(memberId) && memberId > 0
    })
    .slice(0, 100)
    .map((member) => ({
      member_id: Number(member.member_id),
      name: typeof member.name === 'string' ? member.name : '',
      email: typeof member.email === 'string' ? member.email : '',
    }))
}

export const useMeetingDraftStore = defineStore('meetingDraft', {
  state: () => ({
    title: '',
    selectedMembers: [],
    createdMeeting: null,
    invitationMessage: '',
    restored: false,
    updatedAt: null,
  }),

  getters: {
    /**
     * Indique si l'utilisateur possède réellement un travail en cours.
     */
    hasDraft: (state) => {
      return Boolean(
        state.title.trim() ||
        state.selectedMembers.length ||
        state.createdMeeting,
      )
    },

    /**
     * Le titre et les participants ne sont plus modifiables
     * lorsque la réunion existe déjà sur le serveur.
     */
    detailsLocked: (state) => {
      return Boolean(state.createdMeeting)
    },
  },

  actions: {
    /**
     * Sauvegarde les informations légères du brouillon.
     *
     * L'audio n'est pas sauvegardé ici : il est géré avec IndexedDB.
     */
    persist() {
      const storageKey = getDraftStorageKey()

      if (!storageKey) return false

      const updatedAt = Date.now()

      const draft = {
        version: 1,
        title: this.title.slice(0, 250),
        selectedMembers: normalizeMembers(this.selectedMembers),
        createdMeeting: normalizeCreatedMeeting(this.createdMeeting),
        invitationMessage:
          typeof this.invitationMessage === 'string'
            ? this.invitationMessage
            : '',
        updatedAt,
      }

      try {
        window.localStorage.setItem(storageKey, JSON.stringify(draft))
        this.updatedAt = updatedAt
        return true
      } catch {
        return false
      }
    },

    /**
     * Restaure le brouillon correspondant au compte connecté.
     */
    restore() {
      const storageKey = getDraftStorageKey()

      // On vide d'abord la mémoire pour éviter de montrer
      // le brouillon d'un autre utilisateur.
      this.$reset()
      this.restored = true

      if (!storageKey) return false

      try {
        const savedValue = window.localStorage.getItem(storageKey)

        if (!savedValue) return false

        const draft = JSON.parse(savedValue)
        const updatedAt = Number(draft.updatedAt)

        const isExpired =
          !Number.isFinite(updatedAt) ||
          Date.now() - updatedAt > DRAFT_MAX_AGE

        if (draft.version !== 1 || isExpired) {
          window.localStorage.removeItem(storageKey)
          return false
        }

        this.title =
          typeof draft.title === 'string'
            ? draft.title.slice(0, 250)
            : ''

        this.selectedMembers = normalizeMembers(draft.selectedMembers)
        this.createdMeeting = normalizeCreatedMeeting(
          draft.createdMeeting,
        )

        this.invitationMessage =
          typeof draft.invitationMessage === 'string'
            ? draft.invitationMessage
            : ''

        this.updatedAt = updatedAt

        return this.hasDraft
      } catch {
        window.localStorage.removeItem(storageKey)
        return false
      }
    },

    /**
     * Supprime volontairement le brouillon du compte connecté.
     */
    clear() {
      const storageKey = getDraftStorageKey()

      if (storageKey) {
        try {
          window.localStorage.removeItem(storageKey)
        } catch {
          // Le store sera quand même vidé en mémoire.
        }
      }

      this.$reset()
      this.restored = true
    },
  },
})