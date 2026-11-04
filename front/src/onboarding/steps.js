export const ONBOARDING_VERSION = 1

export const onboardingSteps = [
  {
    id: 'navigation',
    label: "Découvrir l'espace",
    description: 'Navigation, profil et notifications',
    route: { name: 'reunion' },
    tour: 'navigation',
    completeOnTour: true,
  },
  {
    id: 'organization_profile',
    label: "Configurer l'organisation",
    description: 'Nom, description et préférences',
    route: { name: 'setting' },
    tour: 'organization',
    roles: ['owner'],
  },
  {
    id: 'invite_team',
    label: 'Inviter votre équipe',
    description: 'Ajoutez un collègue à votre espace',
    route: { name: 'equipe' },
    tour: 'team',
    roles: ['owner', 'admin'],
  },
  {
    id: 'create_meeting',
    label: 'Créer une réunion',
    description: 'Préparez votre premier compte rendu',
    route: { name: 'reunion' },
    tour: 'meeting',
  },
  {
    id: 'invite_participants',
    label: 'Ajouter des participants',
    description: 'Associez les membres concernés',
    route: { name: 'reunion' },
    tour: 'participants',
  },
  {
    id: 'add_audio',
    label: 'Ajouter un audio',
    description: 'Enregistrez ou importez un fichier',
    route: { name: 'reunion' },
    tour: 'audio',
  },
  {
    id: 'generate_report',
    label: 'Générer le compte rendu',
    description: 'Lancez la transcription et les résumés',
    route: { name: 'reunion' },
    tour: 'generation',
  },
  {
    id: 'view_history',
    label: "Explorer l'historique",
    description: 'Retrouvez toutes les réunions',
    route: { name: 'historique' },
    tour: 'history',
    completeOnTour: true,
  },
  {
    id: 'download_report',
    label: 'Télécharger un rapport',
    description: 'Exportez un compte rendu au format Word',
    route: { name: 'historique' },
    tour: 'results',
  },
]

export function stepsForRole(role) {
  return onboardingSteps.filter((step) => !step.roles || step.roles.includes(role))
}
