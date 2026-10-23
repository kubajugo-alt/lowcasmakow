// Builds canva/index.html: one self-contained file for Canva's "import from URL".
// Each site page is rendered in a browser (scripts run, so recipe steps and ingredients are filled in),
// then saved as a fixed-width Canva page (data-document-role="page") with the CSS inlined,
// desktop rules only, and every image/link made absolute so Canva needs nothing else.
//
//   python3 -m http.server 8765 &   (from the repo root)
//   NODE_PATH=$(npm root -g) node scripts/canva-export.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const LOCAL = 'http://localhost:8765';
const LIVE = 'https://lowca-smakow.netlify.app';
const PAGES = [
  ['/index.html', 'Strona główna', 1440],
  ['/historie/dlaczego-kisimy-ogorki.html', 'Artykuł', 1440],
  ['/przepisy/slimaki-w-szarym-sosie.html', 'Przepis', 1440],
  ['/gotowanie.html?r=slimaki-w-szarym-sosie', 'Tryb gotowania', 560],
];

// Inline the stylesheet without phone/tablet rules (Canva's viewport width is unknown).
function desktopCss() {
  let css = fs.readFileSync(path.join(ROOT, 'css/style.css'), 'utf8');
  let out = '', i = 0;
  while (i < css.length) {
    const m = css.indexOf('@media', i);
    if (m === -1) { out += css.slice(i); break; }
    out += css.slice(i, m);
    let j = css.indexOf('{', m), depth = 1; j++;
    while (depth && j < css.length) { if (css[j] === '{') depth++; else if (css[j] === '}') depth--; j++; }
    i = j;
  }
  return out.replace(/url\(\//g, `url(${LIVE}/`);
}

(async () => {
  const browser = await chromium.launch();
  const sections = [];
  for (const [url, label, width] of PAGES) {
    const page = await browser.newPage({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    await page.goto(LOCAL + url, { waitUntil: 'networkidle' });
    const body = await page.evaluate(({ LIVE, cook }) => {
      const abs = (u) => (u && u.startsWith('/') ? LIVE + u : u);
      document.querySelectorAll('script, .skip, form.search-bar, .section-nav').forEach((n) => n.remove());
      document.querySelectorAll('img').forEach((img) => {
        const src = img.currentSrc || img.src;
        img.removeAttribute('srcset'); img.removeAttribute('sizes'); img.removeAttribute('loading');
        img.setAttribute('src', src.replace(/^http:\/\/localhost:8765/, LIVE).replace(/([?&](?:amp;)?w=)1800\b/, '$11200'));
      });
      document.querySelectorAll('a[href]').forEach((a) => a.setAttribute('href', abs(a.getAttribute('href'))));
      document.querySelectorAll('svg.draw').forEach((s) => s.classList.remove('draw'));
      const wrap = document.createElement('div');
      wrap.className = document.body.className + (cook ? ' cook' : '');
      wrap.innerHTML = document.body.innerHTML;
      return wrap.outerHTML;
    }, { LIVE, cook: url.startsWith('/gotowanie') });
    const bodyClass = await page.evaluate(() => document.body.className);
    sections.push(`<section data-document-role="page" data-label="${label}" class="canva-page ${bodyClass}" style="width:${width}px">\n${body}\n</section>`);
    await page.close();
  }
  await browser.close();

  const html = `<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex">
<title>Łowca Smaków — makiety do Canvy</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&amp;family=Instrument+Sans:wght@400;500;600&amp;display=swap" rel="stylesheet">
<style>
${desktopCss()}
/* Canva pages */
body{margin:0}
.canva-page{display:block;margin:0 auto 80px;overflow:hidden;background:var(--paper)}
.canva-page.cook,.canva-page .cook{background:var(--night)}
</style>
</head>
<body>
${sections.join('\n\n')}
</body>
</html>
`;
  fs.mkdirSync(path.join(ROOT, 'canva'), { recursive: true });
  fs.writeFileSync(path.join(ROOT, 'canva/index.html'), html);
  console.log('canva/index.html', (html.length / 1024).toFixed(0) + ' KB', sections.length + ' pages');
})();
