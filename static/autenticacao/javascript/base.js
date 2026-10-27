(() => {
  'use strict';
  if (window.kaitoSidebarInitialized) return;
  window.kaitoSidebarInitialized = true;
  function init() {
    const toggles = document.querySelectorAll('.toggle-sidebar-btn');
    if (!toggles.length) return;
    const desktop = window.matchMedia('(min-width: 1200px)');
    function sync() {
      const expanded = desktop.matches ? !document.body.classList.contains('toggle-sidebar') : document.body.classList.contains('toggle-sidebar');
      toggles.forEach(button => button.setAttribute('aria-expanded', String(expanded)));
    }
    toggles.forEach(button => {
      button.setAttribute('role', 'button');
      button.setAttribute('tabindex', '0');
      button.setAttribute('aria-label', 'Abrir ou fechar menu lateral');
      button.setAttribute('aria-controls', 'sidebar');
      button.addEventListener('click', () => { document.body.classList.toggle('toggle-sidebar'); sync(); });
      button.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); button.click(); }
      });
    });
    desktop.addEventListener('change', sync);
    sync();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once: true});
  else init();
})();
