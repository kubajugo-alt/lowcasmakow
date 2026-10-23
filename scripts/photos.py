# Placeholder photos from Unsplash (Unsplash License), hotlinked from images.unsplash.com.
import html

P = {  # key: (photo path, author, username, alt)
 'hero':       ('photo-1627861446476-42fd9925e151', 'Townsend Walton', 'twalton', 'Słoiki z kiszonymi ogórkami, koperkiem i czosnkiem'),
 'hero2':      ('photo-1462536546956-beef6399d8cf', 'Jonathan Pielmayer', 'jonathanpielmayer', 'Małe ogórki w durszlaku obok pęczka koperku'),
 'reel':       ('photo-1766309593183-8f77e6ee51d6', 'Jakub Żerdzicki', 'jakubzerdzicki', 'Ręce nakładające farsz na krążki ciasta na pierogi'),
 'region':     ('photo-1792582232028-0d8b0c703797', 'Maharram Hasanli', 'maharram', 'Drewniany dom w stylu podhalańskim wśród jesiennych drzew'),
 'milkbar':    ('photo-1612966948332-81d747414a8f', 'Karolina Kołodziejczak', 'rabbit_in_blue', 'Rosół z warzywami w porcelanowej wazie'),
 'snails':     ('photo-1585684278140-f6b0e42a9bc0', 'Ali Robins', 'aliphotos_86', 'Ślimaki w muszlach na żeliwnej patelni'),
 'snails3':    ('photo-1549413468-24b18ebf5d9c', 'Maria Orlova', 'orlovamaria', 'Ślimaki zapiekane z masłem ziołowym w ceramicznym naczyniu'),
 'snailfarm':  ('photo-1621447096587-2f9d8fa16953', 'Olivier Piau', 'o_piau', 'Ślimak na zielonych liściach'),
 'oldbook':    ('photo-1519884705082-b505c3001e63', 'Sergiu Vălenaș', 'svalenas', 'Stara, otwarta księga w ciepłym świetle'),
 'engraving':  ('photo-1602660187275-7275b639d7ea', 'Boudewijn Huysmans', 'boudewijn_huysmans', 'Średniowieczny rękopis na pergaminie'),
 'engraving2': ('photo-1467688695332-6b486449d78f', 'Mark Rasmuson', 'mrasmuson', 'Strony dawnej księgi zapisane gotyckim pismem'),
 'gingerbread':('photo-1768216604497-ecbf03ab5fa0', 'Ksenia Yakovleva', 'ksyfffka07', 'Korzenne ciasto z orzechami i lukrem'),
 'birria':     ('photo-1585803518902-58a3ef005b51', 'Diego Lozano', 'diegonacho', 'Tacos de birria z cebulą i kolendrą, obok miska consommé'),
 'potatodish': ('photo-1633959639799-6d3f66e05710', 'Markus Winkler', 'markuswinkler', 'Pieczone ziemniaki z natką pietruszki na talerzu'),
 'perumarket': ('photo-1683543124235-400a2b31cc73', 'engin akyurt', 'enginakyurt', 'Ziemniaki na straganie targowym'),
 'mexico':     ('photo-1752627580142-8ea39c4eac64', 'stephan de MARANTHI', 'maranthi', 'Czerwone papryczki chile suszące się na słońcu'),
 'market':     ('photo-1545504573-edac76c6a487', 'Daniel Lerman', 'dlerman6', 'Kobieta przygotowująca jedzenie na ulicznym targu'),
 'spices':     ('photo-1611255951322-7ba28f02b2d5', 'Diana Polekhina', 'diana_pole', 'Słoiczki z rozsypanymi przyprawami'),
}
UTM = 'utm_source=lowca_smakow&amp;utm_medium=referral'


def img(key, sizes, eager=False):
    path, _, _, alt = P[key]
    base = f'https://images.unsplash.com/{path}?auto=format&amp;fit=crop&amp;q=70'
    srcset = ', '.join(f'{base}&amp;w={w} {w}w' for w in (480, 800, 1200, 1800))
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return f'<img class="fill" src="{base}&amp;w=1200" srcset="{srcset}" sizes="{sizes}" alt="{alt}" {load} decoding="async">'


def credits(keys):
    seen, parts = [], []
    for k in keys:
        if k in seen:
            continue
        seen.append(k)
        _, a, u, _ = P[k]
        parts.append(f'<a href="https://unsplash.com/@{u}?{UTM}">{html.escape(a)}</a>')
    return ('<p class="meta credits">Zdjęcia zastępcze: ' + ', '.join(parts) +
            f' · <a href="https://unsplash.com/?{UTM}">Unsplash</a></p>')
