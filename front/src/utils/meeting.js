export const processingStates = {
  idle: 'À préparer', queued: 'En attente', preparing: 'Préparation de l’audio',
  transcribing: 'Transcription', writing: 'Rédaction', building: 'Création du Word',
  completed: 'Terminé', failed: 'À relancer',
}

export function isProcessing(meeting) {
  return ['queued', 'preparing', 'transcribing', 'writing', 'building'].includes(meeting?.processing_status)
}

export function statusLabel(meeting) {
  if (meeting?.report_path && (!meeting.processing_status || meeting.processing_status === 'idle')) return 'Terminé'
  return processingStates[meeting?.processing_status] || 'À préparer'
}

export function processingErrorMessage(meeting) {
  if (meeting?.summary_short && meeting?.summary_long) {
    return 'Le document Word n’a pas pu être créé. Vos textes sont conservés.'
  }
  if (meeting?.transcription) {
    return 'Le résumé et le compte rendu n’ont pas pu être générés. Réessayez dans quelques instants.'
  }
  if (meeting?.has_source_audio || meeting?.audio_available) {
    return 'La transcription n’a pas pu être terminée. Réessayez dans quelques instants.'
  }
  return 'Le traitement n’a pas pu être terminé. Réessayez dans quelques instants.'
}

export function formatTime(value = 0) {
  const seconds = Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0
  const hours = Math.floor(seconds / 3600)
  return [hours || null, Math.floor(seconds / 60) % 60, seconds % 60]
    .filter(value => value !== null).map((value, index) => index ? String(value).padStart(2, '0') : String(value)).join(':')
}

export function formatMeetingDate(value) {
  if (!value) return 'Date non renseignée'
  return new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    .format(new Date(/Z$|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`))
}
