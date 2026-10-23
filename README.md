# Łowca Smaków — portal

Static website for **Łowca Smaków** (food anthropology: where what we eat comes from, and how to cook it), built from the portal wireframes (Design canvas *Łowca Smaków portal – wireframes*).

| Page | File |
|---|---|
| Homepage (desktop + mobile, responsive) | `index.html` (generated) |
| Articles (11) | `historie/*.html` (generated) |
| Recipes (4) | `przepisy/*.html` (generated) |
| Cook mode | `gotowanie.html?r=<recipe-slug>` |
| Not found | `404.html` |

`przepis.html` now redirects to `/przepisy/slimaki-w-szarym-sosie.html` (301 in `netlify.toml`).

## Look

The rules live at **`/styl/`** (not indexed), shown with the real components; build new sections from them.

- **Type:** Poppins for headings, Instrument Sans for text. Cormorant Garamond, the decorative face, only for numbers (counters, step numbers), quotes and the pale ghost words behind headings (italic). Sizes are tokens: `--fs-h1` … `--fs-label`.
- **Colour:** the four photo-frame inks (mustard, vermilion, ultramarine, sage) carry the colour and cycle from card to card. Vermilion as `--accent` is for actions only (buttons, links that do something). Section backgrounds are paper, one light panel (`--panel`) or one dark tone (`--dark`: menu, Old Polish band, newsletter, footer). Labels are neutral pills.
- **Two card types:** the photo card (title on the picture: homepage mosaic, recipes) and the framed card (text below: stories, shop, workshops, trips). Hovering a framed card turns its title the colour of its frame and zooms the photo slightly.
- **Homepage (8 sections):**
  1. lead mosaic
  2. new this week
  3. recipes
  4. Old Polish band
  5. maps (Poland and world as tabs)
  6. shop
  7. workshops and trips
  8. newsletter

  Each section uses one of two or three layout patterns. Pale "ghost" words sit only behind "Nowe w tym tygodniu", "Przepisy" and the listing-page titles.
- Masthead: the single-line wordmark (`img/wordmark.svg`). The plate logo (`img/logo.svg`) is used in the footer and favicon.

## Content

Content lives in `content/` as JSON, edited through the CMS (below) or by hand: `content/articles/*.json`, `content/recipes/*.json`, `content/settings/home.json`. Netlify regenerates the pages on every deploy; to do it yourself:

```sh
python3 scripts/build.py
```

All text is draft placeholder copy written to fit the topics; every article and recipe page says so on the page. Check facts, quantities and times before publishing.

No build step for the site itself: plain HTML, CSS (`css/style.css`) and JS (`js/`). Open `index.html`, or serve the folder:

```sh
python3 -m http.server 8000
```

## CMS (panel redakcji)

Editors work at **`/admin`** (Decap CMS, in Polish). Three sections:

- **Historie i reportaże**: articles. The body is built from blocks you can add, drag to reorder and remove: *Tekst* (blank line = new paragraph; `**bold**`, `*italic*`, `[link](https://…)`), *Śródtytuł*, *Cytat*, *Zdjęcie* (coloured frame or none), *Grafika* (SVG/PNG/JPG without a frame; text width, wide or small) and *Wideo z YouTube* (paste any YouTube link). An article can also have a YouTube video instead of its main photo.
- **Przepisy**: recipes with ingredients (amounts scale with the servings stepper; ml convert to glasses and spoons), steps with optional timer minutes, the "Historia w pigułce" box, shop teaser, sources and related stories.
- **Warsztaty**: cooking workshops and food-anthropology evenings (`content/workshops/`). Each has a page at `/warsztaty/<slug>.html` with price, facts, dates (past ones drop off by themselves), programme, what's included, related stories and a sign-up form; `/warsztaty/` lists them all with a made-to-order enquiry form; the first three appear on the homepage.
- **Wyprawy kulinarne**: culinary trips (`content/trips/`), pages at `/wyprawy/<slug>.html` with the day-by-day plan, what is and isn't included and a "Zapytaj o miejsce" form; `/wyprawy/` lists them. A trip's country is highlighted on the "Smaki świata" globe automatically.
- Sign-ups from every workshop and trip page (and the made-to-order forms) arrive in Netlify → Forms → **zapisy**, with the offer, date, name, e-mail, phone, number of people and message. The placeholder offers say on the page that dates, prices and programme are examples to confirm.
- **Strona główna → Warsztaty i wyprawy (teksty)**: the intros and the made-to-order texts.
- **Strona główna**: what the homepage shows and in what order: tagline, lead story, the two stories beside it, the week's three stories, the Old Polish band, published regions on the map, recipe rail, travel reports.

