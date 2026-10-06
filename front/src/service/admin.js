import { apiRequest, getAuthToken, clearAuthToken } from './api'

export function adminRequest(path, options = {}) {
  return apiRequest(`/admin${path}`, { ...options, organization: false }, 'Impossible de joindre l’administration. Réessayez.')
}

export function adminList(resource, values = {}) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(values)) {
    if (value !== '' && value !== undefined && value !== null) query.set(key, String(value))
  }
  return adminRequest(`/${resource}?${query}`)
}

export async function adminFile(meetingId, kind) {
  const response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/admin/meetings/${meetingId}/${kind}`, {
    headers: { Authorization: `Bearer ${getAuthToken()}` },
  })
  if (!response.ok) {
    if (response.status === 401) clearAuthToken()
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || 'Le fichier est indisponible.')
  }
  return response.blob()
}
