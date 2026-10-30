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
      figure.dataset.state=String(index);figure.dataset.animating='true';
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
    figure.querySelectorAll('.dg-switch input').forEach(input=>input.addEventListener('change',()=>{if(input.checked)select(Number(input.value));}));
    if(play)play.addEventListener('click',()=>{playing=!playing;play.setAttribute('aria-pressed',String(playing));play.textContent=playing?'流れを停止':'流れを再生';startFlow();});
    new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;startFlow();},{threshold:.05}).observe(figure);
    document.addEventListener('visibilitychange',startFlow);
    reduced.addEventListener('change',()=>{select(Number(figure.dataset.state||0),true);});
    select(0,true);
  });
})();
