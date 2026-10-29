#!/usr/bin/env python3
"""Builds the Lumaca site from the CMS content in content/ (edited at /admin, or by hand).

    python3 scripts/build.py           # what Netlify runs on every deploy (base directory: lumaca/)
    python3 scripts/build.py --local   # uploaded images without Netlify's image CDN, for a local preview

Same engine as Łowca Smaków (../scripts/build.py): JSON in, static HTML out, Snipcart for the cart,
Netlify Forms for the newsletter and enquiries. Standard library only, Python 3.8+.
"""
import glob
import html
import json
import os
import re
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL = '--local' in sys.argv
# the public address: Netlify sets URL during its builds (it follows a custom domain once one is added)
SITE = (os.environ.get('URL') or 'https://lumaca-slimaki.netlify.app').rstrip('/')
e = html.escape


def load(folder, key='order'):
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'content', folder, '*.json'))):
        slug = os.path.splitext(os.path.basename(f))[0]
        out[slug] = json.load(open(f, encoding='utf-8'))
        out[slug]['slug'] = slug
    return dict(sorted(out.items(), key=lambda kv: kv[1].get(key) or 99))


def setting(name):
    return json.load(open(os.path.join(ROOT, 'content', 'settings', name + '.json'), encoding='utf-8'))


S = setting('site')
HOME = setting('home')
KITCHEN = setting('kuchnia')
FAQ = setting('faq')
B2B = setting('b2b')
PR = load('products')
R = load('recipes')
EV = load('events')
PL = load('places')
PRESS = dict(sorted(load('press', 'date').items(), key=lambda kv: kv[1].get('date') or '', reverse=True))
PAGES = load('pages')
ARTICLES = dict(sorted(load('articles').items(), key=lambda kv: kv[1].get('date') or '', reverse=True))
I18N = {lang: json.load(open(os.path.join(ROOT, 'content', 'i18n', lang + '.json'), encoding='utf-8')) for lang in ('en', 'fr')}
# the pages that exist in all three languages; everything else is Polish only
PATHS = {'home': {'pl': '/', 'en': '/en/', 'fr': '/fr/'},
         'shop': {'pl': '/sklep/', 'en': '/en/shop/', 'fr': '/fr/boutique/'},
         'how': {'pl': '/przepisy/', 'en': '/en/how-to-serve/', 'fr': '/fr/comment-servir/'},
         'kitchen': {'pl': '/nasza-kuchnia/', 'en': '/en/our-kitchen/', 'fr': '/fr/notre-cuisine/'},
         'trade': {'pl': '/dla-firm/', 'en': '/en/trade/', 'fr': '/fr/professionnels/'},
         'contact': {'pl': '/kontakt/', 'en': '/en/contact/', 'fr': '/fr/contact/'}}


def product_path(slug, lang='pl'):
    return {'pl': f'/sklep/{slug}.html', 'en': f'/en/shop/{slug}.html', 'fr': f'/fr/boutique/{slug}.html'}[lang]


ALTS = {}  # any page path → its versions in pl/en/fr
for _v in PATHS.values():
    for _p in _v.values():
        ALTS[_p] = _v
for _s in PR:
    _v = {lang: product_path(_s, lang) for lang in ('pl', 'en', 'fr')}
    for _p in _v.values():
        ALTS[_p] = _v
LANGS = {'pl': ('PL', 'Polski', 'pl_PL'), 'en': ('EN', 'English', 'en_GB'), 'fr': ('FR', 'Français', 'fr_FR')}


def lang_switch(lang, path):
    alts = ALTS.get(path, {})
    links = []
    for code, (short, name, _) in LANGS.items():
        href = alts.get(code) or PATHS['home'][code]
        cur = ' aria-current="true"' if code == lang else ''
        links.append(f'<a href="{href}" hreflang="{code}" lang="{code}" title="{name}"{cur}>{short}</a>')
    return '<nav class="lang" aria-label="Język / Language">' + ''.join(links) + '</nav>'


def hreflang(path):
    alts = ALTS.get(path)
    if not alts:
        return ''
    out = ''.join(f'<link rel="alternate" hreflang="{code}" href="{SITE}{p}">\n' for code, p in alts.items())
    return out + f'<link rel="alternate" hreflang="x-default" href="{SITE}{alts["pl"]}">\n'
# the cart and checkout are Snipcart's (https://snipcart.com); with no public API key set in the CMS
# the shop shows its products but the buttons say "coming soon" and no Snipcart code loads
SHOP_KEY = (S.get('snipcart_key') or '').strip()


def eur_rate():
    """EUR/PLN mid rate from the National Bank of Poland at build time; the CMS value if NBP can't be reached."""
    try:
        from urllib.request import urlopen
        with urlopen('https://api.nbp.pl/api/exchangerates/rates/a/eur/?format=json', timeout=6) as r:
            x = json.load(r)['rates'][0]
            return float(x['mid']), x['effectiveDate']
    except Exception:
        return float(S.get('eur_rate') or 4.3), S.get('eur_rate_date') or ''


EUR, EUR_DATE = eur_rate()
SNIPCART_VERSION = '3.7.4'
CATS = {'sloiki': 'Słoiki', 'zestawy': 'Zestawy', 'liofilizaty': 'Liofilizaty'}
UTM = 'utm_source=lumaca&utm_medium=referral'
OUT = []  # every page written, for the sitemap


# ---------- images and small helpers ----------

def img(image, sizes, eager=False, cls='fill', ratio=None):
    """<img> for a CMS image object {src, alt, credit, credit_url}.
    Unsplash photos get Unsplash's resizer, uploads get Netlify's image CDN (not for SVG)."""
    if not image or not image.get('src'):
        return ''
    src, alt = image['src'], e(image.get('alt') or '')
    load_ = 'fetchpriority="high"' if eager else 'loading="lazy"'
    if src.startswith('https://images.unsplash.com/'):
        base = src.split('?')[0] + '?auto=format&amp;fit=crop&amp;q=70'
        hh = (lambda w: f'&amp;h={round(w / ratio)}') if ratio else (lambda w: '')
        srcset = ', '.join(f'{base}&amp;w={w}{hh(w)} {w}w' for w in (480, 800, 1200, 1600))
        return f'<img class="{cls}" src="{base}&amp;w=1200{hh(1200)}" srcset="{srcset}" sizes="{sizes}" alt="{alt}" {load_} decoding="async">'
    if src.startswith('/') and not src.lower().endswith('.svg') and not LOCAL:
        cdn = lambda w: f'/.netlify/images?url={quote(src)}&amp;w={w}'
        srcset = ', '.join(f'{cdn(w)} {w}w' for w in (480, 800, 1200, 1600))
        return f'<img class="{cls}" src="{cdn(1200)}" srcset="{srcset}" sizes="{sizes}" alt="{alt}" {load_} decoding="async">'
    return f'<img class="{cls}" src="{e(src)}" alt="{alt}" {load_} decoding="async">'


def credits(images):
    seen, parts = [], []
    for im in images:
        if not im or not im.get('credit') or im['credit'] in seen:
            continue
        seen.append(im['credit'])
        url = im.get('credit_url') or ''
        if 'unsplash.com' in url:
            url += ('&' if '?' in url else '?') + UTM
        parts.append(f'<a href="{e(url)}">{e(im["credit"])}</a>' if url else e(im['credit']))
    if not parts:
        return ''
    return ('<p class="credits">Zdjęcia: ' + ', '.join(parts)
            + f' · <a href="{e("https://unsplash.com/?" + UTM)}">Unsplash</a></p>')


def md(text):
    """Tiny Markdown: paragraphs, ## headings, - lists, **bold**, [links](url)."""
    out = []
    for block in re.split(r'\n\s*\n', (text or '').strip()):
        def inline(s):
            s = e(s)
            s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
            return re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', s)
        if block.startswith('## '):
            out.append(f'<h2>{inline(block[3:])}</h2>')
        elif all(l.startswith('- ') for l in block.splitlines()):
            out.append('<ul>' + ''.join(f'<li>{inline(l[2:])}</li>' for l in block.splitlines()) + '</ul>')
        else:
            out.append(f'<p>{inline(block)}</p>')
    return '\n'.join(out)


def eur(x, lang):
    v = float(x) / EUR
    return f'€{v:.2f}' if lang == 'en' else f'{v:.2f}'.replace('.', ',') + '\u00a0€'


def rate_note(lang):
    y, m, d = (EUR_DATE or '----').split('-') if EUR_DATE else ('', '', '')
    date = f'{int(d)} {["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(m) - 1]} {y}' if lang == 'en' and EUR_DATE else (
        f'{d}/{m}/{y}' if EUR_DATE else '')
    return I18N[lang]['ui']['rate_note'].format(date=date, rate=f'{EUR:.4f}'.replace('.', ',') if lang == 'fr' else f'{EUR:.4f}')


def pln(x):
    x = float(x)
    return (f'{x:.2f}'.replace('.', ',').replace(',00', '')) + ' zł'


def tel(n):
    return re.sub(r'[^\d+]', '', n)


def full_name(p):
    return f'{p["kind"]} {p["title"]}' if p['kind'] == 'Ślimaki' else f'{p["title"]}: {p["kind"]}' if p['category'] != 'zestawy' else f'{p["title"]} · {p["kind"]}'


# ---------- search engines and link previews ----------

ORG = {'@type': ['Organization', 'LocalBusiness'], 'name': 'Lumaca', 'url': SITE + '/', 'logo': SITE + '/img/logo-badge.png',
       'email': S['email'], 'telephone': S['phone'], 'description': S['description'],
       'sameAs': [u for u in (S.get('facebook'), S.get('instagram')) if u],
       'address': {'@type': 'PostalAddress', 'streetAddress': 'ul. Miła', 'postalCode': '26-050', 'addressLocality': 'Kołomań',
                   'addressRegion': 'świętokrzyskie', 'addressCountry': 'PL'}}


def abs_image(image, w=1200, h=630):
    src = (image or {}).get('src', '')
    if src.startswith('https://images.unsplash.com/'):
        return src.split('?')[0] + f'?auto=format&fit=crop&w={w}&h={h}&q=75'
    return SITE + src if src.startswith('/') else src


