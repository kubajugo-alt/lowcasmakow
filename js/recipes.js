// Recipe helpers shared by the recipe pages and cook mode.
// The recipes themselves are in js/recipe-data.js, generated from content/recipes/*.json (edit them at /admin).

// Shared countdown: binds a button showing mm:ss (or h:mm:ss); disabled when the step has no minutes.
window.bindTimer = function (btn, minutes, render) {
  if (typeof minutes !== 'number') {
    btn.disabled = true;
    btn.title = 'Czas do uzupełnienia';
    return;
  }
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
};

window.pluralPorcje = function (n, unit) {
  var m10 = n % 10, m100 = n % 100, few = m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14);
  if (unit === 'słoiki') return n + ' ' + (n === 1 ? 'słoik' : few ? 'słoiki' : 'słoików');
  return n + ' ' + (n === 1 ? 'porcja' : few ? 'porcje' : 'porcji');
};

// "250 ml" → scaled, rounded sensibly; metric or cups/spoons.
window.formatQty = function (ing, factor, cups) {
  if (ing.q === null) return 'do smaku';
  var q = ing.q * factor, u = ing.u;
  if (cups && u === 'ml') {
    if (q >= 125) { var g = Math.round(q / 250 * 4) / 4; return fmtNum(g) + ' szkl.'; }
    if (q >= 15) return fmtNum(Math.round(q / 15 * 2) / 2) + ' łyżki';
    return fmtNum(Math.round(q / 5 * 2) / 2) + ' łyżeczki';
  }
  if (u === 'g' || u === 'ml') {
    q = q >= 1000 ? Math.round(q / 50) * 50 : q >= 100 ? Math.round(q / 10) * 10 : Math.round(q);
    if (q >= 1000) return fmtNum(q / 1000) + (u === 'g' ? ' kg' : ' l');
    return q + ' ' + u;
  }
  q = Math.round(q * 2) / 2;
  return fmtNum(q) + (u ? ' ' + u : '');
  function fmtNum(x) { return String(x).replace('.', ',').replace(/,5$/, '½').replace(/^0½$/, '½').replace(/,25$/, '¼').replace(/,75$/, '¾'); }
};
