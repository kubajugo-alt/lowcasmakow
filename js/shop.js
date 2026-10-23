// Product page: the size picker and quantity stepper set what the Snipcart button adds to the cart
// (size → data-item-custom1-value and weight, quantity → data-item-quantity) and update the price shown.
(function () {
  var root = document.querySelector('[data-product]');
  if (!root) return;
  var btn = root.querySelector('.snipcart-add-item');
  var price = root.querySelector('[data-price]');
  var base = parseFloat(root.dataset.base);
  var qty = root.querySelector('#qty');

  function zl(x) { return x.toFixed(2).replace('.', ',').replace(',00', '') + ' zł'; }
  function update() {
    var size = root.querySelector('input[name="size"]:checked');
    var n = qty ? Math.max(1, Math.min(20, parseInt(qty.value, 10) || 1)) : 1;
    var each = base + (size ? parseFloat(size.dataset.delta) : 0);
    price.textContent = zl(each * n);
    if (!btn) return;
    if (size) {
      btn.setAttribute('data-item-custom1-value', size.value);
      btn.setAttribute('data-item-weight', size.dataset.weight);
    }
    btn.setAttribute('data-item-quantity', String(n));
  }
  root.querySelectorAll('input[name="size"]').forEach(function (r) { r.addEventListener('change', update); });
  if (qty) {
    qty.addEventListener('input', update);
    root.querySelectorAll('[data-qty]').forEach(function (b) {
      b.addEventListener('click', function () {
        qty.value = Math.max(1, Math.min(20, (parseInt(qty.value, 10) || 1) + parseInt(b.dataset.qty, 10)));
        update();
      });
    });
  }
  update();
})();
