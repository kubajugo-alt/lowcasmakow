// Recipe helpers shared by the recipe pages and the cooking view.
// The recipes themselves are in js/recipe-data.js, generated from content/recipes/*.json (edit them at /admin).
(function () {
  var UNITS = {
    'słoik': ['słoik', 'słoiki', 'słoików', 'słoika'], 'ząbek': ['ząbek', 'ząbki', 'ząbków', 'ząbka'],
    'garść': ['garść', 'garście', 'garści', 'garści'], 'łyżka': ['łyżka', 'łyżki', 'łyżek', 'łyżki'],
    'listek': ['listek', 'listki', 'listków', 'listka']
  };
  var SERVINGS = { osoby: ['osoba', 'osoby', 'osób'], babeczki: ['babeczka', 'babeczki', 'babeczek'] };

  function plural(n, forms) {
    var m10 = n % 10, m100 = n % 100;
    return n === 1 ? forms[0] : (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) ? forms[1] : forms[2];
  }
  function fmtNum(x) {
    var whole = Math.floor(x), frac = Math.round((x - whole) * 4) / 4;
    var f = frac === 0.25 ? '¼' : frac === 0.5 ? '½' : frac === 0.75 ? '¾' : '';
    if (frac === 1) { whole += 1; f = ''; }
    return (whole || !f ? String(whole) : '') + f;
  }

  window.pluralServings = function (n, unit) { return n + ' ' + plural(n, SERVINGS[unit] || SERVINGS.osoby); };

  // Scaled quantity as text. Jars are always whole (you can't buy half a jar).
  window.formatQty = function (ing, factor) {
    if (ing.q === null || ing.q === undefined) return 'do smaku';
    var q = ing.q * factor, u = ing.u;
    if (u === 'słoik') { q = Math.max(1, Math.ceil(q - 0.01)); return q + ' ' + plural(q, UNITS[u]); }
    if (u === 'g' || u === 'ml') {
      q = q >= 1000 ? Math.round(q / 50) * 50 : q >= 100 ? Math.round(q / 10) * 10 : Math.max(5, Math.round(q / 5) * 5);
      if (q >= 1000) return String(q / 1000).replace('.', ',') + (u === 'g' ? ' kg' : ' l');
      return q + ' ' + u;
    }
    q = Math.max(0.25, Math.round(q * 4) / 4);
    var unit = u;
    if (UNITS[u]) unit = q % 1 ? UNITS[u][3] : plural(q, UNITS[u]);
    return (fmtNum(q) + (unit ? ' ' + unit : '')).trim();
  };

  // Countdown on a button: mm:ss (or h:mm:ss). Click to start, click again to pause.
  window.bindTimer = function (btn, minutes, render) {
    var left = minutes * 60, id = null;
    function pad(n) { return String(n).padStart(2, '0'); }
    function fmt(s) {
      var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
      return (h ? h + ':' + pad(m) : pad(m)) + ':' + pad(sec);
    }
    render(fmt(left), false);
    btn.addEventListener('click', function () {
      if (id) { clearInterval(id); id = null; btn.dataset.running = 'false'; render(fmt(left), false); return; }
      if (left <= 0) left = minutes * 60;
      btn.dataset.running = 'true';
      render(fmt(left), true);
      id = setInterval(function () {
        left -= 1;
        render(fmt(left), true);
        if (left <= 0) {
          clearInterval(id); id = null; btn.dataset.running = 'false';
          render('Gotowe!', false);
          if (navigator.vibrate) navigator.vibrate([300, 150, 300]);
        }
      }, 1000);
    });
    return function stop() { if (id) clearInterval(id); };
  };
})();
