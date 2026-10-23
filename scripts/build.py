#!/usr/bin/env python3
"""Builds the site from the CMS content in content/ (edited at /admin, or by hand).

    python3 scripts/build.py           # what Netlify runs on every deploy
    python3 scripts/build.py --local   # uploaded images without Netlify's image CDN, for a local preview

Reads  content/articles/*.json, content/recipes/*.json, content/settings/home.json
Writes index.html, historie/<slug>.html, przepisy/<slug>.html, js/recipe-data.js
Cook mode (gotowanie.html) and 404.html are hand-written. Standard library only.
"""
import glob
import html
import json
import math
import os
import re
import sys
from datetime import date
from urllib.parse import quote, urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL = '--local' in sys.argv
e = html.escape


def load(folder):
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'content', folder, '*.json'))):
        slug = os.path.splitext(os.path.basename(f))[0]
        out[slug] = json.load(open(f, encoding='utf-8'))
        out[slug]['slug'] = slug
    return out


A = dict(sorted(load('articles').items(), key=lambda kv: kv[1].get('number') or 999))
R = dict(sorted(load('recipes').items(), key=lambda kv: kv[1].get('number') or 99))
HOME = json.load(open(os.path.join(ROOT, 'content', 'settings', 'home.json'), encoding='utf-8'))
WS = dict(sorted(load('workshops').items(), key=lambda kv: kv[1].get('order') or 99))
TR = dict(sorted(load('trips').items(), key=lambda kv: kv[1].get('order') or 99))
OFERTA = json.load(open(os.path.join(ROOT, 'content', 'settings', 'oferta.json'), encoding='utf-8'))
PR = dict(sorted(load('products').items(), key=lambda kv: kv[1].get('order') or 99))
SHOP = json.load(open(os.path.join(ROOT, 'content', 'settings', 'sklep.json'), encoding='utf-8'))
# the cart and checkout are Snipcart's (https://snipcart.com); with no public API key set in the CMS
# the shop shows its products but the buttons say "coming soon" and no Snipcart code loads
SHOP_KEY = (SHOP.get('snipcart_key') or '').strip()
SNIPCART_VERSION = '3.7.4'
CAT = {'kiszonki': 'Kiszonki', 'staropolskie': 'Staropolskie', 'podroze': 'Z podróży',
       'codzien': 'Na co dzień', 'sezonowe': 'Sezonowe'}
CAT_ANCHOR = {'staropolskie': '/#staropolska', 'podroze': '/#podroze'}
UTM = 'utm_source=lowca_smakow&utm_medium=referral'


def no(slug):
    return f"{A[slug].get('number') or 0:03d}"


def rno(slug):
    return f"P{R[slug].get('number') or 0:02d}"


# ---------- images, credits, video ----------

def img(image, sizes, eager=False, cls='fill'):
    """<img> for a CMS image object {src, alt, credit, credit_url}.
    Unsplash photos get Unsplash's resizer, uploads get Netlify's image CDN (not for SVG)."""
    if not image or not image.get('src'):
        return ''
    src, alt = image['src'], e(image.get('alt') or '')
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    if src.startswith('https://images.unsplash.com/'):
        base = src.split('?')[0] + '?auto=format&amp;fit=crop&amp;q=70'
        srcset = ', '.join(f'{base}&amp;w={w} {w}w' for w in (480, 800, 1200, 1800))
        return f'<img class="{cls}" src="{base}&amp;w=1200" srcset="{srcset}" sizes="{sizes}" alt="{alt}" {load} decoding="async">'
    if src.startswith('/') and not src.lower().endswith('.svg') and not LOCAL:
        cdn = lambda w: f'/.netlify/images?url={quote(src)}&amp;w={w}'
        srcset = ', '.join(f'{cdn(w)} {w}w' for w in (480, 800, 1200, 1800))
        return f'<img class="{cls}" src="{cdn(1200)}" srcset="{srcset}" sizes="{sizes}" alt="{alt}" {load} decoding="async">'
    return f'<img class="{cls}" src="{e(src)}" alt="{alt}" {load} decoding="async">'


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
    tail = f' · <a href="{e("https://unsplash.com/?" + UTM)}">Unsplash</a>' if any('unsplash' in (i or {}).get('src', '') for i in images) else ''
    return '<p class="meta credits">Zdjęcia: ' + ', '.join(parts) + tail + '</p>'


def yt_id(url):
    """YouTube video id from any common link form (watch, youtu.be, shorts, embed, live)."""
    if not url:
        return None
    url = url.strip()
    u = urlparse(url)
    if u.hostname in ('youtu.be', 'www.youtu.be'):
        return u.path.strip('/').split('/')[0] or None
    if u.hostname and 'youtube' in u.hostname:
        if u.path == '/watch':
            return (parse_qs(u.query).get('v') or [None])[0]
        m = re.match(r'/(?:shorts|embed|live)/([\w-]{6,})', u.path)
        return m.group(1) if m else None
    return url if re.fullmatch(r'[\w-]{11}', url) else None


PLAY = '<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>'


def video(url, title, cover=None, cls='frame', sizes='(max-width:720px) 100vw, 760px', eager=False):
    """Privacy-friendly YouTube: a photo and a play button; the player loads only on click."""
    vid = yt_id(url)
    if not vid:
        return ''
    poster = img(cover, sizes, eager) if cover else \
        f'<img class="fill" src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy" decoding="async">'
    return (f'<div class="ph {cls} {T()} video ratio-169" data-yt="{e(vid)}" data-yt-title="{e(title)}">{poster}'
            f'<button type="button" class="play" data-yt-play aria-label="Odtwórz wideo: {e(title)}">{PLAY}</button></div>')


# ---------- small markup helpers ----------

TINTS = ['mustard', 'vermilion', 'ultramarine', 'sage']
_tint = [0]


def T():
    """Next frame colour: photo frames cycle through the four inks."""
    tint = TINTS[_tint[0] % len(TINTS)]
    _tint[0] += 1
    return f'tint-{tint}'


def framed(inner, cls=''):
    """An inline photo in a simple coloured frame (used for thumbnails)."""
    return f'<span class="ph frame {T()} {cls}">{inner}</span>'


def md(text):
    """Tiny inline markdown for CMS text: **bold**, *italic*, [link](url). Paragraphs split on blank lines."""
    t = e(text or '')
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)', r'<em>\1</em>', t)
    t = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+|/[^)\s]*)\)', r'<a href="\2">\1</a>', t)
    return [p.strip().replace('\n', '<br>') for p in re.split(r'\n\s*\n', t) if p.strip()]


def first_sentence(t):
    m = re.match(r'(.+?[.!?])(\s|$)', t)
    return m.group(1) if m else t


def recipe_card_image(r):
    return r.get('card_image') or r['image']


# ---------- page frame ----------

FONTS = ('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500'
         '&amp;family=Instrument+Sans:wght@400;500;600&amp;family=Poppins:wght@600;700;800&amp;display=swap')
SEARCH = ('<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
          'stroke-width="1.6" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>')
CART_BTN = ('<button class="icon-btn cart-btn snipcart-checkout" type="button" aria-label="Koszyk">'
            '<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M5 8h14l-1.2 11.2a1 1 0 0 1-1 .8H7.2a1 1 0 0 1-1-.8z"/>'
            '<path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg><span class="snipcart-items-count" aria-hidden="true"></span></button>')
MENU = ('<svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>')
NAV = [('Historie', '/#nowe'), ('Przepisy', '/#przepisy'), ('Wideo', '/#staropolska'),
       ('Smaki regionów', '/#regiony'), ('Smaki świata', '/#swiat'), ('Warsztaty', '/warsztaty/'),
       ('Wyprawy', '/wyprawy/'), ('Sklep', '/sklep/')]
FOOT_NAV = '''<div><a href="/#nowe">Historie</a><a href="/#przepisy">Przepisy</a><a href="/#staropolska">Wideo</a><a href="/warsztaty/">Warsztaty</a><a href="/wyprawy/">Wyprawy kulinarne</a><a href="/sklep/">Sklep</a></div>
      <div><a href="#">O nas</a><a href="#">Współpraca i media kit</a><a href="#">Wydarzenia</a></div>
      <div><a href="#">Instagram</a><a href="#">YouTube</a><a href="#">Kontakt</a></div>'''
