export const roleName = role => ({ owner: 'Propriétaire', admin: 'Administrateur', member: 'Membre' })[role] || role
export const states = { idle: 'Sans traitement', queued: 'En attente', preparing: 'Préparation audio', transcribing: 'Transcription', writing: 'Rédaction', building: 'Création du Word', completed: 'Terminée', failed: 'Échec' }
export const stateName = state => states[state] || state
export const dateLabel = value => value ? new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(/Z$|[+-]\d\d:\d\d$/.test(value) ? value : value + 'Z')) : 'Non renseignée'
export const audioDuration = value => value == null ? 'Non mesurée' : `${Math.floor(value / 3600)} h ${Math.floor((value % 3600) / 60)} min`
export const activeMeeting = item => ['queued', 'preparing', 'transcribing', 'writing', 'building'].includes(item?.processing_status)
