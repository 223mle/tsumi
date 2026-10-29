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
