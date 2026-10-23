// All recipes, keyed by slug. Used by the recipe pages (przepisy/*.html) and cook mode (gotowanie.html?r=slug).
// Ingredient amounts: q = number for the base `servings` (scaled by the stepper), u = unit; q: null = "do smaku".
// A step's timer runs for `minutes`; timer: false hides it.
// Draft content: check quantities and times in the kitchen before publishing.
window.RECIPES = {
  'slimaki-w-szarym-sosie': {
    title: 'Ślimaki w szarym sosie piernikowym',
    servings: 4,
    ingredients: [
      { q: 24, u: 'szt.', n: 'Ślimaki winniczki z hodowli, oczyszczone i zblanszowane' },
      { q: 1, u: 'szt.', n: 'Cebula' },
      { q: 30, u: 'g', n: 'Masło' },
      { q: 60, u: 'g', n: 'Piernik, pokruszony' },
      { q: 250, u: 'ml', n: 'Czerwone wino, wytrawne' },
      { q: 30, u: 'ml', n: 'Ocet winny' },
      { q: 15, u: 'ml', n: 'Miód' },
      { q: 30, u: 'g', n: 'Rodzynki' },
      { q: 20, u: 'g', n: 'Migdały w płatkach' },
      { q: 250, u: 'ml', n: 'Bulion warzywny' },
      { q: null, u: '', n: 'Pieprz, imbir, 2 goździki' }
    ],
    steps: [
      { title: 'Przygotuj ślimaki', timer: false, uses: ['Ślimaki winniczki'],
        text: 'Ślimaki z hodowli kupisz już oczyszczone i zblanszowane, mrożone albo w zalewie. Rozmroź je w lodówce, przepłucz zimną wodą i osusz. Jeśli są w muszlach, wyjmij mięso wykałaczką, a muszle umyj: przydadzą się do podania.' },
      { title: 'Zeszklij cebulę na maśle', timer: true, minutes: 8, uses: ['Cebula', 'Masło'],
        text: 'Cebulę posiekaj drobno. W szerokim rondlu rozgrzej masło i duś cebulę na małym ogniu, aż będzie miękka i szklista, ale nie zrumieniona.' },
      { title: 'Zrób bazę sosu z wina, octu i bulionu', timer: true, minutes: 10, uses: ['Czerwone wino', 'Ocet winny', 'Bulion'],
        text: 'Wlej wino, ocet i bulion, dodaj szczyptę pieprzu i imbiru oraz dwa goździki. Gotuj bez przykrycia, aż płyn zredukuje się mniej więcej o jedną trzecią.' },
      { title: 'Zagęść piernikiem, dodaj miód i bakalie', timer: false, uses: ['Piernik', 'Miód', 'Rodzynki', 'Migdały'],
        text: 'Wyjmij goździki. Wsyp pokruszony piernik i mieszaj, aż się rozpuści, a sos zgęstnieje i nabierze szarobrązowego koloru. Dodaj miód, rodzynki i migdały.' },
      { title: 'Duś ślimaki w sosie', timer: true, minutes: 15, uses: ['Ślimaki winniczki'],
        text: 'Włóż ślimaki do sosu i duś pod przykryciem na bardzo małym ogniu, mieszając od czasu do czasu. Zbyt mocny ogień sprawi, że staną się gumowate.' },
      { title: 'Dopraw i podawaj', timer: false, uses: ['Pieprz, imbir'],
        text: 'Spróbuj i zrównoważ smak: odrobina octu, jeśli sos jest za słodki, łyżeczka miodu, jeśli za kwaśny. Podawaj w muszlach albo na grzance z ciemnego chleba.' }
    ]
  },

  'birria-tacos': {
    title: 'Birria tacos',
    servings: 4,
    ingredients: [
      { q: 1000, u: 'g', n: 'Pręga lub łopatka wołowa (tradycyjnie: koźlina)' },
      { q: 4, u: 'szt.', n: 'Suszone chile guajillo' },
      { q: 2, u: 'szt.', n: 'Suszone chile ancho' },
      { q: 2, u: 'szt.', n: 'Suszone chile de árbol' },
      { q: 2, u: 'szt.', n: 'Pomidory' },
      { q: 1, u: 'szt.', n: 'Cebula' },
      { q: 4, u: 'ząbki', n: 'Czosnek' },
      { q: 15, u: 'ml', n: 'Ocet jabłkowy' },
      { q: 1, u: 'łyżeczka', n: 'Kumin, oregano (najlepiej meksykańskie)' },
      { q: 1, u: 'szt.', n: 'Laska cynamonu i 2 liście laurowe' },
      { q: 1000, u: 'ml', n: 'Bulion wołowy' },
      { q: 12, u: 'szt.', n: 'Tortille kukurydziane' },
      { q: 150, u: 'g', n: 'Ser oaxaca lub mozzarella' },
      { q: null, u: '', n: 'Do podania: cebula, kolendra, limonka' }
    ],
    steps: [
      { title: 'Podpraż i namocz chile', timer: true, minutes: 20, uses: ['Chile guajillo', 'Chile ancho', 'Chile de árbol'],
        text: 'Usuń z papryczek ogonki i nasiona. Praż je kilkanaście sekund z każdej strony na suchej patelni, aż zapachną, a potem zalej gorącą wodą i odstaw do zmięknięcia.' },
      { title: 'Zblenduj marynatę', timer: false, uses: ['Pomidory', 'Cebula', 'Czosnek', 'Ocet', 'Kumin, oregano'],
        text: 'Zmiksuj odsączone chile z pomidorami, połową cebuli, czosnkiem, octem, kuminem, oregano i szklanką bulionu na gładką, ceglastoczerwoną pastę.' },
      { title: 'Obsmaż mięso', timer: false, uses: ['Wołowina'],
        text: 'Pokrój mięso na duże kawałki, posól i obsmaż partiami w garnku z grubym dnem, aż się zrumieni.' },
      { title: 'Duś w marynacie', timer: true, minutes: 180, uses: ['Marynata', 'Bulion', 'Cynamon, liście laurowe'],
        text: 'Zalej mięso marynatą i resztą bulionu, dodaj cynamon i liście laurowe. Duś pod przykryciem na małym ogniu, aż mięso będzie się rozpadać pod widelcem.' },
      { title: 'Rozdrobnij mięso, odbierz tłuszcz', timer: false, uses: ['Wołowina'],
        text: 'Wyjmij mięso i rozdrobnij je widelcami. Z powierzchni wywaru zbierz czerwony tłuszcz do miseczki. Wywar dopraw solą: to consommé do maczania.' },
      { title: 'Smaż tacos i podawaj', timer: true, minutes: 3, uses: ['Tortille', 'Ser', 'Cebula, kolendra, limonka'],
        text: 'Zanurz tortillę w tłuszczu, połóż na gorącej patelni, posyp serem i mięsem, złóż na pół i smaż z obu stron do chrupkości. Podawaj z miską consommé, cebulą, kolendrą i limonką.' }
    ]
  },

  'ogorki-kiszone': {
    title: 'Ogórki kiszone babci',
    servings: 2,
    servingsUnit: 'słoiki',
    ingredients: [
      { q: 1000, u: 'g', n: 'Ogórki gruntowe, małe i twarde' },
      { q: 1000, u: 'ml', n: 'Woda' },
      { q: 30, u: 'g', n: 'Sól kamienna niejodowana' },
      { q: 4, u: 'ząbki', n: 'Czosnek' },
      { q: 2, u: 'szt.', n: 'Baldachy kopru z nasionami' },
      { q: 1, u: 'szt.', n: 'Liść chrzanu i kawałek korzenia' },
      { q: 2, u: 'szt.', n: 'Liście wiśni lub dębu' },
      { q: null, u: '', n: 'Opcjonalnie: ziele angielskie, gorczyca' }
    ],
    steps: [
      { title: 'Namocz ogórki', timer: true, minutes: 120, uses: ['Ogórki'],
        text: 'Umyj ogórki szczoteczką i włóż na dwie godziny do bardzo zimnej wody. Dzięki temu po zakiszeniu zostaną chrupiące.' },
      { title: 'Przygotuj solankę', timer: false, uses: ['Woda', 'Sól'],
        text: 'Zagotuj wodę z solą i odstaw do wystudzenia. Sól musi być niejodowana: jod hamuje pracę bakterii fermentacji mlekowej.' },
      { title: 'Ułóż ogórki w słojach', timer: false, uses: ['Czosnek', 'Koper', 'Chrzan', 'Liście wiśni'],
        text: 'Na dno wyparzonych słoików włóż połowę kopru, czosnku i liści. Ułóż ogórki pionowo, ciasno, a na wierzch resztę przypraw i kawałek chrzanu.' },
      { title: 'Zalej solanką', timer: false, uses: ['Solanka'],
        text: 'Zalej ogórki letnią solanką tak, by były całkowicie przykryte. Wszystko, co wystaje ponad powierzchnię, może spleśnieć. Zakręć słoiki niezbyt mocno.' },
      { title: 'Poczekaj, aż zaczną pracować', timer: false, uses: [],
        text: 'Postaw słoiki w temperaturze pokojowej, najlepiej na talerzu. Po dniu, dwóch solanka zmętnieje i zacznie lekko musować: to znak, że fermentacja ruszyła. Małosolne są gotowe po 3 dniach.' },
      { title: 'Przenieś w chłód', timer: false, uses: [],
        text: 'Po 5–7 dniach przenieś słoiki do piwnicy lub lodówki. W chłodzie ogórki dokiszą się powoli i wytrzymają do wiosny.' }
    ]
  },

  'papa-a-la-huancaina': {
    title: 'Papa a la huancaína',
    servings: 4,
    ingredients: [
      { q: 1000, u: 'g', n: 'Ziemniaki o żółtym miąższu' },
      { q: 3, u: 'szt.', n: 'Papryczki ají amarillo (lub 2 łyżki pasty)' },
      { q: 200, u: 'g', n: 'Queso fresco (lub feta wymieszana z ricottą)' },
      { q: 120, u: 'ml', n: 'Mleko odparowane (skondensowane niesłodzone)' },
      { q: 4, u: 'szt.', n: 'Krakersy solone' },
      { q: 0.5, u: 'szt.', n: 'Cebula' },
      { q: 1, u: 'ząbek', n: 'Czosnek' },
      { q: 30, u: 'ml', n: 'Olej roślinny' },
      { q: 2, u: 'szt.', n: 'Jajka' },
      { q: null, u: '', n: 'Do podania: czarne oliwki, liście sałaty' }
    ],
    steps: [
      { title: 'Ugotuj ziemniaki', timer: true, minutes: 20, uses: ['Ziemniaki'],
        text: 'Ugotuj ziemniaki w mundurkach w osolonej wodzie, aż będą miękkie, ale nie rozpadające się. Ostudź i obierz.' },
      { title: 'Podsmaż ají, cebulę i czosnek', timer: true, minutes: 5, uses: ['Ají amarillo', 'Cebula', 'Czosnek', 'Olej'],
        text: 'Papryczki oczyść z nasion. Podsmaż je na oleju z pokrojoną cebulą i czosnkiem, aż zmiękną. Ostudź.' },
      { title: 'Zblenduj sos', timer: false, uses: ['Queso fresco', 'Mleko', 'Krakersy'],
        text: 'Zmiksuj podsmażone warzywa z serem, mlekiem i krakersami na gęsty, aksamitny, intensywnie żółty sos. Jeśli jest za gęsty, dolej odrobinę mleka.' },
      { title: 'Ugotuj jajka', timer: true, minutes: 10, uses: ['Jajka'],
        text: 'Ugotuj jajka na twardo, przelej zimną wodą, obierz i pokrój w ćwiartki.' },
      { title: 'Podawaj na zimno', timer: false, uses: ['Oliwki', 'Sałata'],
        text: 'Ułóż liście sałaty na półmisku, na nich grube plastry ziemniaków. Polej obficie sosem, udekoruj jajkiem i oliwkami. Podawaj schłodzone, jako przystawkę.' }
    ]
  }
};

