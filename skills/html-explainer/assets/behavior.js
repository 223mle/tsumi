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
    let theme = button.dataset.themeSet;
    // On a phone only the current choice is shown; tapping it moves to the next one.
    if (matchMedia('(max-width: 600px)').matches && button.getAttribute('aria-pressed') === 'true') {
      const order = ['system', 'light', 'dark'];
      theme = order[(order.indexOf(theme) + 1) % order.length];
    }
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
        // Scroll only the tab strip: scrollIntoView would also move the page and cut short a jump in progress.
        const strip = a.closest('ol');
        if (on && strip && strip.scrollWidth > strip.clientWidth) {
          const left = a.offsetLeft - strip.offsetLeft - 12;
          if (left < strip.scrollLeft || left + a.offsetWidth + 24 > strip.scrollLeft + strip.clientWidth) strip.scrollTo({left: Math.max(0, left), behavior: 'smooth'});
        }
      }
    });
  }
  addEventListener('scroll', () => { if (!frame) frame = requestAnimationFrame(update); }, {passive: true});
  addEventListener('resize', update);
  update();
})();
(() => {
  // A glossary term and the diagram parts with the same name light up together.
  // Delegated, so terms inside step texts that are swapped in later also link.
  function link(name, on) {
    document.querySelectorAll('[data-ref]').forEach(el => { if (el.dataset.ref === name) el.classList.toggle('is-linked', on); });
    document.querySelectorAll('.term[data-term]').forEach(el => { if (el.dataset.term === name) el.classList.toggle('is-linked', on); });
  }
  function owner(e) { return e.target.closest && e.target.closest('.term[data-term], [data-ref]'); }
  function name(el) { return el.dataset.term || el.dataset.ref; }
  document.addEventListener('mouseover', e => { const el = owner(e); if (el && !el.contains(e.relatedTarget)) link(name(el), true); });
  document.addEventListener('mouseout', e => { const el = owner(e); if (el && !el.contains(e.relatedTarget)) link(name(el), false); });
  document.addEventListener('focusin', e => { const el = owner(e); if (el) link(name(el), true); });
  document.addEventListener('focusout', e => { const el = owner(e); if (el) link(name(el), false); });
})();
addEventListener('beforeprint', () => document.querySelectorAll('details:not([open])').forEach(d => { d.open = true; d.dataset.printOpened = ''; }));
addEventListener('afterprint', () => document.querySelectorAll('details[data-print-opened]').forEach(d => { d.open = false; delete d.dataset.printOpened; }));
(() => {
  // Show "scroll sideways" hints only where the content really overflows.
  function mark() {
    document.querySelectorAll('.table-wrap').forEach(w => w.classList.toggle('is-scrollable', w.scrollWidth > w.clientWidth + 2));
    document.querySelectorAll('.dg-panel').forEach(p => {
      const box = p.querySelector('.dg-live') || p.querySelector('.dg-scroll');
      const scrolls = !!box && box.scrollWidth > box.clientWidth + 2;
      p.classList.toggle('is-scrollable', scrolls);
      // A box is a keyboard stop and a landmark only while it actually scrolls.
      if (box && box.classList.contains('dg-live')) {
        if (scrolls) { box.tabIndex = 0; box.setAttribute('role', 'region'); }
        else { box.removeAttribute('tabindex'); box.removeAttribute('role'); }
      }
    });
  }
  addEventListener('load', mark); addEventListener('resize', mark); mark();
})();
(() => {
  // Esc hides a term's definition until the pointer or focus leaves it (WCAG 1.4.13).
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    document.querySelectorAll('.term:hover, .term:focus, .term:focus-within').forEach(t => t.classList.add('tip-closed'));
  });
  ['mouseout', 'focusout'].forEach(ev => document.addEventListener(ev, e => {
    const t = e.target.closest && e.target.closest('.term');
    if (t && !t.contains(e.relatedTarget)) t.classList.remove('tip-closed');
  }));
})();
