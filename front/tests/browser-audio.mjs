// Optional real-browser smoke test. Uses a synthetic microphone and stubbed API:
// no user credentials, production data, transcription calls or paid requests.
// EDGE_PATH=".../msedge.exe" node tests/browser-audio.mjs
import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { mkdir, mkdtemp, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { createServer } from 'node:net'

const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
async function freePort() {
  const server = createServer()
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve))
  const port = server.address().port
  await new Promise((resolve) => server.close(resolve))
  return port
}
async function until(action, label, timeout = 15000) {
  const start = Date.now()
  while (Date.now() - start < timeout) {
    try { if (await action()) return } catch {}
    await pause(100)
  }
  throw new Error(`Timed out: ${label}`)
}

const root = resolve(import.meta.dirname, '..')
const cache = resolve(root, 'node_modules/.cache/audio-smoke')
await mkdir(cache, { recursive: true })
const profile = await mkdtemp(resolve(cache, 'edge-'))
const appPort = await freePort()
const debugPort = await freePort()
const origin = `http://127.0.0.1:${appPort}`
const vite = spawn(process.execPath, [resolve(root, 'node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', String(appPort)],
  { cwd: root, windowsHide: true, stdio: 'ignore' })
const browser = spawn(process.env.EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', [
  '--headless=new', '--no-first-run', '--no-default-browser-check', '--disable-background-networking',
  '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--autoplay-policy=no-user-gesture-required',
  '--mute-audio', `--remote-debugging-port=${debugPort}`, `--user-data-dir=${profile}`, 'about:blank',
], { windowsHide: true, stdio: 'ignore' })
let socket
let sequence = 0
const pending = new Map()
const errors = []

try {
  await until(async () => (await fetch(origin)).ok, 'Vite')
  let pages
  await until(async () => { pages = await (await fetch(`http://127.0.0.1:${debugPort}/json/list`)).json(); return pages.length }, 'Edge')
  socket = new WebSocket(pages.find((page) => page.type === 'page').webSocketDebuggerUrl)
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject })
  socket.onmessage = (event) => {
    const message = JSON.parse(event.data)
    if (message.id && pending.has(message.id)) {
      const { resolve, reject, timeout } = pending.get(message.id)
      clearTimeout(timeout)
      pending.delete(message.id)
      if (message.error) reject(new Error(JSON.stringify(message.error)))
      else resolve(message.result)
    }
    if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails)
  }
  function command(method, params = {}) {
    const id = ++sequence
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)) }, 15000)
      pending.set(id, { resolve, reject, timeout })
      socket.send(JSON.stringify({ id, method, params }))
    })
  }
  async function evaluate(expression) {
    const response = await command('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true, userGesture: true })
    if (response.exceptionDetails) throw new Error(JSON.stringify(response.exceptionDetails))
    return response.result.value
  }
  const click = (label) => evaluate(`(() => { const button = [...document.querySelectorAll('button')].find(b => b.getAttribute('aria-label') === ${JSON.stringify(label)} || b.textContent.trim() === ${JSON.stringify(label)}); if (!button || button.disabled) throw new Error('Button unavailable: ' + ${JSON.stringify(label)}); button.click(); return true })()`)
  const enabled = (label) => evaluate(`!![...document.querySelectorAll('button')].find(b => !b.disabled && (b.getAttribute('aria-label') === ${JSON.stringify(label)} || b.textContent.trim() === ${JSON.stringify(label)}))`)

  await command('Runtime.enable')
  await command('Page.enable')
  await command('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false })
  await command('Page.addScriptToEvaluateOnNewDocument', { source: `
    localStorage.setItem('ruinionai.access_token', 'test.' + btoa(JSON.stringify({sub:'audio-smoke-test'})) + '.test');
    window.__apiCalls = [];
    const originalFetch = window.fetch.bind(window);
    window.fetch = async (url, options = {}) => {
      if (!String(url).startsWith('/api/')) return originalFetch(url, options);
      const path = String(url);
      const fields = options.body instanceof FormData ? [...options.body].map(([key, value]) => ({key, size:value.size, name:value.name, type:value.type})) : [];
      window.__apiCalls.push({path, fields, method:options.method || 'GET'});
      const body = path.includes('/auth/me') ? {user:{id:1,first_name:'Audio',last_name:'Test'}, organization:{id:1,name:'Test'}, role:'member'}
        : path.includes('/meetings/invitees') || path.includes('/organization/notifications') ? {items:[],total:0,unread_count:0,offset:0,limit:20}
        : path === '/api/meetings/' && !options.method ? []
        : {id:1, title:'Test', transcription:'Transcription simulée', summary_short:'Résumé simulé'};
      return new Response(JSON.stringify(body), {status:200, headers:{'Content-Type':'application/json'}});
    };
  ` })
  await command('Page.navigate', { url: `${origin}/reunion` })
  await until(() => enabled('Enregistrer'), 'record button')
  await click('Enregistrer')
  await until(() => enabled('Mettre en pause'), 'recording')
  await pause(1500)
  await click('Mettre en pause')
  await until(() => enabled('Écouter l’audio'), 'pause preview')
  assert.equal(await enabled('Générer les résumés'), false)
  await click('Écouter l’audio')
  await until(() => evaluate('document.querySelector("audio").currentTime > 0.2'), 'actual preview playback')
  await click('Reprendre')
  await until(() => enabled('Mettre en pause'), 'resume')
  await pause(1500)
  await click('Terminer')
  await until(() => enabled('Générer les résumés'), 'ready to submit')
  assert.ok(await evaluate('Number(document.querySelector("input[type=range]").max) > 2.5'))
  assert.equal(await evaluate('window.__apiCalls.filter(c => c.method === "POST").length'), 0)
  await until(() => evaluate('document.body.innerText.includes("Brouillon sauvegardé")'), 'saved draft')
  await command('Page.reload')
  await until(() => enabled('Générer les résumés'), 'restored draft')
  assert.ok(await evaluate('document.body.innerText.includes("Brouillon restauré")'))
  // Start near the end of the first part and verify playback advances into the next.
  await evaluate('(() => { const slider = document.querySelector("input[type=range]"); slider.value = 1.2; slider.dispatchEvent(new Event("input", {bubbles:true})); })()')
  const firstUrl = await evaluate('document.querySelector("audio").src')
  await click('Écouter l’audio')
  await until(() => evaluate(`document.querySelector('audio').src !== ${JSON.stringify(firstUrl)} && document.querySelector('audio').currentTime > 0.1`), 'playback crosses segment boundary')
  await click('Générer les résumés')
  await until(() => evaluate('window.__apiCalls.some(c => c.path.endsWith("/summary"))'), 'submission')
  const upload = await evaluate('window.__apiCalls.find(c => c.path.endsWith("/audio"))')
  assert.equal(upload.fields.length, 2)
  assert.ok(upload.fields.every((field) => field.key === 'files' && field.size > 0 && field.type.startsWith('audio/')))
  assert.equal(errors.length, 0, JSON.stringify(errors))
  const screenshot = await command('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true })
  await writeFile(resolve(cache, 'recording.png'), Buffer.from(screenshot.data, 'base64'))
  console.log('PASS: real microphone simulation, pause/listen/resume, seeking across segments, draft reload, one ordered upload, no premature API calls.')
  console.log(`Screenshot: ${resolve(cache, 'recording.png')}`)
  await command('Browser.close').catch(() => {})
} finally {
  socket?.close()
  browser.kill()
  vite.kill()
}
