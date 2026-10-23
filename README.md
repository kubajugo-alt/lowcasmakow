# Łowca Smaków — portal

Static website for **Łowca Smaków** (food anthropology: where what we eat comes from, and how to cook it), built from the portal wireframes (Design canvas *Łowca Smaków portal – wireframes*).

| Page | File |
|---|---|
| Homepage (desktop + mobile, responsive) | `index.html` |
| Articles (11) | `historie/*.html` (generated) |
| Recipes (4) | `przepisy/*.html` (generated) |
| Cook mode | `gotowanie.html?r=<recipe-slug>` |
| Not found | `404.html` |

`przepis.html` now redirects to `/przepisy/slimaki-w-szarym-sosie.html` (301 in `netlify.toml`).

## Content

Article copy lives in `scripts/content.py`, recipes (ingredients with scalable quantities, steps, timer minutes) in `js/recipes.js`. Regenerate the article and recipe pages after editing either:

```sh
python3 scripts/build.py
```

All text is draft placeholder copy written to fit the topics; every article and recipe page says so on the page. Check facts, quantities and times before publishing.

No build step for the site itself: plain HTML, CSS (`css/style.css`) and JS (`js/`). Open `index.html`, or serve the folder:

```sh
python3 -m http.server 8000
```

## What works

- Header: sticky, burger menu below 1100 px, search (filters the recipe grid; on other pages it goes to the homepage).
- Homepage: recipe filter chips, a schematic tile map of the 16 voivodeships linked to the region chips, newsletter form (Netlify Forms, so it collects sign-ups once deployed on Netlify).
- Recipe: ingredient checklist (remembered per browser), servings stepper, unit toggle, step timers, print layout, save (per browser) and share (Web Share API or copy link).
- Cook mode: one step per screen, progress bars, timer, ← / → keys, Screen Wake Lock ("Ekran nie wygaśnie" shows only when the lock is held).

## Still placeholders (from the wireframe)

The photos are placeholder stock from Unsplash (Unsplash License, loaded from `images.unsplash.com`, photographers credited in each page's footer), picked to match each story's topic. Swap them for the shoot's own photography. Still in `[square brackets]`: video lengths and the shop product. Footer pages (O nas, Współpraca, Kontakt, socials) point to `#`.
