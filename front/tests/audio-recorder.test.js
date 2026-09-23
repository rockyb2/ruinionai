import assert from 'node:assert/strict'
import { afterEach, beforeEach, test } from 'node:test'
import { effectScope } from 'vue'
import { useAudioRecorder } from '../src/composables/useAudioRecorder.js'
import { formatAudioTime, locateAudioPosition } from '../src/utils/audio.js'

let scope
let recorders
let tracks
let storage
let writes
let permission

class FakeRecorder extends EventTarget {
  static isTypeSupported(type) { return type === 'audio/mp4' }
  constructor(stream, options) {
    super()
    this.mimeType = options.mimeType
    this.state = 'inactive'
    recorders.push(this)
  }
  start() { this.state = 'recording' }
  stop() {
    this.state = 'inactive'
    // The final bytes arrive asynchronously, just before the stop event.
    queueMicrotask(() => {
      const event = new Event('dataavailable')
      event.data = new Blob([`part-${recorders.indexOf(this)}`], { type: this.mimeType })
      this.dispatchEvent(event)
      this.dispatchEvent(new Event('stop'))
    })
  }
}

beforeEach(() => {
  recorders = []
  tracks = []
  writes = []
  permission = null
  globalThis.window = new EventTarget()
  globalThis.MediaRecorder = FakeRecorder
  Object.defineProperty(globalThis, 'navigator', { configurable: true, value: {
    mediaDevices: { getUserMedia: async () => {
      if (permission) return permission()
      const track = Object.assign(new EventTarget(), { stopped: false, stop() { this.stopped = true } })
      tracks.push(track)
      return { getTracks: () => [track], getAudioTracks: () => [track] }
    } },
  } })
  storage = {
    readAudioDraft: async () => null,
    saveAudioDraft: async (key, value) => { writes.push(structuredClone(value)) },
    deleteAudioDraft: async () => { writes.push('deleted') },
  }
})

afterEach(() => { scope?.stop() })

async function recorder() {
  scope = effectScope()
  const recording = scope.run(() => useAudioRecorder({ draftKey: 'user-1', storage }))
  await recording.restored
  return recording
}

test('pause, resume and finish preserve ordered, independently playable files and MIME extensions', async () => {
  const recording = await recorder()
  await recording.start()
  await recording.pause()
  assert.equal(recording.state.value, 'paused')
  assert.equal(tracks[0].stopped, true)
  assert.equal(recording.segments.value.length, 1)
  const first = recording.segments.value[0].file
  assert.match(first.name, /\.m4a$/)
  assert.equal(first.type, 'audio/mp4')
  await recording.start()
  await recording.finish()
  assert.equal(recording.state.value, 'ready')
  assert.equal(recording.segments.value.length, 2)
  assert.equal(recording.segments.value[0].file, first)
  assert.deepEqual(await Promise.all(recording.segments.value.map((segment) => segment.file.text())), ['part-0', 'part-1'])
  assert.ok(recording.duration.value > 0)
  assert.equal(tracks[1].stopped, true)
})

test('double start or pause cannot create duplicate segments', async () => {
  const recording = await recorder()
  await Promise.all([recording.start(), recording.start()])
  assert.equal(recorders.length, 1)
  await Promise.all([recording.pause(), recording.pause()])
  assert.equal(recording.segments.value.length, 1)
})

test('a microphone refusal on resume preserves the previous recording', async () => {
  const recording = await recorder()
  await recording.start()
  await recording.pause()
  permission = async () => { throw new DOMException('Denied', 'NotAllowedError') }
  await recording.start()
  assert.equal(recording.state.value, 'paused')
  assert.equal(recording.segments.value.length, 1)
  assert.match(recording.error.value, /Autorisez/)
})

test('saved drafts restore without requesting microphone access', async () => {
  storage.readAudioDraft = async () => ({ segments: [{
    id: 'saved', file: new Blob(['saved'], { type: 'audio/webm' }), duration: 3661,
  }], ready: false })
  const recording = await recorder()
  assert.equal(recording.state.value, 'paused')
  assert.equal(recording.duration.value, 3661)
  assert.equal(recorders.length, 0)
  await recording.finish()
  assert.equal(writes.at(-1).ready, true)
  await recording.discard()
  assert.equal(writes.at(-1), 'deleted')
  assert.equal(recording.state.value, 'idle')
})

test('a permission response after navigation immediately releases the microphone', async () => {
  let grant
  const track = { stopped: false, stop() { this.stopped = true } }
  permission = () => new Promise((resolve) => { grant = resolve })
  const recording = await recorder()
  const pending = recording.start()
  scope.stop()
  grant({ getTracks: () => [track] })
  await pending
  assert.equal(track.stopped, true)
  assert.equal(recorders.length, 0)
})

test('storage failure does not prevent listening, finishing or retaining audio', async () => {
  storage.saveAudioDraft = async () => { throw new Error('Quota exceeded') }
  const recording = await recorder()
  await recording.start()
  await recording.pause()
  await recording.finish()
  assert.equal(recording.segments.value.length, 1)
  assert.equal(recording.state.value, 'ready')
  assert.match(recording.draftMessage.value, /indisponible/)
})

test('playback seeking maps the global timeline across segment boundaries', () => {
  assert.deepEqual(locateAudioPosition([10, 20, 15], 14), { index: 1, offset: 4 })
  assert.deepEqual(locateAudioPosition([10, 20, 15], 30), { index: 2, offset: 0 })
  assert.deepEqual(locateAudioPosition([10, 20, 15], 45), { index: 2, offset: 15 })
  assert.equal(formatAudioTime(3661), '01:01:01')
})
