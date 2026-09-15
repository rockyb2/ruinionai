const API_URL = import.meta.env.VITE_API_URL || '/api'
const TOKEN_STORAGE_KEY = 'ruinionai.access_token'

function getTokenStorage(remember) {
  return remember ? window.localStorage : window.sessionStorage
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

  return response.json()
}

async function apiRequest(path, options = {}, fallbackMessage = 'Une erreur est survenue.') {
  const { auth = true, body, headers = {}, ...fetchOptions } = options
  const requestHeaders = { ...headers }

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
  return apiRequest('/auth/me', {}, 'Session invalide.')
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

export async function uploadAudio(meetingId, file) {
  const formData = new FormData()
  formData.append('file', file)

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
    headers: token ? { Authorization: `Bearer ${token}` } : {},
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

export async function getMeeting(meetingId) {
  return apiRequest(`/meetings/${meetingId}`, {}, 'Reunion introuvable.')
}