SECTION_NAV = '''<nav class="section-nav" aria-label="Działy">
  <a href="#tresc" class="chip is-active">Wszystko</a>
  <a href="#nowe" class="chip">Historie</a>
  <a href="#przepisy" class="chip">Przepisy</a>
  <a href="#staropolska" class="chip">Wideo</a>
  <a href="#regiony" class="chip">Regiony</a>
  <a href="#swiat" class="chip">Świat</a>
  <a href="#warsztaty" class="chip">Warsztaty</a>
  <a href="#wyprawy" class="chip">Wyprawy</a>
  <a href="#sklep" class="chip">Sklep</a>
</nav>'''


def shell(title, desc, main, images, current=None, body_class='', body_attrs='', scripts=(), home=False):
    nav = '\n'.join(f'    <a class="navlink" href="{h}"{" aria-current=\"page\"" if n == current else ""}>{n}</a>' for n, h in NAV)
    js = '\n'.join(f'<script src="{s}"></script>' for s in ('/js/site.js', *scripts))
    if SHOP_KEY:
        js += ('\n<script>window.SnipcartSettings = ' + json.dumps({'publicApiKey': SHOP_KEY, 'loadStrategy': 'on-user-interaction',
               'currency': 'pln', 'version': SNIPCART_VERSION, 'modalStyle': 'side'}) + ';</script>\n<script src="/js/snipcart.js"></script>')
    return f'''<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}{"" if home else " — Łowca Smaków"}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#FBFAF7">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
</head>
<body class="{body_class}"{body_attrs}>
<a class="skip" href="#tresc">Przejdź do treści</a>

<header class="site-header">
  <div class="topbar"><div class="wrap"><span>{e(HOME.get('issue', ''))}</span><span class="topbar-r">{e(HOME.get('tagline', ''))}</span></div></div>
  <div class="wrap masthead">
    <div class="left">
      <button class="icon-btn" type="button" aria-label="Szukaj" aria-expanded="false" aria-controls="search" data-search-toggle>
        {SEARCH}
      </button>
    </div>
    <a href="/" class="logo"><img src="/img/wordmark.svg" alt="Łowca Smaków" width="226" height="69"></a>
    <div class="header-actions">
      <button class="icon-btn menu-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="main-nav" data-menu-toggle>
        {MENU}
      </button>
      {CART_BTN if SHOP_KEY else ''}
      <a href="#newsletter" class="btn btn-ink">Newsletter</a>
    </div>
  </div>
  <nav class="main-nav" id="main-nav" aria-label="Główne menu">
{nav}
  </nav>
  <form class="search-bar" id="search" role="search" action="/#przepisy" hidden data-search>
    <div class="wrap">
      <label for="q" class="sr-only">Szukaj przepisów i historii</label>
      <input id="q" name="q" type="search" placeholder="Szukaj przepisów, np. „ogórki”" autocomplete="off">
      <button class="btn btn-ink" type="submit">Szukaj</button>
    </div>
  </form>
</header>
{SECTION_NAV if home else ""}
<main class="wrap" id="tresc">
{main}
{"" if home else newsletter()}
</main>

<footer class="site-footer">
  <div class="wrap">
    <div class="foot-about">
      <a href="/" class="logo"><img src="/img/logo-white.svg" alt="Łowca Smaków" width="248" height="120"></a>
      <p>Antropologia jedzenia: skąd się wzięło to, co jemy — i jak to ugotować.</p>
    </div>
    <nav class="foot-nav" aria-label="Stopka">
      {FOOT_NAV}
    </nav>
    {credits(images)}
    <p class="meta copyright">© 2026 Savour Ventures OÜ</p>
  </div>
</footer>

{js}
</body>
</html>
'''


def newsletter():
    return '''
  <section class="newsletter slim" id="newsletter" aria-labelledby="h-nl">
    <div class="nl-copy">
      <h2 id="h-nl">Jedna historia. Jeden przepis. Co tydzień.</h2>
    </div>
    <form class="nl-form" name="newsletter" method="POST" data-netlify="true" netlify-honeypot="bot-field" data-newsletter>
      <input type="hidden" name="form-name" value="newsletter">
      <p class="sr-only"><label>Nie wypełniaj <input name="bot-field" tabindex="-1"></label></p>
      <label for="nl2" class="sr-only">Adres e-mail</label>
      <div class="nl-row">
        <input id="nl2" name="email" type="email" required placeholder="ty@przyklad.pl" autocomplete="email">
        <button type="submit">Zapisz się</button>
      </div>
      <p class="nl-msg" aria-live="polite" data-nl-msg></p>
    </form>
  </section>'''


def card(href, image, kicker, title, sizes='(max-width:720px) 50vw, 25vw'):
    return (f'<a href="{href}" class="card sm"><div class="ph frame {T()} ratio-43">{img(image, sizes)}</div>'
            f'<p class="kicker">{e(kicker)}</p><h3>{e(title)}</h3></a>')


def article_card(slug):
    a = A[slug]
    label = a.get('place') or a['kicker'].split(' · ')[0]
    return card(f'/historie/{slug}.html', a['image'], label, a['title'])


def recipe_card(slug):
    r = R[slug]
    return card(f'/przepisy/{slug}.html', recipe_card_image(r), 'Przepis', r['title'])


def ref_image(slug):
    return recipe_card_image(R[slug]) if slug in R else A[slug]['image']


def related(slugs, heading='Czytaj dalej', note=''):
    slugs = [s for s in slugs if s in A or s in R]
    if not slugs:
        return ''
    cards = '\n      '.join(recipe_card(s) if s in R else article_card(s) for s in slugs)
    return f'''
  <section class="sec related" aria-labelledby="h-related">
    <div class="sec-head">
      <h2 id="h-related">{heading}</h2>
      {f'<p class="meta">{note}</p>' if note else ''}
    </div>
    <div class="grid grid-4">
      {cards}
    </div>
  </section>'''


# ---------- articles ----------

def block_html(b, state):
    t = b.get('type')
    if t == 'text':
        out = []
        for p in md(b.get('text', '')):
            out.append(f'<p{" class=\"dropcap\"" if not state["dropcap"] else ""}>{p}</p>')
            state['dropcap'] = True
        return '\n      '.join(out)
    if t == 'heading':
        return f'<h2>{e(b.get("text", ""))}</h2>'
    if t == 'quote':
        who = f'<cite>{e(b["source"])}</cite>' if b.get('source') else ''
        return f'<blockquote class="pull"><p>{e(b.get("text", ""))}</p>{who}</blockquote>'
    cap = f'<figcaption>{"".join(md(b["caption"]))}</figcaption>' if b.get('caption') else ''
    if t == 'photo':
        state['images'].append(b.get('image'))
        frame = 'none' if b.get('frame') == 'none' else 'frame'
        inner = img(b.get('image'), '(max-width:720px) 100vw, 760px')
        if frame == 'none':
            pic = f'<div class="ph plain">{inner}</div>'
        else:
            pic = f'<div class="ph frame {T()}">{inner}</div>'
        return f'<figure class="a-fig frame-{frame}">{pic}{cap}</figure>'
    if t == 'graphic':
        state['images'].append(b.get('image'))
        width = b.get('width') or 'text'
        return f'<figure class="a-graphic w-{width}">{img(b.get("image"), "(max-width:720px) 100vw, 1000px", cls="graphic")}{cap}</figure>'
    if t == 'youtube':
        v = video(b.get('url'), b.get('title') or 'Wideo')
        return f'<figure class="a-fig a-video">{v}{cap}</figure>' if v else ''
    return ''


