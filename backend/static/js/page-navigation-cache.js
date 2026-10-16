/* UNIMAP page navigation: Turbo Drive snapshots and restores same-origin pages. */
(() => {
  if (window.__unimapPageNavigationBound) return;
  window.__unimapPageNavigationBound = true;

  // Keep the browser's own back/forward cache enabled and restore scroll on snapshots.
  if (window.Turbo) {
    window.Turbo.session.drive = true;
    window.Turbo.config.cache = true;
    window.Turbo.setProgressBarDelay(120);
  }

  // A small, accessible progress indicator while a server-rendered page is fetched.
  const style = document.createElement('style');
  style.textContent = `#unimap-nav-progress{position:fixed;z-index:99999;top:0;left:0;height:3px;width:0;background:#3987ff;opacity:0;transition:width .18s ease,opacity .18s ease;pointer-events:none}html.turbo-loading #unimap-nav-progress{opacity:1;width:70%}html.turbo-loading.turbo-loaded #unimap-nav-progress{width:100%;opacity:0}`;
  document.head.appendChild(style);
  const bar = document.createElement('div');
  bar.id = 'unimap-nav-progress';
  bar.setAttribute('aria-hidden', 'true');
  document.body.appendChild(bar);
  document.addEventListener('turbo:visit', () => { document.documentElement.classList.add('turbo-loading'); document.documentElement.classList.remove('turbo-loaded'); });
  document.addEventListener('turbo:load', () => {
    document.documentElement.classList.remove('turbo-loading');
    document.documentElement.classList.add('turbo-loaded');
    window.setTimeout(() => document.documentElement.classList.remove('turbo-loaded'), 220);
  });

  // Avoid stale sensitive snapshots. These pages still use Turbo navigation, but
  // are fetched again instead of being restored from the in-memory page cache.
  const sensitive = /\/(?:logout|login|register|notifications|profile(?:\/edit)?|classes|class|class-management|campus-now|feedback\/admin)(?:\/|$)/i;
  const markSensitivePage = () => {
    if (!document.querySelector('meta[name="turbo-cache-control"]') && sensitive.test(location.pathname)) {
      const meta = document.createElement('meta');
      meta.name = 'turbo-cache-control';
      meta.content = 'no-cache';
      document.head.appendChild(meta);
    }
  };
  markSensitivePage();
  document.addEventListener('turbo:load', markSensitivePage);
})();
