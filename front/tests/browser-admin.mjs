import assert from 'node:assert/strict'
import { withBrowser, until } from './browser-helpers.mjs'

await withBrowser('admin-connected', async ({ command, evaluate, click, visibleText, screenshot, errors, origin }) => {
  await command('Page.addScriptToEvaluateOnNewDocument', { source: `
    localStorage.setItem('ruinionai.access_token', 'browser-test-token');
    window.__adminRequests = [];
    window.__denyAdmin = localStorage.getItem('deny-admin') === 'yes';
    const organizations = [{ id: 1, name: 'Ivoir Trips', description: 'Tourisme', members_count: 2, meetings_count: 1, audio_seconds: 3600, created_at: '2026-09-01T10:00:00', invitation_expiration_days: 7 }];
    const users = [{ id: 2, first_name: 'Awa', last_name: 'Koné', name: 'Awa Koné', email: 'awa@example.com', is_active: true, is_super_admin: false, meetings_count: 1, created_at: '2026-09-01T10:00:00', memberships: [{ id: 1, organization_id: 1, organization_name: 'Ivoir Trips', role: 'owner', status: 'active' }] }];
    const meetings = [{ id: 7, title: 'Réunion commerciale', organization_id: 1, organization_name: 'Ivoir Trips', created_by_user_id: 2, created_by_name: 'Awa Koné', date: '2026-09-29T10:14:00', created_at: '2026-09-29T10:14:00', audio_duration: 3600, audio_available: false, has_source_audio: false, has_transcription: true, has_summary: true, has_report: false, processing_status: 'completed', transcription: 'Le budget est validé.', summary_short: 'Budget validé.', summary_long: 'La réunion confirme le budget.', participants: 'Awa Koné' }];
    const json = (value, status = 200) => Promise.resolve(new Response(status === 204 ? null : JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } }));
    window.fetch = async (input, options = {}) => {
      const url = new URL(String(input), location.origin); const path = url.pathname; const method = options.method || 'GET';
      window.__adminRequests.push({ path, method, organization: new Headers(options.headers).get('X-Organization-Id') });
      if (path === '/api/admin/me') return window.__denyAdmin ? json({ detail: 'Droits requis.' }, 403) : json({ id: 1, first_name: 'Super', last_name: 'Admin', email: 'admin@example.com', is_active: true, is_super_admin: true });
      if (path === '/api/admin/organizations' && method === 'GET') return json({ items: organizations, total: organizations.length, offset: 0, limit: 20, stats: { organizations: organizations.length, members: 2, meetings: 1, audio_seconds: 3600 } });
      if (path === '/api/admin/organizations' && method === 'POST') { const body = JSON.parse(options.body); const row = { ...organizations[0], ...body, id: 2, members_count: 1, meetings_count: 0, audio_seconds: 0 }; organizations.unshift(row); return json(row, 201); }
      if (path.startsWith('/api/admin/organizations/') && path.endsWith('/members')) return json({ items: [{ id: 1, user_id: 2, name: 'Awa Koné', email: 'awa@example.com', role: 'owner', status: 'active' }], total: 1, offset: 0, limit: 100 });
      if (path.startsWith('/api/admin/organizations/')) return json(organizations.find(row => row.id === Number(path.split('/').pop())));
      if (path === '/api/admin/users' && method === 'GET') return json({ items: users, total: users.length, offset: 0, limit: 20, stats: { total: users.length, active: users.length, inactive: 0, super_admins: 1 } });
      if (path.startsWith('/api/admin/users/')) return json(users.find(row => row.id === Number(path.split('/').pop())));
      if (path === '/api/admin/meetings' && method === 'GET') return json({ items: meetings, total: meetings.length, offset: 0, limit: 20, stats: { total: 1, completed: 1, failed: 0, active: 0, audio_seconds: 3600 } });
      if (path.startsWith('/api/admin/meetings/')) return json(meetings.find(row => row.id === Number(path.split('/').pop())));
      return json({ detail: 'Route de test absente: ' + method + ' ' + path }, 404);
    };
  ` })
  const navigate = async path => {
    await command('Page.navigate', { url: origin + path })
    try {
      await until(() => evaluate('document.querySelector(".a-profile")?.innerText.includes("Super Admin")'), 'admin identity')
    } catch (error) {
      console.error(await evaluate('document.body.innerText'), JSON.stringify(errors))
      throw error
    }
  }
  await navigate('/admin/organisations')
  await until(() => visibleText('Ivoir Trips'), 'organizations loaded')
  assert.equal(await visibleText('Gestion réelle des organisations'), true)
  assert.equal(await evaluate('window.__adminRequests.some(row => row.organization !== null)'), false, 'admin calls must not use an organization context')
  await click('Voir Ivoir Trips')
  await until(() => visibleText('Expiration des invitations'), 'organization details')
  await click('Nouvelle organisation')
  await until(() => evaluate('!!document.querySelector("dialog[open]")'), 'organization dialog')
  await evaluate(`(() => { const dialog=document.querySelector('dialog[open]'); const name=dialog.querySelector('input[required]'); name.value='Nouvelle équipe'; name.dispatchEvent(new Event('input',{bubbles:true})); const select=dialog.querySelector('select'); select.value='2'; select.dispatchEvent(new Event('change',{bubbles:true})); dialog.querySelector('form').requestSubmit(); })()`)
  await until(() => visibleText('Organisation créée.'), 'organization created')
  await navigate('/admin/utilisateurs')
  await until(() => visibleText('Awa Koné'), 'users loaded')
  await click('Voir Awa Koné')
  await until(() => visibleText('Organisations et rôles'), 'user details')
  await navigate('/admin/reunions')
  await until(() => visibleText('Réunion commerciale'), 'meetings loaded')
  await click('Voir Réunion commerciale')
  await click('Transcription')
  assert.equal(await visibleText('Le budget est validé.'), true)
  await screenshot('connected-desktop.png')
  await command('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true })
  assert.equal(await evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), true, 'mobile overflow')
  await screenshot('connected-mobile.png')
  await evaluate("localStorage.setItem('deny-admin', 'yes')")
  await command('Page.reload')
  await until(() => visibleText('Accès refusé'), 'forbidden admin')
  assert.equal(errors.length, 0, JSON.stringify(errors))
  console.log('PASS: admin authorization, real API screens, creation, details, transcript, desktop and mobile.')
})