def article_page(a):
    _tint[0] = 0
    words = sum(len((b.get('text') or '').split()) for b in a['body']) + len(a['lead'].split())
    mins = max(2, math.ceil(words / 200))
    others = [s for s in A if s != a['slug']]
    same = [s for s in others if A[s]['section'] == a['section']]
    rel = ([a['recipe']] if a.get('recipe') in R else []) + same + [s for s in others if s not in same]
    rel = rel[:3]
    state = {'dropcap': False, 'images': []}
    body = '\n      '.join(x for x in (block_html(b, state) for b in a['body']) if x)
    recipe_box = ''
    if a.get('recipe') in R:
        r = R[a['recipe']]
        recipe_box = f'''
      <aside class="a-recipe" aria-label="Przepis do tego tekstu">
        {framed(img(recipe_card_image(r), '160px'))}
        <div>
          <p class="kicker">Przepis do tego tekstu</p>
          <h2><a href="/przepisy/{a['recipe']}.html">{e(r['title'])}</a></h2>
          <p class="meta">{e(CAT.get(r['category'], ''))} · {e(r.get('card_meta', ''))}</p>
        </div>
      </aside>'''
    hero = video(a.get('video'), a['title'], a['image'], sizes='(max-width:720px) 100vw, 1216px', eager=True) or \
        f'<div class="ph frame {T()}">{img(a["image"], "(max-width:720px) 100vw, 1216px", eager=True)}</div>'
    main = f'''
  <nav class="crumbs" aria-label="Ścieżka">
    <a href="/">Strona główna</a><span aria-hidden="true">›</span><span>{e(a['section'])}</span>
  </nav>

  <article class="article">
    <header class="a-head">
      <p class="kicker"><span class="no">№ {no(a['slug'])}</span> {e(a['kicker'])}</p>
      <h1>{e(a['title'])}</h1>
      <p class="lead">{e(a['lead'])}</p>
      <p class="meta">{mins} min czytania · <span class="draft">Tekst roboczy, do weryfikacji przed publikacją</span></p>
    </header>
    <figure class="a-hero">{hero}</figure>
    <div class="a-body">
      {body}
      {recipe_box}
    </div>
  </article>
{related(rel)}'''
    images = [a['image']] + state['images'] + ([recipe_card_image(R[a['recipe']])] if a.get('recipe') in R else []) + [ref_image(s) for s in rel]
    return shell(a['title'], a['lead'], main, images, body_class='article-page')


# ---------- recipes ----------

def recipe_page(slug, r):
    _tint[0] = 1
    name = r['title']
    vid = yt_id(r.get('video'))
    watch = (f'<button type="button" class="watch" data-yt-play><span>{PLAY.replace("24", "14")}</span>Obejrzyj odcinek</button>'
             if vid else '')
    media_attrs = f' data-yt="{e(vid)}" data-yt-title="{e(name)}"' if vid else ''
    shop = ''
    prods = products_for_recipe(slug)
    if prods:
        shop = '\n'.join(f'''
      <div class="shop shop-live" id="sklep">
        <a href="/sklep/{ps}.html" tabindex="-1" aria-hidden="true">{framed(img(pp['image'], '64px'), 'small')}</a>
        <div>
          <p class="label">Ze spiżarni Łowcy</p>
          <p class="shop-t"><a href="/sklep/{ps}.html">{e(pp['title'])}</a> <span>{pln(float(pp['price']))}</span></p>
        </div>
        {buy_button(ps, pp, 'btn btn-sm btn-light', 'Do koszyka')}
      </div>''' for ps, pp in prods[:2])
    elif r.get('shop'):
        sh = r['shop']
        shop = f'''
      <div class="shop" id="sklep">
        {framed(img(sh.get('image'), '64px'), 'small')}
        <div>
          <p class="label">{e(sh.get('label', ''))}</p>
          <p style="font-weight:600">[{e(sh.get('title', ''))}]</p>
        </div>
      </div>'''
    sources = ''
    if r.get('sources'):
        srcs = ''.join(f'<p>{"".join(md(s.replace("<i>", "*").replace("</i>", "*")))}</p>' for s in r['sources'])
        sources = f'<div class="sources"><p class="kicker">Źródła</p>{srcs}</div>'
    aside = r.get('aside') or {}
    story = aside.get('story')
    aside_html = ''
    if aside:
        link = f'<a href="/historie/{story}.html" style="font-weight:600;font-size:15px">Przeczytaj całą historię →</a>' if story in A else ''
        aside_html = f'''
    <aside class="pill-history" aria-labelledby="h-pigulka">
      <p class="kicker" id="h-pigulka">{e(aside.get('title') or 'Historia w pigułce')}</p>
      <div class="ph frame {T()}">{img(aside.get('image'), '(max-width:720px) 100vw, 40vw')}</div>
      <p class="serif">{e(aside.get('text', ''))}</p>
      <p class="body" style="font-size:15px">{e(aside.get('note', ''))}</p>
      {link}
    </aside>'''
    crumb = (CAT.get(r['category'], 'Przepisy'), CAT_ANCHOR.get(r['category'], '/#przepisy'))
    main = f'''
  <nav class="crumbs" aria-label="Ścieżka">
    <a href="/#przepisy">Przepisy</a><span aria-hidden="true">›</span><a href="{crumb[1]}">{e(crumb[0])}</a><span aria-hidden="true">›</span><span aria-current="page">{e(name)}</span>
  </nav>

  <section class="r-head">
    <div class="r-title">
      <p class="kicker"><span class="no">{rno(slug)}</span> {e(r['kicker'])}</p>
      <h1>{e(name)}</h1>
      <p class="sub">{e(r.get('subtitle', ''))}</p>
    </div>
    <dl class="r-stats">
      <div><dt class="meta">Przygotowanie</dt><dd>{e(r.get('prep', ''))}</dd></div>
      <div><dt class="meta">Gotowanie</dt><dd>{e(r.get('cook', ''))}</dd></div>
      <div><dt class="meta" data-servings-label>Porcje</dt><dd data-servings-stat></dd></div>
      <div><dt class="meta">Trudność</dt><dd>{e(r.get('level', ''))}</dd></div>
    </dl>
  </section>

  <div class="tools">
    <a href="#skladniki" class="tool primary">Do przepisu ↓</a>
    <a href="/gotowanie.html?r={slug}" class="tool">
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="6" y="2" width="12" height="20" rx="2"/><path d="M11 18h2"/></svg>
      Tryb gotowania</a>
    <button type="button" class="tool" data-print>
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 9V3h12v6"/><rect x="4" y="9" width="16" height="8" rx="1"/><path d="M7 14h10v7H7z"/></svg>
      Drukuj</button>
    <button type="button" class="tool" aria-pressed="false" data-save>
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M6 3h12v18l-6-4-6 4z"/></svg>
      <span>Zapisz</span></button>
    <button type="button" class="tool" data-share>
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg>
      <span>Udostępnij</span></button>
  </div>

  <section class="r-media">
    <div class="ph frame {T()}"{media_attrs}>{img(r['image'], '(max-width:720px) 100vw, 60vw', eager=True)}
      {watch}
    </div>
    {aside_html}
  </section>

  <section class="r-body" id="skladniki">
    <div class="ingredients">
      <div class="ing-head">
        <h2>Składniki</h2>
        <div class="stepper">
          <button type="button" class="step-btn" aria-label="Mniej" data-dec>−</button>
          <output aria-live="polite" data-servings></output>
          <button type="button" class="step-btn" aria-label="Więcej" data-inc>+</button>
        </div>
      </div>
      <div class="tools" role="group" aria-label="Jednostki">
        <button type="button" class="tool sm" aria-pressed="true" data-units="metric">Metryczne</button>
        <button type="button" class="tool sm" aria-pressed="false" data-units="cups">Szklanki i łyżki</button>
      </div>
      <ul class="ing-list" data-ingredients></ul>
      {shop}
    </div>

    <div class="method">
      <h2>Przygotowanie</h2>
      <ol class="steps" data-steps></ol>
      {sources}
      <p class="meta draft">Przepis roboczy: ilości i czasy do sprawdzenia w kuchni przed publikacją.</p>
    </div>
  </section>
{related(r.get('related') or [], 'Z tej samej opowieści', 'Dobrane po serii, regionie i składnikach')}'''
    images = [r['image'], aside.get('image')] + [pp['image'] for _, pp in prods[:2]] + ([r['shop'].get('image')] if r.get('shop') and not prods else []) + \
             [ref_image(s) for s in r.get('related') or [] if s in A or s in R]
    return shell(name, r.get('subtitle', ''), main, images, current='Przepisy', body_class='recipe',
                 body_attrs=f' data-recipe="{slug}"', scripts=('/js/recipe-data.js', '/js/recipes.js', '/js/recipe.js'))