def crumbs_ld(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': k + 1, 'name': name, 'item': SITE + path} for k, (name, path) in enumerate(items)]}


def ld_script(objs):
    return '\n'.join('<script type="application/ld+json">'
                     + json.dumps({'@context': 'https://schema.org', **o}, ensure_ascii=False).replace('</', '<\\/') + '</script>'
                     for o in objs)


def crumbs(items):
    parts = []
    for k, (name, path) in enumerate(items):
        last = k == len(items) - 1
        parts.append(f'<span aria-current="page">{e(name)}</span>' if last else f'<a href="{path}">{e(name)}</a>')
    return '<nav class="crumbs" aria-label="Ścieżka">' + '<span aria-hidden="true">/</span>'.join(parts) + '</nav>'


# ---------- page frame ----------

ICONS = {
    'facebook': ('Facebook', '<path d="M14 8h3V4h-3c-2.8 0-4.5 1.8-4.5 4.6V11H7v4h2.5v9h4v-9h3l.5-4h-3.5V9c0-.6.4-1 1-1z"/>'),
    'instagram': ('Instagram', '<rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="1.8"/>'
                  '<circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="17.4" cy="6.6" r="1.2"/>'),
}


def social():
    links = ''.join(f'<a href="{e(S[k])}" aria-label="{name}" title="{name}" rel="noopener" target="_blank">'
                    f'<svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="currentColor">{svg}</svg></a>'
                    for k, (name, svg) in ICONS.items() if S.get(k))
    return f'<p class="social">{links}</p>' if links else ''

CART = ('<button class="icon-btn snipcart-checkout" type="button" aria-label="Koszyk">'
        '<svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M5 8h14l-1.2 11.2a1 1 0 0 1-1 .8H7.2a1 1 0 0 1-1-.8z"/>'
        '<path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg><span class="snipcart-items-count" aria-hidden="true"></span></button>')
MENU = ('<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>')
NAV = [('Sklep', '/sklep/'), ('Zestawy i prezenty', '/zestawy/'), ('Przepisy', '/przepisy/'), ('Nasza kuchnia', '/nasza-kuchnia/'),
       ('Gdzie spróbować', '/gdzie-sprobowac/'), ('Dla gastronomii i firm', '/dla-firm/')]


def shell(title, desc, main, images=(), current=None, path='/', image=None, og_type='website', ld=(), body_class='', home=False):
    OUT.append(path)
    cur = ' aria-current="page"'
    nav = '\n'.join(f'      <a href="{h}"{cur if n == current else ""}>{n}</a>' for n, h in NAV)
    js = '<script src="/js/site.js" defer></script>'
    if SHOP_KEY:
        js += ('\n<script>window.SnipcartSettings = ' + json.dumps({'publicApiKey': SHOP_KEY, 'loadStrategy': 'on-user-interaction',
               'currency': 'pln', 'version': SNIPCART_VERSION, 'modalStyle': 'side'}) + ';</script>\n<script src="/js/snipcart.js"></script>')
    og_img = ''
    if image and image.get('src'):
        og_img = (f'<meta property="og:image" content="{e(abs_image(image))}">\n<meta property="og:image:width" content="1200">\n'
                  f'<meta property="og:image:height" content="630">\n')
    pages_nav = ''.join(f'<a href="/{s}/">{e(p["title"])}</a>' for s, p in PAGES.items())
    return f'''<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}{"" if home else " · Lumaca"}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#1B1A18">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:site_name" content="Lumaca">
<meta property="og:locale" content="pl_PL">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{path}">
{og_img}<meta name="twitter:card" content="summary_large_image">
{hreflang(path)}{ld_script(ld)}
<link rel="icon" href="/img/favicon-64.png" type="image/png">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<link rel="preload" href="/fonts/lora-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/instrument-sans-normal-400-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/css/fonts.css">
<link rel="stylesheet" href="/css/style.css">
</head>
<body class="{body_class}">
<a class="skip" href="#tresc">Przejdź do treści</a>
<header class="site-header">
  <div class="topbar"><div class="wrap">
    <span>{e(HOME.get("hero_badge", "").capitalize())} · darmowa dostawa od {pln(S["free_shipping_from"])}</span>
    <a href="tel:{tel(S["phone"])}">{e(S["phone"])}</a>
  </div></div>
  <div class="wrap bar">
    <a href="/" class="logo"><img src="/img/logo-yellow.png" alt="Lumaca" width="237" height="34"></a>
    <nav class="main-nav" id="main-nav" aria-label="Główne menu">
{nav}
    </nav>
    <div class="actions">
      {lang_switch('pl', path)}
      {CART if SHOP_KEY else ''}
      <button class="icon-btn menu-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="main-nav" data-menu>{MENU}</button>
    </div>
  </div>
</header>
<main id="tresc">
{main}
{newsletter()}
</main>
<footer class="site-footer">
  <div class="wrap foot">
    <div class="foot-brand">
      <img src="/img/logo-badge.png" alt="Lumaca" width="120" height="120" loading="lazy">
      <p>{e(S["description"])}</p>
    </div>
    <nav class="foot-col" aria-label="Sklep">
      <h2>Sklep</h2>{''.join(f'<a href="{h}">{n}</a>' for n, h in NAV)}
    </nav>
    <nav class="foot-col" aria-label="Informacje">
      <h2>Informacje</h2><a href="/nasza-kuchnia/#artykuly">Artykuły</a><a href="/przepisy/#faq">Pytania i odpowiedzi</a><a href="/w-mediach/">Lumaca w mediach</a>{pages_nav}<a href="/kontakt/">Kontakt</a>
    </nav>
    <div class="foot-col contact">
      <h2>Kontakt</h2>
      <a href="tel:{tel(S["phone"])}">{e(S["phone"])}</a><a href="mailto:{e(S["email"])}">{e(S["email"])}</a>
      <span>{e(S["address"])}</span><span>{e(S["hours"])}</span>{social()}
    </div>
  </div>
  <div class="wrap foot-meta">
    <p>© 2026 Lumaca · Przetwórnia ślimaków, weterynaryjny numer zakładu {e(S["vet_number"])}</p>
    {credits(images)}
  </div>
</footer>
{js}
</body>
</html>
'''


def newsletter():
    return f'''
<section class="newsletter" id="newsletter" aria-labelledby="h-nl">
  <div class="wrap nl">
    <div>
      <h2 id="h-nl">{e(S["newsletter_title"])}</h2>
      <p>{e(S["newsletter_text"])}</p>
    </div>
    <form class="nl-form" name="newsletter" method="POST" data-netlify="true" netlify-honeypot="bot-field" data-ajax data-ok="Dziękujemy! Sprawdź skrzynkę: wysłaliśmy przepis i kod na darmową dostawę.">
      <input type="hidden" name="form-name" value="newsletter">
      <p class="sr-only"><label>Nie wypełniaj <input name="bot-field" tabindex="-1"></label></p>
      <label for="nl-email" class="sr-only">Adres e-mail</label>
      <div class="nl-row">
        <input id="nl-email" name="email" type="email" required placeholder="twoj@email.pl" autocomplete="email">
        <button class="btn btn-gold" type="submit">Zapisz się</button>
      </div>
      <p class="form-msg" aria-live="polite" data-msg></p>
    </form>
  </div>
</section>'''


def write(path, text):
    dest = os.path.join(ROOT, path.lstrip('/'))
    if dest.endswith('/'):
        dest += 'index.html'
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(text)


# ---------- shop ----------

def buy_button(slug, p, cls='btn btn-ink', label='Do koszyka'):
    if not p.get('available', True):
        return f'<button type="button" class="{cls}" disabled>{e(p.get("badge") or "Chwilowo niedostępne")}</button>'
    if not SHOP_KEY:
        return f'<a class="{cls}" href="/kontakt/?zamowienie={quote(full_name(p))}">Zamów</a>'
    attrs = {'data-item-id': slug, 'data-item-name': full_name(p), 'data-item-price': f'{float(p["price"]):.2f}',
             'data-item-url': f'/sklep/{slug}.html', 'data-item-description': p.get('lead', ''),
             'data-item-image': abs_image(p.get('image'), 400, 400), 'data-item-categories': CATS.get(p['category'], ''),
             'data-item-weight': str(p.get('weight') or 450)}
    a = ' '.join(f'{k}="{e(v)}"' for k, v in attrs.items())
    return f'<button type="button" class="{cls} snipcart-add-item" {a}>{label}</button>'


def jar_photo(p, sizes, eager=False):
    if p.get('image', {}).get('src'):
        return img(p['image'], sizes, eager)
    return '<span class="soon"><img src="/img/mark-yellow.png" alt="" width="110" height="49"></span>'


def product_card(slug, p, sizes='(max-width:720px) 50vw, 25vw'):
    badge = f'<span class="badge">{e(p["badge"])}</span>' if p.get('badge') else ''
    return f'''<article class="product-card" style="--stripe:{e(p.get("stripe") or "#C9A35A")}">
  <a href="/sklep/{slug}.html" class="pc-photo" tabindex="-1" aria-hidden="true">{jar_photo(p, sizes)}{badge}</a>
  <div class="pc-body">
    <p class="kind">{e(p["kind"])}</p>
    <h3><a href="/sklep/{slug}.html">{e(p["title"])}</a></h3>
    <p class="pc-occ">{e(p.get("occasion", ""))}</p>
    <p class="pc-buy"><span class="price">{pln(p["price"])}</span>{buy_button(slug, p, "btn btn-ink btn-sm")}</p>
  </div>
</article>'''


def shop_page():
    groups = []
    for c, name in CATS.items():
        items = [(s, p) for s, p in PR.items() if p['category'] == c]
        if not items:
            continue
        groups.append(f'''
  <section class="sec" id="{c}" aria-labelledby="h-{c}">
    <h2 id="h-{c}" class="sec-title">{name}</h2>
    <div class="grid products">{"".join(product_card(s, p) for s, p in items)}</div>
  </section>''')
    notice = '' if SHOP_KEY else f'<p class="notice">{e(S["shop_notice"])} <a href="tel:{tel(S["phone"])}">{e(S["phone"])}</a> · <a href="mailto:{e(S["email"])}">{e(S["email"])}</a></p>'
    jump = ''.join(f'<a class="chip" href="#{c}">{n}</a>' for c, n in CATS.items() if any(p['category'] == c for p in PR.values()))
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Sklep', '/sklep/')])}
  <header class="page-head">
    <h1>Sklep</h1>
    <p class="lead">Gotowe dania ze ślimaków: każdy słoik to 250 g, w tym 100 g mięsa ślimaka. Podgrzej i podaj w 5 minut.</p>
    <nav class="chips" aria-label="Kategorie">{jump}</nav>
    {notice}
  </header>
  {"".join(groups)}
  {ship_box()}
</div>'''
    write('/sklep/', shell('Sklep: ślimaki w słoikach, zestawy, liofilizaty', 'Ślimaki w bulionie królewskim, w oleju cytrynowo-pietruszkowym, w zielonym pesto i w sosie pomidorowym. Zestawy na prezent. ' + S['shipping'],
                           main, [p['image'] for p in PR.values()], current='Sklep', path='/sklep/', image=HOME['hero_image'],
                           ld=[crumbs_ld([('Strona główna', '/'), ('Sklep', '/sklep/')])]))


def ship_box():
    return f'''<aside class="ship" aria-label="Dostawa i płatności">
    <div><h2>Dostawa</h2><p>{e(S["shipping"])}</p></div>
    <div><h2>Płatność</h2><p>{e(S["payments"])}</p></div>
    <div><h2>Zapisz się, zapłać mniej</h2><p>Darmowa dostawa pierwszego zamówienia dla zapisanych do <a href="#newsletter">newslettera</a>.</p></div>
  </aside>'''


def product_page(slug, p):
    name = full_name(p)
    recs = [r for r in p.get('recipes') or [] if r in R]
    ways = p.get('ways') or []
    ways_html = ''
    if ways:
        ways_html = '<section class="ways" aria-labelledby="h-ways"><h2 id="h-ways">Jak podać w 5 minut</h2><ol>' + ''.join(
            f'<li><h3>{e(w["title"])}</h3><p>{e(w["text"])}</p>'
            + (f'<a href="/przepisy/{w["recipe"]}.html">Przepis</a>' if w.get('recipe') in R else '') + '</li>' for w in ways) + '</ol></section>'
    facts = [('Waga netto', p.get('net_weight')), ('Skład', p.get('ingredients')), ('Alergeny', p.get('allergens')),
             ('Przechowywanie', p.get('storage')), ('Trwałość', p.get('shelf_life'))]
    facts_html = ''.join(f'<div><dt>{k}</dt><dd>{e(v)}</dd></div>' for k, v in facts if v)
    dish = p.get('dish_image') if p.get('dish_image', {}).get('src') and p.get('dish_image', {}).get('src') != p['image'].get('src') else None
    gallery = (f'<div class="pr-photos">' + (f'<figure class="dish">{img(dish, "(max-width:720px) 100vw, 40vw", True)}<figcaption>Podanie</figcaption></figure>' if dish else '')
               + f'<figure class="jar">{jar_photo(p, "(max-width:720px) 100vw, 30vw", not dish)}</figure></div>')
    video = ''
    if p.get('video'):
        video = f'<p><a class="btn btn-line" href="{e(p["video"])}">Zobacz wideo z przepisem</a></p>'
    rec_cards = ''.join(recipe_card(r) for r in recs)
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Sklep', '/sklep/'), (name, f'/sklep/{slug}.html')])}
  <article class="product" style="--stripe:{e(p.get("stripe") or "#C9A35A")}" data-product>
    {gallery}
    <div class="pr-info">
      <div class="label-card">
        <p class="kind">{e(p["kind"])}</p>
        <h1>{e(p["title"])}</h1>
        {f'<p class="badge-inline">{e(p["badge"])}</p>' if p.get('badge') else ''}
        <p class="pr-price">{pln(p["price"])}</p>
      </div>
      <p class="lead">{e(p["lead"])}</p>
      <div class="pr-buy">{qty_box(p)}{buy_button(slug, p, "btn btn-gold btn-buy")}</div>
      {'' if SHOP_KEY else f'<p class="notice small">{e(S["shop_notice"])}</p>'}
      <dl class="pr-quick">
        {f'<div><dt>Na okazję</dt><dd>{e(p["occasion"])}</dd></div>' if p.get('occasion') else ''}
        {f'<div><dt>Gotowe w 5 minut</dt><dd>{e(p["ready_in_5"])}</dd></div>' if p.get('ready_in_5') else ''}
        {f'<div><dt>Do tego</dt><dd>{e(p["pairing"])}</dd></div>' if p.get('pairing') else ''}
      </dl>
      {video}
    </div>
  </article>
  {ways_html}
  <section class="facts" aria-labelledby="h-facts"><h2 id="h-facts">Skład i informacje</h2><dl>{facts_html}</dl></section>
  {f'<section class="sec"><h2 class="sec-title">Przepisy z tym słoikiem</h2><div class="grid recipes">{rec_cards}</div></section>' if rec_cards else ''}
  {ship_box()}
</div>'''
    path = f'/sklep/{slug}.html'
    ld = [crumbs_ld([('Strona główna', '/'), ('Sklep', '/sklep/'), (name, path)])]
    if SHOP_KEY and p.get('image', {}).get('src'):
        ld.append({'@type': 'Product', 'name': name, 'description': p['lead'], 'sku': slug, 'image': [abs_image(p['image'], 1200, 1200)],
                   'brand': {'@type': 'Brand', 'name': 'Lumaca'}, 'category': CATS.get(p['category'], ''),
                   'offers': {'@type': 'Offer', 'price': f'{float(p["price"]):.2f}', 'priceCurrency': 'PLN', 'url': SITE + path,
                              'availability': 'https://schema.org/' + ('InStock' if p.get('available', True) else 'OutOfStock')}})
    images = [p['image'], dish] + [R[r]['image'] for r in recs]
    write(path, shell(name, p['lead'], main, images, current='Sklep', path=path, image=dish or p['image'], og_type='product', ld=ld,
                      body_class='product-page'))


def qty_box(p):
    if not (p.get('available', True) and SHOP_KEY):
        return ''
    return ('<div class="qty"><label for="qty">Ilość</label><div class="stepper"><button type="button" data-qty="-1" aria-label="Mniej">−</button>'
            '<input id="qty" type="number" min="1" max="24" value="1" inputmode="numeric"><button type="button" data-qty="1" aria-label="Więcej">+</button></div></div>')


# ---------- recipes ----------

def recipe_card(slug, sizes='(max-width:720px) 100vw, 33vw'):
    r = R[slug]
    return f'''<article class="recipe-card">
  <a href="/przepisy/{slug}.html" class="rc-photo" tabindex="-1" aria-hidden="true">{img(r["image"], sizes)}</a>
  <p class="kind">{e(r.get("way", ""))} · {e(r["time"])}</p>
  <h3><a href="/przepisy/{slug}.html">{e(r["title"])}</a></h3>
</article>'''


def recipe_page(slug, r):
    p = PR.get(r.get('product'))
    jar = ''
    if p:
        jar = f'''<aside class="jar-box">
      <a href="/sklep/{r["product"]}.html" class="jb-photo" tabindex="-1" aria-hidden="true">{jar_photo(p, "120px")}</a>
      <div><p class="kind">Z tego słoika</p><p class="jb-name"><a href="/sklep/{r["product"]}.html">{e(full_name(p))}</a></p><p class="price">{pln(p["price"])}</p></div>
      {buy_button(r["product"], p, "btn btn-gold btn-sm")}
    </aside>'''
    ingr = ''.join(f'<li>{e(i)}</li>' for i in r['ingredients'])
    steps = ''.join(f'<li>{e(s)}</li>' for s in r['steps'])
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Przepisy', '/przepisy/'), (r['title'], f'/przepisy/{slug}.html')])}
  <article class="recipe">
    <header class="recipe-head">
      <div>
        <p class="kind">{e(r.get("way", ""))}</p>
        <h1>{e(r["title"])}</h1>
        <p class="lead">{e(r["lead"])}</p>
        <ul class="meta-list"><li><strong>Czas:</strong> {e(r["time"])}</li><li><strong>Porcje:</strong> {e(r["serves"])}</li></ul>
      </div>
      <figure class="recipe-photo">{img(r["image"], "(max-width:720px) 100vw, 50vw", True)}</figure>
    </header>
    <div class="recipe-body">
      <section class="ingredients"><h2>Składniki</h2><ul>{ingr}</ul>{jar}</section>
      <section class="steps"><h2>Przygotowanie</h2><ol>{steps}</ol>
        {f'<p class="tip"><strong>Wskazówka:</strong> {e(r["tip"])}</p>' if r.get('tip') else ''}
        {f'<p class="tip"><strong>Do wina:</strong> {e(r["wine"])}</p>' if r.get('wine') else ''}
      </section>
    </div>
  </article>
</div>'''
    path = f'/przepisy/{slug}.html'
    m = re.match(r'(\d+)\s*min', r['time'])
    ld = [crumbs_ld([('Strona główna', '/'), ('Przepisy', '/przepisy/'), (r['title'], path)]),
          {'@type': 'Recipe', 'name': r['title'], 'description': r['lead'], 'image': [abs_image(r['image'], 1200, 900)],
           'author': {'@type': 'Organization', 'name': 'Lumaca'}, 'recipeYield': r['serves'], 'recipeCategory': 'Przystawka',
           'recipeCuisine': 'polska', 'recipeIngredient': r['ingredients'],
           'recipeInstructions': [{'@type': 'HowToStep', 'text': s} for s in r['steps']], **({'totalTime': f'PT{m.group(1)}M'} if m else {})}]
    write(path, shell(r['title'], r['lead'], main, [r['image']] + ([p['image']] if p else []), current='Przepisy', path=path,
                      image=r['image'], og_type='article', ld=ld))


def faq_html(hid='faq'):
    items = ''.join(f'<details><summary>{e(i["q"])}</summary><p>{e(i["a"])}</p></details>' for i in FAQ['items'])
    return f'<section class="faq" id="{hid}" aria-labelledby="h-{hid}"><h2 id="h-{hid}" class="sec-title">{e(FAQ["title"])}</h2>{items}</section>'


def faq_ld():
    return {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': i['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': i['a']}}
                                                for i in FAQ['items']]}


def three_ways():
    ways = [('Na grzance', 'grzanki-ze-slimakami'), ('Z makaronem', 'tagliatelle-ze-slimakami-w-pesto'), ('W babeczce', 'babeczki-ze-slimakami')]
    out = []
    for k, (t, slug) in enumerate(ways):
        r = R.get(slug)
        if not r:
            continue
        out.append(f'''<li class="way">
      <a href="/przepisy/{slug}.html" class="way-photo" tabindex="-1" aria-hidden="true">{img(r["image"], "(max-width:720px) 100vw, 33vw")}</a>
      <span class="step">{k + 1}</span>
      <h3><a href="/przepisy/{slug}.html">{t}</a></h3>
      <p>{e(r["lead"])}</p>
    </li>''')
    return '<ol class="three-ways">' + ''.join(out) + '</ol>'


def recipes_page():
    cards = ''.join(recipe_card(s) for s in R)
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Przepisy', '/przepisy/')])}
  <header class="page-head">
    <h1>Jak podać ślimaki</h1>
    <p class="lead">{e(HOME["how_text"])}</p>
  </header>
  {three_ways()}
  <section class="sec" aria-labelledby="h-all"><h2 id="h-all" class="sec-title">Wszystkie przepisy</h2><div class="grid recipes">{cards}</div></section>
  <section class="sec" aria-labelledby="h-read"><h2 id="h-read" class="sec-title">Czytaj też</h2><div class="grid recipes">{"".join(article_card(x) for x in list(ARTICLES)[:3])}</div></section>
  {faq_html()}
  <p class="more-link">Gdzie kupić słoiki i spróbować ślimaków na żywo? <a href="/gdzie-sprobowac/">Sklepy, jarmarki i warsztaty</a></p>
</div>'''
    write('/przepisy/', shell('Jak podać ślimaki: przepisy w 5 minut', 'Ślimaki na grzance, z makaronem i w babeczce: proste przepisy z gotowych słoików Lumaca, odpowiedzi na najczęstsze pytania i lista miejsc, gdzie można kupić słoiki.',
                              main, [r['image'] for r in R.values()], current='Przepisy', path='/przepisy/', image=R[next(iter(R))]['image'],
                              ld=[crumbs_ld([('Strona główna', '/'), ('Przepisy', '/przepisy/')]), faq_ld()]))


# ---------- the other pages ----------

def event_list():
    rows = ''.join(f'''<li class="event">
      <p class="when">{e(ev.get("when") or ev.get("date") or "")}</p>
      <div><p class="kind">{e(ev.get("kind", ""))}</p><h3>{f'<a href="{e(ev["url"])}">{e(ev["title"])}</a>' if ev.get('url') else e(ev["title"])}</h3>
      <p>{e(ev.get("place", ""))}{" · " + e(ev["city"]) if ev.get("city") and ev.get("city") != ev.get("place") else ""}</p><p class="muted">{e(ev.get("text", ""))}</p></div>
    </li>''' for ev in EV.values())
    return f'<ul class="events">{rows}</ul>'


def place_list():
    rows = ''.join(f'''<li class="place"><p class="kind">{e(pl.get("kind", ""))} · {e(pl.get("city", ""))}</p>
      <h3>{f'<a href="{e(pl["url"])}">{e(pl["name"])}</a>' if pl.get('url') else e(pl["name"])}</h3>
      {f'<p>{e(pl["address"])}</p>' if pl.get('address') else ''}<p class="muted">{e(pl.get("text", ""))}</p></li>''' for pl in PL.values())
    return f'<ul class="places">{rows}</ul>'


def where_page():
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Gdzie spróbować', '/gdzie-sprobowac/')])}
  <header class="page-head">
    <h1>Gdzie spróbować</h1>
    <p class="lead">Ślimaki najlepiej przekonują na żywo. Spotkaj nas na jarmarku albo warsztatach, kup słoik w sklepie w regionie albo odbierz zamówienie w przetwórni.</p>
  </header>
  <section class="sec" aria-labelledby="h-ev"><h2 id="h-ev" class="sec-title">Kalendarz: degustacje, jarmarki, warsztaty</h2>{event_list()}
    <p class="muted">Dokładne terminy wysyłamy w newsletterze.</p></section>
  <section class="sec" aria-labelledby="h-pl"><h2 id="h-pl" class="sec-title">Sklepy i odbiór osobisty</h2>{place_list()}
    <p class="more-link">Prowadzisz sklep, restaurację albo winnicę? <a href="/dla-firm/">Współpraca dla gastronomii i sklepów</a></p></section>
  <section class="band-dark lowca">
    <div><p class="kind">Warsztaty</p><h2>„Ślimaki od kuchni” z Łowcą Smaków</h2>
    <p>Łowca Smaków gotuje, Grażyna opowiada historię ślimaków w polskiej kuchni. W winnicach sandomierskich, sklepach z winem i szkołach gotowania.</p>
    <a class="btn btn-gold" href="{e(S["lowca_url"])}/warsztaty/">Warsztaty Łowcy Smaków</a></div>
  </section>
</div>'''
    write('/gdzie-sprobowac/', shell('Gdzie spróbować i kupić ślimaki Lumaca', 'Jarmarki z degustacją, warsztaty z Łowcą Smaków, sklepy w Sandomierzu i Szydłowie oraz odbiór osobisty w przetwórni w Kołomaniu.',
                                     main, current='Gdzie spróbować', path='/gdzie-sprobowac/',
                                     ld=[crumbs_ld([('Strona główna', '/'), ('Gdzie spróbować', '/gdzie-sprobowac/')])]))


def kitchen_page():
    K = KITCHEN
    story = ''.join(f'<li><span class="num">{k + 1}</span><h3>{e(s["title"])}</h3><p>{e(s["text"])}</p></li>' for k, s in enumerate(K['story']))
    facts = ''.join(f'<li><h3>{e(f["title"])}</h3><p>{e(f["text"])}</p></li>' for f in K['facts'])
    gphoto = img(K['grazyna_image'], '(max-width:720px) 100vw, 40vw') or '<div class="photo-todo"><img src="/img/mark-yellow.png" alt="" width="110" height="49"><p>Tu zdjęcie Grażyny i Tomasza w przetwórni</p></div>'
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Nasza kuchnia', '/nasza-kuchnia/')])}
  <header class="page-head">
    <h1>{e(K["title"])}</h1>
    <p class="lead">{e(K["lead"])}</p>
  </header>
  <section class="story" aria-labelledby="h-story"><h2 id="h-story" class="sec-title">Zapomniany polski przysmak</h2><ol>{story}</ol></section>
  <section class="person">
    <figure>{gphoto}</figure>
    <div class="label-card dark"><p class="kind">Właściciele</p><h2>{e(K["grazyna_title"])}</h2><p>{e(K["grazyna_text"])}</p></div>
  </section>
  <section class="sec" aria-labelledby="h-facts"><h2 id="h-facts" class="sec-title">{e(K["facts_title"])}</h2><ul class="fact-grid">{facts}</ul></section>
  <section class="sec" id="artykuly" aria-labelledby="h-arts">
    <div class="sec-head"><h2 id="h-arts" class="sec-title">Z naszej kuchni: artykuły</h2><a class="more" href="/artykuly/">Wszystkie artykuły</a></div>
    <p class="sec-lead">Jak podać ślimaki, gdzie je kupić, jakie wino do nich wybrać i skąd się wzięły na polskim stole.</p>
    <div class="grid recipes">{"".join(article_card(x) for x in ARTICLES)}</div>
  </section>
  <section class="band-dark lowca">
    <div><p class="kind">Łowca Smaków</p><h2>{e(K["lowca_title"])}</h2><p>{e(K["lowca_text"])}</p>
    <a class="btn btn-gold" href="{e(K["lowca_url"])}">Ślimaki według Czernieckiego</a></div>
  </section>
</div>'''
    write('/nasza-kuchnia/', shell('Nasza kuchnia: zapomniany polski przysmak', K['lead'], main, [K['grazyna_image']], current='Nasza kuchnia',
                                   path='/nasza-kuchnia/', image=HOME['kitchen_image'],
                                   ld=[crumbs_ld([('Strona główna', '/'), ('Nasza kuchnia', '/nasza-kuchnia/')]), ORG]))


def form(name, fields, cta, ok, extra='<input type="hidden" name="jezyk" value="pl">', err='Nie udało się wysłać. Napisz do nas: info@lumaca.eco'):
    rows = []
    for f in fields:
        kind, fid, label = f[0], f[1], f[2]
        req = ' required' if (len(f) > 3 and f[3]) else ''
        if kind == 'textarea':
            rows.append(f'<label class="field wide"><span>{label}</span><textarea name="{fid}" rows="4"{req}></textarea></label>')
        elif kind == 'select':
            opts = ''.join(f'<option>{e(o)}</option>' for o in f[4])
            rows.append(f'<label class="field"><span>{label}</span><select name="{fid}"{req}>{opts}</select></label>')
        else:
            rows.append(f'<label class="field"><span>{label}</span><input type="{kind}" name="{fid}"{req}></label>')
    return f'''<form class="form" name="{name}" method="POST" data-netlify="true" netlify-honeypot="bot-field" data-ajax data-ok="{e(ok)}" data-err="{e(err)}">
      <input type="hidden" name="form-name" value="{name}">{extra}
      <p class="sr-only"><label>Nie wypełniaj <input name="bot-field" tabindex="-1"></label></p>
      <div class="fields">{"".join(rows)}</div>
      <button class="btn btn-gold" type="submit">{cta}</button>
      <p class="form-msg" aria-live="polite" data-msg></p>
    </form>'''


def b2b_page():
    B = B2B
    seg = ''.join(f'<li><h3>{e(s["title"])}</h3><p>{e(s["text"])}</p></li>' for s in B['segments'])
    facts = ''.join(f'<div><dt>{e(f["k"])}</dt><dd>{e(f["v"])}</dd></div>' for f in B['facts'])
    names = ''.join(f'<tr><td>{e(full_name(p))}</td><td lang="en">{e(p["name_en"])}</td><td lang="fr">{e(p["name_fr"])}</td></tr>'
                    for p in PR.values() if p.get('name_en'))
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Dla gastronomii i firm', '/dla-firm/')])}
  <header class="page-head">
    <h1>{e(B["title"])}</h1>
    <p class="lead">{e(B["lead"])}</p>
    <p><a class="btn btn-gold" href="#zapytanie">Zapytaj o ofertę</a></p>
  </header>
  <section class="sec" aria-labelledby="h-seg"><h2 id="h-seg" class="sec-title">Dla kogo</h2><ul class="fact-grid">{seg}</ul></section>
  <section class="facts" aria-labelledby="h-tech"><h2 id="h-tech">Karta techniczna w skrócie</h2><dl>{facts}</dl><p class="muted">{e(B["docs_text"])}</p></section>
  <section class="band-dark"><div><p class="kind">Program</p><h2>{e(B["chefs_title"])}</h2><p>{e(B["chefs_text"])}</p></div></section>
  <section class="sec" aria-labelledby="h-names"><h2 id="h-names" class="sec-title">Nazwy produktów: PL · EN · FR</h2>
    <div class="table-wrap"><table class="names"><thead><tr><th>Polski</th><th>English</th><th>Français</th></tr></thead><tbody>{names}</tbody></table></div></section>
  <section class="sec enquiry" id="zapytanie" aria-labelledby="h-form"><h2 id="h-form" class="sec-title">Zapytanie o ofertę</h2>
    <p>Odpowiadamy w ciągu dwóch dni roboczych. Chętnie przyjedziemy z degustacją.</p>
    {form("zapytanie-b2b", [("text", "firma", "Firma", True), ("select", "rodzaj", "Rodzaj działalności", True, ["Restauracja lub bar winny", "Sklep lub delikatesy", "Winnica", "Hotel", "Catering lub eventy", "Prezenty firmowe", "Dystrybutor lub eksport", "Inne"]),
          ("text", "miasto", "Miasto", False), ("text", "osoba", "Imię i nazwisko", True), ("email", "email", "E-mail", True), ("tel", "telefon", "Telefon", False),
          ("textarea", "wiadomosc", "Czego szukasz?", False)], "Wyślij zapytanie", "Dziękujemy! Odezwiemy się w ciągu dwóch dni roboczych.")}
  </section>
</div>'''
    write('/dla-firm/', shell('Dla gastronomii, sklepów i firm', B['lead'], main, current='Dla gastronomii i firm', path='/dla-firm/',
                              ld=[crumbs_ld([('Strona główna', '/'), ('Dla gastronomii i firm', '/dla-firm/')])]))


def sets_page():
    sets = [(s, p) for s, p in PR.items() if p['category'] == 'zestawy']
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Zestawy i prezenty', '/zestawy/')])}
  <header class="page-head">
    <h1>Zestawy i prezenty</h1>
    <p class="lead">Ślimaki to prezent, którego nikt się nie spodziewa, a każdy chce spróbować. W każdym zestawie karta z przepisami „3 sposoby w 5 minut”.</p>
  </header>
  <div class="grid products two">{"".join(product_card(s, p, "(max-width:720px) 100vw, 50vw") for s, p in sets)}</div>
  <section class="sec enquiry" id="firmy" aria-labelledby="h-gift"><h2 id="h-gift" class="sec-title">Prezenty firmowe</h2>
    <p>Zestawy dla klientów i pracowników z limitowanej serii rocznika 2026. Przy większych zamówieniach dołączymy kartkę z Twoim logo i życzeniami.</p>
    {form("prezenty-firmowe", [("text", "firma", "Firma", True), ("text", "osoba", "Imię i nazwisko", True), ("email", "email", "E-mail", True), ("tel", "telefon", "Telefon", False),
          ("number", "liczba", "Ile zestawów?", False), ("textarea", "wiadomosc", "Termin i szczegóły", False)], "Zapytaj o prezenty", "Dziękujemy! Wyślemy ofertę w ciągu dwóch dni roboczych.")}
  </section>
</div>'''
    write('/zestawy/', shell('Zestawy i prezenty ze ślimakami', 'Zestaw świąteczny z limitowanej serii i zestaw na wieczór z winem. Prezenty firmowe na zamówienie.',
                             main, [p['image'] for s, p in sets], current='Zestawy i prezenty', path='/zestawy/',
                             image=sets[0][1]['image'] if sets else None, ld=[crumbs_ld([('Strona główna', '/'), ('Zestawy i prezenty', '/zestawy/')])]))


def press_page():
    def press_item(x):
        title = e(x['title'])
        if x.get('url'):
            title = f'<a href="{e(x["url"])}">{title}</a>'
        return f'<li><p class="kind">{e(x.get("outlet", ""))} · {e(x.get("date", ""))}</p><h3>{title}</h3></li>'
    items = ''.join(press_item(x) for x in PRESS.values() if x.get('title'))
    story = ''.join(f'<li>{e(s["title"])}. {e(s["text"])}</li>' for s in KITCHEN['story'])
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Lumaca w mediach', '/w-mediach/')])}
  <header class="page-head">
    <h1>Lumaca w mediach</h1>
    <p class="lead">Zapomniany polski przysmak wraca na stół. Dla dziennikarzy: historia, bohaterka, zdjęcia dań i przetwórni, przepisy i fragmenty wideo Łowcy Smaków.</p>
  </header>
  <section class="sec"><h2 class="sec-title">Publikacje</h2>{f'<ul class="press">{items}</ul>' if items else '<p class="muted">Pierwsze publikacje pojawią się tu wkrótce.</p>'}</section>
  <section class="sec"><h2 class="sec-title">Historia w trzech zdaniach</h2><ol class="plain">{story}</ol></section>
  <section class="band-dark"><div><p class="kind">Pakiet medialny</p><h2>Porozmawiaj z Grażyną Nawrocką</h2>
    <p>Wyślemy komunikat, biogram i zdjęcia Grażyny i Tomasza Nawrockich, teczkę faktów, trzy przepisy i zdjęcia dań. Zestaw degustacyjny dla redakcji na życzenie.</p>
    <a class="btn btn-gold" href="mailto:{e(S["email"])}?subject=Media">{e(S["email"])}</a></div></section>
</div>'''
    write('/w-mediach/', shell('Lumaca w mediach', 'Publikacje o Lumace i pakiet medialny: zapomniany polski przysmak wraca na stół.', main, path='/w-mediach/',
                               ld=[crumbs_ld([('Strona główna', '/'), ('Lumaca w mediach', '/w-mediach/')])]))


def contact_page():
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Kontakt', '/kontakt/')])}
  <header class="page-head"><h1>Kontakt</h1><p class="lead">Zamówienia, pytania o ślimaki, współpraca. Odpowiadamy w dni robocze.</p></header>
  <div class="contact-grid">
    <div class="label-card dark">
      <p class="kind">Przetwórnia Lumaca</p>
      <p class="big"><a href="tel:{tel(S["phone"])}">{e(S["phone"])}</a></p>
      <p class="big"><a href="mailto:{e(S["email"])}">{e(S["email"])}</a></p>
      <p>{e(S["address"])}<br>{e(S["region"])}</p>
      <p>{e(S["hours"])}</p>
      <p><a href="https://www.google.com/maps/search/?api=1&amp;query={quote(S["address"])}">Jak dojechać (Mapy Google)</a></p>
      {social()}
    </div>
    {form("kontakt", [("text", "imie", "Imię", True), ("email", "email", "E-mail", True), ("tel", "telefon", "Telefon", False), ("text", "zamowienie", "Dotyczy", False),
          ("textarea", "wiadomosc", "Wiadomość", True)], "Wyślij", "Dziękujemy! Odpowiemy najszybciej, jak to możliwe.")}
  </div>
</div>'''
    write('/kontakt/', shell('Kontakt', f'Lumaca, przetwórnia ślimaków. {S["address"]}. Tel. {S["phone"]}, {S["email"]}.', main, path='/kontakt/',
                             ld=[crumbs_ld([('Strona główna', '/'), ('Kontakt', '/kontakt/')]), ORG]))


def plain_pages():
    for slug, p in PAGES.items():
        main = f'''
<div class="wrap narrow">
  {crumbs([('Strona główna', '/'), (p['title'], f'/{slug}/')])}
  <header class="page-head"><h1>{e(p["title"])}</h1></header>
  <div class="prose">{md(p.get("body", ""))}</div>
</div>'''
        write(f'/{slug}/', shell(p['title'], f'{p["title"]}: Lumaca, sklep ze ślimakami w słoikach.', main, path=f'/{slug}/'))


def home_page():
    H = HOME
    best = [(s, p) for s, p in PR.items() if p.get('bestseller')][:3]
    occ = ''.join(f'''<li class="occ"><a href="{e(o["link"])}"><span class="occ-photo">{img(o["image"], "(max-width:720px) 50vw, 25vw", ratio=0.8)}</span>
      <span class="occ-t">{e(o["title"])}</span><span class="occ-x">{e(o["text"])}</span></a></li>''' for o in H['occasions'])
    sets = [(s, p) for s, p in PR.items() if p['category'] == 'zestawy'][:1]
    set_band = ''
    if sets:
        s, p = sets[0]
        set_band = f'''
<section class="set-band" aria-labelledby="h-set">
  <div class="wrap set-grid">
    <figure>{img(p["image"], "(max-width:720px) 100vw, 50vw")}</figure>
    <div class="label-card dark">
      <p class="kind">{e(p["kind"])}{" · " + e(p["badge"]) if p.get("badge") else ""}</p>
      <h2 id="h-set">{e(p["title"])}</h2>
      <p>{e(p["lead"])}</p>
      <p class="pr-price">{pln(p["price"])}</p>
      <p class="btns"><a class="btn btn-gold" href="/sklep/{s}.html">Zobacz zestaw</a> <a class="btn btn-line-light" href="/zestawy/">Wszystkie zestawy i prezenty firmowe</a></p>
    </div>
  </div>
</section>'''
    press = list(PRESS.values())[:4]
    press_html = ''
    if press:
        press_html = '<section class="wrap sec"><h2 class="sec-title">Piszą o nas</h2><ul class="press">' + ''.join(
            f'<li><p class="kind">{e(x.get("outlet", ""))}</p><h3>{e(x["title"])}</h3></li>' for x in press) + '</ul></section>'
    main = f'''
<section class="hero" aria-labelledby="h-hero">
  <figure class="hero-photo">{img(H["hero_image"], "100vw", True)}</figure>
  <div class="wrap hero-in">
    <div class="label-card hero-card">
      <img class="hero-mark" src="/img/mark-yellow.png" alt="" width="90" height="40">
      <h1 id="h-hero">{e(H["hero_title"])}</h1>
      <p class="hero-badge">{e(H["hero_badge"])}</p>
      <p>{e(H["hero_text"])}</p>
      <p class="btns"><a class="btn btn-gold" href="/sklep/">Do sklepu</a> <a class="btn btn-line-light" href="/zestawy/">Zestawy na prezent</a></p>
    </div>
  </div>
</section>

<section class="wrap sec" aria-labelledby="h-best">
  <div class="sec-head"><h2 id="h-best" class="sec-title">{e(H["bestsellers_title"])}</h2><a class="more" href="/sklep/">Wszystkie produkty</a></div>
  <div class="grid products three">{"".join(product_card(s, p, "(max-width:720px) 100vw, 33vw") for s, p in best)}</div>
</section>

<section class="wrap sec" aria-labelledby="h-how">
  <div class="sec-head"><h2 id="h-how" class="sec-title">{e(H["how_title"])}</h2><a class="more" href="/przepisy/">Wszystkie przepisy</a></div>
  <p class="sec-lead">{e(H["how_text"])}</p>
  {three_ways()}
</section>

<section class="wrap sec" aria-labelledby="h-occ">
  <h2 id="h-occ" class="sec-title">{e(H["occasions_title"])}</h2>
  <ul class="occasions">{occ}</ul>
</section>
{set_band}
<section class="wrap sec kitchen" aria-labelledby="h-kit">
  <figure>{img(H["kitchen_image"], "(max-width:720px) 100vw, 50vw")}</figure>
  <div>
    <p class="kind">Zapomniany polski przysmak</p>
    <h2 id="h-kit" class="sec-title">{e(H["kitchen_title"])}</h2>
    <p>{e(H["kitchen_text"])}</p>
    <ol class="plain small">{"".join(f'<li>{e(s["title"])}.</li>' for s in KITCHEN["story"])}</ol>
    <p class="btns"><a class="btn btn-ink" href="/nasza-kuchnia/">Poznaj naszą historię</a> <a class="btn btn-line" href="/nasza-kuchnia/#artykuly">Artykuły i poradniki</a></p>
  </div>
</section>
{press_html}
<section class="wrap sec" aria-labelledby="h-art">
  <div class="sec-head"><h2 id="h-art" class="sec-title">Z naszej kuchni</h2><a class="more" href="/nasza-kuchnia/#artykuly">Więcej w Naszej kuchni</a></div>
  <div class="grid recipes">{"".join(article_card(x) for x in list(ARTICLES)[:3])}</div>
</section>
<section class="wrap sec" aria-labelledby="h-where">
  <div class="sec-head"><h2 id="h-where" class="sec-title">{e(H["where_title"])}</h2><a class="more" href="/gdzie-sprobowac/">Kalendarz i sklepy</a></div>
  <div class="where-grid">{event_list()}{place_list()}</div>
</section>'''
    images = [H['hero_image']] + [p['image'] for s, p in best] + [o['image'] for o in H['occasions']] + [H['kitchen_image']] + [R[r]['image'] for r in R]
    write('/', shell('Lumaca: ślimaki gotowe do stołu', S['description'], main, images, path='/', image=H['hero_image'], home=True,
                     body_class='home', ld=[ORG, {'@type': 'WebSite', 'name': 'Lumaca', 'url': SITE + '/'}]))


def not_found():
    main = '''
<div class="wrap narrow nf">
  <img src="/img/logo-badge.png" alt="" width="160" height="160">
  <h1>Tej strony nie ma</h1>
  <p class="lead">Ślimak się nie spieszy, ale tu chyba skręcił nie tam, gdzie trzeba.</p>
  <p class="btns"><a class="btn btn-ink" href="/">Strona główna</a> <a class="btn btn-line" href="/sklep/">Sklep</a></p>
</div>'''
    write('/404.html', shell('Nie znaleziono strony', 'Ta strona nie istnieje.', main, path='/404.html'))
    OUT.remove('/404.html')


# ---------- articles (Polish blog) ----------

MONTHS = ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca', 'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia']


def pl_date(d):
    y, m, dd = (d or '2026-01-01').split('-')
    return f'{int(dd)} {MONTHS[int(m) - 1]} {y}'


def article_card(slug, sizes='(max-width:720px) 100vw, 33vw'):
    a = ARTICLES[slug]
    return f'''<article class="recipe-card article-card">
  <a href="/artykuly/{slug}.html" class="rc-photo" tabindex="-1" aria-hidden="true">{img(a["image"], sizes)}</a>
  <p class="kind">{pl_date(a.get("date"))}</p>
  <h3><a href="/artykuly/{slug}.html">{e(a["title"])}</a></h3>
  <p class="muted small-text">{e(a["lead"])}</p>
</article>'''


def articles_page():
    cards = ''.join(article_card(s) for s in ARTICLES)
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Nasza kuchnia', '/nasza-kuchnia/'), ('Artykuły', '/artykuly/')])}
  <header class="page-head">
    <h1>Artykuły</h1>
    <p class="lead">Jak podać ślimaki, gdzie je kupić, jakie wino do nich wybrać i skąd się wzięły na polskim stole.</p>
  </header>
  <div class="grid recipes">{cards}</div>
</div>'''
    write('/artykuly/', shell('Artykuły o ślimakach: jak podać, gdzie kupić, do jakiego wina', 'Poradniki i historie Lumaki: jak podać ślimaki, przepisy na szybkie przystawki, gdzie kupić gotowe ślimaki, jakie wino do ślimaków.',
                              main, [a['image'] for a in ARTICLES.values()], current='Nasza kuchnia', path='/artykuly/',
                              ld=[crumbs_ld([('Strona główna', '/'), ('Nasza kuchnia', '/nasza-kuchnia/'), ('Artykuły', '/artykuly/')])]))


def article_page(slug, a):
    prods = [x for x in a.get('products') or [] if x in PR]
    recs = [x for x in a.get('recipes') or [] if x in R]
    more = [x for x in ARTICLES if x != slug][:3]
    aside = ''
    if prods:
        aside = '<aside class="art-shop"><h2>Z tego artykułu</h2>' + ''.join(product_card(x, PR[x], '(max-width:720px) 100vw, 300px') for x in prods[:2]) + '</aside>'
    main = f'''
<div class="wrap">
  {crumbs([('Strona główna', '/'), ('Nasza kuchnia', '/nasza-kuchnia/'), ('Artykuły', '/artykuly/'), (a['title'], f'/artykuly/{slug}.html')])}
  <article class="article">
    <header class="article-head">
      <p class="kind">{pl_date(a.get("date"))} · Lumaca</p>
      <h1>{e(a["title"])}</h1>
      <p class="lead">{e(a["lead"])}</p>
    </header>
    <figure class="article-photo">{img(a["image"], "(max-width:1200px) 100vw, 1200px", True)}</figure>
    <div class="article-body">
      <div class="prose">{md(a.get("body", ""))}</div>
      {aside}
    </div>
  </article>
  {f'<section class="sec"><h2 class="sec-title">Przepisy</h2><div class="grid recipes">{"".join(recipe_card(r) for r in recs)}</div></section>' if recs else ''}
  <section class="sec"><h2 class="sec-title">Czytaj dalej</h2><div class="grid recipes">{"".join(article_card(x) for x in more)}</div></section>
</div>'''
    path = f'/artykuly/{slug}.html'
    ld = [crumbs_ld([('Strona główna', '/'), ('Nasza kuchnia', '/nasza-kuchnia/'), ('Artykuły', '/artykuly/'), (a['title'], path)]),
          {'@type': 'Article', 'headline': a['title'], 'description': a['lead'], 'image': [abs_image(a['image'])], 'datePublished': a.get('date'),
           'author': {'@type': 'Organization', 'name': 'Lumaca'}, 'publisher': {'@type': 'Organization', 'name': 'Lumaca', 'logo': {'@type': 'ImageObject', 'url': SITE + '/img/logo-badge.png'}},
           'keywords': a.get('keywords', ''), 'inLanguage': 'pl', 'mainEntityOfPage': SITE + path}]
    images = [a['image']] + [PR[x]['image'] for x in prods] + [R[x]['image'] for x in recs]
    write(path, shell(a['title'], a['lead'], main, images, current='Nasza kuchnia', path=path, image=a['image'], og_type='article', ld=ld))


# ---------- English and French ----------

def tr(p, lang):
    """A product with its English or French fields laid over the Polish ones."""
    return {**p, **(p.get(lang) or {})}


def tname(p):
    return f'{p["kind"]} {p["title"]}' if p['kind'] in ('Ślimaki', 'Snails', 'Escargots') else (
        f'{p["title"]}: {p["kind"]}' if p['category'] != 'zestawy' else f'{p["title"]} · {p["kind"]}')


def shell_i18n(lang, title, desc, main, path, images=(), current=None, image=None, og_type='website', ld=(), body_class='', home=False):
    OUT.append(path)
    U = I18N[lang]['ui']
    P = {k: v[lang] for k, v in PATHS.items()}
    nav_items = [('shop', U['shop']), ('how', U['how']), ('kitchen', U['kitchen']), ('trade', U['trade']), ('contact', U['contact'])]
    cur = ' aria-current="page"'
    nav = '\n'.join(f'      <a href="{P[k]}"{cur if k == current else ""}>{n}</a>' for k, n in nav_items)
    og_img = (f'<meta property="og:image" content="{e(abs_image(image))}">\n') if image and image.get('src') else ''
    cta = f'''
<section class="newsletter" aria-labelledby="h-cta">
  <div class="wrap nl">
    <div><h2 id="h-cta">{e(U["cta_title"])}</h2><p>{e(U["cta_text"])}</p></div>
    <p><a class="btn btn-gold" href="{P["trade"]}#enquiry">{e(U["cta_btn"])}</a></p>
  </div>
</section>''' if current != 'trade' else ''
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}{"" if home else " · Lumaca"}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#1B1A18">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:site_name" content="Lumaca">
<meta property="og:locale" content="{LANGS[lang][2]}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{path}">
{og_img}<meta name="twitter:card" content="summary_large_image">
{hreflang(path)}{ld_script(ld)}
<link rel="icon" href="/img/favicon-64.png" type="image/png">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<link rel="preload" href="/fonts/lora-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/css/fonts.css">
<link rel="stylesheet" href="/css/style.css">
</head>
<body class="{body_class}">
<a class="skip" href="#content">{e(U["skip"])}</a>
<header class="site-header">
  <div class="topbar"><div class="wrap">
    <span>{e(U["topbar"])}</span>
    <a href="tel:{tel(S["phone"])}">{e(S["phone"])}</a>
  </div></div>
  <div class="wrap bar">
    <a href="{P["home"]}" class="logo"><img src="/img/logo-yellow.png" alt="Lumaca" width="237" height="34"></a>
    <nav class="main-nav" id="main-nav" aria-label="{e(U["menu"])}">
{nav}
    </nav>
    <div class="actions">
      {lang_switch(lang, path)}
      <button class="icon-btn menu-toggle" type="button" aria-label="{e(U["menu"])}" aria-expanded="false" aria-controls="main-nav" data-menu>{MENU}</button>
    </div>
  </div>
</header>
<main id="content">
{main}
{cta}
</main>
<footer class="site-footer">
  <div class="wrap foot">
    <div class="foot-brand">
      <img src="/img/logo-badge.png" alt="Lumaca" width="120" height="120" loading="lazy">
      <p>{e(U["footer_about"])}</p>
    </div>
    <nav class="foot-col" aria-label="Lumaca">
      <h2>Lumaca</h2>{"".join(f'<a href="{P[k]}">{n}</a>' for k, n in nav_items)}
    </nav>
    <div class="foot-col contact">
      <h2>{e(U["contact"])}</h2>
      <a href="tel:{tel(S["phone"])}">{e(S["phone"])}</a><a href="mailto:{e(S["email"])}">{e(S["email"])}</a>
      <span>{e(S["address"])}, Poland</span>{social()}
    </div>
  </div>
  <div class="wrap foot-meta">
    <p>© 2026 Lumaca · {e(U["vet"])} {e(S["vet_number"])}</p>
  </div>
</footer>
<script src="/js/site.js" defer></script>
</body>
</html>
'''


def i_card(slug, p, lang, sizes='(max-width:720px) 50vw, 25vw'):
    U = I18N[lang]['ui']
    q = tr(p, lang)
    badge = f'<span class="badge">{e(q["badge"])}</span>' if q.get('badge') else ''
    link = product_path(slug, lang)
    return f'''<article class="product-card" style="--stripe:{e(p.get("stripe") or "#C9A35A")}">
  <a href="{link}" class="pc-photo" tabindex="-1" aria-hidden="true">{jar_photo(p, sizes)}{badge}</a>
  <div class="pc-body">
    <p class="kind">{e(q["kind"])}</p>
    <h3><a href="{link}">{e(q["title"])}</a></h3>
    <p class="pc-occ">{e(q.get("occasion", ""))}</p>
    <p class="pc-buy"><span class="price">{eur(p["price"], lang)} <small>{pln(p["price"])}</small></span><a class="btn btn-ink btn-sm" href="{link}">{e(U["order"]) if p.get("available", True) else e(q.get("badge") or U["unavailable"])}</a></p>
  </div>
</article>'''


def i_three_ways(lang):
    H = I18N[lang]['how']
    pics = ['grzanki-ze-slimakami', 'tagliatelle-ze-slimakami-w-pesto', 'babeczki-ze-slimakami']
    return '<ol class="three-ways">' + ''.join(f'''<li class="way">
      <span class="way-photo">{img(R[r]["image"], "(max-width:720px) 100vw, 33vw") if r in R else ""}</span>
      <span class="step">{k + 1}</span><h3>{e(w["title"])}</h3><p>{e(w["text"])}</p></li>''' for k, (w, r) in enumerate(zip(H['ways'], pics))) + '</ol>'


def i_home(lang):
    T = I18N[lang]
    H, U, P = T['home'], T['ui'], {k: v[lang] for k, v in PATHS.items()}
    jars = [(s, p) for s, p in PR.items() if p['category'] == 'sloiki' and p.get('available', True)][:4]
    K = T['kitchen']
    main = f'''
<section class="hero" aria-labelledby="h-hero">
  <figure class="hero-photo">{img(HOME["hero_image"], "100vw", True)}</figure>
  <div class="wrap hero-in">
    <div class="label-card hero-card">
      <img class="hero-mark" src="/img/mark-yellow.png" alt="" width="90" height="40">
      <h1 id="h-hero">{e(H["hero_title"])}</h1>
      <p class="hero-badge">{e(H["hero_badge"])}</p>
      <p>{e(H["hero_text"])}</p>
      <p class="btns"><a class="btn btn-gold" href="{P["shop"]}">{e(H["cta_shop"])}</a> <a class="btn btn-line-light" href="{P["trade"]}">{e(H["cta_trade"])}</a></p>
    </div>
  </div>
</section>
<section class="wrap sec"><div class="sec-head"><h2 class="sec-title">{e(H["best"])}</h2><a class="more" href="{P["shop"]}">{e(U["all_products"])}</a></div>
  <div class="grid products">{"".join(i_card(s, p, lang) for s, p in jars)}</div><p class="muted small-text rate-note">{e(rate_note(lang))}</p></section>
<section class="wrap sec"><div class="sec-head"><h2 class="sec-title">{e(H["how"])}</h2><a class="more" href="{P["how"]}">{e(U["how"])}</a></div>
  <p class="sec-lead">{e(H["how_text"])}</p>{i_three_ways(lang)}</section>
<section class="wrap sec kitchen">
  <figure>{img(KITCHEN["grazyna_image"], "(max-width:720px) 100vw, 50vw")}</figure>
  <div><p class="kind">{e(K["owners_kind"])}</p><h2 class="sec-title">{e(K["title"])}</h2><p>{e(K["owners_text"])}</p>
    <ol class="plain small">{"".join(f'<li>{e(x["title"])}.</li>' for x in K["story"])}</ol>
    <a class="btn btn-ink" href="{P["kitchen"]}">{e(U["learn_more"])}</a></div>
</section>'''
    write(P['home'], shell_i18n(lang, H['title'], H['hero_text'], main, P['home'], image=HOME['hero_image'], home=True, body_class='home',
                                ld=[{**ORG, 'description': U['footer_about']}, {'@type': 'WebSite', 'name': 'Lumaca', 'url': SITE + P['home'], 'inLanguage': lang}]))


def i_shop(lang):
    T = I18N[lang]
    U, P, SH = T['ui'], {k: v[lang] for k, v in PATHS.items()}, T['shop']
    groups = ''.join(f'''<section class="sec" id="{c}"><h2 class="sec-title">{e(U["cats"][c])}</h2>
    <div class="grid products">{"".join(i_card(s, p, lang) for s, p in PR.items() if p["category"] == c)}</div></section>'''
                     for c in CATS if any(p['category'] == c for p in PR.values()))
    main = f'''
<div class="wrap">
  {crumbs([(U['home'], P['home']), (SH['title'], P['shop'])])}
  <header class="page-head"><h1>{e(SH["title"])}</h1><p class="lead">{e(SH["lead"])}</p>
    <p class="notice">{e(SH["notice"])} <a href="{P["trade"]}#enquiry">{e(U["cta_btn"])}</a></p></header>
  {groups}
  <p class="muted small-text rate-note">{e(rate_note(lang))}</p>
</div>'''
    write(P['shop'], shell_i18n(lang, SH['title'], SH['lead'], main, P['shop'], current='shop', image=HOME['hero_image']))


def i_product(slug, p, lang):
    T = I18N[lang]
    U, P = T['ui'], {k: v[lang] for k, v in PATHS.items()}
    q = tr(p, lang)
    name = tname(q)
    dish = p.get('dish_image') if p.get('dish_image', {}).get('src') and p.get('dish_image', {}).get('src') != p['image'].get('src') else None
    gallery = ('<div class="pr-photos">' + (f'<figure class="dish">{img(dish, "(max-width:720px) 100vw, 40vw", True)}</figure>' if dish else '')
               + f'<figure class="jar">{jar_photo(p, "(max-width:720px) 100vw, 30vw", not dish)}</figure></div>')
    ways = q.get('ways') or []
    ways_html = (f'<section class="ways"><h2>{e(U["ways"])}</h2><ol>' + ''.join(f'<li><h3>{e(w["title"])}</h3><p>{e(w["text"])}</p></li>' for w in ways)
                 + '</ol></section>') if ways else ''
    facts = [(U['net'], q.get('net_weight')), (U['ingredients'], q.get('ingredients')), (U['allergens'], q.get('allergens')),
             (U['storage'], q.get('storage')), (U['shelf'], q.get('shelf_life'))]
    facts_html = ''.join(f'<div><dt>{k}</dt><dd>{e(v)}</dd></div>' for k, v in facts if v)
    order = f'{P["contact"]}?zamowienie={quote(name)}'
    btn = (f'<a class="btn btn-gold btn-buy" href="{order}">{e(U["order"])}</a>' if p.get('available', True)
           else f'<button type="button" class="btn btn-gold btn-buy" disabled>{e(q.get("badge") or U["unavailable"])}</button>')
    main = f'''
<div class="wrap">
  {crumbs([(U['home'], P['home']), (U['shop'], P['shop']), (name, product_path(slug, lang))])}
  <article class="product" style="--stripe:{e(p.get("stripe") or "#C9A35A")}">
    {gallery}
    <div class="pr-info">
      <div class="label-card"><p class="kind">{e(q["kind"])}</p><h1>{e(q["title"])}</h1>
        {f'<p class="badge-inline">{e(q["badge"])}</p>' if q.get('badge') else ''}
        <p class="pr-price">{eur(p["price"], lang)}</p><p class="small-text">{pln(p["price"])} · {e(U["retail"])}</p></div>
      <p class="lead">{e(q["lead"])}</p>
      <div class="pr-buy">{btn}</div>
      <dl class="pr-quick">
        {f'<div><dt>{e(U["occasion"])}</dt><dd>{e(q["occasion"])}</dd></div>' if q.get('occasion') else ''}
        {f'<div><dt>{e(U["serve5"])}</dt><dd>{e(q["ready_in_5"])}</dd></div>' if q.get('ready_in_5') else ''}
        {f'<div><dt>{e(U["pairing"])}</dt><dd>{e(q["pairing"])}</dd></div>' if q.get('pairing') else ''}
      </dl>
    </div>
  </article>
  {ways_html}
  {f'<section class="facts"><h2>{e(U["facts"])}</h2><dl>{facts_html}</dl></section>' if facts_html else ''}
  <p class="muted small-text rate-note">{e(rate_note(lang))}</p>
</div>'''
    path = product_path(slug, lang)
    write(path, shell_i18n(lang, name, q['lead'], main, path, current='shop', image=dish or p['image'], og_type='product', body_class='product-page'))


def i_how(lang):
    T = I18N[lang]
    U, P, H = T['ui'], {k: v[lang] for k, v in PATHS.items()}, T['how']
    faq = ''.join(f'<details><summary>{e(x["q"])}</summary><p>{e(x["a"])}</p></details>' for x in H['faq'])
    main = f'''
<div class="wrap">
  {crumbs([(U['home'], P['home']), (H['title'], P['how'])])}
  <header class="page-head"><h1>{e(H["title"])}</h1><p class="lead">{e(H["lead"])}</p></header>
  {i_three_ways(lang)}
  <section class="faq" id="faq"><h2 class="sec-title">{e(U["faq"])}</h2>{faq}</section>
</div>'''
    ld = [{'@type': 'FAQPage', 'inLanguage': lang, 'mainEntity': [{'@type': 'Question', 'name': x['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': x['a']}} for x in H['faq']]}]
    write(P['how'], shell_i18n(lang, H['title'], H['lead'], main, P['how'], current='how', image=R['grzanki-ze-slimakami']['image'], ld=ld))


def i_kitchen(lang):
    T = I18N[lang]
    U, P, K = T['ui'], {k: v[lang] for k, v in PATHS.items()}, T['kitchen']
    story = ''.join(f'<li><span class="num">{k + 1}</span><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p></li>' for k, x in enumerate(K['story']))
    facts = ''.join(f'<li><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p></li>' for x in K['facts'])
    main = f'''
<div class="wrap">
  {crumbs([(U['home'], P['home']), (K['title'], P['kitchen'])])}
  <header class="page-head"><h1>{e(K["title"])}</h1><p class="lead">{e(K["lead"])}</p></header>
  <section class="story"><ol>{story}</ol></section>
  <section class="person"><figure>{img(KITCHEN["grazyna_image"], "(max-width:720px) 100vw, 40vw")}</figure>
    <div class="label-card dark"><p class="kind">{e(K["owners_kind"])}</p><h2>{e(K["owners_title"])}</h2><p>{e(K["owners_text"])}</p></div></section>
  <section class="sec"><h2 class="sec-title">{e(K["facts_title"])}</h2><ul class="fact-grid">{facts}</ul></section>
</div>'''
    write(P['kitchen'], shell_i18n(lang, K['title'], K['lead'], main, P['kitchen'], current='kitchen', image=KITCHEN['grazyna_image']))


def i_trade(lang):
    T = I18N[lang]
    U, P, B = T['ui'], {k: v[lang] for k, v in PATHS.items()}, T['trade']
    seg = ''.join(f'<li><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p></li>' for x in B['segments'])
    facts = ''.join(f'<div><dt>{e(x["k"])}</dt><dd>{e(x["v"])}</dd></div>' for x in B['facts'])
    names = ''.join(f'<tr><td lang="pl">{e(full_name(p))}</td><td lang="en">{e(p["name_en"])}</td><td lang="fr">{e(p["name_fr"])}</td></tr>'
                    for p in PR.values() if p.get('name_en'))
    L = {'en': {'firma': 'Company', 'rodzaj': 'Business type', 'kraj': 'Country', 'osoba': 'Name', 'telefon': 'Phone', 'wiadomosc': 'What are you looking for?',
                'opts': ['Importer or distributor', 'Retailer or delicatessen', 'Restaurant, wine bar or hotel', 'Private label', 'Other']},
         'fr': {'firma': 'Société', 'rodzaj': 'Activité', 'kraj': 'Pays', 'osoba': 'Nom', 'telefon': 'Téléphone', 'wiadomosc': 'Que recherchez-vous ?',
                'opts': ['Importateur ou distributeur', 'Épicerie fine ou commerce', 'Restaurant, bar à vin ou hôtel', 'Marque de distributeur', 'Autre']}}[lang]
    enquiry = form('zapytanie-b2b', [('text', 'firma', L['firma'], True), ('select', 'rodzaj', L['rodzaj'], True, L['opts']), ('text', 'miasto', L['kraj'], False),
                                     ('text', 'osoba', L['osoba'], True), ('email', 'email', 'E-mail', True), ('tel', 'telefon', L['telefon'], False),
                                     ('textarea', 'wiadomosc', L['wiadomosc'], False)], U['send'], U['form_ok'],
                   extra=f'<input type="hidden" name="jezyk" value="{lang}">', err={'en': 'Sending failed. Please email info@lumaca.eco', 'fr': 'Échec de l’envoi. Écrivez-nous : info@lumaca.eco'}[lang])
    main = f'''
<div class="wrap">
  {crumbs([(U['home'], P['home']), (B['title'], P['trade'])])}
  <header class="page-head"><h1>{e(B["title"])}</h1><p class="lead">{e(B["lead"])}</p><p><a class="btn btn-gold" href="#enquiry">{e(U["cta_btn"])}</a></p></header>
  <section class="sec"><ul class="fact-grid">{seg}</ul></section>
  <section class="facts"><h2>{e(U["facts"])}</h2><dl>{facts}</dl><p class="muted">{e(B["docs"])}</p></section>
  <section class="sec"><h2 class="sec-title">{e(B["names_title"])}</h2>
    <div class="table-wrap"><table class="names"><thead><tr><th>Polski</th><th>English</th><th>Français</th></tr></thead><tbody>{names}</tbody></table></div></section>
  <section class="sec enquiry" id="enquiry"><h2 class="sec-title">{e(B["form_title"])}</h2><p>{e(B["form_lead"])}</p>{enquiry}</section>
</div>'''
    write(P['trade'], shell_i18n(lang, B['title'], B['lead'], main, P['trade'], current='trade', image=HOME['hero_image']))


def i_contact(lang):
    T = I18N[lang]
    U, P, C = T['ui'], {k: v[lang] for k, v in PATHS.items()}, T['contact']
    L = {'en': ('Name', 'Phone', 'Subject', 'Message'), 'fr': ('Nom', 'Téléphone', 'Objet', 'Message')}[lang]
    contact_form = form('kontakt', [('text', 'imie', L[0], True), ('email', 'email', 'E-mail', True), ('tel', 'telefon', L[1], False), ('text', 'zamowienie', L[2], False),
                                    ('textarea', 'wiadomosc', L[3], True)], U['send'], U['form_ok'], extra=f'<input type="hidden" name="jezyk" value="{lang}">',
                        err={'en': 'Sending failed. Please email info@lumaca.eco', 'fr': 'Échec de l’envoi. Écrivez-nous : info@lumaca.eco'}[lang])
    main = f'''
<div class="wrap">
  {crumbs([(U['home'], P['home']), (C['title'], P['contact'])])}
  <header class="page-head"><h1>{e(C["title"])}</h1><p class="lead">{e(C["lead"])}</p></header>
  <div class="contact-grid">
    <div class="label-card dark"><p class="kind">Lumaca</p>
      <p class="big"><a href="tel:{tel(S["phone"])}">{e(S["phone"])}</a></p><p class="big"><a href="mailto:{e(S["email"])}">{e(S["email"])}</a></p>
      <p>{e(S["address"])}<br>Poland</p><p>{e(C["hours"])}</p>
      <p><a href="https://www.google.com/maps/search/?api=1&amp;query={quote(S["address"])}">{e(C["map"])}</a></p>{social()}</div>
    {contact_form}
  </div>
</div>'''
    write(P['contact'], shell_i18n(lang, C['title'], C['lead'], main, P['contact'], current='contact', ld=[ORG]))


def i18n_pages():
    for lang in ('en', 'fr'):
        i_home(lang)
        i_shop(lang)
        for s, p in PR.items():
            i_product(s, p, lang)
        i_how(lang)
        i_kitchen(lang)
        i_trade(lang)
        i_contact(lang)


def write_sitemap():
    urls = ''.join(f'<url><loc>{SITE}{p}</loc></url>' for p in OUT)
    write('/sitemap.xml', f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    write('/robots.txt', f'User-agent: *\nDisallow: /admin/\n\nSitemap: {SITE}/sitemap.xml\n')


def main():
    home_page()
    shop_page()
    for s, p in PR.items():
        product_page(s, p)
    sets_page()
    recipes_page()
    for s, r in R.items():
        recipe_page(s, r)
    kitchen_page()
    where_page()
    b2b_page()
    press_page()
    contact_page()
    plain_pages()
    articles_page()
    for s, a in ARTICLES.items():
        article_page(s, a)
    i18n_pages()
    not_found()
    write_sitemap()
    print(f'Lumaca: {len(OUT)} pages, {len(PR)} products, {len(R)} recipes, {len(ARTICLES)} articles, EN + FR → {SITE}')


if __name__ == '__main__':
    main()
