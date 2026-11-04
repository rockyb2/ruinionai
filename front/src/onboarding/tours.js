import { driver } from 'driver.js'

const tours = {
  navigation: [
    ['[data-tour="sidebar-new-meeting"]', 'Nouvelle réunion', 'Commencez ici pour enregistrer ou importer une réunion.'],
    ['[data-tour="sidebar-history"]', 'Historique', 'Retrouvez vos transcriptions, résumés et comptes rendus.'],
    ['[data-tour="sidebar-team"]', 'Votre équipe', 'Gérez les membres et les invitations de votre organisation.'],
    ['[data-tour="notifications"]', 'Notifications', 'Suivez les invitations et l’activité importante.'],
    ['[data-tour="profile-menu"]', 'Votre profil', 'Accédez aux paramètres et à votre session.'],
  ],
  organization: [
    ['[data-tour="organization-settings"]', "Identité de l'organisation", 'Complétez les informations visibles par votre équipe.'],
    ['[data-tour="organization-save"]', 'Enregistrer', 'Sauvegardez les changements pour terminer cette étape.'],
  ],
  team: [
    ['[data-tour="team-page"]', 'Espace équipe', 'Consultez les membres et les invitations.'],
    ['[data-tour="team-invite"]', 'Inviter un collègue', 'Saisissez son adresse, choisissez son rôle puis envoyez le lien.'],
  ],
  meeting: [
    ['[data-tour="meeting-title"]', 'Titre de la réunion', 'Choisissez un titre clair pour la retrouver facilement.'],
    ['[data-tour="meeting-participants"]', 'Participants', 'Sélectionnez les membres concernés par cette réunion.'],
    ['[data-tour="meeting-audio"]', 'Source audio', 'Enregistrez directement ou importez un fichier existant.'],
    ['[data-tour="meeting-generate"]', 'Génération IA', 'Lancez la transcription, les résumés et le document Word.'],
  ],
  participants: [
    ['[data-tour="meeting-participants"]', 'Inviter les participants', 'Les membres choisis recevront une notification dans RuinionAI.'],
  ],
  audio: [
    ['[data-tour="meeting-audio"]', 'Enregistrer ou importer', 'Utilisez le microphone ou déposez un fichier MP3, WAV, M4A ou WEBM.'],
  ],
  generation: [
    ['[data-tour="meeting-pipeline"]', 'Ce que RuinionAI prépare', 'Transcription, résumé court, compte rendu détaillé, actions et document Word.'],
    ['[data-tour="meeting-generate"]', 'Lancer le traitement', 'Le traitement continue même si vous quittez la page.'],
  ],
  history: [
    ['[data-tour="history-page"]', 'Mémoire de votre équipe', 'Toutes les réunions sont regroupées ici.'],
    ['[data-tour="history-filters"]', 'Filtres et recherche', 'Filtrez par état ou recherchez un titre, un participant ou un mot-clé.'],
    ['[data-tour="history-card"]', 'Ouvrir une réunion', 'Cliquez sur une carte pour consulter tous les résultats.'],
  ],
  results: [
    ['[data-tour="history-card"]', 'Choisir une réunion terminée', 'Ouvrez une réunion traitée pour accéder à son compte rendu et à son export Word.'],
    ['[data-tour="meeting-results"]', 'Résultats de la réunion', 'Passez de la transcription au résumé puis au compte rendu détaillé.'],
    ['[data-tour="meeting-download"]', 'Export Word', 'Téléchargez le document final lorsqu’il est disponible.'],
  ],
}

function visibleTourSteps(tourId) {
  return (tours[tourId] || []).flatMap(([selector, title, description]) => {
    const element = document.querySelector(selector)
    if (!element || element.getClientRects().length === 0) return []
    const rect = element.getBoundingClientRect()
    if (rect.right <= 0 || rect.left >= window.innerWidth || rect.bottom <= 0 || rect.top >= window.innerHeight) return []
    const availableSpace = {
      top: rect.top,
      right: window.innerWidth - rect.right,
      bottom: window.innerHeight - rect.bottom,
      left: rect.left,
    }
    const side = Object.entries(availableSpace).sort((a, b) => b[1] - a[1])[0][0]
    return [{
      element,
      popover: { title, description, side, align: 'center' },
    }]
  })
}

export function runOnboardingTour(tourId, { onComplete, onClose } = {}) {
  const steps = visibleTourSteps(tourId)
  if (!steps.length) return false

  const tour = driver({
    steps,
    animate: true,
    smoothScroll: true,
    allowClose: true,
    allowKeyboardControl: true,
    overlayClickBehavior: 'none',
    overlayColor: '#0f172a',
    overlayOpacity: 0.7,
    stagePadding: 8,
    stageRadius: 14,
    popoverClass: 'ruinion-driver-popover',
    showProgress: true,
    progressText: '{{current}} sur {{total}}',
    nextBtnText: 'Suivant',
    prevBtnText: 'Précédent',
    doneBtnText: 'Terminer',
    closeBtnLabel: 'Fermer le tutoriel',
    onDestroyed: (_element, _step, { reason }) => {
      try {
        if (reason === 'done') onComplete?.()
      } finally {
        onClose?.(reason)
      }
    },
  })
  tour.drive()
  return true
}

export function highlightOnboardingFeature(selector, title, description) {
  const element = document.querySelector(selector)
  if (!element || element.getClientRects().length === 0) return false
  const rect = element.getBoundingClientRect()
  if (rect.right <= 0 || rect.left >= window.innerWidth || rect.bottom <= 0 || rect.top >= window.innerHeight) return false
  const side = rect.right < window.innerWidth / 2 ? 'right' : 'left'
  let handleResize
  const highlight = driver({
    animate: true,
    overlayColor: '#0f172a',
    overlayOpacity: 0.62,
    stagePadding: 8,
    stageRadius: 16,
    popoverClass: 'ruinion-driver-popover',
    doneBtnText: 'Compris',
    closeBtnLabel: 'Fermer',
    onDestroyed: () => window.removeEventListener('resize', handleResize),
  })
  handleResize = () => {
    const nextRect = element.getBoundingClientRect()
    if (nextRect.right <= 0 || nextRect.left >= window.innerWidth || nextRect.bottom <= 0 || nextRect.top >= window.innerHeight) {
      highlight.destroy()
    }
  }
  window.addEventListener('resize', handleResize, { passive: true })
  highlight.highlight({
    element,
    popover: { title, description, side, align: 'end' },
  })
  return true
}