def recipe_data_js():
    data = {}
    for slug, r in R.items():
        data[slug] = {
            'title': r['title'], 'servings': r.get('servings') or 4,
            'servingsUnit': 'słoiki' if r.get('servings_unit') == 'słoiki' else None,
            'ingredients': [{'q': i.get('q'), 'u': i.get('u') or '', 'n': i.get('n') or ''} for i in r.get('ingredients') or []],
            'steps': [{'title': s.get('title', ''), 'text': s.get('text', ''), 'timer': bool(s.get('minutes')),
                       'minutes': s.get('minutes') or None, 'uses': s.get('uses') or []} for s in r.get('steps') or []],
        }
    return ('// Generated by scripts/build.py from content/recipes/*.json. Edit recipes in the CMS (/admin), not here.\n'
            'window.RECIPES = ' + json.dumps(data, ensure_ascii=False, indent=1) + ';\n')


# ---------- homepage ----------

# Voivodeship outlines for the "Smaki regionów" map, made by scripts/map-paths.py from GUGiK's boundaries.
with open(os.path.join(ROOT, 'scripts', 'wojewodztwa.json'), encoding='utf-8') as f:
    MAP = json.load(f)
# Country outlines for the "Smaki świata" map (Natural Earth, public domain), same script.
with open(os.path.join(ROOT, 'scripts', 'swiat.json'), encoding='utf-8') as f:
    WORLD = json.load(f)
CHIPS = ['Podkarpackie', 'Świętokrzyskie', 'Małopolskie', 'Lubelskie', 'Śląskie', 'Pomorskie', 'Podlaskie']


# ---------- workshops and culinary trips ----------

MONTHS = ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca', 'lipca', 'sierpnia',
          'września', 'października', 'listopada', 'grudnia']
MON3 = ['sty', 'lut', 'mar', 'kwi', 'maj', 'cze', 'lip', 'sie', 'wrz', 'paź', 'lis', 'gru']
KINDS = {'warsztaty': ('Warsztaty', 'warsztat', WS), 'wyprawy': ('Wyprawy kulinarne', 'wyprawa', TR)}


def pl_date(d):
    y, m, dd = (int(x) for x in d.split('-'))
    return f'{dd} {MONTHS[m - 1]} {y}'


def pl_span(d, end=None):
    """6–16 marca 2027, 28 lutego – 6 marca 2027 or a single day."""
    if not end or end == d:
        return pl_date(d)
    y1, m1, d1 = (int(x) for x in d.split('-'))
    y2, m2, d2 = (int(x) for x in end.split('-'))
    if (y1, m1) == (y2, m2):
        return f'{d1}–{d2} {MONTHS[m1 - 1]} {y1}'
    return f'{d1} {MONTHS[m1 - 1]}{"" if y1 == y2 else f" {y1}"} – {d2} {MONTHS[m2 - 1]} {y2}'


def zl(n):
    return f'{n:,}'.replace(',', '\u00a0') + '\u00a0zł'


def upcoming(o):
    today = date.today().isoformat()
    return sorted((d for d in o.get('dates') or [] if (d.get('end') or d['date']) >= today), key=lambda d: d['date'])


def offer_label(kind, o):
    return o.get('kind') or 'Warsztaty' if kind == 'warsztaty' else o.get('country') or 'Wyprawa'


def date_badge(d):
    y, m, dd = (int(x) for x in d['date'].split('-'))
    return f'<span class="badge" aria-hidden="true"><b>{dd}</b>{MON3[m - 1]}</span>'


def offer_card(kind, slug, o, sizes='(max-width:720px) 100vw, 33vw'):
    nxt = upcoming(o)
    when = (pl_span(nxt[0]['date'], nxt[0].get('end')) + (f', {nxt[0]["time"]}' if nxt[0].get('time') else '')) if nxt else 'Nowe terminy wkrótce'
    group = f'<span class="date">{e(o["group"])}</span>' if o.get('group') else ''
    more = f' <span class="more-dates">+{len(nxt) - 1} {"termin" if len(nxt) == 2 else "terminy"}</span>' if len(nxt) > 1 else ''
    return (f'<a href="/{kind}/{slug}.html" class="offer-card"><span class="ph frame {T()} ratio-43">{img(o["image"], sizes)}'
            f'{date_badge(nxt[0]) if nxt else ""}</span>'
            f'<span class="offer-body">{tags([offer_label(kind, o), o.get("duration")], 2)}'
            f'<h3>{e(o["title"])}</h3>'
            f'<span class="when">{e(when)}{more}</span>'
            f'<span class="pills"><span class="price">od {zl(o["price"])}</span>{group}</span>'
            f'</span></a>')


def booking_form(offer, dates, cta, fid):
    opts = ''.join(f'<option>{e(x)}</option>' for x in dates) + '<option>Inny termin lub pytanie</option>'
    termin = (f'<label for="{fid}-t">Termin</label><select id="{fid}-t" name="termin">{opts}</select>'
              if dates else '<input type="hidden" name="termin" value="Na zamówienie">')
    return f'''<form class="booking" name="zapisy" method="POST" data-netlify="true" netlify-honeypot="bot-field" data-booking>
        <input type="hidden" name="form-name" value="zapisy">
        <input type="hidden" name="oferta" value="{e(offer)}">
        <p class="sr-only"><label>Nie wypełniaj <input name="bot-field" tabindex="-1"></label></p>
        {termin}
        <label for="{fid}-n">Imię i nazwisko</label><input id="{fid}-n" name="imie" required autocomplete="name">
        <label for="{fid}-e">E-mail</label><input id="{fid}-e" name="email" type="email" required autocomplete="email">
        <div class="two">
          <div><label for="{fid}-p">Telefon <span>(opcjonalnie)</span></label><input id="{fid}-p" name="telefon" type="tel" autocomplete="tel"></div>
          <div><label for="{fid}-o">Liczba osób</label><input id="{fid}-o" name="osoby" type="number" min="1" max="30" value="1" required></div>
        </div>
        <label for="{fid}-m">Wiadomość <span>(opcjonalnie)</span></label><textarea id="{fid}-m" name="wiadomosc" rows="3"></textarea>
        <label class="check"><input type="checkbox" name="zgoda" value="tak" required> Zgadzam się na kontakt w sprawie zapisu.</label>
        <button type="submit" class="btn btn-ink">{cta}</button>
        <p class="nl-msg" aria-live="polite" data-booking-msg></p>
      </form>'''


def offer_page(kind, slug, o):
    _tint[0] = 0
    section, _, _ = KINDS[kind]
    trip = kind == 'wyprawy'
    state = {'dropcap': False, 'images': []}
    body = '\n      '.join(x for x in (block_html(b, state) for b in o.get('body') or []) if x)
    nxt = upcoming(o)
    labels = [pl_span(d['date'], d.get('end')) + (f', godz. {d["time"]}' if d.get('time') else '') for d in nxt]
    note = lambda d: f'<span class="note">{e(d["note"])}</span>' if d.get('note') else ''
    dates = ''.join(f'<li><span class="d">{e(lab)}</span>{note(d)}</li>' for lab, d in zip(labels, nxt)) or '<li><span class="d">Nowe terminy wkrótce</span><span class="note">Zapisz się, a damy znać jako pierwszym.</span></li>'
    facts = [('Gdzie', o.get('country') if trip else o.get('place')), ('Czas', o.get('duration')),
             ('Grupa', o.get('group')), ('Poziom', o.get('level'))]
    facts = ''.join(f'<div><dt>{k}</dt><dd>{e(v)}</dd></div>' for k, v in facts if v)
    steps = o.get('itinerary' if trip else 'program') or []
    plan = ''.join(f'<li><h3>{e(st["title"])}</h3><p>{e(st.get("text", ""))}</p></li>' for st in steps)
    inc = ''.join(f'<li>{e(x)}</li>' for x in o.get('includes') or [])
    exc = ''.join(f'<li>{e(x)}</li>' for x in o.get('excludes') or [])
    lists = (f'<div class="incl"><div><h2>W cenie</h2><ul class="yes">{inc}</ul></div>'
             + (f'<div><h2>Poza ceną</h2><ul class="no-list">{exc}</ul></div>' if exc else '') + '</div>') if inc else ''
    sub = f'<p class="sub">{e(o["subtitle"])}</p>' if o.get('subtitle') else ''
    rel = [s for s in o.get('related') or [] if s in A or s in R]
    main = f'''
  <nav class="crumbs" aria-label="Ścieżka">
    <a href="/">Strona główna</a><span aria-hidden="true">›</span><a href="/{kind}/">{section}</a><span aria-hidden="true">›</span><span>{e(o['title'])}</span>
  </nav>

  <article class="offer">
    <header class="o-head">
      {tags([offer_label(kind, o), o.get('duration')], 2)}
      <h1>{e(o['title'])}</h1>
      {sub}
      <p class="lead">{e(o['lead'])}</p>
    </header>
    <figure class="o-hero"><div class="ph frame {T()}">{img(o['image'], '(max-width:720px) 100vw, 760px', eager=True)}</div></figure>
    <aside class="o-book" aria-labelledby="h-book">
      <p class="o-price"><span>od</span> {zl(o['price'])}</p>
      <p class="meta">{e(o.get('price_note', ''))}</p>
      <dl class="facts">{facts}</dl>
      <h2 id="h-book">Terminy</h2>
      <ul class="dates">{dates}</ul>
      {booking_form(o['title'], labels, 'Zapytaj o miejsce' if trip else 'Zapisz się', 'b')}
      <p class="meta draft">Oferta przykładowa: terminy, ceny i program do potwierdzenia przed publikacją.</p>
    </aside>
    <div class="o-body">
      {body}
      <h2>{'Plan wyprawy' if trip else 'Program'}</h2>
      <ol class="plan">{plan}</ol>
      {lists}
    </div>
  </article>
{related(rel, 'Poczytaj przed wyjazdem' if trip else 'Poczytaj przed warsztatami') if rel else ''}'''
    images = [o['image']] + state['images'] + [ref_image(s) for s in rel]
    return shell(o['title'], o['lead'], main, images, current='Wyprawy' if trip else 'Warsztaty', body_class='offer-page')


