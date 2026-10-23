#!/usr/bin/env python3
"""Builds the article and recipe pages from scripts/content.py.

    python3 scripts/build.py

Writes historie/<slug>.html, przepisy/<slug>.html and img/orn/*.svg.
The homepage (index.html), cook mode and 404 are hand-written.
"""
import html
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import ARTICLES, RECIPE_PAGES, RECIPE_CARDS  # noqa: E402
from ornaments import inline, write_files  # noqa: E402
from photos import img, credits  # noqa: E402

A = {a['slug']: a for a in ARTICLES}
FONTS = ('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500'
         '&amp;family=Instrument+Sans:wght@400;500;600&amp;display=swap')
SEARCH = ('<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
          'stroke-width="1.6" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>')
MENU = ('<svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>')
NAV = [('Historie', '/#nowe'), ('Przepisy', '/#przepisy'), ('Wideo', '/#staropolska'),
       ('Podróże', '/#podroze'), ('Smaki regionów', '/#regiony'), ('Sklep', '/przepisy/slimaki-w-szarym-sosie.html#sklep')]
e = html.escape


def shell(title, desc, main, photo_keys, current=None, body_class='', body_attrs='', scripts=()):
    nav = '\n'.join(f'    <a class="navlink" href="{h}"{" aria-current=\"page\"" if n == current else ""}>{n}</a>' for n, h in NAV)
    js = '\n'.join(f'<script src="{s}"></script>' for s in ('/js/site.js', *scripts))
    return f'''<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} — Łowca Smaków</title>
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
  <div class="wrap masthead">
    <div class="left">
      <button class="icon-btn" type="button" aria-label="Szukaj" aria-expanded="false" aria-controls="search" data-search-toggle>
        {SEARCH}
      </button>
    </div>
    <a href="/" class="logo"><img src="/img/logo.svg" alt="Łowca Smaków" width="199" height="96"></a>
    <div class="header-actions">
      <button class="icon-btn menu-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="main-nav" data-menu-toggle>
        {MENU}
      </button>
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

<main class="wrap" id="tresc">
{main}
{newsletter()}
</main>

<footer class="site-footer slim">
  <div class="wrap">
    <a href="/" class="logo"><img src="/img/logo-white.svg" alt="Łowca Smaków" width="149" height="72"></a>
    <p class="meta">© 2026 Savour Ventures OÜ</p>
    {credits(photo_keys)}
  </div>
</footer>

{js}
</body>
</html>
'''


