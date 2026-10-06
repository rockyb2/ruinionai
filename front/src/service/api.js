const API_URL = import.meta.env.VITE_API_URL || '/api'
const TOKEN_STORAGE_KEY = 'ruinionai.access_token'
const ORGANIZATION_STORAGE_KEY = 'ruinionai.organization_id'

function getTokenStorage(remember) {
  return remember ? window.localStorage : window.sessionStorage
}

function getAuthStorage() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY)
    ? window.localStorage
    : window.sessionStorage
}

function setOrganizationContext(organizationId) {
  const normalizedId = Number(organizationId)

  if (Number.isSafeInteger(normalizedId) && normalizedId > 0 && getAuthToken()) {
    const storage = getAuthStorage()
    window.localStorage.removeItem(ORGANIZATION_STORAGE_KEY)
    window.sessionStorage.removeItem(ORGANIZATION_STORAGE_KEY)
    storage.setItem(ORGANIZATION_STORAGE_KEY, String(normalizedId))
  }
}

function getOrganizationHeaders() {
  const organizationId =
    window.localStorage.getItem(ORGANIZATION_STORAGE_KEY) ||
    window.sessionStorage.getItem(ORGANIZATION_STORAGE_KEY)

  return /^[1-9]\d*$/.test(organizationId || '')
    ? { 'X-Organization-Id': organizationId }
    : {}
}

export function getAuthToken() {
  return (
    window.localStorage.getItem(TOKEN_STORAGE_KEY) ||
    window.sessionStorage.getItem(TOKEN_STORAGE_KEY)
  )
}

export function setAuthToken(token, remember = true) {
  clearAuthToken()

  if (token) {
    getTokenStorage(remember).setItem(TOKEN_STORAGE_KEY, token)
  }
}

export function clearAuthToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY)
  window.sessionStorage.removeItem(TOKEN_STORAGE_KEY)
  window.localStorage.removeItem(ORGANIZATION_STORAGE_KEY)
  window.sessionStorage.removeItem(ORGANIZATION_STORAGE_KEY)
}

export function isAuthenticated() {
  return Boolean(getAuthToken())
}

async function parseApiError(response, fallbackMessage) {
  try {
    const data = await response.json()

    if (Array.isArray(data.detail)) {
      return data.detail
        .map((item) => item.msg || item.message || fallbackMessage)
        .join(' ')
    }

    return data.detail || data.message || fallbackMessage
  } catch {
    return fallbackMessage
  }
}

async function requestJson(response, fallbackMessage) {
  if (!response.ok) {
    if (response.status === 401) {
      clearAuthToken()
    }

    const error = new Error(await parseApiError(response, fallbackMessage))
    error.status = response.status
    throw error
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

export async function apiRequest(path, options = {}, fallbackMessage = 'Une erreur est survenue.') {
  const { auth = true, organization = true, body, headers = {}, ...fetchOptions } = options
  const requestHeaders = {
    ...(auth && organization ? getOrganizationHeaders() : {}),
    ...headers,
  }

  if (auth) {
    const token = getAuthToken()

    if (token) {
      requestHeaders.Authorization = `Bearer ${token}`
    }
  }

  const isFormData = body instanceof FormData

  if (body && !isFormData) {
    requestHeaders['Content-Type'] = 'application/json'
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...fetchOptions,
    headers: requestHeaders,
    body: body && !isFormData ? JSON.stringify(body) : body,
  })

  return requestJson(response, fallbackMessage)
}

export async function registerUser(data, remember = true) {
  const response = await apiRequest(
    '/auth/register',
    {
      method: 'POST',
      auth: false,
      body: data,
    },
    'Impossible de creer le compte.',
  )

  setAuthToken(response.access_token, remember)
  setOrganizationContext(response.organization?.id)
  return response
}

export async function loginUser(data, remember = true) {
  const response = await apiRequest(
    '/auth/login',
    {
      method: 'POST',
      auth: false,
      body: data,
    },
    'Impossible de se connecter.',
  )

  setAuthToken(response.access_token, remember)
  return response
}

export function logoutUser() {
  clearAuthToken()
}

export async function getCurrentUser() {
  const response = await apiRequest('/auth/me', {}, 'Session invalide.')
  setOrganizationContext(response.organization?.id)
  return response
}

export async function acceptOrganizationInvitation(token) {
  const remember = Boolean(window.localStorage.getItem(TOKEN_STORAGE_KEY))
  const response = await apiRequest(
    '/invitations/accept',
    {
      method: 'POST',
      body: { token },
    },
    "Impossible d'accepter l'invitation.",
  )

  setAuthToken(response.access_token, remember)
  setOrganizationContext(response.organization?.id)
  return response
}

export async function registerFromInvitation(data, remember = true) {
  const response = await apiRequest(
    '/invitations/register',
    {
      method: 'POST',
      auth: false,
      body: data,
    },
    "Impossible de creer le compte depuis cette invitation.",
  )

  setAuthToken(response.access_token, remember)
  setOrganizationContext(response.organization?.id)
  return response
}

export async function listMeetings() {
  return apiRequest('/meetings/', {}, 'Impossible de charger les reunions.')
}

export async function createMeeting(data) {
  return apiRequest(
    '/meetings/',
    {
      method: 'POST',
      body: data,
    },
    'Impossible de creer la reunion.',
  )
}

export async function listMeetingInvitees({ q = '', offset = 0, limit = 50 } = {}) {
  const query = new URLSearchParams({ q, offset: String(offset), limit: String(limit) })
  return apiRequest(`/meetings/invitees?${query}`, {}, 'Impossible de charger les membres de l’équipe.')
}

export async function uploadAudio(meetingId, audio) {
  const formData = new FormData()
  if (Array.isArray(audio)) {
    audio.forEach((file) => formData.append('files', file, file.name))
  } else {
    formData.append('file', audio)
  }

  return apiRequest(
    `/meetings/${meetingId}/audio`,
    {
      method: 'POST',
      body: formData,
    },
    'Impossible de transcrire la note vocale.',
  )
}

export async function generateSummary(meetingId) {
  return apiRequest(
    `/meetings/${meetingId}/summary`,
    {
      method: 'POST',
    },
    'Impossible de generer le resume.',
  )
}

export const generate_Summary = generateSummary

export async function downloadMeetingReport(meetingId) {
  const token = getAuthToken()
  const response = await fetch(`${API_URL}/meetings/${meetingId}/report`, {
    headers: token
      ? { Authorization: `Bearer ${token}`, ...getOrganizationHeaders() }
      : {},
  })

  if (!response.ok) {
    if (response.status === 401) {
      clearAuthToken()
    }

    const error = new Error(await parseApiError(response, 'Impossible de telecharger le compte rendu.'))
    error.status = response.status
    throw error
  }

  const blob = await response.blob()
  const disposition = response.headers.get('content-disposition') || ''
  const filenameMatch = disposition.match(/filename="?([^"]+)"?/)
  const filename = filenameMatch?.[1] || `compte-rendu-${meetingId}.docx`
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export async function getMeeting(meetingId, options = {}) {
  return apiRequest(`/meetings/${meetingId}`, options, 'Réunion introuvable.')
}

export async function getMeetingAudio(meetingId, signal) {
  const response = await fetch(`${API_URL}/meetings/${meetingId}/audio`, {
    signal, headers: { ...getOrganizationHeaders(), Authorization: `Bearer ${getAuthToken()}` },
  })
  if (!response.ok) await requestJson(response, 'Impossible de charger l’enregistrement.')
  return response.blob()
}



// gestion des équipes
export async function listOrganizationsMembers({ offset = 0, limit = 50} = {}){
   const query = new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
  })

  return apiRequest(
    `/organization/members?${query}`,
    {},
    'Impossible de charger les membres.',
  )
}

