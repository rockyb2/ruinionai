const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function parseApiError(response, fallbackMessage) {
  try {
    const data = await response.json();
    return data.detail || data.message || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

async function requestJson(response, fallbackMessage) {
  if (!response.ok) {
    throw new Error(await parseApiError(response, fallbackMessage));
  }

  return response.json();
}

export async function createMeeting(data) {
  const response = await fetch(`${API_URL}/meetings/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  return requestJson(response, "Impossible de créer la réunion.");
}

export async function uploadAudio(meetingId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/meetings/${meetingId}/audio`, {
    method: "POST",
    body: formData,
  });

  return requestJson(response, "Impossible de transcrire la note vocale.");
}

export async function generate_Summary(meetingId) {
  const response = await fetch(`${API_URL}/meetings/${meetingId}/summary`, {
    method: "POST",
  });

  return requestJson(response, "Impossible de générer le résumé.");
}

export async function getMeeting(meetingId) {
  const response = await fetch(`${API_URL}/meetings/${meetingId}`);

  return requestJson(response, "Réunion introuvable.");
}
