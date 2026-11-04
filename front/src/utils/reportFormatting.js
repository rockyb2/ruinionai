const SECTION_PATTERN = /^\s*(\d+[.)])\s+(.+)$/
const BULLET_PATTERN = /^\s*[-•]\s+(.+)$/
const DOSSIER_PATTERN = /^\s*Dossier\s*:\s*(.+)$/i
const LABEL_PATTERN = /^\s*(Contexte|Points discutés|Informations importantes|Propositions non validées|Incertitudes et contradictions)\s*:\s*(.*)$/i

export function inlineSegments(value = '') {
  const segments = []
  const pattern = /\*\*(.+?)\*\*/g
  let cursor = 0
  let match

  while ((match = pattern.exec(value)) !== null) {
    if (match.index > cursor) segments.push({ text: value.slice(cursor, match.index), strong: false })
    segments.push({ text: match[1], strong: true })
    cursor = pattern.lastIndex
  }
  if (cursor < value.length) segments.push({ text: value.slice(cursor), strong: false })
  return segments.length ? segments : [{ text: value, strong: false }]
}

function dossierParts(value) {
  const separator = value.indexOf(' — ')
  if (separator < 0) return { dossier: value.trim(), text: '' }
  return {
    dossier: value.slice(0, separator).trim(),
    text: value.slice(separator + 3).trim(),
  }
}

export function meetingTextBlocks(value = '') {
  return String(value)
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const section = line.match(SECTION_PATTERN)
      if (section) return { type: 'section', number: section[1], text: section[2].replace(/^\*\*|\*\*$/g, '') }

      const bullet = line.match(BULLET_PATTERN)
      if (bullet) {
        const bulletText = bullet[1]
        const legacyReference = bulletText.match(/^\[([^\]]+)]\s*(.+)$/)
        if (legacyReference) {
          return {
            type: 'dossier-reference',
            dossier: legacyReference[1].trim(),
            text: legacyReference[2].trim(),
            segments: inlineSegments(legacyReference[2].trim()),
          }
        }
        const dossierReference = bulletText.match(DOSSIER_PATTERN)
        if (dossierReference) {
          const parts = dossierParts(dossierReference[1].replace(/^\*\*|\*\*$/g, ''))
          if (parts.text) return { type: 'dossier-reference', ...parts, segments: inlineSegments(parts.text) }
        }
        return { type: 'bullet', segments: inlineSegments(bulletText) }
      }

      const dossier = line.match(DOSSIER_PATTERN)
      if (dossier) {
        const parts = dossierParts(dossier[1].replace(/^\*\*|\*\*$/g, ''))
        return { type: parts.text ? 'dossier-reference' : 'dossier', ...parts, segments: inlineSegments(parts.text) }
      }

      const legacyReference = line.match(/^\[([^\]]+)]\s*(.+)$/)
      if (legacyReference) {
        return {
          type: 'dossier-reference',
          dossier: legacyReference[1].trim(),
          text: legacyReference[2].trim(),
          segments: inlineSegments(legacyReference[2].trim()),
        }
      }

      const label = line.match(LABEL_PATTERN)
      if (label) return { type: 'label', label: label[1], text: label[2], segments: inlineSegments(label[2]) }

      return { type: 'paragraph', segments: inlineSegments(line) }
    })
}
