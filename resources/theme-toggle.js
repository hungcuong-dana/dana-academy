// DANA·OJ — Compile theme toggle (data-theme + localStorage, no reload).
// CSRF is attached automatically by the global $.ajaxSetup in common.js.
(function () {
  'use strict';
  var root = document.documentElement;

  function syncThemeIcon() {
    var isDark = root.getAttribute('data-theme') === 'dark';
    var moons = document.querySelectorAll('[data-theme-moon]');
    var suns = document.querySelectorAll('[data-theme-sun]');
    var i;
    for (i = 0; i < moons.length; i++) moons[i].style.display = isDark ? '' : 'none';
    for (i = 0; i < suns.length; i++) suns[i].style.display = isDark ? 'none' : '';
  }

  window.setTheme = function (theme) {
    root.setAttribute('data-theme', theme);
    try { localStorage.setItem('dana-theme', theme); } catch (e) {}
    syncThemeIcon();
    // Persist server-side for cross-device sync (best-effort, no reload).
    // The endpoint is @login_required, so only POST for authenticated users.
    if (window.TOGGLE_DARKMODE_URL && window.jQuery && window.user && window.user.id) {
      jQuery.post(window.TOGGLE_DARKMODE_URL, { mode: theme });
    }
  };

  window.toggleTheme = function () {
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    window.setTheme(next);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', syncThemeIcon);
  } else {
    syncThemeIcon();
  }
})();
