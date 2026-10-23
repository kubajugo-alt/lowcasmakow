// Recipe page: ingredients checklist, servings, units, steps with timers, print / save / share
(function () {
  var R = window.RECIPE;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };

  // ingredients (ticks survive a reload)
  var ticksKey = 'ls:' + R.slug + ':ticks', ticks = store.get(ticksKey) || {};
  var list = $('[data-ingredients]');
  R.ingredients.forEach(function (ing, i) {
    var li = document.createElement('li');
    li.innerHTML = '<label><input type="checkbox"><span class="name"></span><span class="qty"></span></label>';
    $('.name', li).textContent = ing.name;
    $('.qty', li).textContent = ing.qty;
    var cb = $('input', li);
    cb.checked = !!ticks[i];
    cb.addEventListener('change', function () { ticks[i] = cb.checked; store.set(ticksKey, ticks); });
    list.appendChild(li);
  });

  // servings
  var n = R.servings, out = $('[data-servings]'), stat = $('[data-servings-stat]');
  var dec = $('[data-dec]'), inc = $('[data-inc]');
  function renderServings() {
    out.textContent = window.pluralPorcje(n);
    stat.textContent = n;
    dec.disabled = n <= 1; inc.disabled = n >= 12;
  }
  dec.addEventListener('click', function () { n = Math.max(1, n - 1); renderServings(); });
  inc.addEventListener('click', function () { n = Math.min(12, n + 1); renderServings(); });
  renderServings();

  // units toggle
  $$('[data-units]').forEach(function (b) {
    b.addEventListener('click', function () {
      $$('[data-units]').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
    });
  });

  // steps
  var ol = $('[data-steps]');
  R.steps.forEach(function (s, i) {
    var li = document.createElement('li');
    li.innerHTML = '<span class="n"></span><div class="txt"><h3></h3><p></p></div>';
    $('.n', li).textContent = i + 1;
    $('h3', li).textContent = s.title;
    $('p', li).textContent = s.text || R.stepText;
    if (s.timer) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'tool sm timer'; b.style.alignSelf = 'flex-start';
      b.innerHTML = '<svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M10 2h4"/></svg><span>Minutnik · [XX] min</span>';
      $('.txt', li).appendChild(b);
      window.bindTimer(b, s.minutes, function (t, running) { $('span', b).textContent = (running ? 'Stop · ' : 'Minutnik · ') + t; });
    }
    ol.appendChild(li);
  });

  // print / save / share
  $('[data-print]').addEventListener('click', function () { window.print(); });

  var saveBtn = $('[data-save]'), savedKey = 'ls:saved', saved = store.get(savedKey) || [];
  function renderSave() {
    var on = saved.indexOf(R.slug) !== -1;
    saveBtn.setAttribute('aria-pressed', String(on));
    $('span', saveBtn).textContent = on ? 'Zapisano' : 'Zapisz';
  }
  saveBtn.addEventListener('click', function () {
    var i = saved.indexOf(R.slug);
    if (i === -1) saved.push(R.slug); else saved.splice(i, 1);
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
