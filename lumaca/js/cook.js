// Cooking view: one step per screen, big type, timer, keeps the screen awake.
(function () {
  var slug = new URLSearchParams(location.search).get('r');
  var keys = Object.keys(window.RECIPES);
  if (!window.RECIPES[slug]) slug = keys[0];
  var R = window.RECIPES[slug], steps = R.steps, i = 0, stopTimer = null;
  var back = '/przepisy/' + slug + '.html';
  var $ = function (s) { return document.querySelector(s); };
  $('[data-close]').href = back;
  document.title = 'Tryb gotowania: ' + R.title + ' · Lumaca';
  $('[data-recipe-title]').textContent = R.title;
  var bars = $('[data-bars]');
  steps.forEach(function () { bars.appendChild(document.createElement('span')); });
  bars.style.gridTemplateColumns = 'repeat(' + steps.length + ',minmax(0,1fr))';
  var ing = $('[data-cook-ing]');
  R.ingredients.forEach(function (x) {
    var li = document.createElement('li'), q = window.formatQty(x, 1);
    li.textContent = x.n + (q === 'do smaku' ? '' : ' · ' + q);
    ing.appendChild(li);
  });

  function render() {
    var s = steps[i], last = i === steps.length - 1;
    $('[data-count]').textContent = 'Krok ' + (i + 1) + ' z ' + steps.length;
    Array.prototype.forEach.call(bars.children, function (b, k) { b.classList.toggle('on', k <= i); });
    $('[data-title]').textContent = s.title;
    $('[data-desc]').textContent = s.text;
    // timer is rebuilt per step so a running countdown never leaks into the next one
    if (stopTimer) stopTimer();
    var old = $('[data-timer]'), t = old.cloneNode(true);
    old.parentNode.replaceChild(t, old);
    t.hidden = !s.minutes; t.dataset.running = 'false';
    if (s.minutes) stopTimer = window.bindTimer(t, s.minutes, function (time, running) {
      t.querySelector('[data-timer-time]').textContent = time;
      t.querySelector('[data-timer-label]').textContent = running ? 'Zatrzymaj' : 'Uruchom minutnik';
    });
    $('[data-prev]').disabled = i === 0;
    $('[data-next]').textContent = last ? 'Smacznego!' : 'Dalej →';
    window.scrollTo(0, 0);
  }
  $('[data-prev]').addEventListener('click', function () { if (i > 0) { i--; render(); } });
  $('[data-next]').addEventListener('click', function () {
    if (i === steps.length - 1) { location.href = back; return; }
    i++; render();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight' && i < steps.length - 1) { i++; render(); }
    if (e.key === 'ArrowLeft' && i > 0) { i--; render(); }
  });
  render();

  // keep the screen on while cooking
  function wake() {
    if (!('wakeLock' in navigator) || document.visibilityState !== 'visible') return;
    navigator.wakeLock.request('screen').then(function (l) {
      $('[data-wake]').hidden = false;
      l.addEventListener('release', function () { $('[data-wake]').hidden = true; });
    }).catch(function () {});
  }
  document.addEventListener('visibilitychange', wake);
  wake();
})();
