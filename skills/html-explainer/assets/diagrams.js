(() => {
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const SVG='http://www.w3.org/2000/svg';
  const numberPattern=/-?(?:\d*\.\d+|\d+\.?\d*)(?:e[+-]?\d+)?/gi;
  const animated=new Set(['x','y','x1','y1','x2','y2','width','height','cx','cy','r','opacity','transform','d']);
  function interpolator(a,b){
    if(a===null || b===null) return t=>t<.5?a:b;
    const aa=a.match(numberPattern),bb=b.match(numberPattern);
    if(!aa||!bb||aa.length!==bb.length||a.replace(numberPattern,'#')!==b.replace(numberPattern,'#'))return t=>t<.5?a:b;
    const av=aa.map(Number),bv=bb.map(Number);return t=>{let i=0;return b.replace(numberPattern,()=>String(av[i]+(bv[i]-av[i++])*t));};
  }
  function liveClone(svg){
    const clone=svg.cloneNode(true);const replacements=new Map();
    clone.querySelectorAll('[id]').forEach(el=>{replacements.set(el.id,el.id+'-live');el.id+='-live';});
    [clone,...clone.querySelectorAll('*')].forEach(el=>{
      for(const attr of [...el.attributes]){
        let value=attr.value;
        if(attr.name==='aria-labelledby')value=value.split(' ').map(id=>replacements.get(id)||id).join(' ');
        else value=value.replace(/url\(#([^)]+)\)/g,(_,id)=>`url(#${replacements.get(id)||id})`);
        if(value!==attr.value)el.setAttribute(attr.name,value);
      }
    });return clone;
  }
  document.querySelectorAll('[data-diagram]').forEach(figure=>{
    const panels=[...figure.querySelectorAll('.dg-panel')].map(panel=>{
      const scenes=[...panel.querySelectorAll('.dg-static-scene svg')].map(liveClone);
      const svg=scenes[0].cloneNode(true);
      const defs=svg.querySelector('defs')||svg.insertBefore(document.createElementNS(SVG,'defs'),svg.firstChild);
      scenes.slice(1).forEach(scene=>scene.querySelectorAll('defs>*').forEach(el=>defs.append(el.cloneNode(true))));
      panel.querySelector('.dg-live').append(svg);
      return {svg,scenes};
    });
    figure.classList.add('dg-enhanced');
    let transition=0,flowFrame=0,visible=false,playing=false,flowOrigin=0,particles=[];
    const play=figure.querySelector('.dg-play');
    const stepButtons=[...figure.querySelectorAll('[data-step]')];
    const stepText=figure.querySelector('.dg-step-text'),stepCount=figure.querySelector('.dg-step-count'),autoButton=figure.querySelector('[data-autoplay]');
    function removeParticles(){particles.forEach(p=>p.node.remove());particles=[];}
    function particleFrame(now){
      if(!playing||!visible||reduced.matches||document.hidden){flowFrame=0;return;}
      particles.forEach(p=>{
        const opacity=Number(p.path.getAttribute('opacity')??1);
        if(opacity<.1){p.node.style.display='none';return;}
        p.node.style.display='';
        const len=p.path.getTotalLength();
        const progress=((now-flowOrigin)/2200+p.phase)%1;
        const point=p.path.getPointAtLength(progress*len);
        p.node.setAttribute('transform',`translate(${point.x},${point.y})`);
      });flowFrame=requestAnimationFrame(particleFrame);
    }
    function startFlow(){
      cancelAnimationFrame(flowFrame);removeParticles();
      if(!playing||!visible||reduced.matches)return;
      panels.forEach(({svg})=>svg.querySelectorAll('path[data-flow]').forEach((path,i)=>{
        const request=path.dataset.flow==='request';
        const node=document.createElementNS(SVG,request?'circle':'rect');
        node.setAttribute('class','dg-flow-particle'+(request?' dg-flow-request':''));node.setAttribute('aria-hidden','true');
        if(request)node.setAttribute('r','3');else{node.setAttribute('x','-4');node.setAttribute('y','-3');node.setAttribute('width','8');node.setAttribute('height','6');node.setAttribute('rx','1');}
        svg.append(node);particles.push({path,node,phase:(i*.19)%1});
      }));flowOrigin=performance.now();flowFrame=requestAnimationFrame(particleFrame);
    }
    function select(index,instant=false){
      cancelAnimationFrame(transition);cancelAnimationFrame(flowFrame);removeParticles();
      const updates=[];
      panels.forEach(({svg,scenes})=>{
        const target=scenes[Math.min(index,scenes.length-1)];
        ['title','desc'].forEach(tag=>{const a=svg.querySelector(tag),b=target.querySelector(tag);if(a&&b)a.textContent=b.textContent;});
        const live=new Map([...svg.querySelectorAll('[data-key]')].map(el=>[el.dataset.key,el]));
        const wanted=new Map([...target.querySelectorAll('[data-key]')].map(el=>[el.dataset.key,el]));
        wanted.forEach((dest,key)=>{
          let el=live.get(key);
          if(!el){
            // Insert the highest missing keyed ancestor once, retaining its child geometry.
            let ancestor=dest.parentElement;while(ancestor&&ancestor!==target){if(ancestor.hasAttribute('data-key')&&!live.has(ancestor.dataset.key))return;ancestor=ancestor.parentElement;}
            el=dest.cloneNode(true);el.setAttribute('opacity','0');svg.append(el);
            live.set(key,el);el.querySelectorAll('[data-key]').forEach(child=>live.set(child.dataset.key,child));
          }
          const attrs=[];
          for(const attr of dest.attributes){
            if(animated.has(attr.name))attrs.push([attr.name,interpolator(el.getAttribute(attr.name),attr.value)]);
            else if(attr.name!=='id'&&attr.name!=='data-key')el.setAttribute(attr.name,attr.value);
          }
          if(!dest.hasAttribute('opacity'))attrs.push(['opacity',interpolator(el.getAttribute('opacity')||'1','1')]);
          updates.push({el,attrs,dest,text:dest.tagName.toLowerCase()==='text'||(dest.classList.contains('dg-edge-label')&&!dest.querySelector('[data-key]'))});
        });
        live.forEach((el,key)=>{if(!wanted.has(key))updates.push({el,attrs:[['opacity',interpolator(el.getAttribute('opacity')||'1','0')]],dest:null,text:false});});
      });
      figure.dataset.state=String(index);figure.dataset.animating='true';syncSteps(index);
      const duration=instant||reduced.matches?0:760;const start=performance.now();
      function frame(now){
        const linear=duration?Math.min(1,(now-start)/duration):1;const t=linear<.5?4*linear**3:1-(-2*linear+2)**3/2;
        updates.forEach(({el,attrs,dest,text})=>{
          attrs.forEach(([key,interpolate])=>{const value=interpolate(t);if(value!==null)el.setAttribute(key,value);});
          if(text&&linear>=.5&&dest)el.replaceChildren(...[...dest.childNodes].map(n=>n.cloneNode(true)));
          if(linear===1)el.setAttribute('aria-hidden',String(dest===null));
        });
        if(linear<1)transition=requestAnimationFrame(frame);else{figure.dataset.animating='false';figure.dataset.renderedState=String(index);startFlow();}
      }frame(start);
    }
    function syncSteps(index){
      const tpl=figure.querySelector(`template[data-step-text="${index}"]`);
      if(stepText&&tpl)stepText.replaceChildren(tpl.content.cloneNode(true));
      if(!stepButtons.length)return;
      stepButtons.forEach((b,i)=>{b.setAttribute('aria-current',i===index?'step':'false');b.classList.toggle('is-done',i<index);});
      if(stepCount)stepCount.textContent=`${index+1} / ${stepButtons.length}`;
      // On narrow screens the drawing scrolls sideways; bring the current step into view.
      panels.forEach(({svg})=>{
        const box=svg.parentElement,cur=svg.querySelector('.is-current .dg-msg-line, .dg-msg.is-current');
        if(!cur||box.scrollWidth<=box.clientWidth+2)return;
        const r=cur.getBoundingClientRect(),b=box.getBoundingClientRect();
        const target=r.width>b.width-40?box.scrollLeft+r.left-b.left-40:box.scrollLeft+(r.left+r.right)/2-(b.left+b.right)/2;
        box.scrollTo({left:Math.max(0,target),behavior:reduced.matches?'auto':'smooth'});
      });
      figure.querySelectorAll('[data-go]').forEach(b=>{const next=index+Number(b.dataset.go);b.disabled=next<0||next>=stepButtons.length;});
    }
    function go(delta){const n=stepButtons.length;const next=Math.max(0,Math.min(n-1,Number(figure.dataset.state||0)+delta));if(next!==Number(figure.dataset.state||0))select(next);return next;}
    let autoTimer=0;
    function stopAuto(){clearTimeout(autoTimer);autoTimer=0;if(autoButton){autoButton.setAttribute('aria-pressed','false');autoButton.textContent='自動で進める';}}
    function tick(){if(!autoTimer)return;if(!visible){stopAuto();return;}const n=stepButtons.length;const cur=Number(figure.dataset.state||0);if(cur>=n-1){stopAuto();return;}go(1);autoTimer=setTimeout(tick,reduced.matches?2600:3200);}
    figure.querySelectorAll('[data-step]').forEach(b=>b.addEventListener('click',()=>{stopAuto();select(Number(b.dataset.step));}));
    figure.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>{stopAuto();go(Number(b.dataset.go));}));
    if(autoButton)autoButton.addEventListener('click',()=>{
      if(autoTimer){stopAuto();return;}
      if(Number(figure.dataset.state||0)>=stepButtons.length-1)select(0);
      autoButton.setAttribute('aria-pressed','true');autoButton.textContent='停止';autoTimer=setTimeout(tick,reduced.matches?1600:2200);
    });
    if(stepButtons.length)figure.addEventListener('keydown',e=>{
      if(e.target.closest('input,textarea'))return;
      if(e.key==='ArrowRight'){stopAuto();go(1);e.preventDefault();}
      else if(e.key==='ArrowLeft'){stopAuto();go(-1);e.preventDefault();}
    });
    figure.querySelectorAll('.dg-switch input').forEach(input=>input.addEventListener('change',()=>{if(input.checked)select(Number(input.value));}));
    const gridButton=figure.querySelector('.dg-grid-toggle');
    if(gridButton)gridButton.addEventListener('click',()=>{
      // Small multiples: the static scenes, already in the page for print, side by side.
      const on=gridButton.getAttribute('aria-pressed')!=='true';
      gridButton.setAttribute('aria-pressed',String(on));gridButton.textContent=on?'1つずつ見る':'すべて並べる';
      figure.classList.toggle('dg-grid',on);figure.querySelectorAll('.dg-switch input').forEach(i=>i.disabled=on);
    });
    if(play)play.addEventListener('click',()=>{playing=!playing;play.setAttribute('aria-pressed',String(playing));play.textContent=playing?'流れを停止':'流れを再生';startFlow();});
    new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;startFlow();},{threshold:.05}).observe(figure);
    document.addEventListener('visibilitychange',startFlow);
    reduced.addEventListener('change',()=>{select(Number(figure.dataset.state||0),true);});
    select(0,true);
  });
})();
(() => {
  // One floating tooltip for chart marks that carry data-tip; the text follows variant changes because it is an attribute.
  const tip=document.createElement('div');tip.className='dg-tip';tip.setAttribute('role','tooltip');tip.hidden=true;document.body.append(tip);
  function show(el,x,y){tip.textContent=el.getAttribute('data-tip');tip.hidden=false;const r=tip.getBoundingClientRect();
    tip.style.left=Math.max(8,Math.min(innerWidth-r.width-8,x-r.width/2))+'px';tip.style.top=Math.max(8,y-r.height-12)+'px';}
  document.addEventListener('pointermove',e=>{const el=e.target.closest&&e.target.closest('.dg-live [data-tip]');if(el)show(el,e.clientX,e.clientY);else tip.hidden=true;});
  document.addEventListener('scroll',()=>{tip.hidden=true;},{passive:true});
})();