Photos and graphics: upload a file (stored in `img/uploads/`, resized on the fly by Netlify's image CDN) or paste a link (e.g. from Unsplash). Each has fields for the alt text and the photographer's credit, which appears in the page footer.

YouTube videos are privacy-friendly: the page shows a photo with a play button and loads the player from `youtube-nocookie.com` only when clicked.

Every save is a commit to `main` on GitHub; Netlify then runs `python3 scripts/build.py` (see `netlify.toml`) and publishes.

### One-time setup

1. **Automatic deploys**: Netlify must build from the GitHub repo (Project configuration → Build & deploy → Continuous deployment → linked to `kubajugo-alt/lowcasmakow`, branch `main`). Without it, CMS saves reach GitHub but not the live site.
2. **Login**: the CMS signs in with GitHub. Create a GitHub OAuth app (GitHub → Settings → Developer settings → OAuth Apps → New) with *Authorization callback URL* `https://api.netlify.com/auth/done`, then add its Client ID and secret in Netlify (Project configuration → Access & security → OAuth → Install provider → GitHub). Every editor needs a GitHub account with write access to the repo.

### Shop (Snipcart)

Spice mixes are products in the CMS (*Sklep: mieszanki przypraw*, `content/products/`). The build makes `/sklep/` (all mixes, filter by category), one page per mix at `/sklep/<slug>.html` (sizes, quantity, ingredients, how to use, its story, the recipes it goes with), a strip of four on the homepage, and a "Do koszyka" box on every recipe the mix is linked to.

The cart, checkout, payments, order e-mails, stock, shipping rates, discounts and taxes are [Snipcart](https://snipcart.com)'s. It runs on top of these pages: each "Do koszyka" button carries the product (`snipcart-add-item` with `data-item-*`; every size is listed with its price difference, so Snipcart can check the price of whichever size is in the cart). `js/snipcart.js` is Snipcart's official loader (v3.7.4 pinned in `build.py`); it loads on the first interaction, in Polish because the pages are `lang="pl"`, and the cart takes the site's colours from the CSS variables on `#snipcart`. `js/shop.js` connects the size picker and quantity on product pages to the button.

Links to the shop are worked out from links that already exist, so nothing needs maintaining by hand:

- a mix's "Pasuje do przepisów" and "Powiązane historie" put a "Ze spiżarni Łowcy" box on those recipes and stories, and on workshops and trips linked to them;
- a mix whose *Pochodzenie* starts with a country also appears on travel stories from that country (their *Miejsce*), on trips there, and in that country's list on the "Smaki świata" globe;
- the first Old Polish mix sits in the "Kuchnia staropolska" band on the homepage;
- the menu, the footer, the mobile chips, "Na skróty" and the 404 page link to `/sklep/`.

Until a key is set, the shop shows its products with "Wkrótce w sprzedaży" buttons and no Snipcart code loads.

To open the shop:

1. Create an account at snipcart.com.
2. In the dashboard:
   - **Domains & URLs**: add `lowca-smakow.netlify.app` (and the final domain later). Snipcart's crawler checks prices on the product pages, so it must be able to reach them.
   - **Regional settings**: currency PLN.
   - **Payment gateway**: Stripe for cards, Apple Pay and Google Pay, or Mollie to also take BLIK and Przelewy24.
   - **Shipping**: rates by weight. Every size has a weight with its packaging.
   - **Taxes**: VAT, if applicable.
   - **Notifications**: the e-mail address that gets new orders.
3. Copy **Account → API Keys → Public API key** into the CMS: *Strona główna → Sklep: ustawienia → Klucz Snipcart*. Save, and the next build turns the buttons into "Do koszyka" and adds the cart to the header.

Use Snipcart's test key and test payments first, then switch to the live key.

The product ID in Snipcart is the page address (`birria`, `staropolska`…). Once a mix has been sold, don't rename it.

## Editing locally

```sh
npx decap-server &                 # lets /admin edit the files on disk (no login)
python3 -m http.server 8765 &
open http://localhost:8765/admin/
python3 scripts/build.py --local   # rebuild after saving (--local: uploads without the image CDN)
```

## What works

- Header: sticky, burger menu below 1100 px, site search: typing shows the best matches from stories, recipes, workshops, trips and the shop, ignoring Polish accents; Enter opens `/szukaj/?q=…` with every result. The build writes the index to `js/search-index.json`, and `js/search.js` loads it on first use.
- Listing pages: `/historie/` (newest first, filter by section) and `/przepisy/` (filter by category); `?k=…` opens them filtered, which is what breadcrumbs use.
- "Nowe w tym tygodniu" shows the current week's dates (Monday–Sunday), recomputed in the browser so they're never stale.
- Search engines and link previews: every page has a canonical URL, Open Graph/Twitter tags and breadcrumbs. Structured data per page type:
  - Recipe on recipes;
  - Article on stories (plus VideoObject for episodes);
  - Event per workshop date;
  - Product once the shop is open.
  
  The build also writes `sitemap.xml` and `robots.txt`; the site address comes from Netlify's `URL`.
- "Wersja robocza" switch on stories, recipes, workshops and trips shows the "to be checked" note; switch it off once the content is verified.
- Homepage: recipe filter chips; a map of Poland with the 16 voivodeships (click, tap or Enter selects one, in step with the region chips; regions with a published episode are mustard with a pin); newsletter form (Netlify Forms, so it collects sign-ups once deployed on Netlify).
- Map outlines: GUGiK's register of boundaries (PRG) via [ppatrzyk/polska-geojson](https://github.com/ppatrzyk/polska-geojson), turned into SVG paths by `scripts/map-paths.py` (writes `scripts/wojewodztwa.json`, which the build reads). Regions with an episode are set in the CMS under *Strona główna → Smaki regionów*.
- "Smaki świata": a globe you can spin (drag, arrow keys; Enter picks the country in the middle). Countries with stories are mustard with pins; clicking one lists its stories and recipes; the country chips turn the globe to it. `js/globe.js` draws it on a canvas with d3-geo (self-hosted in `js/vendor/`, ISC licence) from `js/world-globe.json`, and loads only when the section is near the screen. Until then (or without JavaScript) a flat map shows instead (`scripts/swiat.json`, Equal Earth projection). Both come from Natural Earth 1:110m countries (public domain) via `scripts/map-paths.py world|globe`. Countries and their stories are set in the CMS under *Strona główna → Smaki świata*: one entry per article or recipe, and a country can have several.
- Recipe: ingredient checklist (remembered per browser), servings stepper, unit toggle, step timers, print layout, save (per browser) and share (Web Share API or copy link).
- Cook mode: one step per screen, progress bars, timer, ← / → keys, Screen Wake Lock ("Ekran nie wygaśnie" shows only when the lock is held).

## Still placeholders (from the wireframe)

The photos are placeholder stock from Unsplash (Unsplash License, loaded from `images.unsplash.com`, photographers credited in each page's footer), picked to match each story's topic. Swap them for the shoot's own photography. Still in `[square brackets]`: video lengths and the shop product. Footer pages (O nas, Współpraca, Kontakt, socials) point to `#`.

## Fonts

Cormorant Garamond, Instrument Sans and Poppins (SIL Open Font License) are served from this site, not from Google: `fonts/*.woff2` plus `css/fonts.css`, Latin and Latin Extended only (enough for Polish). Loading fonts from Google's servers sends visitors' IP addresses to Google, which EU courts have found to breach GDPR. Pages preload the two most used files (Poppins 700, Instrument Sans 400). To add a weight, fetch the Google Fonts CSS for it once and add its Latin and Latin Extended `@font-face` blocks and files the same way. The Canva export still links Google Fonts, because only Canva's importer reads it.

## Canva

`canva/index.html` is a self-contained copy of four pages (homepage, an article, a recipe, cook mode) for Canva's "import from URL", which ignores external stylesheets. Each page is rendered in a browser, then saved with the CSS inlined and absolute image links. Rebuild it after design changes, deploy, then re-import `https://lowca-smakow.netlify.app/canva/` in Canva:

```sh
python3 -m http.server 8765 &
NODE_PATH=$(npm root -g) node scripts/canva-export.js
```