def offer_list(kind):
    _tint[0] = 0
    section, _, items = KINDS[kind]
    trip = kind == 'wyprawy'
    cards = '\n      '.join(offer_card(kind, s, o) for s, o in items.items())
    intro = OFERTA.get('trips_intro' if trip else 'workshops_intro', '')
    main = f'''
  <nav class="crumbs" aria-label="Ścieżka">
    <a href="/">Strona główna</a><span aria-hidden="true">›</span><span>{section}</span>
  </nav>
  <header class="list-head">
    <h1 data-ghost="{section.split()[0]}">{section}</h1>
    <p class="lead">{e(intro)}</p>
  </header>
  <section class="sec" aria-label="{section}">
    <div class="grid grid-3 offers">
      {cards}
    </div>
  </section>
  <section class="custom" aria-labelledby="h-custom">
    <div>
      <p class="kicker">Na zamówienie</p>
      <h2 id="h-custom">{'Wyprawa dla Twojej grupy' if trip else 'Warsztaty dla firm, szkół i przyjaciół'}</h2>
      <p class="body">{e(OFERTA.get('trips_custom' if trip else 'workshops_custom', ''))}</p>
    </div>
    {booking_form(('Wyprawa' if trip else 'Warsztaty') + ' na zamówienie', [], 'Wyślij zapytanie', 'c')}
  </section>'''
    return shell(section, intro, main, [o['image'] for o in items.values()], current='Wyprawy' if trip else 'Warsztaty',
                 body_class='offer-list')


# ---------- shop (spice mixes; cart and checkout by Snipcart) ----------

SHOP_CATS = {'polska': 'Kuchnia polska', 'swiat': 'Kuchnie świata', 'kiszenie': 'Do kiszenia'}
CHILI = ('<svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24"><path fill="currentColor" d="M17.5 3c.8 1 1 2.3.6 3.4 '
         '1.6 1.1 2.3 3 1.7 5.2C18.4 17 12.6 21 5.5 21 4 21 3 20.2 3.5 19c3.5-.6 7.6-3.4 9.1-8.1.4-1.4 1.3-2.5 2.6-3 .1-1.3-.3-2.6'
         '-1-3.4z"/></svg>')


def pln(x):
    return (f'{x:.2f}'.replace('.', ',').replace(',00', '')) + '\u00a0zł'


def heat(n):
    n = int(n or 0)
    label = ['łagodna', 'lekko ostra', 'ostra', 'bardzo ostra'][min(n, 3)]
    return (f'<span class="heat" title="Ostrość: {label}"><span class="sr-only">Ostrość: {label}</span>'
            + ''.join(f'<span class="{"on" if k < n else "off"}">{CHILI}</span>' for k in range(3)) + '</span>')


def product_image_url(image):
    src = (image or {}).get('src', '')
    if src.startswith('https://images.unsplash.com/'):
        return src.split('?')[0] + '?auto=format&fit=crop&w=400&h=400&q=70'
    return src


def buy_button(slug, p, cls='btn btn-ink', label='Do koszyka'):
    """Snipcart "add to cart" button. Every size is listed with its price difference, so Snipcart's crawler
    can check the price of whichever size is in the cart; the product page's size picker sets the chosen one."""
    if not p.get('available', True):
        return f'<button type="button" class="{cls}" disabled>Chwilowo niedostępne</button>'
    if not SHOP_KEY:
        return f'<button type="button" class="{cls}" disabled>Wkrótce w sprzedaży</button>'
    sizes = p.get('sizes') or []
    attrs = {'data-item-id': slug, 'data-item-name': p['title'] + (f' — {p["subtitle"]}' if p.get('subtitle') else ''),
             'data-item-price': f'{float(p["price"]):.2f}', 'data-item-url': f'/sklep/{slug}.html',
             'data-item-description': p.get('lead', ''), 'data-item-image': product_image_url(p.get('image')),
             'data-item-categories': SHOP_CATS.get(p.get('category'), '')}
    if sizes:
        attrs['data-item-weight'] = str(sizes[0].get('weight') or 100)
        attrs['data-item-custom1-name'] = 'Opakowanie'
        attrs['data-item-custom1-options'] = '|'.join(
            sz['label'] + (f'[+{float(sz["price_delta"]):.2f}]' if sz.get('price_delta') else '') for sz in sizes)
        attrs['data-item-custom1-value'] = sizes[0]['label']
    a = ' '.join(f'{k}="{e(v)}"' for k, v in attrs.items())
    return f'<button type="button" class="{cls} snipcart-add-item" {a}>{label}</button>'


def product_card(slug, p, sizes='(max-width:720px) 50vw, 25vw'):
    badge = f'<span class="p-badge">{e(p["badge"])}</span>' if p.get('badge') else ''
    many = len(p.get('sizes') or []) > 1
    return (f'<article class="product-card" data-cat="{e(p.get("category", ""))}">'
            f'<a href="/sklep/{slug}.html" class="p-photo" tabindex="-1" aria-hidden="true"><span class="ph frame {T()} ratio-1">{img(p["image"], sizes)}</span>{badge}</a>'
            f'<div class="p-body"><p class="p-origin">{e(p.get("origin", ""))} {heat(p.get("heat"))}</p>'
            f'<h3><a href="/sklep/{slug}.html">{e(p["title"])}</a></h3><p class="p-sub">{e(p.get("subtitle", ""))}</p>'
            f'<p class="p-buy"><span class="p-price">{"od " if many else ""}{pln(float(p["price"]))}</span>'
            f'{buy_button(slug, p, "btn btn-ink btn-sm")}</p></div></article>')


def shop_notice():
    return '' if SHOP_KEY else f'<p class="shop-notice">{e(SHOP.get("notice") or "Sklep w przygotowaniu.")}</p>'


