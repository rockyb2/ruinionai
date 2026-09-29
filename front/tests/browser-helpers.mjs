import { spawn } from 'node:child_process'
import { mkdir, mkdtemp, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { createServer } from 'node:net'

export const pause = ms => new Promise(resolve => setTimeout(resolve, ms))
export async function until(action, label) {
  const start = Date.now()
  while (Date.now() - start < 15000) {
    if (await action()) return
    await pause(100)
  }
  throw new Error(`Timed out: ${label}`)
}
async function freePort() {
  const server = createServer()
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
  const port = server.address().port
  await new Promise(resolve => server.close(resolve))
  return port
}

export async function withBrowser(name, test) {
  const root = resolve(import.meta.dirname, '..')
  const cache = resolve(root, 'node_modules/.cache', name)
  await mkdir(cache, { recursive: true })
  const profile = await mkdtemp(resolve(cache, 'edge-'))
  const appPort = await freePort(), debugPort = await freePort()
  const origin = `http://127.0.0.1:${appPort}`
  const vite = spawn(process.execPath, [resolve(root, 'node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', String(appPort)], { cwd: root, windowsHide: true, stdio: 'ignore' })
  const browser = spawn(process.env.EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', [
    '--headless=new', '--no-first-run', '--no-default-browser-check', '--disable-background-networking', '--mute-audio',
    `--remote-debugging-port=${debugPort}`, `--user-data-dir=${profile}`, 'about:blank',
  ], { windowsHide: true, stdio: 'ignore' })
  let socket, sequence = 0
  const pending = new Map(), errors = []
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
    async function screenshot(filename) {
      const shot = await command('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true })
      await writeFile(resolve(cache, filename), Buffer.from(shot.data, 'base64'))
    }
    await command('Runtime.enable')
    await command('Page.enable')
    await command('Emulation.setDeviceMetricsOverride', { width: 1600, height: 1000, deviceScaleFactor: 1, mobile: false })
    await test({ command, evaluate, click, visibleText, screenshot, errors, origin })
    console.log('Screenshots: ' + cache)
    await command('Browser.close').catch(() => {})
  } finally {
    socket?.close()
    browser.kill()
    vite.kill()
  }
}
