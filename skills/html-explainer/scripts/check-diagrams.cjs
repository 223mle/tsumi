#!/usr/bin/env node
const fs=require('node:fs');const path=require('node:path');const {pathToFileURL}=require('node:url');const {chromium}=require('playwright');
async function inspect(page){return page.evaluate(()=>{
  const errors=[];
  function shown(el){for(let p=el;p&&p instanceof Element;p=p.parentElement){const s=getComputedStyle(p);if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)<.05)return false;}return true;}
  document.querySelectorAll('.dg-live svg').forEach(svg=>{
    const bounds=svg.getBoundingClientRect();if(!bounds.width)return;
    const keys=[...svg.querySelectorAll('[data-key]')].map(e=>e.dataset.key);
    if(new Set(keys).size!==keys.length)errors.push('duplicate animation key');
    svg.querySelectorAll('[data-label]').forEach(el=>{if(!shown(el))return;const r=el.getBoundingClientRect();if(r.width&&r.height&&(r.left<bounds.left-2||r.right>bounds.right+2||r.top<bounds.top-2||r.bottom>bounds.bottom+2))errors.push(`clipped label: ${el.textContent.trim()}`);});
    const labels=[...svg.querySelectorAll('.dg-edge-label,text[data-label]')].filter(el=>!el.closest('.dg-edge-label')||el.matches('.dg-edge-label')).filter(shown).filter(el=>el.textContent.trim()).map(el=>({text:el.textContent.trim(),r:el.getBoundingClientRect()}));
    for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){const a=labels[i],b=labels[j];const w=Math.min(a.r.right,b.r.right)-Math.max(a.r.left,b.r.left),h=Math.min(a.r.bottom,b.r.bottom)-Math.max(a.r.top,b.r.top);if(w>3&&h>3)errors.push(`overlapping labels: ${a.text} / ${b.text}`);}
  });
  if(document.documentElement.scrollWidth>innerWidth+1)errors.push('page overflow');
  return errors;
});}
async function snapshot(figure){return figure.evaluate(f=>[...f.querySelectorAll('.dg-live [data-key]')].map(e=>[e.dataset.key,['x','y','width','d','transform','opacity'].map(k=>e.getAttribute(k)).join('|'),e.textContent]).sort((a,b)=>a[0].localeCompare(b[0])));}
async function main(){const [input,out]=process.argv.slice(2);if(!input||!out)throw Error('Usage: check-diagrams.cjs document.html evidence-dir');fs.mkdirSync(out,{recursive:true});const report={input:path.resolve(input),checks:[],errors:[]};const b=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
  function check(name,passed,detail){report.checks.push({name,passed,detail});if(!passed)report.errors.push(name+(detail?': '+detail:''));}
  try{
    for(const theme of ['light','dark']){
      const c=await b.newContext({viewport:{width:1440,height:1000},colorScheme:theme,reducedMotion:'no-preference'});await c.route(/^https?:/,r=>r.abort());const p=await c.newPage();p.on('pageerror',e=>report.errors.push(e.message));await p.goto(pathToFileURL(path.resolve(input)).href);
      const diagrams=p.locator('[data-diagram]');check(`${theme}: diagrams found`,await diagrams.count()>0);
      for(let i=0;i<await diagrams.count();i++){
        const f=diagrams.nth(i),id=await f.getAttribute('id');await f.scrollIntoViewIfNeeded();
        check(`${theme}/${id}: initial geometry`,(await inspect(p)).length===0,(await inspect(p)).join('; '));
        await f.screenshot({path:path.join(out,`${theme}-${id}-initial.png`)});
        const radios=f.locator('.dg-switch input');
        if(await radios.count()>1){
          const before=await snapshot(f);await radios.first().focus();await p.keyboard.press('ArrowRight');await p.waitForTimeout(280);const middle=await snapshot(f);
          await p.waitForFunction(id=>document.getElementById(id).dataset.animating==='false',id);const after=await snapshot(f);
          check(`${theme}/${id}: interpolated transition`,JSON.stringify(before)!==JSON.stringify(middle)&&JSON.stringify(middle)!==JSON.stringify(after));
          check(`${theme}/${id}: synchronized state`,await f.getAttribute('data-rendered-state')==='1');
          // Compare all visible target labels with the selected static source, including reused edge IDs.
          const labels=await f.evaluate(fig=>[...fig.querySelectorAll('.dg-panel')].every(panel=>{
            const scenes=panel.querySelectorAll('.dg-static-scene');const target=scenes[Math.min(1,scenes.length-1)];const live=panel.querySelector('.dg-live');
            const sameText=[...target.querySelectorAll('text')].every(el=>!el.textContent.trim()||live.textContent.includes(el.textContent));
            const targetKeys=new Map([...target.querySelectorAll('[data-key]')].map(el=>[el.dataset.key,el.tagName]));
            const kinds=[...live.querySelectorAll('[data-key]')].every(el=>!targetKeys.has(el.dataset.key)||targetKeys.get(el.dataset.key)===el.tagName);
            return sameText&&kinds;
          }));check(`${theme}/${id}: updated label text`,labels);
          const errors=await inspect(p);check(`${theme}/${id}: after geometry`,!errors.length,errors.join('; '));
          await f.screenshot({path:path.join(out,`${theme}-${id}-after.png`)});
          // Keep one picture per variant so every state can be read, not only the second one.
          for(let v=0;v<await radios.count();v++){await radios.nth(v).check();await p.waitForFunction(id=>document.getElementById(id).dataset.animating==='false',id);await f.screenshot({path:path.join(out,`${theme}-${id}-variant-${v+1}.png`)});}
          await radios.first().check();await radios.nth(1).check();await radios.first().check();await p.waitForFunction(id=>document.getElementById(id).dataset.animating==='false',id);check(`${theme}/${id}: rapid reversal`,await f.getAttribute('data-rendered-state')==='0');
        }
        const stepButtons=f.locator('[data-step]');
        if(await stepButtons.count()>1){
          const n=await stepButtons.count();const text0=await f.locator('.dg-step-text').textContent();
          const before=await snapshot(f);await f.locator('[data-go="1"]').click();await p.waitForTimeout(280);const middle=await snapshot(f);
          await p.waitForFunction(id=>document.getElementById(id).dataset.animating==='false',id);const after=await snapshot(f);
          check(`${theme}/${id}: step interpolates`,JSON.stringify(before)!==JSON.stringify(middle)&&JSON.stringify(middle)!==JSON.stringify(after));
          check(`${theme}/${id}: step text follows`,(await f.getAttribute('data-rendered-state'))==='1'&&(await f.locator('.dg-step-text').textContent())!==text0&&(await stepButtons.nth(1).getAttribute('aria-current'))==='step');
          await f.locator('[data-go="1"]').focus();await p.keyboard.press('ArrowLeft');await p.waitForFunction(id=>document.getElementById(id).dataset.animating==='false',id);
          check(`${theme}/${id}: arrow keys step`,(await f.getAttribute('data-rendered-state'))==='0');
          await stepButtons.nth(n-1).click();await p.waitForFunction(id=>document.getElementById(id).dataset.animating==='false',id);
          check(`${theme}/${id}: last step disables next`,await f.locator('[data-go="1"]').isDisabled());
          const errors=await inspect(p);check(`${theme}/${id}: step geometry`,!errors.length,errors.join('; '));
          for(let v=0;v<n;v++){await stepButtons.nth(v).click();await p.waitForFunction(id=>document.getElementById(id).dataset.animating==='false',id);await f.screenshot({path:path.join(out,`${theme}-${id}-step-${v+1}.png`)});}
          await stepButtons.first().click();await p.waitForFunction(id=>document.getElementById(id).dataset.animating==='false',id);
        }
        const range=f.locator('.dg-slider input');if(await range.count()){
          const max=Number(await range.getAttribute('max'));
          for(let v=0;v<=max;v++){await range.evaluate((r,v)=>{r.value=v;r.dispatchEvent(new Event('input'));},v);await p.waitForFunction(id=>document.getElementById(id).dataset.animating==='false',id);await f.screenshot({path:path.join(out,`${theme}-${id}-value-${v}.png`)});}
          const errors=await inspect(p);
          check(`${theme}/${id}: slider reaches every value`,(await f.getAttribute('data-rendered-state'))===String(max)&&(await f.locator('.dg-slider output').textContent())===(JSON.parse(await range.getAttribute('data-labels'))[max]),errors.join('; '));
          check(`${theme}/${id}: slider geometry`,!errors.length,errors.join('; '));
          await range.focus();await p.keyboard.press('Home');await p.waitForFunction(id=>document.getElementById(id).dataset.animating==='false',id);
          check(`${theme}/${id}: slider keyboard`,(await f.getAttribute('data-rendered-state'))==='0');
        }
        const grid=f.locator('.dg-grid-toggle');if(await grid.count()){
          await grid.click();const all=await f.locator('.dg-static-scene').evaluateAll(es=>es.filter(e=>getComputedStyle(e.closest('.dg-panel')).display!=='none').every(e=>e.getBoundingClientRect().height>0));
          const errors=await inspect(p);check(`${theme}/${id}: small multiples show every variant`,all&&!errors.length,errors.join('; '));
          await f.screenshot({path:path.join(out,`${theme}-${id}-all.png`)});await grid.click();
          check(`${theme}/${id}: back to one variant`,await f.locator('.dg-live').evaluateAll(es=>es.some(e=>e.getBoundingClientRect().height>0)));
        }
        const play=f.locator('.dg-play');if(await play.count()){
          await play.click();await p.waitForTimeout(120);const x=await f.locator('.dg-flow-particle').evaluateAll(es=>es.map(e=>e.getAttribute('transform')));await p.waitForTimeout(240);const y=await f.locator('.dg-flow-particle').evaluateAll(es=>es.map(e=>e.getAttribute('transform')));check(`${theme}/${id}: moving flow`,x.length>0&&JSON.stringify(x)!==JSON.stringify(y));await play.click();check(`${theme}/${id}: stop flow`,await f.locator('.dg-flow-particle').count()===0);
        }
      }
      await p.emulateMedia({media:'print'});check(`${theme}: print scenes`,await p.locator('[data-diagram]').evaluateAll(fs=>fs.every(f=>{const scenes=[...f.querySelectorAll('.dg-panel:not(.dg-narrow) .dg-static-scene')];const shown=s=>s.getBoundingClientRect().height>0;
        // A step-through figure prints its final, complete scene plus every step as text.
        if(f.dataset.mode==='steps')return shown(scenes.at(-1))&&f.querySelector('.dg-step-notes').getBoundingClientRect().height>0;return scenes.every(shown);})));await c.close();
    }
    const c=await b.newContext({viewport:{width:390,height:1000},reducedMotion:'reduce'});const p=await c.newPage();await p.goto(pathToFileURL(path.resolve(input)).href);
    for(const f of await p.locator('[data-diagram]').all()){
      const radios=f.locator('.dg-switch input');if(await radios.count()>1){await radios.nth(1).check();check('reduced motion: immediate state',await f.getAttribute('data-animating')==='false');}
      const next=f.locator('[data-go="1"]');if(await next.count()){await next.click();check('reduced motion: immediate step',await f.getAttribute('data-animating')==='false');}
    }
    check('mobile: geometry',!(await inspect(p)).length,(await inspect(p)).join('; '));await p.screenshot({path:path.join(out,'mobile.png'),fullPage:true});await c.close();
    const nc=await b.newContext({javaScriptEnabled:false,viewport:{width:390,height:1000}});const np=await nc.newPage();await np.goto(pathToFileURL(path.resolve(input)).href);check('no JS: every scene or step visible',await np.locator('[data-diagram]').evaluateAll(fs=>fs.length>0&&fs.every(f=>{const scenes=[...f.querySelectorAll('.dg-static-scene')].filter(s=>getComputedStyle(s.closest('.dg-panel')).display!=='none');const shown=s=>s.getBoundingClientRect().height>0;
      if(f.dataset.mode==='steps')return shown(scenes.at(-1))&&f.querySelectorAll('.dg-step-notes li').length===scenes.length;return scenes.every(shown);})));await nc.close();
  }finally{await b.close();report.passed=report.errors.length===0;fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');}
  console.log(JSON.stringify({passed:report.passed,checks:report.checks.length,errors:report.errors,evidence:out}));process.exitCode=report.passed?0:1;
}
main().catch(e=>{console.error(e);process.exitCode=2;});