def shop_page():
    _tint[0] = 0
    cards = '\n      '.join(product_card(s, p) for s, p in PR.items())
    used = [c for c in SHOP_CATS if any(p.get('category') == c for p in PR.values())]
    chips = ''.join(f'<button type="button" class="chip" data-filter="{c}" aria-pressed="false">{SHOP_CATS[c]}</button>' for c in used)
    main = f'''
  <nav class="crumbs" aria-label="Ścieżka">
    <a href="/">Strona główna</a><span aria-hidden="true">›</span><span>Sklep</span>
  </nav>
  <header class="list-head">
    <h1 data-ghost="Spiżarnia">Sklep</h1>
    <p class="lead">{e(SHOP.get('intro', ''))}</p>
    {shop_notice()}
  </header>
  <section class="sec" aria-label="Mieszanki przypraw" data-filterable>
    <div class="chips" role="group" aria-label="Filtruj">
      <button type="button" class="chip" data-filter="all" aria-pressed="true">Wszystkie</button>
      {chips}
    </div>
    <div class="grid products">
      {cards}
    </div>
    <p class="meta" aria-live="polite" data-recipes-empty hidden>Wkrótce więcej mieszanek w tej kategorii.</p>
  </section>
  <p class="shop-ship">{e(SHOP.get('shipping', ''))}</p>'''
    return shell('Sklep', SHOP.get('intro', ''), main, [p['image'] for p in PR.values()], current='Sklep', body_class='shop-page')


def product_page(slug, p):
    _tint[0] = 0
    state = {'dropcap': False, 'images': []}
    body = '\n      '.join(x for x in (block_html(b, state) for b in p.get('body') or []) if x)
    sizes = p.get('sizes') or []
    base = float(p['price'])
    picker = ''
    if len(sizes) > 1:
        opts = ''.join(
            f'<label class="size"><input type="radio" name="size" value="{e(sz["label"])}" data-delta="{float(sz.get("price_delta") or 0):.2f}" '
            f'data-weight="{sz.get("weight") or 100}"{" checked" if k == 0 else ""}><span>{e(sz["label"])}'
            f'<b>{pln(base + float(sz.get("price_delta") or 0))}</b></span></label>' for k, sz in enumerate(sizes))
        picker = f'<fieldset class="sizes"><legend>Opakowanie</legend>{opts}</fieldset>'
    qty = ('<div class="qty"><label for="qty">Ilość</label><div class="stepper"><button type="button" data-qty="-1" aria-label="Mniej">−</button>'
           '<input id="qty" type="number" min="1" max="20" value="1" inputmode="numeric"><button type="button" data-qty="1" aria-label="Więcej">+</button></div></div>'
           if p.get('available', True) and SHOP_KEY else '')
    recs = [r for r in p.get('recipes') or [] if r in R]
    arts = [a for a in p.get('articles') or [] if a in A]
    facts = ''.join(f'<div><h2>{h}</h2><p>{e(t)}</p></div>' for h, t in (('Skład', p.get('ingredients')), ('Jak używać', p.get('use'))) if t)
    badge = f'<span class="p-badge">{e(p["badge"])}</span>' if p.get('badge') else ''
    main = f'''
  <nav class="crumbs" aria-label="Ścieżka">
    <a href="/">Strona główna</a><span aria-hidden="true">›</span><a href="/sklep/">Sklep</a><span aria-hidden="true">›</span><span>{e(p['title'])}</span>
  </nav>

  <article class="product" data-product data-base="{base:.2f}">
    <figure class="pr-photo"><div class="ph frame {T()} ratio-1">{img(p['image'], '(max-width:720px) 100vw, 50vw', eager=True)}</div>{badge}</figure>
    <div class="pr-info">
      {tags([SHOP_CATS.get(p.get('category'), ''), p.get('origin')], 2)}
      <h1>{e(p['title'])}</h1>
      <p class="sub">{e(p.get('subtitle', ''))}</p>
      <p class="pr-price"><span data-price>{pln(base)}</span> {heat(p.get('heat'))}</p>
      <p class="lead">{e(p.get('lead', ''))}</p>
      {picker}
      <div class="pr-buy">{qty}{buy_button(slug, p, 'btn btn-ink btn-buy')}</div>
      {shop_notice()}
      <p class="shop-ship">{e(SHOP.get('shipping', ''))}</p>
      <div class="pr-facts">{facts}</div>
    </div>
    <div class="pr-body">{body}</div>
  </article>
{related(recs, 'Ugotuj z tą mieszanką') if recs else ''}
{related(arts, 'Historia w słoiku') if arts else ''}'''
    images = [p['image']] + state['images'] + [ref_image(x) for x in recs + arts]
    return shell(f'{p["title"]}: {p.get("subtitle", "")}', p.get('lead', ''), main, images, current='Sklep',
                 body_class='product-page', scripts=('/js/shop.js',))


def products_for_recipe(slug):
    return [(s, p) for s, p in PR.items() if slug in (p.get('recipes') or [])]


GO = '<span class="go" aria-hidden="true"></span>'
DAYS = {'Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela'}


def tags(parts, n=3):
    """Red tag pills (after alemeksyk.eu)."""
    seen, out = set(), []
    for t in parts:
        t = (t or '').strip()
        if t and t not in seen and t not in DAYS and not t.startswith(('Odcinek', 'Część', 'Seria')):
            seen.add(t); out.append(t)
    return '<span class="tags">' + ''.join(f'<span class="tag">{e(t)}</span>' for t in out[:n]) + '</span>'


def article_tags(a, n=3):
    return tags([a['section']] + a['kicker'].split(' · '), n)


def datepill(a):
    d = a.get('date') or ''
    return f'<span class="date">{d[8:10]}.{d[5:7]}.{d[:4]}</span>' if len(d) == 10 else ''


def wpisy(n):
    few = n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14)
    return f'{n} {"wpis" if n == 1 else "wpisy" if few else "wpisów"}'


