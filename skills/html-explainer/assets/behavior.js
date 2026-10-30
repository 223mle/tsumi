(() => {
  const root = document.documentElement;
  const controls = document.querySelectorAll('[data-theme-set]');
  function apply(theme) {
    if (theme === 'system') delete root.dataset.theme;
    else root.dataset.theme = theme;
    controls.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.themeSet === theme)));
  }
  let saved = 'system';
  try { saved = localStorage.getItem('tsumi-html-theme') || 'system'; } catch (_) {}
  apply(['light', 'dark', 'system'].includes(saved) ? saved : 'system');
  controls.forEach(button => button.addEventListener('click', () => {
    const theme = button.dataset.themeSet;
    apply(theme);
    try { localStorage.setItem('tsumi-html-theme', theme); } catch (_) {}
  }));
})();
(() => {
  const bar = document.querySelector('.progress span');
  const links = [...document.querySelectorAll('.toc a[href^="#"]')];
  const targets = links.map(a => document.getElementById(decodeURIComponent(a.hash.slice(1)))).filter(Boolean);
  let frame = 0;
  function update() {
    frame = 0;
    const doc = document.documentElement;
    const max = doc.scrollHeight - innerHeight;
    if (bar) bar.style.setProperty('--read', max > 0 ? Math.min(1, scrollY / max).toFixed(4) : '1');
    let current = targets[0];
    for (const t of targets) if (t.getBoundingClientRect().top <= innerHeight * 0.3) current = t;
    links.forEach(a => {
      const on = current && a.hash === '#' + current.id;
      if (on !== (a.getAttribute('aria-current') === 'true')) {
        a.setAttribute('aria-current', String(on));
        if (on && matchMedia('(max-width: 960px)').matches) a.scrollIntoView({block: 'nearest', inline: 'nearest'});
      }
    });
  }
  addEventListener('scroll', () => { if (!frame) frame = requestAnimationFrame(update); }, {passive: true});
  addEventListener('resize', update);
  update();
})();
(() => {
  // A glossary term and the diagram parts with the same name light up together.
  const terms = document.querySelectorAll('.term[data-term]');
  function link(name, on) {
    document.querySelectorAll('[data-ref]').forEach(el => { if (el.dataset.ref === name) el.classList.toggle('is-linked', on); });
    document.querySelectorAll('.term[data-term]').forEach(el => { if (el.dataset.term === name) el.classList.toggle('is-linked', on); });
  }
  terms.forEach(term => {
    const name = term.dataset.term;
    ['mouseenter', 'focus'].forEach(ev => term.addEventListener(ev, () => link(name, true)));
    ['mouseleave', 'blur'].forEach(ev => term.addEventListener(ev, () => link(name, false)));
  });
  document.addEventListener('mouseover', e => {
    const part = e.target.closest && e.target.closest('[data-ref]');
    if (part && !part.contains(e.relatedTarget)) link(part.dataset.ref, true);
  });
  document.addEventListener('mouseout', e => {
    const part = e.target.closest && e.target.closest('[data-ref]');
    if (part && !part.contains(e.relatedTarget)) link(part.dataset.ref, false);
  });
})();