def newsletter():
    return f'''
  <section class="newsletter slim" aria-labelledby="h-nl">
    <div class="nl-copy">
      {inline('flourish', 'flourish draw')}
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


def card(href, key, kicker, title, sizes='(max-width:720px) 50vw, 25vw'):
    return (f'<a href="{href}" class="card sm"><div class="ph" style="height:220px">{img(key, sizes)}</div>'
            f'<p class="kicker">{e(kicker)}</p><h3>{e(title)}</h3></a>')


def article_card(slug):
    a = A[slug]
    return card(f'/historie/{slug}.html', a['img'], a['kicker'].split(' · ')[0] if a['section'] != 'Z podróży' else a['kicker'].split(' · ')[-1], a['title'])


def recipe_card(slug):
    key, meta, title, _ = RECIPE_CARDS[slug]
    return card(f'/przepisy/{slug}.html', key, 'Przepis', title)


def related(slugs, heading='Czytaj dalej', note=''):
    cards = '\n      '.join(recipe_card(s) if s in RECIPE_CARDS else article_card(s) for s in slugs)
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


def body_html(blocks):
    out, first = [], True
    for kind, val in blocks:
        if kind == 'p':
            out.append(f'<p{" class=\"dropcap\"" if first else ""}>{e(val)}</p>')
            first = False
        elif kind == 'h2':
            out.append(f'<h2>{e(val)}</h2>')
        elif kind == 'quote':
            out.append(f'<blockquote class="pull">{inline("fork", "pull-fork draw")}<p>{e(val)}</p>{inline("knife", "pull-knife draw")}</blockquote>')
        elif kind == 'img':
            out.append(f'<figure class="a-fig"><div class="ph">{img(val, "(max-width:720px) 100vw, 760px")}</div></figure>')
    return '\n      '.join(out)


def words(blocks):
    return sum(len(v.split()) for k, v in blocks if k in ('p', 'h2', 'quote'))


def article_page(a):
    mins = max(2, math.ceil((words(a['body']) + len(a['lead'].split())) / 200))
    others = [s for s in A if s != a['slug']]
    same = [s for s in others if A[s]['section'] == a['section']]
    rel = ([a['recipe']] if a.get('recipe') else []) + same + [s for s in others if s not in same]
    rel = rel[:3]
    recipe_box = ''
    if a.get('recipe'):
        key, meta, title, _ = RECIPE_CARDS[a['recipe']]
        recipe_box = f'''
      <aside class="a-recipe" aria-label="Przepis do tego tekstu">
        <div class="ph">{img(key, '160px')}</div>
        <div>
          <p class="kicker">Przepis do tego tekstu</p>
          <h2><a href="/przepisy/{a['recipe']}.html">{e(title)}</a></h2>
          <p class="meta">{e(meta)}</p>
        </div>
      </aside>'''
    main = f'''
  <nav class="crumbs" aria-label="Ścieżka">
    <a href="/">Strona główna</a><span aria-hidden="true">›</span><span>{e(a['section'])}</span>
  </nav>

  <article class="article">
    <header class="a-head">
      {inline('plate', 'a-plate draw')}
      <p class="kicker">{e(a['kicker'])}</p>
      <h1>{e(a['title'])}</h1>
      <p class="lead">{e(a['lead'])}</p>
      <p class="meta">{mins} min czytania · <span class="draft">Tekst roboczy, do weryfikacji przed publikacją</span></p>
    </header>
    <figure class="a-hero"><div class="ph">{img(a['img'], '(max-width:720px) 100vw, 1216px', eager=True)}</div></figure>
    <div class="a-body">
      {body_html(a['body'])}
      {recipe_box}
    </div>
  </article>
{related(rel)}'''
    keys = [a['img']] + [v for k, v in a['body'] if k == 'img'] + \
           ([RECIPE_CARDS[a['recipe']][0]] if a.get('recipe') else []) + \
           [RECIPE_CARDS[s][0] if s in RECIPE_CARDS else A[s]['img'] for s in rel]
    return shell(a['title'], a['lead'], main, keys, current=None, body_class='article-page')


def recipe_page(slug, r):
    name = RECIPE_CARDS[slug][2]
    video = ('<button type="button" class="watch" disabled title="Wideo wkrótce"><span><svg aria-hidden="true" width="14" height="14" '
             'viewBox="0 0 24 24" fill="#FFFFFF"><path d="M8 5v14l11-7z"/></svg></span>Obejrzyj odcinek · [mm:ss]</button>') if r['video'] else ''
    shop = ''
    if r['shop']:
        k, label, title = r['shop']
        shop = f'''
      <div class="shop" id="sklep">
        <div class="ph">{img(k, '64px')}</div>
        <div>
          <p class="label">{e(label)}</p>
          <p style="font-weight:600">[{e(title)}]</p>
        </div>
      </div>'''
    sources = ''
    if r['sources']:
        srcs = ''.join(f'<p>{s}</p>' for s in r['sources'])
        sources = f'<div class="sources"><p class="kicker">Źródła</p>{srcs}</div>'
    a1, a2 = r['aside']
    main = f'''
  <nav class="crumbs" aria-label="Ścieżka">
    <a href="/#przepisy">Przepisy</a><span aria-hidden="true">›</span><a href="{r['crumb'][1]}">{e(r['crumb'][0])}</a><span aria-hidden="true">›</span><span aria-current="page">{e(name)}</span>
  </nav>

  <section class="r-head">
    <div class="r-title">
      <p class="kicker">{e(r['kicker'])}</p>
      <h1>{e(name)}</h1>
      <p class="sub">{e(r['sub'])}</p>
    </div>
    <dl class="r-stats">
      <div><dt class="meta">Przygotowanie</dt><dd>{e(r['prep'])}</dd></div>
      <div><dt class="meta">Gotowanie</dt><dd>{e(r['cook'])}</dd></div>
      <div><dt class="meta" data-servings-label>Porcje</dt><dd data-servings-stat></dd></div>
      <div><dt class="meta">Trudność</dt><dd>{e(r['level'])}</dd></div>
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
    <div class="ph">{img(r['img'], '(max-width:720px) 100vw, 60vw', eager=True)}
      {video}
    </div>
    <aside class="pill-history" aria-labelledby="h-pigulka">
      {inline('plate', 'pill-plate')}
      <p class="kicker" id="h-pigulka">{e(r['aside_title'])}</p>
      <div class="ph">{img(r['aside_img'], '(max-width:720px) 100vw, 40vw')}</div>
      <p class="serif">{e(a1)}</p>
      <p class="body" style="font-size:15px">{e(a2)}</p>
      <a href="/historie/{r['story']}.html" style="font-weight:600;font-size:15px">Przeczytaj całą historię →</a>
    </aside>
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
{related(r['related'], 'Z tej samej opowieści', 'Dobrane po serii, regionie i składnikach')}'''
    keys = [r['img'], r['aside_img']] + ([r['shop'][0]] if r['shop'] else []) + \
           [RECIPE_CARDS[s][0] if s in RECIPE_CARDS else A[s]['img'] for s in r['related']]
    return shell(name, r['sub'], main, keys, current='Przepisy', body_class='recipe',
                 body_attrs=f' data-recipe="{slug}"', scripts=('/js/recipes.js', '/js/recipe.js'))


def main():
    write_files(ROOT)
    for d in ('historie', 'przepisy'):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    for a in ARTICLES:
        open(os.path.join(ROOT, 'historie', f"{a['slug']}.html"), 'w').write(article_page(a))
    for slug, r in RECIPE_PAGES.items():
        open(os.path.join(ROOT, 'przepisy', f'{slug}.html'), 'w').write(recipe_page(slug, r))
    print(f'{len(ARTICLES)} articles, {len(RECIPE_PAGES)} recipes')


if __name__ == '__main__':
    main()
