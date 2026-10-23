// Łowca Smaków — header, search, region map, recipe filters, newsletter
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

  // recipe filter chips
  function setFilter(root, f) {
    $$('[data-filter]', root).forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.filter === f)); });
    var shown = 0;
    $$('[data-cat]', root).forEach(function (c) {
      var hit = f === 'all' || c.dataset.cat === f;
      c.hidden = !hit; if (hit) shown++;
    });
    var empty = $('[data-recipes-empty]', root);
    empty.textContent = 'Wkrótce więcej przepisów w tej kategorii.';
    empty.hidden = !!shown;
  }
  $$('[data-recipes]').forEach(function (root) {
    $$('[data-filter]', root).forEach(function (b) {
      b.addEventListener('click', function () { setFilter(root, b.dataset.filter); });
    });
  });

  // regions: map tiles and chips select the same region
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
        c.addEventListener('click', function () { t.click(); });
        chips.insertBefore(c, more);
      });
      more.remove();
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
