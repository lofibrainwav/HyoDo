// Dependency-free CDP acceptance checks. Node 22+ (native WebSocket).
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const base = process.argv[2] || 'http://localhost:4321';
const OUT = resolve(process.argv[3] || fileURLToPath(new URL('../verify-output/', import.meta.url)));
mkdirSync(OUT, { recursive: true });
const reports = {}, failures = [], consoleMsgs = [];
const sleep = ms => new Promise(r => setTimeout(r, ms));
let chrome, ws, profile;
try {
 const candidates = process.env.CHROME_BIN ? [process.env.CHROME_BIN] : ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'google-chrome', 'chromium', 'chromium-browser'];
 const binary = candidates.find(c => c.includes('/') ? existsSync(c) : spawnSync('which', [c], {stdio:'ignore'}).status === 0);
 if (!binary) throw new Error('Chrome not found: set CHROME_BIN or install google-chrome/chromium.');
 profile = mkdtempSync(join(tmpdir(), 'eg-verify-'));
 let launchError, exited = false, exitCode = null, exitSignal = null;
 // CI runners are slower to hand out a DevTools port and often disallow the
 // Chrome sandbox and /dev/shm size Chrome assumes locally.
 const chromeArgs = ['--headless=new', '--disable-gpu', '--enable-unsafe-swiftshader', '--disable-dev-shm-usage', '--hide-scrollbars', '--remote-debugging-port=0', `--user-data-dir=${profile}`];
 if (process.env.CI) chromeArgs.push('--no-sandbox');
 chromeArgs.push('about:blank');
 chrome = spawn(binary, chromeArgs, {stdio:'ignore'});
 chrome.on('error', error => { launchError = error; });
 chrome.on('exit', (code, signal) => { exited = true; exitCode = code; exitSignal = signal; });
 let port;
 const PORT_WAIT_MS = 30000, POLL_MS = 250;
 for (let waited = 0; waited < PORT_WAIT_MS; waited += POLL_MS) {
  if (launchError || exited) break;
  try { port = readFileSync(join(profile,'DevToolsActivePort'),'utf8').split('\n')[0]; break; } catch { await sleep(POLL_MS); }
 }
 if(!port) throw new Error(`Chrome did not start (sandbox may prohibit launch): ${launchError?.message || (exited ? `exited early (code ${exitCode}, signal ${exitSignal ?? 'none'})` : `DevTools port unavailable after ${PORT_WAIT_MS / 1000}s`)}`);
 const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, {method:'PUT',signal:AbortSignal.timeout(5000)})).json();
 ws = new WebSocket(target.webSocketDebuggerUrl);
 await new Promise((resolve,reject) => { const timer=setTimeout(()=>reject(new Error('CDP connection timed out')),5000); ws.onopen=()=>{clearTimeout(timer);resolve();}; ws.onerror=error=>{clearTimeout(timer);reject(error);}; });
 let id=0; const pending=new Map();
 ws.onmessage = ev => {
  const m=JSON.parse(ev.data);
  if(m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  else if(m.method==='Runtime.consoleAPICalled' && ['error','warning'].includes(m.params.type)) consoleMsgs.push(m.params.type+': '+m.params.args.map(a=>a.value || a.description).join(' '));
  else if(m.method==='Runtime.exceptionThrown') consoleMsgs.push('exception: '+JSON.stringify(m.params.exceptionDetails));
  else if(m.method==='Log.entryAdded' && m.params.entry.level==='error') consoleMsgs.push('log-error: '+m.params.entry.text);
 };
 const call=(method,params={})=>new Promise((resolve,reject)=>{
  const i=++id; const timer=setTimeout(()=>{pending.delete(i);reject(new Error(`${method} timed out${method==='Runtime.evaluate'?': '+String(params.expression||'').replace(/\s+/g,' ').slice(0,120):''}`));},30000);
  pending.set(i,m=>{clearTimeout(timer);m.error?reject(new Error(JSON.stringify(m.error))):resolve(m);});
  ws.send(JSON.stringify({id:i,method,params}));
 });
 const evalJs=async expression=>{const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.result.exceptionDetails)throw new Error(JSON.stringify(r.result.exceptionDetails));return r.result.result.value;};
 await call('Runtime.enable'); await call('Log.enable'); await call('Page.enable');
 // Headless windows are unfocused, so element.focus() would not fire focus handlers without this.
 await call('Emulation.setFocusEmulationEnabled', { enabled: true });
 for (const route of ['/evidence-graph/', '/']) {
 const URL_ = new URL(route,base).href;
 const prefix = route==='/' ? 'embedded-' : 'full-';
 const check=(ok,name)=>{if(!ok) failures.push(`${route}: ${name}`);};
const geometry = () => evalJs(`(async()=>{
 document.activeElement?.blur();
 await new Promise(r=>setTimeout(r,150));
 const svg=document.querySelector('#eg-edges'), matrix=svg.getScreenCTM();
 const cells=[...document.querySelectorAll('#eg-root button')];
 const violations=[]; let endpointDeviation=0;
 for(const path of svg.querySelectorAll('path[data-target]')){
  const endpoints=[path.dataset.source,path.dataset.target];
  const len=path.getTotalLength();
  for(let d=0;d<=len;d+=4){
   const p=path.getPointAtLength(d).matrixTransform(matrix);
   for(const c of cells){if(endpoints.includes(c.dataset.eventId))continue;const r=c.getBoundingClientRect();if(p.x>r.left+2&&p.x<r.right-2&&p.y>r.top+2&&p.y<r.bottom-2)violations.push(endpoints.join('->')+' crosses '+c.dataset.eventId);}
  }
  if(path.classList.contains('edge-broken'))continue;
  for(const [id,d] of [[endpoints[0],0],[endpoints[1],len]]){
   const c=cells.find(c=>c.dataset.eventId===id);if(!c){endpointDeviation=Infinity;continue;}
   const r=c.getBoundingClientRect(),p=path.getPointAtLength(d).matrixTransform(matrix);
   const dx=Math.max(r.left-p.x,0,p.x-r.right),dy=Math.max(r.top-p.y,0,p.y-r.bottom);
   const distance=dx||dy?Math.hypot(dx,dy):Math.min(p.x-r.left,r.right-p.x,p.y-r.top,r.bottom-p.y);
   endpointDeviation=Math.max(endpointDeviation,distance);
  }
 }
 return {violations,endpointDeviation,edgeCount:svg.querySelectorAll('path[data-target]').length};
})()`);
const shot = async (file) => { const r = await call('Page.captureScreenshot', { format: 'png' }); writeFileSync(`${OUT}/${file}`, Buffer.from(r.result.data, 'base64')); };
const load = async () => { await call('Page.navigate', { url: URL_ }); await sleep(300); await evalJs(`document.querySelector('.eg-main')?.scrollIntoView({block:'center'})`); for(let n=0;n<60;n++){ if(await evalJs(`document.querySelectorAll('#eg-root button').length === 14`)) return; await sleep(100); } throw new Error('graph mount timed out'); };


const report = {}; reports[route] = report;
await call('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });
// Desktop
await call('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
await load();
report.desktop = await evalJs(`(async () => {
  const out = {};
  const panel = document.getElementById('eg-panel');
  const cells = [...document.querySelectorAll('#eg-root button')];
  out.cellCount = cells.length;
  out.placeholder = panel.textContent.replace(/\\s+/g, ' ').trim().slice(0, 80);
  out.animAtRest = document.querySelectorAll('animateMotion, animate').length;
  const ask = cells.find(c => c.dataset.eventId === 'evt-e2');
  out.askFound = !!ask;
  ask.focus();
  await new Promise(r => setTimeout(r, 200));
  out.focusedId = document.activeElement && document.activeElement.dataset.eventId;
  out.panelAfterFocus = panel.textContent.replace(/\\s+/g, ' ').trim().slice(0, 320);
  out.panelChanged = out.panelAfterFocus !== out.placeholder;
  out.animWhileActive = document.querySelectorAll('animateMotion, animate').length;
  out.isButton = ask instanceof HTMLButtonElement;
  document.getElementById('eg-root').dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
  await new Promise(r => setTimeout(r, 200));
  out.panelAfterEscape = panel.textContent.replace(/\\s+/g, ' ').trim().slice(0, 80);
  out.focusKeptAfterEscape = document.activeElement === ask;
  out.animAfterEscape = document.querySelectorAll('animateMotion, animate').length;
  out.ariaLive = panel.getAttribute('aria-live');
  out.describedBy = document.getElementById('eg-root').getAttribute('aria-describedby');
  out.hasBanner = !!document.querySelector('.eg-banner');
  out.pageOverflow = document.documentElement.scrollWidth > document.documentElement.clientWidth;
  return out; })()`);
// Focus a cell for the screenshot (ASK decision with evidence edge lit)
await evalJs(`(() => { const b = [...document.querySelectorAll('#eg-root button')].find(c => c.dataset.eventId === 'evt-e2'); b.focus(); return true; })()`);
await sleep(300);
await shot(prefix + 'verify-desktop-focused.png');
// Real key events: Tab from the first cell, then Escape
await evalJs(`(() => { document.querySelector('#eg-root button').focus(); return true; })()`);
await call('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
await call('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
await sleep(200);
report.realTab = await evalJs(`JSON.stringify({active: document.activeElement.dataset.eventId, panel: document.getElementById('eg-panel').textContent.replace(/\\s+/g,' ').trim().slice(0,100)})`);
await call('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
await call('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
await sleep(200);
report.realEscape = await evalJs(`JSON.stringify({active: document.activeElement.dataset.eventId, panel: document.getElementById('eg-panel').textContent.replace(/\\s+/g,' ').trim().slice(0,80)})`);
report.desktopGeometry = await geometry();
check(report.desktopGeometry.edgeCount === 15 && report.desktopGeometry.violations.length === 0 && report.desktopGeometry.endpointDeviation !== null && report.desktopGeometry.endpointDeviation < 0.05, 'desktop independent geometry and endpoints');
report.motionByCell = await evalJs(`(async()=>{
 const results=[];
 for(const cell of document.querySelectorAll('#eg-root button')){
  cell.focus();await new Promise(r=>setTimeout(r,30));
  results.push({id:cell.dataset.eventId,count:document.querySelectorAll('#eg-edges animateMotion').length});
 }
 return results;
})()`);
check(report.motionByCell.every(c=>['evt-e2','evt-r2'].includes(c.id)?c.count>0:c.count===0),'only decisions with evidence refs animate');
// Reduced motion
await call('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
await load();
report.reducedMotion = await evalJs(`(async () => { const b = [...document.querySelectorAll('#eg-root button')].find(c => c.dataset.eventId === 'evt-e2'); b.focus(); await new Promise(r => setTimeout(r, 200)); return { media: matchMedia('(prefers-reduced-motion: reduce)').matches, animWhileActive: document.querySelectorAll('animateMotion, animate').length, cssAnimations: [...document.querySelectorAll('.eg-page *')].filter(e => getComputedStyle(e).animationName !== 'none').length }; })()`);
await call('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });
// Mobile 375
await call('Emulation.setDeviceMetricsOverride', { width: 375, height: 900, deviceScaleFactor: 2, mobile: true });
await load();
report.mobile = await evalJs(`(() => { const d = document.documentElement; const g = document.getElementById('eg-root'); return { innerWidth: innerWidth, docScrollWidth: d.scrollWidth, clientWidth: d.clientWidth, pageOverflow: d.scrollWidth > d.clientWidth, gridWrapScrolls: g.scrollWidth > g.clientWidth }; })()`);
await shot(prefix + 'verify-mobile-375.png');

report.mobileScroll = await evalJs(`(async()=>{scrollTo(1000,0);await new Promise(r=>requestAnimationFrame(r));return {x:scrollX,width:document.body.getBoundingClientRect().width};})()`);
check(report.desktop.cellCount===14,'expected 14 cells');
check(report.desktop.animAtRest===0 && report.desktop.animWhileActive>0 && report.desktop.animAfterEscape===0,'motion must be active only for selected evidence decision');
check(report.desktop.panelChanged && report.desktop.focusKeptAfterEscape && report.desktop.panelAfterEscape===report.desktop.placeholder,'focus and Escape panel contract');
const tab=JSON.parse(report.realTab), escape=JSON.parse(report.realEscape);
check(!!tab.active && tab.panel.includes(tab.active),'real Tab reaches cell and fills panel');
check(escape.active===tab.active && escape.panel===report.desktop.placeholder,'real Escape clears panel and keeps focus');
check(report.reducedMotion.media && report.reducedMotion.animWhileActive===0 && report.reducedMotion.cssAnimations===0,'reduced motion');
check(report.mobileScroll.x===0 && report.mobileScroll.width<=375,'375px body width and horizontal scroll');
check(report.mobile.gridWrapScrolls,'mobile grid has internal scrolling');
report.geometry = await geometry();
check(report.geometry.edgeCount===15 && report.geometry.violations.length===0,'independent edge collision sampler');
check(report.geometry.endpointDeviation!==null && report.geometry.endpointDeviation<0.05,'endpoint deviation (rounding tolerance 0.05px)');
}
if(consoleMsgs.some(m=>/error:|log-error:|exception:|edge crosses cell|fallback crosses cell/.test(m))) failures.push('console errors, exceptions, or collision warnings');
} catch(error) { failures.push(error.message); }
finally {
 ws?.close();
 if(chrome && chrome.exitCode===null) { chrome.kill(); await Promise.race([new Promise(r=>chrome.once('exit',r)),sleep(2000)]); if(chrome.exitCode===null && chrome.signalCode===null) { chrome.kill('SIGKILL'); await Promise.race([new Promise(r=>chrome.once('exit',r)),sleep(1000)]); } }
 // Chrome may still be flushing its profile on Linux; retry, and never let cleanup mask the verdict.
 if(profile) { try { rmSync(profile,{recursive:true,force:true,maxRetries:10,retryDelay:200}); } catch(error) { console.warn('profile cleanup skipped: '+error.message); } }
}
console.log(JSON.stringify({pages:reports,console:consoleMsgs,failures},null,2));
if(failures.length) { console.error('Evidence graph verification FAILED:\n'+failures.map(f=>' - '+f).join('\n')); process.exitCode=1; }
else console.log('Evidence graph verification passed: both pages, keyboard, motion, geometry, mobile and console.');
