// Cook mode: one step per screen, big type, timer, keeps the screen awake
(function () {
  var slug = new URLSearchParams(location.search).get('r');
  if (!window.RECIPES[slug]) slug = 'slimaki-w-szarym-sosie';
  var R = window.RECIPES[slug], steps = R.steps, i = 0;
  var back = '/przepisy/' + slug + '.html';
  document.querySelector('[data-close]').href = back;
  document.title = 'Tryb gotowania — ' + R.title + ' — Łowca Smaków';
  var $ = function (s) { return document.querySelector(s); };
  var bars = $('[data-bars]');
  steps.forEach(function () { bars.appendChild(document.createElement('span')); });
  bars.style.gridTemplateColumns = 'repeat(' + steps.length + ',minmax(0,1fr))';

  function render() {
    var s = steps[i], last = i === steps.length - 1;
    $('[data-count]').textContent = 'Krok ' + (i + 1) + ' z ' + steps.length;
    Array.prototype.forEach.call(bars.children, function (b, k) { b.classList.toggle('on', k <= i); });
    $('[data-title]').textContent = s.title;
    $('[data-desc]').textContent = s.text;
    var uses = $('[data-uses]');
    $('[data-uses-wrap]').hidden = !s.uses.length;
    uses.innerHTML = '';
    s.uses.forEach(function (u) {
      var p = document.createElement('span');
      p.className = 'pill'; p.textContent = u;
      uses.appendChild(p);
    });
    // timer: rebuilt per step so a running countdown never leaks into the next one
    var old = $('[data-timer]'), t = old.cloneNode(true);
    old.parentNode.replaceChild(t, old);
    t.hidden = !s.timer;
    t.disabled = false; t.removeAttribute('title');
    t.querySelector('[data-timer-label]').textContent = 'Uruchom minutnik';
    t.querySelector('[data-timer-time]').textContent = '[XX:00]';
    if (s.timer) window.bindTimer(t, s.minutes, function (time, running) {
      t.querySelector('[data-timer-time]').textContent = time;
      t.querySelector('[data-timer-label]').textContent = running ? 'Zatrzymaj' : 'Uruchom minutnik';
    });
    $('[data-prev]').disabled = i === 0;
    $('[data-next]').textContent = last ? 'Smacznego!' : 'Dalej →';
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
  var lock = null;
  function wake() {
    if (!('wakeLock' in navigator) || document.visibilityState !== 'visible') return;
    navigator.wakeLock.request('screen').then(function (l) {
      lock = l; $('[data-wake]').hidden = false;
      l.addEventListener('release', function () { $('[data-wake]').hidden = true; });
    }).catch(function () {});
  }
  document.addEventListener('visibilitychange', wake);
  wake();
})();
