// Lumaca: mobile menu, Netlify form posts without leaving the page, quantity stepper on product pages
(function () {
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  var btn = $('[data-menu]'), nav = $('#main-nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', String(open));
    });
  }

  // forms (newsletter, enquiries, contact) post to Netlify Forms; the thank-you text comes from data-ok
  $$('form[data-ajax]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var msg = $('[data-msg]', form), submit = $('button[type="submit"]', form);
      submit.disabled = true;
      fetch('/', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                   body: new URLSearchParams(new FormData(form)).toString() })
        .then(function (r) {
          if (!r.ok) throw new Error(r.status);
          msg.textContent = form.dataset.ok;
          form.reset();
        })
        .catch(function () { msg.textContent = 'Nie udało się wysłać. Napisz do nas: info@lumaca.eco'; })
        .then(function () { submit.disabled = false; });
    });
  });

  // ?zamowienie=… (from "Zamów" before the online shop opens) fills the contact form
  var order = new URLSearchParams(location.search).get('zamowienie');
  var field = $('form[name="kontakt"] [name="zamowienie"]');
  if (order && field) field.value = 'Zamówienie: ' + order;

  // product page: the quantity stepper sets how many jars the Snipcart button adds
  var product = $('[data-product]');
  var qty = product && $('#qty', product);
  if (qty) {
    var add = $('.snipcart-add-item', product);
    var set = function (n) {
      n = Math.max(1, Math.min(24, parseInt(n, 10) || 1));
      qty.value = n;
      if (add) add.setAttribute('data-item-quantity', String(n));
    };
    qty.addEventListener('input', function () { set(qty.value); });
    $$('[data-qty]', product).forEach(function (b) {
      b.addEventListener('click', function () { set((parseInt(qty.value, 10) || 1) + parseInt(b.dataset.qty, 10)); });
    });
  }
})();