export async function updateOrganizationMemberRole(memberId,role){
  return apiRequest(
      `/organization/members/${memberId}/role`,
    {
      method: 'PATCH',
      body: { role },
    },
    'Impossible de modifier le role du membre.',
  )
}


export async function updateOrganizationMemberStatus(memberId, status) {
  return apiRequest(
    `/organization/members/${memberId}/status`,
    {
      method: 'PATCH',
      body: { status },
    },
    'Impossible de modifier le statut du membre.',
  )
}

export async function createOrganizationInvitation({ email, role = 'member'}){
   return apiRequest(
    '/organization/invitations',
    {
      method: 'POST',
      body: { email, role },
    },
    "Impossible de creer l'invitation.",
  )
}

export async function listOrganizationInvitations({ offset = 0, limit = 50 } = {}) {
  const query = new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
  })

  return apiRequest(
    `/organization/invitations?${query}`,
    {},
    'Impossible de charger les invitations.',
  )
}

export async function revokeOrganizationInvitation(invitationId) {
  return apiRequest(
    `/organization/invitations/${invitationId}/revoke`,
    {
      method: 'POST',
    },
    "Impossible de revoquer l'invitation.",
  )
}



export async function getOrganizationSettings() {
  return apiRequest(
    '/organization/settings',
    {},
    "Impossible de charger les paramètres de l'organisation.",
  )
}

export async function updateOrganizationSettings(data) {
  return apiRequest(
    '/organization/settings',
    {
      method: 'PATCH',
      body: data,
    },
    "Impossible d'enregistrer les paramètres de l'organisation.",
  )
}

export async function renewOrganizationInvitation(invitationId) {
  return apiRequest(
    `/organization/invitations/${invitationId}/renew`,
    {
      method: 'POST',
    },
    "Impossible de générer un nouveau lien d'invitation.",
  )
}

export async function syncOrganizationNotifications() {
  return apiRequest(
    '/organization/notifications/sync',
    {
      method: 'POST',
    },
    'Impossible de synchroniser les notifications.',
  )
}

export async function listOrganizationNotifications({
  offset = 0,
  limit = 20,
  unreadOnly = false,
} = {}) {
  const query = new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
    unread_only: String(unreadOnly),
  })
  return apiRequest(
    `/organization/notifications?${query}`,
    {},
    'Impossible de charger les notifications.',
  )
}

export async function markOrganizationNotificationRead(notificationId) {
  return apiRequest(
    `/organization/notifications/${notificationId}/read`,
    {
      method: 'PATCH',
    },
    'Impossible de marquer la notification comme lue.',
  )
}

export async function markAllOrganizationNotificationsRead() {
  return apiRequest(
    '/organization/notifications/read-all',
    {
      method: 'POST',
    },
    'Impossible de marquer les notifications comme lues.',
  )
}
