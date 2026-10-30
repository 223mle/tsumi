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
