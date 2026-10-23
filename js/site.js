// Łowca Smaków — header, search, region and world maps, recipe filters, newsletter, sign-ups
(function () {
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // mobile / tablet menu
  var menuBtn = $('[data-menu-toggle]'), nav = $('#main-nav');
  if (menuBtn && nav) {
    menuBtn.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      menuBtn.setAttribute('aria-expanded', String(open));
    });
    $$('a', nav).forEach(function (a) {
      a.addEventListener('click', function () { nav.classList.remove('is-open'); menuBtn.setAttribute('aria-expanded', 'false'); });
    });
  }

  // search: filters the recipe grid by title
  var searchBtn = $('[data-search-toggle]'), search = $('[data-search]');
  if (searchBtn && search) {
    searchBtn.addEventListener('click', function () {
      search.hidden = !search.hidden;
      searchBtn.setAttribute('aria-expanded', String(!search.hidden));
      if (!search.hidden) $('input', search).focus();
    });
    search.addEventListener('submit', function (e) {
      var recipes = $('[data-recipes]');
      if (!recipes) return; // other pages: let the form go to the homepage
      e.preventDefault();
      var q = $('input', search).value.trim().toLowerCase();
      setFilter(recipes, 'all');
      var shown = 0;
      $$('[data-cat]', recipes).forEach(function (c) {
        var hit = !q || c.textContent.toLowerCase().indexOf(q) !== -1;
        c.hidden = !hit; if (hit) shown++;
      });
      var empty = $('[data-recipes-empty]', recipes);
      empty.textContent = shown ? '' : 'Nic nie znaleźliśmy dla „' + q + '”.';
      empty.hidden = !!shown;
      recipes.scrollIntoView();
    });
    var q0 = new URLSearchParams(location.search).get('q');
    if (q0 && $('[data-recipes]')) { $('input', search).value = q0; search.hidden = false; search.requestSubmit(); }
  }

  // filter chips: recipes on the homepage, spice mixes in the shop
  function setFilter(root, f) {
    $$('[data-filter]', root).forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.filter === f)); });
    var shown = 0;
    $$('[data-cat]', root).forEach(function (c) {
      var hit = f === 'all' || c.dataset.cat === f;
      c.hidden = !hit; if (hit) shown++;
    });
    var empty = $('[data-recipes-empty]', root);
    if (!empty) return;
    if (root.hasAttribute('data-recipes')) empty.textContent = 'Wkrótce więcej przepisów w tej kategorii.';
    empty.hidden = !!shown;
  }
  $$('[data-recipes], [data-filterable]').forEach(function (root) {
    $$('[data-filter]', root).forEach(function (b) {
      b.addEventListener('click', function () { setFilter(root, b.dataset.filter); });
    });
    // ?k=kiszonki (from a breadcrumb or a link) opens the listing already filtered
    var k = new URLSearchParams(location.search).get('k');
    if (k && root.hasAttribute('data-filterable') && $$('[data-filter]', root).some(function (b) { return b.dataset.filter === k; })) setFilter(root, k);
  });

  // regions: the map of voivodeships and the chips select the same region
  var regions = $('[data-regions]');
  if (regions) {
    var out = $('[data-region-out]', regions);
    $$('[data-region]', regions).forEach(function (b) {
      b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', function () {
        var name = b.dataset.region;
        $$('[data-region]', regions).forEach(function (x) { x.setAttribute('aria-pressed', String(x.dataset.region === name)); });
        var tileWithStory = $('.tile[data-region="' + name + '"][data-story]', regions);
        out.innerHTML = '';
        if (tileWithStory) {
          var link = document.createElement('a');
          link.href = tileWithStory.dataset.story; link.textContent = name + ': ' + tileWithStory.dataset.storyLabel + ' →';
          out.appendChild(link);
        } else {
          out.textContent = name + ' — odcinek wkrótce.';
        }
      });
      // map shapes are SVG paths with role="button": make Enter and Space work like a click
      if (b.tagName.toLowerCase() === 'path') b.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); b.dispatchEvent(new MouseEvent('click', { bubbles: true })); }
      });
    });
    var more = $('[data-regions-more]', regions);
    if (more) more.addEventListener('click', function (e) {
      e.preventDefault();
      var chips = more.parentNode, have = $$('[data-region]', chips).map(function (c) { return c.dataset.region; });
      $$('.tile', regions).forEach(function (t) {
        if (have.indexOf(t.dataset.region) !== -1) return;
        var c = document.createElement('button');
        c.type = 'button'; c.className = 'chip'; c.dataset.region = t.dataset.region; c.textContent = t.dataset.region;
        c.setAttribute('aria-pressed', t.getAttribute('aria-pressed'));
        c.addEventListener('click', function () { t.dispatchEvent(new MouseEvent('click', { bubbles: true })); });
        chips.insertBefore(c, more);
      });
      more.remove();
    });
  }

  // world map: countries with stories list them; chips select the same country
  var world = $('[data-world]');
  if (world) {
    var wout = $('[data-world-out]', world);
    var pick = function (name) {
      $$('[data-country]', world).forEach(function (x) {
        if (x.classList.contains('has-story') || x.classList.contains('chip')) x.setAttribute('aria-pressed', String(x.dataset.country === name));
      });
      var shape = $('path.has-story[data-country="' + name + '"]', world);
      wout.innerHTML = '';
      var h = document.createElement('p'); h.className = 'world-name'; h.textContent = name; wout.appendChild(h);
      if (!shape) {
        var p = document.createElement('p'); p.className = 'meta'; p.textContent = 'Jeszcze tu nie byliśmy.'; wout.appendChild(p);
        return;
      }
      var list = document.createElement('ul');
      JSON.parse(shape.dataset.stories).forEach(function (s) {
        var li = document.createElement('li'), a = document.createElement('a');
        a.href = s[0]; a.textContent = s[1] + ' →'; li.appendChild(a); list.appendChild(li);
      });
      wout.appendChild(list);
    };
    $$('[data-country]', world).forEach(function (el) {
      if (el.classList.contains('has-story') || el.classList.contains('chip')) el.setAttribute('aria-pressed', 'false');
      el.addEventListener('click', function () { pick(el.dataset.country); });
      if (el.tagName.toLowerCase() === 'path' && el.classList.contains('has-story')) el.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(el.dataset.country); }
      });
    });
  }

  // newsletter: Netlify Forms when deployed there
  $$('[data-newsletter]').forEach(function (form) {
    var msg = $('[data-nl-msg]', form);
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = $('button[type="submit"]', form);
      btn.disabled = true;
      fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(new FormData(form)).toString()
      }).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        form.reset();
        msg.textContent = 'Dziękujemy! Pierwsza historia już wkrótce w Twojej skrzynce.';
      }).catch(function () {
        msg.textContent = 'Nie udało się zapisać. Spróbuj ponownie za chwilę.';
      }).then(function () { btn.disabled = false; });
    });
  });

  // header cart (Snipcart fills the count): hide the badge while the cart is empty
  $$('.snipcart-items-count').forEach(function (el) {
    var set = function () { var t = el.textContent.trim(); el.hidden = !t || t === '0'; };
    set();
    new MutationObserver(set).observe(el, { childList: true, characterData: true, subtree: true });
  });

  // issue line: weeks (Monday–Sunday) since the first issue, so it stays current between deploys (same rule as build.py)
  var MONTHS = ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca', 'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia'];
  $$('[data-issue-start]').forEach(function (el) {
    var monday = function (d) { d = new Date(d.getFullYear(), d.getMonth(), d.getDate()); d.setDate(d.getDate() - (d.getDay() + 6) % 7); return d; };
    var p = el.dataset.issueStart.split('-');
    var start = monday(new Date(+p[0], +p[1] - 1, +p[2])), mon = monday(new Date());
    var sun = new Date(mon); sun.setDate(mon.getDate() + 6);
    var n = Math.max(1, Math.round((mon - start) / 864e5 / 7) + 1);
    var span = mon.getMonth() === sun.getMonth()
      ? mon.getDate() + '–' + sun.getDate() + ' ' + MONTHS[mon.getMonth()] + ' ' + sun.getFullYear()
      : mon.getDate() + ' ' + MONTHS[mon.getMonth()] + (mon.getFullYear() === sun.getFullYear() ? '' : ' ' + mon.getFullYear()) +
        ' – ' + sun.getDate() + ' ' + MONTHS[sun.getMonth()] + ' ' + sun.getFullYear();
    el.textContent = 'Wydanie nr ' + (n < 10 ? '0' + n : n) + ' · ' + span;
  });

  // workshop and trip sign-ups: Netlify Forms ("zapisy"), same as the newsletter
  $$('[data-booking]').forEach(function (form) {
    var msg = $('[data-booking-msg]', form);
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = $('button[type="submit"]', form);
      btn.disabled = true;
      fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(new FormData(form)).toString()
      }).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        form.reset();
        msg.textContent = 'Dziękujemy! Odpiszemy w ciągu dwóch dni roboczych.';
      }).catch(function () {
        msg.textContent = 'Nie udało się wysłać. Spróbuj ponownie za chwilę.';
      }).then(function () { btn.disabled = false; });
    });
  });

  // YouTube: show a photo and a play button; load the player (privacy-enhanced mode) only on click
  $$('[data-yt]').forEach(function (box) {
    var btn = $('[data-yt-play]', box);
    if (!btn) return;
    btn.addEventListener('click', function () {
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(box.dataset.yt) + '?autoplay=1&rel=0';
      f.title = box.dataset.ytTitle || 'Wideo';
      f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
      f.allowFullscreen = true;
      f.className = 'fill';
      box.classList.add('is-playing');
      box.innerHTML = '';
      box.appendChild(f);
      f.focus();
    });
  });
})();
