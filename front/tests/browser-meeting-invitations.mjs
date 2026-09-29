// Real browser, stubbed API, synthetic microphone. No invitations or AI calls leave this test.
import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { mkdir, mkdtemp, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { createServer } from 'node:net'

const pause = ms => new Promise(resolve => setTimeout(resolve, ms))
async function freePort() {
  const server = createServer()
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
  const port = server.address().port
  await new Promise(resolve => server.close(resolve))
  return port
}
async function until(action, label) {
  const start = Date.now()
  while (Date.now() - start < 15000) {
    if (await action()) return
    await pause(100)
  }
  throw new Error(`Timed out: ${label}`)
}

const root = resolve(import.meta.dirname, '..')
const cache = resolve(root, 'node_modules/.cache/meeting-invitations-smoke')
await mkdir(cache, { recursive: true })
const profile = await mkdtemp(resolve(cache, 'edge-'))
const appPort = await freePort()
const debugPort = await freePort()
const origin = `http://127.0.0.1:${appPort}`
const vite = spawn(process.execPath, [resolve(root, 'node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', String(appPort)], { cwd: root, windowsHide: true, stdio: 'ignore' })
const browser = spawn(process.env.EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', [
  '--headless=new', '--no-first-run', '--no-default-browser-check', '--disable-background-networking',
  '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--mute-audio',
  `--remote-debugging-port=${debugPort}`, `--user-data-dir=${profile}`, 'about:blank',
], { windowsHide: true, stdio: 'ignore' })
let socket
let sequence = 0
const pending = new Map()
const errors = []

try {
  await until(async () => { try { return (await fetch(origin)).ok } catch { return false } }, 'Vite')
  let pages
  await until(async () => { try { pages = await (await fetch(`http://127.0.0.1:${debugPort}/json/list`)).json(); return pages.length } catch { return false } }, 'Edge')
  socket = new WebSocket(pages.find(page => page.type === 'page').webSocketDebuggerUrl)
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject })
  socket.onmessage = event => {
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
  const click = label => evaluate(`(() => { const element = [...document.querySelectorAll('button,input')].find(e => e.getAttribute('aria-label') === ${JSON.stringify(label)} || e.textContent.trim() === ${JSON.stringify(label)}); if (!element || element.disabled) throw new Error('Unavailable: ' + ${JSON.stringify(label)}); element.click() })()`)
  const visibleText = text => evaluate(`document.body.innerText.includes(${JSON.stringify(text)})`)
  await command('Runtime.enable')
  await command('Page.enable')
  await command('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false })
  await command('Page.addScriptToEvaluateOnNewDocument', { source: `
    localStorage.setItem('ruinionai.access_token', 'test.' + btoa(JSON.stringify({sub:'invitations-smoke-test'})) + '.test');
    window.__apiCalls = [];
    window.__meetings = [];
    window.__failCreate = true;
    window.__failSummary = true;
    window.__read = false;
    const originalFetch = window.fetch.bind(window);
    window.fetch = async (url, options = {}) => {
      if (!String(url).startsWith('/api/')) return originalFetch(url, options);
      const path = String(url);
      const method = options.method || 'GET';
      const payload = options.body && !(options.body instanceof FormData) ? JSON.parse(options.body) : null;
      window.__apiCalls.push({path, method, payload});
      const json = (body, status=200) => new Response(JSON.stringify(body), {status,headers:{'Content-Type':'application/json'}});
      const meeting = {id:41,title:'Réunion commerciale',participants:'Julie Martin, Awa Koné',participant_member_ids:[12]};
      const notification = {id:7,kind:'meeting_invitation',meeting_id:41,title:'Invitation à une réunion',message:'Julie vous invite à la réunion',is_read:window.__read,created_at:'2026-09-25T10:00:00'};
      if (path === '/api/auth/me') return json({user:{id:1,first_name:'Julie',last_name:'Martin'},organization:{id:1,name:'Équipe'},role:'member'});
      if (path.startsWith('/api/meetings/invitees')) {
        const q = new URL(path, location.origin).searchParams.get('q');
        return json({items:q === 'introuvable' ? [] : [{member_id:12,name:'Awa Koné',email:'awa@example.test'}],total:q === 'introuvable' ? 0 : 1,offset:0,limit:20});
      }
      if (path === '/api/meetings/' && method === 'POST') {
        if (window.__failCreate) { window.__failCreate = false; return json({detail:'Membre indisponible, réessayez.'},422) }
        window.__meetings = [meeting]; return json(meeting);
      }
      if (path === '/api/meetings/') return json(window.__meetings);
      if (path.endsWith('/summary')) {
        if (window.__failSummary) { window.__failSummary = false; return json({detail:'Génération temporairement indisponible.'},502) }
        window.__meetings = [{...meeting,has_source_audio:true,processing_status:'completed',summary_short:'Résumé simulé',transcription:'Transcription simulée'}];
        return json(window.__meetings[0]);
      }
      if (path.endsWith('/audio')) return json({...meeting,has_source_audio:true,processing_status:'queued'});
      if (path === '/api/meetings/41') return json(window.__meetings[0]);
      if (path.startsWith('/api/organization/notifications?')) return json({items:[notification],total:1,unread_count:window.__read ? 0 : 1});
      if (path === '/api/organization/notifications/7/read') { window.__read = true; return json({...notification,is_read:true}) }
      return json({detail:'Unexpected test API call: ' + path},500);
    };
  ` })
  await command('Page.navigate', { url: `${origin}/reunion` })
  await until(() => visibleText('Awa Koné'), 'member directory')
  assert.equal(await evaluate('document.querySelector("input[placeholder=Nom]")'), null)
  assert.equal(await evaluate('!!document.querySelector("button[aria-label=Notifications]")'), true)
  await evaluate(`(() => { const input = document.querySelector('input[aria-label="Rechercher un membre à inviter"]'); input.value = 'introuvable'; input.dispatchEvent(new Event('input', {bubbles:true})) })()`)
  await until(() => visibleText('Aucun membre ne correspond'), 'search empty state')
  await evaluate(`(() => { const input = document.querySelector('input[aria-label="Rechercher un membre à inviter"]'); input.value = ''; input.dispatchEvent(new Event('input', {bubbles:true})) })()`)
  await until(() => visibleText('Awa Koné'), 'restored members')
  await click('Inviter Awa Koné')
  await click('Retirer Awa Koné')
  await click('Inviter Awa Koné')
  const screenshot = await command('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true })
  await writeFile(resolve(cache, 'invitees.png'), Buffer.from(screenshot.data, 'base64'))
  await click('Inviter à la réunion')
  await until(() => visibleText('Membre indisponible, réessayez.'), 'invitation error')
  await click('Inviter à la réunion')
  await until(() => visibleText('Invitation envoyée à 1 membre'), 'invitation without audio')
  const creationCalls = await evaluate('window.__apiCalls.filter(c => c.path === "/api/meetings/" && c.method === "POST")')
  assert.equal(creationCalls.length, 2)
  assert.deepEqual(creationCalls[1].payload, {title:'Réunion commerciale', participant_member_ids:[12]})
  assert.equal(await evaluate('window.__apiCalls.some(c => c.path.endsWith("/audio"))'), false)
  await click('Enregistrer')
  await until(() => visibleText('Mettre en pause'), 'recording')
  await pause(1200)
  await click('Terminer')
  await until(() => evaluate('[...document.querySelectorAll("button")].some(b => b.textContent.trim() === "Générer les résumés" && !b.disabled)'), 'ready audio')
  await click('Générer les résumés')
  await until(() => visibleText('Génération temporairement indisponible.'), 'summary error')
  await click('Générer les résumés')
  await until(() => visibleText('Transcription simulée'), 'summary retry opens history')
  await until(() => evaluate('!!document.querySelector("[data-testid=transcript-panel]")'), 'detail view mounted')
  await click('Résumé')
  await until(() => visibleText('Résumé simulé'), 'saved summary')
  assert.equal(await evaluate('window.__apiCalls.filter(c => c.path === "/api/meetings/" && c.method === "POST").length'), 2)
  assert.equal(await evaluate('window.__apiCalls.filter(c => c.path.endsWith("/audio") && c.method === "POST").length'), 1)
  assert.equal(await evaluate('window.__apiCalls.some(c => c.path.endsWith("/notifications/sync"))'), false)
  await click('Notifications')
  await until(() => visibleText('Voir la réunion →'), 'meeting notification')
  await evaluate(`document.querySelector('dialog button.mb-2').click()`)
  await until(() => evaluate('location.pathname === "/historique" && location.search === "?meeting=41"'), 'meeting link')
  await until(() => visibleText('Réunion commerciale'), 'invited meeting')
  assert.equal(await evaluate('window.__read'), true)
  assert.equal(errors.length, 0, JSON.stringify(errors))
  console.log('PASS: member selection/search/removal, invitation before audio, error recovery, no duplicate invitations on generation retry, member notifications and exact meeting link.')
  console.log('Screenshot: ' + resolve(cache, 'invitees.png'))
  await command('Browser.close').catch(() => {})
} finally {
  socket?.close()
  browser.kill()
  vite.kill()
}
