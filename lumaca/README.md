# Lumaca

The website of Lumaca (lumaca.eco): ready-made snail dishes from a small processing plant in Świętokrzyskie.
It runs on the same engine as Łowca Smaków (the rest of this repository): content in JSON, a Python build script that writes
static HTML, Decap CMS at `/admin`, Snipcart for the cart, Netlify Forms for the newsletter and enquiries.

Preview: https://lumaca-slimaki.netlify.app (Netlify project `lumaca-slimaki`).

## What the site is built on

The structure and wording follow the marketing plan ("Lumaca – plan marketingowy", section "Strona lumaca.eco: diagnoza i rekomendacje"):

- Menu: Sklep · Zestawy i prezenty · Przepisy · Nasza kuchnia · Gdzie spróbować · Dla gastronomii i firm. Terms, delivery and privacy are in the footer.
- Homepage, top to bottom: served dish + "Ślimaki gotowe do stołu" + "gotowe w 5 minut"; three bestsellers with prices; "Jak to podać" (three ways);
  occasions; the Christmas set; "Nasza kuchnia" (Grażyna, the forgotten Polish delicacy); press (shown once there is any); where to try; newsletter.
- Product page: dish name, served dish next to the jar, price and button, occasion, how to serve in 5 minutes, pairing, three ways,
  then weight and meat content, ingredients, allergens, storage.
- Shop: three categories (jars, sets, freeze-dried), square photos, no filters or sorting, everything in Polish.
- Gone: "Food & Beauty", "Snails Farm", "ecological", health claims, the "Dlaczego ślimaki" page, "tuszki", the vinegar jar and frozen meat.
  Old WordPress addresses redirect to the new pages (`netlify.toml`).
- Look: black and gold from the black label on warm linen; the black card with a gold double rule is the label.
  Lora for headings and dish names, Instrument Sans for text.
- Logo: the client's black-and-yellow badge (from lumaca.eco, `freepik_br_…png`) without the "Food & Beauty" line:
  `img/logo-badge.png` (round), `img/logo-yellow.png` (snail + name, header), `img/mark-yellow.png` (snail alone), favicons.
  The plan asks to confirm full rights to this logo before registering the trademark.

## Running it

    python3 scripts/build.py --local     # writes the pages; then serve this folder, e.g. python3 -m http.server

Netlify: base directory `lumaca`, build command `python3 scripts/build.py`, publish directory `.` (all in `netlify.toml`).

## CMS

`/admin` edits `lumaca/content/` in this repository (GitHub backend, branch main). Login needs the GitHub OAuth provider
installed on this Netlify project too (Project configuration → Access & security → OAuth), same as for Łowca Smaków.

Collections: products, recipes, events (calendar), places (where to buy), press, info pages, and settings
(contact and shop, homepage, "Nasza kuchnia", FAQ, B2B).

## Shop

Until a Snipcart public API key is set in the CMS (Ustawienia → Kontakt, sklep, dostawa), product buttons say "Zamów"
and open the contact form with the product filled in. With the key, they add to the Snipcart cart; payments
(BLIK, cards, fast transfers) come from the payment gateway connected in Snipcart.

## To confirm with the owners before going live

- Prices: jars at 49,90 zł (the plan's recommendation; the old shop had 44,90 zł), sets at 199 zł (4 jars) and 99 zł (2 jars).
- "Rocznik 2026" and the numbered Christmas series (a decision listed in the plan).
- One phone number for everything (the site uses +48 501 501 130).
- Allergens: molluscs on every jar; whether the court-bouillon contains celery and the wine sulphites.
- Photos: the jar and Lio photos are the real product shots with the new black label rendered on by AI (Higgsfield),
  i.e. mock-ups until the new labels are printed and photographed. Served dishes are cropped from the pro bono team's
  draft visuals; the owners' photo (Grażyna and Tomasz Nawroccy) is missing; occasions use Unsplash photos.
- Terms of sale and privacy policy texts (the old site had lorem ipsum).
- EN and FR versions (product names in three languages are on the B2B page for now).
