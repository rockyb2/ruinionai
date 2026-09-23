export const MAX_AUDIO_BYTES = 500 * 1024 * 1024
export const MAX_AUDIO_SEGMENTS = 100

export function formatAudioTime(seconds) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0))
  return [Math.floor(total / 3600), Math.floor(total / 60) % 60, total % 60]
    .map((value) => String(value).padStart(2, '0'))
    .join(':')
}

export function audioExtension(mimeType) {
  const type = mimeType.split(';')[0]
  return { 'audio/mp4': 'm4a', 'audio/ogg': 'ogg', 'audio/mpeg': 'mp3', 'audio/wav': 'wav' }[type] || 'webm'
}

export function locateAudioPosition(durations, seconds) {
  let remaining = Math.max(0, seconds)
  for (let index = 0; index < durations.length; index += 1) {
    if (remaining < durations[index] || index === durations.length - 1) {
      return { index, offset: Math.min(remaining, durations[index]) }
    }
    remaining -= durations[index]
  }
  return { index: 0, offset: 0 }
}
