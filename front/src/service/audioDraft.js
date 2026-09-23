// A local draft per account. Nothing is sent to the transcription API here.
const DATABASE = 'ruinionai-audio'
const STORE = 'drafts'

export function audioDraftKey(token) {
  try {
    // Only used to partition local drafts, never to authorize an API request.
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const { sub } = JSON.parse(atob(payload.padEnd(Math.ceil(payload.length / 4) * 4, '=')))
    return sub ? `recording:${sub}` : null
  } catch {
    return null
  }
}

function openDatabase() {
  return new Promise((resolve, reject) => {
    if (!globalThis.indexedDB) {
      reject(new Error('Le stockage local est indisponible.'))
      return
    }
    const request = indexedDB.open(DATABASE, 1)
    request.onupgradeneeded = () => request.result.createObjectStore(STORE)
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
    request.onblocked = () => reject(new Error('Le stockage local est occupé.'))
  })
}

async function transaction(key, mode, action) {
  const database = await openDatabase()
  try {
    return await new Promise((resolve, reject) => {
      const tx = database.transaction(STORE, mode)
      const request = action(tx.objectStore(STORE), key)
      tx.oncomplete = () => resolve(request.result)
      tx.onerror = () => reject(tx.error)
      tx.onabort = () => reject(tx.error || new Error('Sauvegarde interrompue.'))
    })
  } finally {
    database.close()
  }
}

export const readAudioDraft = (key) => transaction(key, 'readonly', (store) => store.get(key))
export const saveAudioDraft = (key, draft) => transaction(key, 'readwrite', (store) => store.put(draft, key))
export const deleteAudioDraft = (key) => transaction(key, 'readwrite', (store) => store.delete(key))