def home_page():
    _tint[0] = 0
    H = HOME
    L = H['lead']
    lead = A[L['article']]
    images = [lead['image']]

    def numbered(slug):
        return f'<span class="no">№ {no(slug)}</span>'

    def week_card(w):
        a = A[w['article']]; images.append(a['image'])
        return (f'<a href="/historie/{a["slug"]}.html" class="card week-card">'
                f'<p class="day"><em>{e(w["day"])}</em> <span>{e(w.get("date", ""))}</span></p>'
                f'<div class="ph frame {T()} ratio-45">{img(a["image"], "(max-width:720px) 100vw, 33vw")}</div>'
                f'<div class="card-body">{article_tags(a, 2)}'
                f'<h3>{e(a["title"])}</h3><p class="excerpt">{e(first_sentence(a["lead"]))}</p><p class="pills">{numbered(a["slug"])}{datepill(a)}</p></div></a>')

    def side_article(slug):
        a = A[slug]; images.append(a['image'])
        return (f'<a href="/historie/{slug}.html" class="card row">{framed(img(a["image"], "120px"))}'
                f'<div class="card-body"><p class="kicker">{numbered(slug)} Historia</p><h4>{e(a["title"])}</h4></div></a>')

    def side_recipe(slug, title):
        r = R[slug]; im = recipe_card_image(r); images.append(im)
        return (f'<a href="/przepisy/{slug}.html" class="card row">{framed(img(im, "120px"))}'
                f'<div class="card-body"><p class="kicker"><span class="no">{rno(slug)}</span> Przepis</p><h4>{e(title or r["title"])}</h4></div></a>')

    def recipe_tile(slug):
        r = R[slug]; im = recipe_card_image(r); images.append(im)
        return (f'<a href="/przepisy/{slug}.html" class="ov ov-tile" data-cat="{e(r["category"])}">{img(im, "(max-width:720px) 70vw, 25vw")}'
                f'<span class="ov-body">{tags([CAT.get(r["category"], "")] + (r.get("card_meta") or "").split(" · ")[:1])}'
                f'<span class="h">{e(r["title"])}</span><span class="pills"><span class="no">{rno(slug)}</span></span></span></a>')

    def travel_card(slug):
        a = A[slug]; images.append(a['image'])
        place = a.get('place') or a['section']
        return (f'<a href="/historie/{slug}.html" class="travel-item"><span class="vlabel">{e(place)}</span>'
                f'{framed(img(a["image"], "(max-width:720px) 100vw, 22vw"), "ratio-1")}'
                f'<span class="travel-t"><span class="no">№ {no(slug)}</span><span class="h">{e(a["title"])}</span>'
                f'<span class="excerpt">{e(first_sentence(a["lead"]))}</span>{GO}</span></a>')

    def overlay(slug, cls='', sizes='(max-width:720px) 100vw, 30vw'):
        a = A[slug]; images.append(a['image'])
        return (f'<article class="ov {cls}">{img(a["image"], sizes)}<div class="ov-body">{article_tags(a)}'
                f'<h2 class="h"><a class="stretch" href="/historie/{slug}.html">{e(a["title"])}</a></h2>'
                f'<p class="pills">{numbered(slug)}{datepill(a)}</p></div></article>')

    def shortcut(label, href, image, count):
        images.append(image)
        return (f'<a class="shortcut" href="{href}"><span class="ring">{img(image, "120px")}</span>'
                f'<span class="h">{e(label)}</span><span class="n">{count if isinstance(count, str) else wpisy(count)}</span></a>')

    by_section = lambda sec: [a for a in A.values() if a['section'] == sec]
    shortcuts = []
    for label, href, sec in [('Historie', '#nowe', 'Historie'), ('Wideo', '#staropolska', 'Wideo'),
                             ('Smaki regionów', '#regiony', 'Smaki regionów'), ('Z podróży', '#podroze', 'Z podróży')]:
        items = by_section(sec)
        if items:
            shortcuts.append(shortcut(label, href, items[0]['image'], len(items)))
    if R:
        shortcuts.insert(1, shortcut('Przepisy', '#przepisy', recipe_card_image(next(iter(R.values()))), len(R)))
    images += [o['image'] for o in list(WS.values())[:3] + list(TR.values())[:3] + list(PR.values())[:4]]
    if WS:
        n = sum(len(upcoming(o)) for o in WS.values())
        shortcuts.append(shortcut('Warsztaty', '/warsztaty/', next(iter(WS.values()))['image'],
                                  f'{n} {"termin" if n == 1 else "terminy" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "terminów"}'))
    if PR:
        n = len(PR)
        shortcuts.append(shortcut('Sklep', '/sklep/', next(iter(PR.values()))['image'],
                                  f'{n} {"mieszanka" if n == 1 else "mieszanki" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "mieszanek"}'))
    if TR:
        n = len(TR)
        shortcuts.append(shortcut('Wyprawy', '/wyprawy/', next(iter(TR.values()))['image'],
                                  f'{n} {"wyprawa" if n == 1 else "wyprawy" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "wypraw"}'))

    op = H['old_polish']
    feat = A[op['feature']]; images.append(feat['image'])
    sides = [s for s in (op.get('side_articles') or []) if s in A]
    side = [side_article(sides[0])] if sides else []
    if op.get('side_recipe') in R:
        side.append(side_recipe(op['side_recipe'], op.get('side_recipe_title')))
    side += [side_article(s) for s in sides[1:]]

    stories = {s['region']: s for s in H['regions'].get('stories', []) if s.get('article') in A}

    def tile(name, r):
        s = stories.get(name)
        extra = f' data-story="/historie/{s["article"]}.html" data-story-label="{e(s.get("label") or A[s["article"]]["title"])}"' if s else ''
        label = f'{name}, jest odcinek' if s else name
        return (f'        <path class="tile{" has-story" if s else ""}" d="{r["d"]}" data-region="{name}"{extra} '
                f'role="button" tabindex="0" aria-label="{label}"><title>{name}</title></path>')

    def pin(name, r):
        return (f'        <g class="pin" transform="translate({r["x"]} {r["y"]})"><circle r="7"/><circle class="dot" r="2.6"/>'
                f'<text y="-13">{name}</text></g>')

    # "Smaki świata": countries with stories (articles or recipes) chosen in the CMS
    by_country = {}
    for slug, o in TR.items():
        if o.get('country') in WORLD['regions']:
            by_country.setdefault(o['country'], []).append([f'/wyprawy/{slug}.html', f'Wyprawa: {o["title"]}'])
    for st in (H.get('world') or {}).get('stories', []):
        href = (f'/historie/{st["article"]}.html' if st.get('article') in A else
                f'/przepisy/{st["recipe"]}.html' if st.get('recipe') in R else None)
        if not href or st.get('country') not in WORLD['regions']:
            print('  ! Smaki świata: skipped', st, file=sys.stderr); continue
        title = A[st['article']]['title'] if st.get('article') in A else R[st['recipe']]['title']
        by_country.setdefault(st['country'], []).append([href, st.get('label') or title])

    def country(name, r):
        st = by_country.get(name)
        if not st:
            return f'        <path class="tile" d="{r["d"]}" data-country="{e(name)}"><title>{e(name)}</title></path>'
        return (f'        <path class="tile has-story" d="{r["d"]}" data-country="{e(name)}" data-stories="{e(json.dumps(st, ensure_ascii=False))}" '
                f'role="button" tabindex="0" aria-label="{e(name)}: {wpisy(len(st))}"><title>{e(name)}</title></path>')

    countries = '\n'.join(country(n, r) for n, r in WORLD['regions'].items())
    world_pins = '\n'.join(pin(n, WORLD['regions'][n]) for n in by_country)
    world_chips = '\n'.join(f'        <button type="button" class="chip" data-country="{e(n)}" aria-pressed="false">{e(n)}</button>' for n in by_country)
    nk = len(by_country)
    kraje = 'kraj' if nk == 1 else 'kraje' if nk % 10 in (2, 3, 4) and nk % 100 not in (12, 13, 14) else 'krajów'

    regions = MAP['regions']
    tiles = '\n'.join(tile(n, r) for n, r in regions.items())
    pins = '\n'.join(pin(n, regions[n]) for n in stories if n in regions)
    chips = '\n'.join(f'        <button type="button" class="chip" data-region="{c}" aria-pressed="false">{c}</button>' for c in CHIPS)
    issue = [s for s in H.get('issue_list', []) if s in A]
    lead_recipe = f'<a href="/przepisy/{L["recipe"]}.html" class="tag tag-link">Przepis →</a>' if L.get('recipe') in R else ''

    main = f"""
  <section class="mosaic" aria-label="Historia tygodnia">
    <article class="ov ov-lead">
      {img(lead['image'], '(max-width:720px) 100vw, 66vw', eager=True)}
      <div class="ov-body">
        {article_tags(lead)}
        <h1 class="h"><a class="stretch" href="/historie/{lead['slug']}.html">{e(lead['title'])}</a></h1>
        <p class="lead">{e(L.get('text') or lead['lead'])}</p>
        <p class="pills">{numbered(lead['slug'])}{datepill(lead)}{lead_recipe}</p>
      </div>
    </article>
    {''.join(overlay(s, 'ov-side') for s in issue[:2])}
  </section>

  <section class="sec shortcuts-sec" aria-labelledby="h-skroty">
    <div class="sec-head"><h2 id="h-skroty" data-ghost="Na skróty">Na skróty</h2></div>
    <nav class="shortcuts" aria-label="Działy">
      {''.join(shortcuts)}
    </nav>
  </section>

  <section class="sec" id="nowe" aria-labelledby="h-nowe">
    <div class="sec-head">
      <h2 id="h-nowe" data-ghost="W tym tygodniu">Nowe w tym tygodniu</h2>
      <p class="meta">{e(H.get('issue', ''))}</p>
    </div>
    <div class="grid grid-3 week">
      {''.join(week_card(w) for w in H.get('week', []) if w.get('article') in A)}
    </div>
  </section>

  <section class="bleed dark" id="staropolska" aria-labelledby="h-staro">
    <div class="bleed-in">
      <div class="sec-head">
        <h2 id="h-staro" data-ghost="Staropolska">{e(op.get('title') or 'Kuchnia staropolska')}</h2>
        <a href="/historie/{(sides or [feat['slug']])[0]}.html">Cała seria →</a>
      </div>
      <div class="feature">
        <a href="/historie/{feat['slug']}.html" class="card feature-main">
          <div class="ph frame {T()} ratio-1610">{img(feat['image'], '(max-width:720px) 100vw, 62vw')}
            <span class="play">{PLAY}</span>
          </div>
          <p class="kicker">{numbered(feat['slug'])} {e(op.get('feature_label', ''))}</p>
          <h3>{e(feat['title'])}</h3>
          <p class="body">{e(first_sentence(feat['lead']))}</p>
        </a>
        <div class="feature-side">
          {''.join(side)}
        </div>
      </div>
    </div>
  </section>

  <section class="regions" id="regiony" aria-labelledby="h-regiony" data-regions>
    <div class="map" role="group" aria-label="Mapa województw">
      <svg class="pl-map" viewBox="{MAP['viewBox']}" xmlns="http://www.w3.org/2000/svg">
{tiles}
        <g class="pins" aria-hidden="true">
{pins}
        </g>
      </svg>
      <p class="map-key" aria-hidden="true"><span class="sw has"></span> Jest odcinek <span class="sw soon"></span> Wkrótce</p>
    </div>
    <div class="regions-copy">
      <p class="counter" aria-hidden="true">{len(stories):02d}<span>/16</span></p>
      <p class="kicker">Seria w 16 częściach</p>
      <h2 id="h-regiony">Smaki regionów</h2>
      <p class="body">{e(H['regions'].get('intro', ''))}</p>
      <div class="chips">
{chips}
        <a href="#regiony" class="chip" data-regions-more>+ 9 kolejnych</a>
      </div>
      <p class="region-pick" aria-live="polite" data-region-out></p>
    </div>
  </section>

  <section class="regions world" id="swiat" aria-labelledby="h-swiat" data-world>
    <div class="regions-copy">
      <p class="counter" aria-hidden="true">{nk:02d}<span> {kraje}</span></p>
      <p class="kicker">Z podróży</p>
      <h2 id="h-swiat">Smaki świata</h2>
      <p class="body">{e((H.get('world') or {}).get('intro', ''))}</p>
    </div>
    <div class="world-side">
      <div class="chips" role="group" aria-label="Kraje">
{world_chips}
      </div>
      <div class="world-pick" aria-live="polite" data-world-out><p class="meta">Wybierz kraj, żeby zobaczyć historie i przepisy.</p></div>
    </div>
    <div class="map world-map" role="group" aria-label="Mapa świata">
      <svg class="pl-map w-map" viewBox="{WORLD['viewBox']}" xmlns="http://www.w3.org/2000/svg">
{countries}
        <g class="pins" aria-hidden="true">
{world_pins}
        </g>
      </svg>
      <p class="map-key" aria-hidden="true"><span class="sw has"></span> Nasze historie <span class="sw soon"></span> Jeszcze tu nie byliśmy</p>
    </div>
  </section>

  <section class="sec" id="przepisy" aria-labelledby="h-przepisy" data-recipes>
    <div class="sec-head">
      <h2 id="h-przepisy" data-ghost="Przepisy">Przepisy</h2>
      <a href="#przepisy">Wszystkie przepisy →</a>
    </div>
    <div class="chips" role="group" aria-label="Filtruj przepisy">
      <button type="button" class="chip" data-filter="all" aria-pressed="true">Wszystkie</button>
      {''.join(f'<button type="button" class="chip" data-filter="{k}" aria-pressed="false">{v}</button>' for k, v in CAT.items())}
    </div>
    <div class="rail">
      {''.join(recipe_tile(s) for s in H.get('recipes', []) if s in R)}
    </div>
    <p class="meta" aria-live="polite" data-recipes-empty hidden>Wkrótce więcej przepisów w tej kategorii.</p>
  </section>

  <section class="sec shop-sec" id="sklep" aria-labelledby="h-sklep" data-filterable>
    <div class="sec-head">
      <h2 id="h-sklep" data-ghost="Spiżarnia">Ze spiżarni Łowcy</h2>
      <a href="/sklep/">Cały sklep →</a>
    </div>
    <p class="sec-intro">{e(SHOP.get('intro', ''))}</p>
    <div class="grid products">
      {''.join(product_card(s, p) for s, p in list(PR.items())[:4])}
    </div>
  </section>

  <section class="sec offers-sec" id="warsztaty" aria-labelledby="h-warsztaty">
    <div class="sec-head">
      <h2 id="h-warsztaty" data-ghost="Warsztaty">Warsztaty</h2>
      <a href="/warsztaty/">Wszystkie warsztaty →</a>
    </div>
    <p class="sec-intro">{e(OFERTA.get('workshops_intro', ''))}</p>
    <div class="grid grid-3 offers">
      {''.join(offer_card('warsztaty', s, o) for s, o in list(WS.items())[:3])}
    </div>
  </section>

  <section class="sec travel-split" id="podroze" aria-labelledby="h-podroze">
    <div class="travel-panel">
      <div class="travel-panel-in">
        <p class="kicker">Reportaże</p>
        <h2 id="h-podroze">Z podróży</h2>
        <p class="body">Targi, kuchnie i ludzie: jedzenie oglądane tam, gdzie się rodzi.</p>
        <a href="/historie/{(H.get('travel') or ['peru-ziemniaki'])[0]}.html" class="btn btn-line">Wszystkie reportaże</a>
      </div>
    </div>
    <div class="travel-list">
      {''.join(travel_card(s) for s in H.get('travel', []) if s in A)}
    </div>
  </section>

  <section class="bleed trips-band" id="wyprawy" aria-labelledby="h-wyprawy">
    <div class="bleed-in">
      <div class="sec-head">
        <h2 id="h-wyprawy" data-ghost="Wyprawy">Wyprawy kulinarne</h2>
        <a href="/wyprawy/">Wszystkie wyprawy →</a>
      </div>
      <p class="sec-intro">{e(OFERTA.get('trips_intro', ''))}</p>
      <div class="grid grid-3 offers">
        {''.join(offer_card('wyprawy', s, o) for s, o in list(TR.items())[:3])}
      </div>
    </div>
  </section>

  <section class="statement" id="newsletter" aria-labelledby="h-nl">
    <h2 id="h-nl">Jedna historia.<br>Jeden przepis.<br><em>Co tydzień.</em></h2>
    <form class="nl-form" name="newsletter" method="POST" data-netlify="true" netlify-honeypot="bot-field" data-newsletter>
      <input type="hidden" name="form-name" value="newsletter">
      <p class="sr-only"><label>Nie wypełniaj <input name="bot-field" tabindex="-1"></label></p>
      <p class="body">{e((H.get('newsletter') or {}).get('text', ''))}</p>
      <label for="nl-email">Adres e-mail</label>
      <div class="nl-row">
        <input id="nl-email" name="email" type="email" required placeholder="ty@przyklad.pl" autocomplete="email">
        <button type="submit">Zapisz się</button>
      </div>
      <p class="nl-msg" aria-live="polite" data-nl-msg></p>
    </form>
  </section>
"""
    return shell('Łowca Smaków — antropologia jedzenia', 'Antropologia jedzenia: skąd się wzięło to, co jemy — i jak to ugotować.',
                 main, images, body_class='home', home=True, scripts=('/js/globe.js',))


