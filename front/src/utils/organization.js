export const roleLabels = {
  owner: 'Propriétaire',
  admin: 'Administrateur',
  member: 'Membre',
}

export function roleLabel(role) {
  return roleLabels[role] || 'Membre'
}
