// Site search: stories, recipes, workshops, trips and spice mixes from js/search-index.json (written by build.py).
// Typing in the header search shows the best matches; Enter opens /szukaj/?q=… with all of them.
// Matching ignores case and Polish diacritics ("slimaki" finds "Ślimaki"); every word must match the start of a word.
(function () {
  var index = null, loading = null;
  function load() {
    if (index) return Promise.resolve(index);
    if (!loading) loading = fetch('/js/search-index.json').then(function (r) { return r.json(); }).then(function (d) {
      index = d.map(function (it) {
        it._t = norm(it.t); it._s = norm(it.k + ' ' + it.s); it._x = norm(it.x || '');
        return it;
      });
      return index;
    });
    return loading;
  }
  function norm(t) {
    return (' ' + t).toLowerCase().replace(/ł/g, 'l').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, ' ');
  }
  function search(q) {
    var words = norm(q).trim().split(' ').filter(Boolean);
    if (!words.length) return [];
    var res = [];
    index.forEach(function (it) {
      var score = 0;
      for (var i = 0; i < words.length; i++) {
        var w = ' ' + words[i];
        var s = (it._t.indexOf(w) !== -1 ? 6 : 0) + (it._s.indexOf(w) !== -1 ? 3 : 0) + (it._x.indexOf(w) !== -1 ? 1 : 0);
        if (!s) return;
        score += s;
      }
      res.push([score, it]);
    });
    return res.sort(function (a, b) { return b[0] - a[0] || (b[1].d || '').localeCompare(a[1].d || ''); }).map(function (r) { return r[1]; });
  }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function item(it, tag) {
    return '<' + tag + ' class="result"><a href="' + esc(it.u) + '">' +
      (it.i ? '<img src="' + esc(it.i) + '" alt="" width="64" height="64" loading="lazy">' : '<span class="noimg"></span>') +
      '<span class="r-body"><span class="tag">' + esc(it.k) + '</span><span class="r-t">' + esc(it.t) + '</span>' +
      (it.s ? '<span class="r-s">' + esc(it.s) + '</span>' : '') + '</span></a></' + tag + '>';
  }

  // header: live results under the search bar
  var form = document.querySelector('[data-search]');
  if (form) {
    var input = form.querySelector('input'), live = form.querySelector('#search-live'), timer;
    var show = function () {
      var q = input.value.trim();
      if (q.length < 2) { live.hidden = true; input.setAttribute('aria-expanded', 'false'); return; }
      load().then(function () {
        var hits = search(q);
        live.innerHTML = hits.length
          ? '<ul>' + hits.slice(0, 6).map(function (it) { return item(it, 'li'); }).join('') + '</ul>' +
            (hits.length > 6 ? '<a class="all" href="/szukaj/?q=' + encodeURIComponent(q) + '">Wszystkie wyniki (' + hits.length + ') →</a>' : '')
          : '<p class="none">Nic nie znaleźliśmy dla „' + esc(q) + '”.</p>';
        live.hidden = false; input.setAttribute('aria-expanded', 'true');
      });
    };
    input.addEventListener('focus', load);
    input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(show, 120); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { live.hidden = true; input.setAttribute('aria-expanded', 'false'); }
      if (e.key === 'ArrowDown' && !live.hidden) { var a = live.querySelector('a'); if (a) { e.preventDefault(); a.focus(); } }
    });
    live.addEventListener('keydown', function (e) {
      var links = [].slice.call(live.querySelectorAll('a')), i = links.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' && i < links.length - 1) { e.preventDefault(); links[i + 1].focus(); }
      if (e.key === 'ArrowUp') { e.preventDefault(); (i > 0 ? links[i - 1] : input).focus(); }
      if (e.key === 'Escape') { input.focus(); live.hidden = true; }
    });
  }

  // /szukaj/?q=…: all results
  var page = document.querySelector('[data-search-page]');
  if (page) {
    var q = new URLSearchParams(location.search).get('q') || '';
    var box = page.querySelector('input'), list = page.querySelector('[data-results]'), head = page.querySelector('[data-results-h]');
    box.value = q;
    if (!q.trim()) { head.textContent = 'Wpisz, czego szukasz: przepis, składnik, kraj, przyprawę.'; box.focus(); return; }
    document.title = 'Szukaj: ' + q + ' — Łowca Smaków';
    load().then(function () {
      var hits = search(q);
      var n = hits.length, word = n === 1 ? 'wynik' : (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14)) ? 'wyniki' : 'wyników';
      head.textContent = n ? n + ' ' + word + ' dla „' + q + '”' : 'Nic nie znaleźliśmy dla „' + q + '”. Spróbuj innego słowa albo zajrzyj do przepisów.';
      list.innerHTML = hits.map(function (it) { return item(it, 'li'); }).join('');
    });
  }
})();
