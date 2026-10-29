// Recipe page: servings scaling, ingredient checklist, shopping list, timers, print / save / share.
(function () {
  var slug = document.body.dataset.recipe;
  var R = window.RECIPES && window.RECIPES[slug];
  if (!R) return;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  var step = R.servingsUnit === 'babeczki' ? 6 : 1, max = step * 12;
  var n = R.servings;
  $$('[hidden]').forEach(function (el) { if (el.matches('.tools button, [data-stepper]')) el.hidden = false; });

  // checklist: ticked = "I have it"; ticks survive a reload
  var ticksKey = 'lumaca:' + slug + ':ticks', ticks = store.get(ticksKey) || {};
  var items = $$('[data-ingredients] li');
  items.forEach(function (li, i) {
    var cb = $('input', li);
    cb.checked = !!ticks[i];
    cb.addEventListener('change', function () { ticks[i] = cb.checked; store.set(ticksKey, ticks); });
  });
  function factor() { return n / R.servings; }
  function renderQty() {
    items.forEach(function (li, i) { $('.qty', li).textContent = window.formatQty(R.ingredients[i], factor()); });
  }

  // servings
  var out = $('[data-servings]'), dec = $('[data-dec]'), inc = $('[data-inc]');
  function renderServings() {
    out.textContent = window.pluralServings(n, R.servingsUnit);
    dec.disabled = n <= step; inc.disabled = n >= max;
    renderQty();
  }
  dec.addEventListener('click', function () { n = Math.max(step, n - step); renderServings(); });
  inc.addEventListener('click', function () { n = Math.min(max, n + step); renderServings(); });
  renderServings();

  // timers
  $$('.timer[data-minutes]').forEach(function (b) {
    window.bindTimer(b, +b.dataset.minutes, function (t, running) { $('span', b).textContent = (running ? 'Stop · ' : 'Minutnik · ') + t; });
  });

  // shopping list: everything not ticked, scaled to the chosen servings, as a .txt download
  $('[data-list]').addEventListener('click', function () {
    var need = R.ingredients.filter(function (ing, i) { return !ticks[i]; });
    var lines = ['LISTA ZAKUPÓW', R.title + ' · ' + window.pluralServings(n, R.servingsUnit), ''];
    need.forEach(function (ing) {
      var q = window.formatQty(ing, factor());
      lines.push('[ ] ' + ing.n + (q === 'do smaku' ? '' : ' · ' + q));
    });
    if (!need.length) lines.push('Masz już wszystko. Smacznego!');
    if (R.product) lines.push('', 'Słoiki Lumaca: ' + location.origin + '/sklep/' + R.product + '.html');
    lines.push('Przepis: ' + location.origin + location.pathname, '');
    var blob = new Blob(['﻿' + lines.join('\r\n')], { type: 'text/plain;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'lista-zakupow-' + slug + '.txt';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  });

  $('[data-print]').addEventListener('click', function () { window.print(); });

  var saveBtn = $('[data-save]'), savedKey = 'lumaca:saved', saved = store.get(savedKey) || [];
  function renderSave() {
    var on = saved.indexOf(slug) !== -1;
    saveBtn.setAttribute('aria-pressed', String(on));
    $('span', saveBtn).textContent = on ? 'Zapisano' : 'Zapisz';
  }
  saveBtn.addEventListener('click', function () {
    var i = saved.indexOf(slug);
    if (i === -1) saved.push(slug); else saved.splice(i, 1);
    store.set(savedKey, saved); renderSave();
  });
  renderSave();

  var shareBtn = $('[data-share]');
  shareBtn.addEventListener('click', function () {
    var data = { title: document.title, url: location.href };
    if (navigator.share) { navigator.share(data).catch(function () {}); return; }
    var label = $('span', shareBtn);
    (navigator.clipboard ? navigator.clipboard.writeText(location.href) : Promise.reject())
      .then(function () { label.textContent = 'Skopiowano link'; })
      .catch(function () { label.textContent = 'Skopiuj adres z paska'; })
      .then(function () { setTimeout(function () { label.textContent = 'Udostępnij'; }, 2500); });
  });
})();
