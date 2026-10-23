// Recipe content shared by przepis.html and gotowanie.html.
// Quantities, step texts and timer minutes are still to be written ([...] placeholders from the wireframe);
// a step's timer starts working as soon as `minutes` is a number.
window.RECIPE = {
  slug: 'slimaki-w-szarym-sosie',
  title: 'Ślimaki w szarym sosie piernikowym',
  servings: 4,
  ingredients: [
    { name: 'Ślimaki winniczki z hodowli', qty: '[ilość]' },
    { name: 'Cebula', qty: '[ilość]' },
    { name: 'Masło', qty: '[ilość]' },
    { name: 'Piernik, pokruszony', qty: '[ilość]' },
    { name: 'Czerwone wino', qty: '[ilość]' },
    { name: 'Ocet winny', qty: '[ilość]' },
    { name: 'Miód', qty: '[ilość]' },
    { name: 'Rodzynki', qty: '[ilość]' },
    { name: 'Migdały w płatkach', qty: '[ilość]' },
    { name: 'Bulion', qty: '[ilość]' },
    { name: 'Pieprz, imbir, goździki', qty: '[ilość]' }
  ],
  steps: [
    { title: 'Przygotuj ślimaki', timer: false, minutes: null, uses: ['Ślimaki winniczki'] },
    { title: 'Zeszklij cebulę na maśle', timer: true, minutes: null, uses: ['Cebula', 'Masło'] },
    { title: 'Zrób bazę sosu z wina, octu i bulionu', timer: true, minutes: null, uses: ['Czerwone wino', 'Ocet winny', 'Bulion'] },
    { title: 'Zagęść piernikiem, dodaj miód i bakalie', timer: false, minutes: null, uses: ['Piernik', 'Miód', 'Rodzynki', 'Migdały'] },
    { title: 'Duś ślimaki w sosie', timer: true, minutes: null, uses: ['Ślimaki winniczki'] },
    { title: 'Dopraw i podawaj', timer: false, minutes: null, uses: ['Pieprz, imbir, goździki'] }
  ],
  stepText: '[Opis kroku — uwspółcześniona wersja Czernieckiego, 2–4 zdania.]'
};

// Shared countdown: binds a button showing mm:ss; returns nothing if the step has no minutes yet.
window.bindTimer = function (btn, minutes, render) {
  if (typeof minutes !== 'number') {
    btn.disabled = true;
    btn.title = 'Czas do uzupełnienia';
    return;
  }
  var left = minutes * 60, id = null;
  function fmt(s) { return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); }
  render(fmt(left), false);
  btn.addEventListener('click', function () {
    if (id) { clearInterval(id); id = null; btn.dataset.running = 'false'; render(fmt(left), false); return; }
    if (left <= 0) left = minutes * 60;
    btn.dataset.running = 'true';
    render(fmt(left), true);
    id = setInterval(function () {
      left -= 1;
      render(fmt(left), true);
      if (left <= 0) {
        clearInterval(id); id = null; btn.dataset.running = 'false';
        render('Gotowe!', false);
        if (navigator.vibrate) navigator.vibrate([300, 150, 300]);
      }
    }, 1000);
  });
};

window.pluralPorcje = function (n) {
  var m10 = n % 10, m100 = n % 100;
  var w = n === 1 ? 'porcja' : (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) ? 'porcje' : 'porcji';
  return n + ' ' + w;
};
