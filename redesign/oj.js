// DANA·OJ — shared behaviours
(function(){
  const root = document.documentElement;
  const saved = localStorage.getItem('dana-theme');
  if(saved){ root.setAttribute('data-theme', saved); }
  window.toggleTheme = function(){
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('dana-theme', next);
    syncThemeIcon();
  };
  function syncThemeIcon(){
    const isDark = root.getAttribute('data-theme') === 'dark';
    document.querySelectorAll('[data-theme-moon]').forEach(e=>e.style.display = isDark ? '' : 'none');
    document.querySelectorAll('[data-theme-sun]').forEach(e=>e.style.display = isDark ? 'none' : '');
  }
  document.addEventListener('DOMContentLoaded', syncThemeIcon);
})();
