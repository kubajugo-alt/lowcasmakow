# Łowca Smaków — portal

Static website for **Łowca Smaków** (food anthropology: where what we eat comes from, and how to cook it), built from the portal wireframes (Design canvas *Łowca Smaków portal – wireframes*).

| Page | File | Wireframe |
|---|---|---|
| Homepage (desktop + mobile, responsive) | `index.html` | Strona główna — desktop / mobile |
| Recipe | `przepis.html` | Przepis — desktop |
| Cook mode | `gotowanie.html` | Tryb gotowania — mobile |

No build step: plain HTML, CSS (`css/style.css`) and JS (`js/`). Open `index.html`, or serve the folder:

```sh
python3 -m http.server 8000
```

## What works

- Header: sticky, burger menu below 1100 px, search (filters the recipe grid; on other pages it goes to the homepage).
- Homepage: recipe filter chips, a schematic tile map of the 16 voivodeships linked to the region chips, newsletter form (Netlify Forms, so it collects sign-ups once deployed on Netlify).
- Recipe: ingredient checklist (remembered per browser), servings stepper, unit toggle, step timers, print layout, save (per browser) and share (Web Share API or copy link).
- Cook mode: one step per screen, progress bars, timer, ← / → keys, Screen Wake Lock ("Ekran nie wygaśnie" shows only when the lock is held).

## Still placeholders (from the wireframe)

Everything in `[square brackets]` and every hatched image block is waiting for real content: photos and video, article leads, quantities, step texts, times. Recipe content lives in `js/recipe-data.js`; a step's timer starts working as soon as its `minutes` is a number. Links to stories that don't exist yet point to `#`.
