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

The masthead uses the single-line wordmark (`img/wordmark.svg`, `img/wordmark-white.svg`, from the supplied Canva PDF); the plate logo (`img/logo.svg`, `img/logo-white.svg`) stays in the footer and favicon. Four inks (mustard, vermilion, ultramarine, sage) plus burgundy for the Old Polish band.

After [alemeksyk.eu](https://www.alemeksyk.eu/):

- a vermilion menu bar under the masthead;
- the lead story in a photo mosaic with two more stories beside it, titles in white on the picture over a dark gradient;
- red tag pills from each story's section and kicker, and grey date pills (`№ 001`, `26.10.2026`);
- "Na skróty": round photo shortcuts to the sections, with counts;
- huge pale words behind each section title (`data-ghost` on the `h2`);
- recipes as rounded photo cards with the title on the picture;
- Poppins for headings, Instrument Sans for text, Cormorant Garamond kept for italic accents.

Kept from earlier rounds: photos with text below sit in simple coloured frames with a soft pinned-photo shadow; catalogue numbers `№ 001` / `P01`; staggered Monday / Wednesday / Sunday columns; "Z podróży" as a sticky sage panel beside a zigzag list (after [kukbuk.pl](https://kukbuk.pl/)); the newsletter as a full-width ultramarine block.

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
- **Strona główna**: what the homepage shows and in what order: issue line, lead story, the two stories beside it, the week's three stories, the Old Polish band, published regions on the map, recipe rail, travel reports.

Photos and graphics: upload a file (stored in `img/uploads/`, resized on the fly by Netlify's image CDN) or paste a link (e.g. from Unsplash). Each has fields for the alt text and the photographer's credit, which appears in the page footer.

YouTube videos are privacy-friendly: the page shows a photo with a play button and loads the player from `youtube-nocookie.com` only when clicked.

Every save is a commit to `main` on GitHub; Netlify then runs `python3 scripts/build.py` (see `netlify.toml`) and publishes.

### One-time setup

1. **Automatic deploys**: Netlify must build from the GitHub repo (Project configuration → Build & deploy → Continuous deployment → linked to `kubajugo-alt/lowcasmakow`, branch `main`). Without it, CMS saves reach GitHub but not the live site.
2. **Login**: the CMS signs in with GitHub. Create a GitHub OAuth app (GitHub → Settings → Developer settings → OAuth Apps → New) with *Authorization callback URL* `https://api.netlify.com/auth/done`, then add its Client ID and secret in Netlify (Project configuration → Access & security → OAuth → Install provider → GitHub). Every editor needs a GitHub account with write access to the repo.

### Editing locally

```sh
npx decap-server &                 # lets /admin edit the files on disk (no login)
python3 -m http.server 8765 &
open http://localhost:8765/admin/
python3 scripts/build.py --local   # rebuild after saving (--local: uploads without the image CDN)
```

## What works

- Header: sticky, burger menu below 1100 px, search (filters the recipe grid; on other pages it goes to the homepage).
- Homepage: recipe filter chips; a map of Poland with the 16 voivodeships (click, tap or Enter selects one, in step with the region chips; regions with a published episode are mustard with a pin); newsletter form (Netlify Forms, so it collects sign-ups once deployed on Netlify).
- Map outlines: GUGiK's register of boundaries (PRG) via [ppatrzyk/polska-geojson](https://github.com/ppatrzyk/polska-geojson), turned into SVG paths by `scripts/map-paths.py` (writes `scripts/wojewodztwa.json`, which the build reads). Regions with an episode are set in the CMS under *Strona główna → Smaki regionów*.
- "Smaki świata": a globe you can spin (drag, arrow keys; Enter picks the country in the middle). Countries with stories are mustard with pins; clicking one lists its stories and recipes; the country chips turn the globe to it. `js/globe.js` draws it on a canvas with d3-geo (self-hosted in `js/vendor/`, ISC licence) from `js/world-globe.json`, and loads only when the section is near the screen. Until then (or without JavaScript) a flat map shows instead (`scripts/swiat.json`, Equal Earth projection). Both come from Natural Earth 1:110m countries (public domain) via `scripts/map-paths.py world|globe`. Countries and their stories are set in the CMS under *Strona główna → Smaki świata*: one entry per article or recipe, and a country can have several.
- Recipe: ingredient checklist (remembered per browser), servings stepper, unit toggle, step timers, print layout, save (per browser) and share (Web Share API or copy link).
- Cook mode: one step per screen, progress bars, timer, ← / → keys, Screen Wake Lock ("Ekran nie wygaśnie" shows only when the lock is held).

## Still placeholders (from the wireframe)

The photos are placeholder stock from Unsplash (Unsplash License, loaded from `images.unsplash.com`, photographers credited in each page's footer), picked to match each story's topic. Swap them for the shoot's own photography. Still in `[square brackets]`: video lengths and the shop product. Footer pages (O nas, Współpraca, Kontakt, socials) point to `#`.

## Canva

`canva/index.html` is a self-contained copy of four pages (homepage, an article, a recipe, cook mode) for Canva's "import from URL", which ignores external stylesheets. Each page is rendered in a browser, then saved with the CSS inlined and absolute image links. Rebuild it after design changes, deploy, then re-import `https://lowca-smakow.netlify.app/canva/` in Canva:

```sh
python3 -m http.server 8765 &
NODE_PATH=$(npm root -g) node scripts/canva-export.js
```