def main():
    for d in ('historie', 'przepisy', 'warsztaty', 'wyprawy', 'sklep'):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    # pages for content deleted in the CMS disappear too
    for d, have in (('historie', A), ('przepisy', R), ('warsztaty', WS), ('wyprawy', TR), ('sklep', PR)):
        for f in glob.glob(os.path.join(ROOT, d, '*.html')):
            name = os.path.splitext(os.path.basename(f))[0]
            if name not in have and name != 'index':
                os.remove(f)
    open(os.path.join(ROOT, 'sklep', 'index.html'), 'w', encoding='utf-8').write(shop_page())
    for slug, pr in PR.items():
        open(os.path.join(ROOT, 'sklep', f'{slug}.html'), 'w', encoding='utf-8').write(product_page(slug, pr))
    for kind, (_, _, items) in KINDS.items():
        open(os.path.join(ROOT, kind, 'index.html'), 'w', encoding='utf-8').write(offer_list(kind))
        for slug, o in items.items():
            open(os.path.join(ROOT, kind, f'{slug}.html'), 'w', encoding='utf-8').write(offer_page(kind, slug, o))
    for a in A.values():
        open(os.path.join(ROOT, 'historie', f"{a['slug']}.html"), 'w', encoding='utf-8').write(article_page(a))
    for slug, r in R.items():
        open(os.path.join(ROOT, 'przepisy', f'{slug}.html'), 'w', encoding='utf-8').write(recipe_page(slug, r))
    open(os.path.join(ROOT, 'js', 'recipe-data.js'), 'w', encoding='utf-8').write(recipe_data_js())
    open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(home_page())
    print(f'index, {len(A)} articles, {len(R)} recipes, {len(WS)} workshops, {len(TR)} trips, {len(PR)} products'
          + ('' if SHOP_KEY else ' (shop: no Snipcart key yet, buttons say "coming soon")'))


if __name__ == '__main__':
    main()
