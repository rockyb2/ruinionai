// Real browser and playable synthetic audio; all API/provider responses are local fixtures.
import assert from 'node:assert/strict'
import { withBrowser, until, pause } from './browser-helpers.mjs'

await withBrowser('history-smoke', async ({ command, evaluate, click, visibleText, screenshot, errors, origin }) => {
  await command('Page.addScriptToEvaluateOnNewDocument', { source: `
    localStorage.setItem('ruinionai.access_token', 'test.history.test');
    window.__apiCalls = [];
    const seed = [
      {id:101,title:'Synthèse financière ITI',participants:'Jonathan Zadi, Awa Koné, Boris',processing_status:'completed',has_source_audio:true,audio_available:true,audio_duration:12,transcription:'Le budget est validé. Awa prépare le planning.',transcription_segments:[{start:0,end:4,text:'Le budget est validé pour le prochain trimestre.'},{start:4,end:8,text:'Awa prépare le planning et confirme les disponibilités.'},{start:8,end:12,text:'Les marges de transport seront vérifiées vendredi.'}],summary_short:'Le budget est validé. Les marges seront vérifiées vendredi.',summary_long:'1. Résumé long\\nL’équipe a validé le budget.\\n\\n2. Points importants\\nLes marges et le planning.',report_path:'/reports/test.docx',created_at:'2026-09-25T12:00:00'},
      {id:102,title:'Ancienne réunion commerciale',participants:'Awa Koné',processing_status:'idle',transcription:'Les objectifs commerciaux sont fixés.',summary_short:'Objectifs validés.',created_at:'2026-09-20T09:30:00'},
      {id:103,title:'Planification de l’équipe',participants:'Jonathan Zadi, Awa Koné',processing_status:'failed',transcription:'Le planning est prêt.',summary_short:'Le planning est prêt et sauvegardé.',summary_long:'Le planning doit être partagé.',processing_error:'La création du Word a échoué. Les résumés sont conservés.',created_at:'2026-09-24T10:00:00'},
      {id:104,title:'Réunion en traitement',participants:'Jonathan Zadi',processing_status:'queued',has_source_audio:true,created_at:'2026-09-26T09:00:00'}
    ];
    window.__meetings = JSON.parse(localStorage.getItem('history-fixtures') || JSON.stringify(seed));
    window.__save = () => localStorage.setItem('history-fixtures',JSON.stringify(window.__meetings));
    window.__retryReads = 0;
    const originalFetch = window.fetch.bind(window);
    window.fetch = async (url, options = {}) => {
      if (!String(url).startsWith('/api/')) return originalFetch(url, options);
      const path = String(url), method = options.method || 'GET';
      window.__apiCalls.push({path,method,headers:options.headers});
      const json = (body,status=200) => new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json'}});
      if (path === '/api/auth/me') return json({user:{id:1,first_name:'Jonathan',last_name:'Zadi'},organization:{id:1,name:'Ruinion AI'},role:'member'});
      if (path.includes('/organization/notifications') || path.includes('/meetings/invitees')) return json({items:[],total:0,unread_count:0});
      if (path === '/api/meetings/') return json(window.__meetings);
      const id = Number(path.split('/')[3]);
      const meeting = window.__meetings.find(m => m.id === id);
      if (meeting && path.endsWith('/audio')) {
        const buffer = new ArrayBuffer(44 + 16000*2*12), view = new DataView(buffer);
        const str = (offset,value) => [...value].forEach((letter,i) => view.setUint8(offset+i,letter.charCodeAt(0)));
        str(0,'RIFF'); view.setUint32(4,buffer.byteLength-8,true); str(8,'WAVE'); str(12,'fmt ');
        view.setUint32(16,16,true); view.setUint16(20,1,true); view.setUint16(22,1,true); view.setUint32(24,16000,true); view.setUint32(28,32000,true); view.setUint16(32,2,true); view.setUint16(34,16,true); str(36,'data'); view.setUint32(40,buffer.byteLength-44,true);
        return new Response(buffer,{headers:{'Content-Type':'audio/wav'}});
      }
      if (meeting && path.endsWith('/summary')) {meeting.processing_status='queued'; meeting.processing_error=null; window.__retryReads=0; window.__save(); return json(meeting,202)}
      if (meeting && path.endsWith('/report')) return new Response('fake docx',{headers:{'Content-Type':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','Content-Disposition':'attachment; filename="test.docx"'}});
      if (meeting) {
        if (id === 103 && ['queued','building'].includes(meeting.processing_status)) {
          window.__retryReads++;
          meeting.processing_status = window.__retryReads < 2 ? 'building' : 'completed';
          if (meeting.processing_status === 'completed') meeting.report_path='/reports/planning.docx';
          window.__save();
        }
        return json(meeting);
      }
      return json({detail:'Not found'},404);
    };
  ` })
  await command('Page.navigate', { url: `${origin}/historique` })
  await until(() => evaluate('document.querySelectorAll("[data-testid=meeting-card]").length === 4'), 'history gallery')
  await screenshot('history-desktop.png')
  await evaluate(`(() => { const input=document.querySelector('input[aria-label="Rechercher une réunion"]'); input.value='financière'; input.dispatchEvent(new Event('input',{bubbles:true})) })()`)
  await until(() => evaluate('document.querySelectorAll("[data-testid=meeting-card]").length === 1'), 'search filter')
  await evaluate(`document.querySelector('[data-testid="meeting-card"]').click()`)
  await until(() => evaluate('document.querySelector("audio")?.readyState >= 1'), 'authenticated audio')
  const positions = await evaluate(`['transcript-panel','audio-panel'].map(name=> {const r=document.querySelector('[data-testid='+name+']').getBoundingClientRect(); return {x:r.x,y:r.y,width:r.width}})`)
  assert.ok(positions[0].x < positions[1].x)
  assert.equal(positions[0].y,positions[1].y)
  await click('Écouter à 0:04')
  await until(() => evaluate('document.querySelector("audio").currentTime > 4.1 && !document.querySelector("audio").paused'), 'timestamp seeks and plays')
  const auth = await evaluate('window.__apiCalls.find(c=>c.path.endsWith("/audio")).headers')
  assert.equal(auth.Authorization,'Bearer test.history.test')
  assert.equal(auth['X-Organization-Id'],'1')
  await evaluate('document.querySelector("audio").pause()')
  await screenshot('meeting-desktop.png')
  await click('Résumé')
  await until(() => visibleText('Les marges seront vérifiées vendredi.'), 'summary tab')
  await click('Compte rendu')
  await until(() => visibleText('1. Résumé long'), 'report tab')
  await click('Transcription')
  await evaluate(`(() => {const input=document.querySelector('input[aria-label="Rechercher dans la transcription"]'); input.value='planning'; input.dispatchEvent(new Event('input',{bubbles:true}))})()`)
  await until(() => evaluate('document.querySelectorAll("[data-segment]").length === 1'), 'transcript search')
  await command('Emulation.setDeviceMetricsOverride', {width:390,height:844,deviceScaleFactor:1,mobile:true})
  await pause(150)
  assert.equal(await evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),true,'mobile has no horizontal overflow')
  const mobile = await evaluate(`['transcript-panel','audio-panel'].map(name=>document.querySelector('[data-testid='+name+']').getBoundingClientRect().top)`)
  assert.ok(mobile[1] > mobile[0])
  await screenshot('meeting-mobile.png')
  await command('Emulation.setDeviceMetricsOverride', {width:1600,height:1000,deviceScaleFactor:1,mobile:false})
  await evaluate(`document.querySelector('a[href="/historique"]').click()`)
  await until(() => evaluate(`!!document.querySelector('input[aria-label="Rechercher une réunion"]')`), 'gallery search returns')
  await evaluate(`(() => { const input=document.querySelector('input[aria-label="Rechercher une réunion"]'); input.value=''; input.dispatchEvent(new Event('input',{bubbles:true})) })()`)
  await until(() => evaluate('document.querySelectorAll("[data-testid=meeting-card]").length === 4'), 'return to gallery')
  await evaluate(`document.querySelector('a[href="/historique?meeting=102"]').click()`)
  await until(() => visibleText('n’a pas été conservé'), 'legacy audio state')
  assert.equal(await evaluate('document.querySelector("audio")'),null)
  await evaluate(`document.querySelector('a[href="/historique"]').click()`)
  await until(() => evaluate('!!document.querySelector("[data-testid=meeting-card]")'), 'gallery before retry')
  await evaluate(`document.querySelector('a[href="/historique?meeting=103"]').click()`)
  await until(() => visibleText('Recréer le Word'), 'word retry')
  await click('Résumé')
  await until(() => visibleText('Le planning est prêt et sauvegardé.'), 'partial result remains readable')
  await click('Recréer le Word')
  await until(() => visibleText('Création du Word'), 'background Word state')
  await until(() => visibleText('Télécharger le Word'), 'polled completion')
  assert.equal(await evaluate('window.__apiCalls.filter(c=>c.path.endsWith("/summary")).length'),1)
  await command('Page.reload')
  await until(() => visibleText('Télécharger le Word'), 'reload retains completed result')
  await evaluate(`document.querySelector('a[href="/historique"]').click()`)
  await until(() => evaluate('!!document.querySelector("[data-testid=meeting-card]")'), 'gallery before queued task')
  await evaluate(`document.querySelector('a[href="/historique?meeting=104"]').click()`)
  await until(() => visibleText('Le traitement continue'), 'queued task visible')
  await evaluate("window.__meetings.find(m=>m.id===104).processing_status='writing'; window.__save()")
  await until(() => visibleText('Rédaction'), 'polling updates stage')
  await command('Page.reload')
  await until(() => visibleText('Rédaction'), 'reload resumes polling')
  assert.equal(errors.length,0,JSON.stringify(errors))
  console.log('PASS: gallery/search, protected audio, timestamp seeking, text tabs/search, mobile layout, legacy audio, Word-only retry, polling and reload.')
})
