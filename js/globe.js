// Smaki świata: a globe you can spin. Replaces the flat map (still in the page as the fallback)
// once it is near the screen. Drawn on a canvas with d3-geo (js/vendor, ISC licence);
// countries come from js/world-globe.json (scripts/map-paths.py globe).
// Drag or use the arrow keys to turn it; click a country (or press Enter for the one in the middle)
// to list its stories; the country chips turn the globe to that country.
(function () {
  var world = document.querySelector('[data-world]');
  if (!world || !window.HTMLCanvasElement || !window.fetch) return;
  var holder = world.querySelector('.world-map');
  var flat = holder.querySelector('svg');
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  function load(src) {
    return new Promise(function (ok, fail) {
      var s = document.createElement('script');
      s.src = src; s.onload = ok; s.onerror = fail;
      document.head.appendChild(s);
    });
  }

  var started = false;
  function start() {
    if (started) return;
    started = true;
    load('/js/vendor/d3-array.min.js')
      .then(function () { return load('/js/vendor/d3-geo.min.js'); })
      .then(function () { return fetch('/js/world-globe.json'); })
      .then(function (r) { return r.json(); })
      .then(init)
      .catch(function () { /* keep the flat map */ });
  }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (es, o) {
      if (es.some(function (e) { return e.isIntersecting; })) { o.disconnect(); start(); }
    }, { rootMargin: '400px' }).observe(world);
  } else {
    start();
  }

  function init(geo) {
    var d3 = window.d3;
    var css = getComputedStyle(document.documentElement);
    var ink = function (name, fallback) { return (css.getPropertyValue(name) || '').trim() || fallback; };
    var C = {
      sea: ink('--ultramarine', '#2B4796'), land: '#F3EBDC', hover: '#FFFFFF', border: 'rgba(43,71,150,.55)',
      story: ink('--mustard', '#E3A52A'), picked: ink('--vermilion', '#C2411C'), text: ink('--ink', '#121212')
    };

    // d3 wants clockwise outer rings; flip any polygon that came out "inside-out"
    geo.features.forEach(function (f) {
      f.geometry.coordinates.forEach(function (poly) {
        if (d3.geoArea({ type: 'Polygon', coordinates: poly }) > 2 * Math.PI) poly.forEach(function (r) { r.reverse(); });
      });
    });

    var stories = {};
    $$('path.has-story', flat).forEach(function (p) { stories[p.dataset.country] = true; });
    var byName = {}, centre = {};
    geo.features.forEach(function (f) {
      var n = f.properties.n;
      byName[n] = f;
      // centre of the largest part, so islands and overseas land don't pull the pin away
      var best = null, area = -1;
      f.geometry.coordinates.forEach(function (poly) {
        var g = { type: 'Polygon', coordinates: poly }, a = d3.geoArea(g);
        if (a > area) { area = a; best = g; }
      });
      centre[n] = d3.geoCentroid(best);
    });

    var canvas = document.createElement('canvas');
    canvas.className = 'globe';
    canvas.tabIndex = 0;
    canvas.setAttribute('role', 'application');
    canvas.setAttribute('aria-label', 'Globus. Strzałki obracają, Enter wybiera kraj na środku. Kraje z historiami są też na liście obok.');
    var tip = document.createElement('p');
    tip.className = 'globe-tip';
    tip.setAttribute('aria-hidden', 'true');
    tip.hidden = true;
    var hint = document.createElement('p');
    hint.className = 'globe-hint';
    hint.textContent = 'Przeciągnij, żeby obrócić glob';
    holder.classList.add('has-globe');
    holder.insertBefore(hint, flat);
    holder.insertBefore(canvas, flat);
    holder.insertBefore(tip, flat);

    var ctx = canvas.getContext('2d');
    var proj = d3.geoOrthographic().clipAngle(90).precision(0.6);
    var path = d3.geoPath(proj, ctx);
    var grat = d3.geoGraticule10();
    var rot = [100, -15];        // start over the Americas
    var size = 0, dpr = 1, hover = null, picked = null;
    var spin = !still, idleAt = 0, visible = true, anim = null;

    function resize() {
      size = Math.min(holder.clientWidth, 560);
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = canvas.height = Math.round(size * dpr);
      canvas.style.width = canvas.style.height = size + 'px';
      proj.translate([size / 2, size / 2]).scale(size / 2 - 6);
      draw();
    }

    function draw() {
      var r = size / 2 - 6, c = size / 2;
      proj.rotate(rot);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, size, size);
      // sea
      ctx.beginPath(); ctx.arc(c, c, r, 0, 2 * Math.PI);
      ctx.fillStyle = C.sea; ctx.fill();
      ctx.beginPath(); path(grat);
      ctx.strokeStyle = 'rgba(255,255,255,.1)'; ctx.lineWidth = 0.8; ctx.stroke();
      // land
      geo.features.forEach(function (f) {
        var n = f.properties.n;
        ctx.beginPath(); path(f);
        ctx.fillStyle = n === picked ? C.picked : stories[n] ? C.story : n === hover ? C.hover : C.land;
        ctx.fill();
        ctx.strokeStyle = C.border; ctx.lineWidth = 0.6; ctx.stroke();
      });
      // light from the top left, darker towards the rim
      var g = ctx.createRadialGradient(c - r * 0.35, c - r * 0.4, r * 0.1, c, c, r);
      g.addColorStop(0, 'rgba(255,255,255,.22)');
      g.addColorStop(0.55, 'rgba(255,255,255,0)');
      g.addColorStop(1, 'rgba(10,20,50,.38)');
      ctx.beginPath(); ctx.arc(c, c, r, 0, 2 * Math.PI);
      ctx.fillStyle = g; ctx.fill();
      // pins for countries with stories, on the visible side only
      var mid = [-rot[0], -rot[1]];
      ctx.font = '700 13px Poppins, system-ui, sans-serif';
      ctx.textAlign = 'center';
      Object.keys(stories).forEach(function (n) {
        if (!centre[n] || d3.geoDistance(centre[n], mid) > 1.45) return;
        var p = proj(centre[n]);
        ctx.beginPath(); ctx.arc(p[0], p[1], 6, 0, 2 * Math.PI);
        ctx.fillStyle = '#fff'; ctx.fill();
        ctx.lineWidth = 1.5; ctx.strokeStyle = C.text; ctx.stroke();
        ctx.beginPath(); ctx.arc(p[0], p[1], 2.4, 0, 2 * Math.PI);
        ctx.fillStyle = C.text; ctx.fill();
        ctx.lineWidth = 4; ctx.lineJoin = 'round'; ctx.strokeStyle = '#fff';
        ctx.strokeText(n, p[0], p[1] - 12);
        ctx.fillStyle = C.text; ctx.fillText(n, p[0], p[1] - 12);
      });
    }

    function countryAt(x, y) {
      var c = size / 2, r = size / 2 - 6;
      if ((x - c) * (x - c) + (y - c) * (y - c) > r * r) return null;
      var ll = proj.invert([x, y]);
      if (!ll) return null;
      for (var i = 0; i < geo.features.length; i++) {
        if (d3.geoContains(geo.features[i], ll)) return geo.features[i].properties.n;
      }
      return null;
    }

    // selecting goes through the flat map's shapes, so the list and the chips update as before
    function choose(n) {
      var shape = flat.querySelector('path[data-country="' + (window.CSS && CSS.escape ? CSS.escape(n) : n) + '"]');
      if (shape) shape.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    }
    world.addEventListener('click', function (e) {
      var el = e.target.closest && e.target.closest('[data-country]');
      if (!el) return;
      picked = el.dataset.country;
      if (el.classList.contains('chip')) turnTo(picked); else draw();
    });

    function turnTo(n) {
      if (!centre[n]) return;
      var from = rot.slice(), to = [-centre[n][0], -centre[n][1] * 0.8];
      var d = ((to[0] - from[0]) % 360 + 540) % 360 - 180;   // the short way round
      to[0] = from[0] + d;
      spin = false; idleAt = Date.now();
      if (still) { rot = to; draw(); return; }
      var t0 = performance.now();
      anim = function (now) {
        var t = Math.min(1, (now - t0) / 900), k = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        rot = [from[0] + (to[0] - from[0]) * k, from[1] + (to[1] - from[1]) * k];
        if (t === 1) anim = null;
      };
    }

    // dragging, with a little momentum
    var drag = null, vel = [0, 0];
    canvas.addEventListener('pointerdown', function (e) {
      drag = { x: e.clientX, y: e.clientY, sx: e.clientX, sy: e.clientY, moved: false };
      vel = [0, 0]; spin = false; anim = null;
      canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener('pointermove', function (e) {
      var b = canvas.getBoundingClientRect();
      if (drag) {
        var k = 90 / (size / 2), dx = e.clientX - drag.x, dy = e.clientY - drag.y;
        drag.x = e.clientX; drag.y = e.clientY;
        if (Math.abs(e.clientX - drag.sx) + Math.abs(e.clientY - drag.sy) > 4) drag.moved = true;
        vel = [dx * k, -dy * k];
        rot = [rot[0] + vel[0], Math.max(-75, Math.min(75, rot[1] + vel[1]))];
        tip.hidden = true;
        draw();
        return;
      }
      if (e.pointerType !== 'mouse') return;
      var n = countryAt(e.clientX - b.left, e.clientY - b.top);
      if (n !== hover) { hover = n; draw(); }
      canvas.style.cursor = n ? 'pointer' : 'grab';
      tip.hidden = !n;
      if (n) {
        tip.textContent = n + (stories[n] ? '' : ' · jeszcze tu nie byliśmy');
        tip.style.left = (e.clientX - b.left) + 'px';
        tip.style.top = (e.clientY - b.top) + 'px';
      }
    });
    canvas.addEventListener('pointerleave', function () { if (!drag && hover) { hover = null; tip.hidden = true; draw(); } });
    canvas.addEventListener('pointerup', function (e) {
      var b = canvas.getBoundingClientRect();
      if (drag && !drag.moved) {
        var n = countryAt(e.clientX - b.left, e.clientY - b.top);
        if (n) choose(n);
        vel = [0, 0];
      }
      drag = null; idleAt = Date.now();
      hint.classList.add('done');
    });
    canvas.addEventListener('pointercancel', function () { drag = null; idleAt = Date.now(); });

    canvas.addEventListener('keydown', function (e) {
      var step = { ArrowLeft: [-12, 0], ArrowRight: [12, 0], ArrowUp: [0, -10], ArrowDown: [0, 10] }[e.key];
      if (step) {
        e.preventDefault();
        spin = false; anim = null; idleAt = Date.now();
        rot = [rot[0] + step[0], Math.max(-75, Math.min(75, rot[1] + step[1]))];
        draw();
      } else if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        var n = countryAt(size / 2, size / 2);
        if (n) choose(n);
      }
    });

    // gentle spin until someone touches it; again after a while of nothing
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) { visible = es[0].isIntersecting; }).observe(canvas);
    }
    function frame(now) {
      if (visible) {
        if (anim) { anim(now); draw(); }
        else if (drag === null && (Math.abs(vel[0]) > 0.02 || Math.abs(vel[1]) > 0.02)) {
          vel = [vel[0] * 0.93, vel[1] * 0.93];
          rot = [rot[0] + vel[0], Math.max(-75, Math.min(75, rot[1] + vel[1]))];
          draw();
        } else if (!still && (spin || (!drag && idleAt && Date.now() - idleAt > 8000 && document.activeElement !== canvas))) {
          spin = true;
          rot[0] += 0.12;
          draw();
        }
      }
      requestAnimationFrame(frame);
    }

    function $$(sel, root) { return Array.prototype.slice.call(root.querySelectorAll(sel)); }
    window.addEventListener('resize', resize);
    resize();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(draw);
    requestAnimationFrame(frame);
  }
})();