// Shared countdown: binds a button showing mm:ss (or h:mm:ss); disabled when the step has no minutes.
window.bindTimer = function (btn, minutes, render) {
  if (typeof minutes !== 'number') {
    btn.disabled = true;
    btn.title = 'Czas do uzupełnienia';
    return;
  }
  var left = minutes * 60, id = null;
  function pad(n) { return String(n).padStart(2, '0'); }
  function fmt(s) {
    var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
    return (h ? h + ':' + pad(m) : pad(m)) + ':' + pad(sec);
  }
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

window.pluralPorcje = function (n, unit) {
  var m10 = n % 10, m100 = n % 100, few = m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14);
  if (unit === 'słoiki') return n + ' ' + (n === 1 ? 'słoik' : few ? 'słoiki' : 'słoików');
  return n + ' ' + (n === 1 ? 'porcja' : few ? 'porcje' : 'porcji');
};

// "250 ml" → scaled, rounded sensibly; metric or cups/spoons.
window.formatQty = function (ing, factor, cups) {
  if (ing.q === null) return 'do smaku';
  var q = ing.q * factor, u = ing.u;
  if (cups && u === 'ml') {
    if (q >= 125) { var g = Math.round(q / 250 * 4) / 4; return fmtNum(g) + ' szkl.'; }
    if (q >= 15) return fmtNum(Math.round(q / 15 * 2) / 2) + ' łyżki';
    return fmtNum(Math.round(q / 5 * 2) / 2) + ' łyżeczki';
  }
  if (u === 'g' || u === 'ml') {
    q = q >= 1000 ? Math.round(q / 50) * 50 : q >= 100 ? Math.round(q / 10) * 10 : Math.round(q);
    if (q >= 1000) return fmtNum(q / 1000) + (u === 'g' ? ' kg' : ' l');
    return q + ' ' + u;
  }
  q = Math.round(q * 2) / 2;
  return fmtNum(q) + (u ? ' ' + u : '');
  function fmtNum(x) { return String(x).replace('.', ',').replace(/,5$/, '½').replace(/^0½$/, '½').replace(/,25$/, '¼').replace(/,75$/, '¾'); }
};
