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

Black on white. The masthead uses the single-line wordmark (`img/wordmark.svg`, `img/wordmark-white.svg`, from the supplied Canva PDF); the plate logo (`img/logo.svg`, `img/logo-white.svg`) stays in the footer and favicon. Fine 1 px rules. Photos sit in simple coloured frames that cycle through four inks (mustard, vermilion, ultramarine, sage), with a soft shadow like pinned prints; burgundy is for the Old Polish band. The structure follows highly rated food and culture magazines:

- an issue line above the masthead and a numbered "W tym wydaniu" index beside a very large lead headline (NYT Cooking, The Gourmand);
- catalogue numbers on every story, `№ 001`, and recipes `P01` (Cereal);
- Monday / Wednesday / Sunday columns for the week's stories, staggered rather than in a flat row;
- a full-width band for the Old Polish series (Apartamento, Bon Appétit);
- a side-scrolling recipe rail.

After [kukbuk.pl](https://kukbuk.pl/), the layout is less regular:

- small uppercase labels set vertically beside the section headings and travel photos;
- "read more" drawn as a long line ending in an arrow;
- "Z podróży" as a sticky sage panel beside a zigzag list of stories;
- the newsletter as a full-width ultramarine block.

Type: Cormorant Garamond for headings, Instrument Sans for text.

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
- **Strona główna**: what the homepage shows and in what order: issue line, lead story, "W tym wydaniu", the week's three stories, the Old Polish band, published regions on the map, recipe rail, travel reports.

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
- Homepage: recipe filter chips, a schematic tile map of the 16 voivodeships linked to the region chips, newsletter form (Netlify Forms, so it collects sign-ups once deployed on Netlify).
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
