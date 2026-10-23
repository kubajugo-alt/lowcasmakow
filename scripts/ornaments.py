# Line ornaments taken from the logo: plate rings, fork, knife, looping tendril.
# Inline versions use currentColor (and pathLength=1 so they can draw themselves in);
# file versions in img/orn/ are fixed-colour backgrounds for CSS.
import os

W = 'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" fill="none"'

FLOURISH = 'M2 18C40 18 70 18 92 16C104 15 112 6 106 4C99 2 96 14 104 20C112 26 124 22 128 14C131 8 124 4 120 10C116 16 126 18 140 18C170 18 196 18 218 18'
CURL = 'M64 16H36C26 16 22 5 14 5C6 5 4 15 11 19C18 23 26 17 22 10'
TENDRIL = 'M0 18H96C106 18 116 12 115 6C114 0 104 1 104 8C104 16 113 20 124 18C130 17 135 18 144 18H240'
FORK = ('M8 4V38C8 50 14 56 17 58V152C17 157 23 157 23 152V58C26 56 32 50 32 38V4'
        'M14.5 4V34M20 4V34M25.5 4V34')
KNIFE = 'M21 4C31 12 33 42 30 70C29 79 25 82 25 87V152C25 157 17 157 17 152V84C13 72 12 32 21 4Z'
PLATE_OUT = 'M100 8C151 8 192 49 192 100C192 151 151 192 100 192C49 192 8 151 8 100C8 49 49 8 110 8.6'
PLATE_IN = 'M100 28C140 28 172 60 172 100C172 140 140 172 100 172C60 172 28 140 28 100C28 60 60 28 106 28.3'
PLATE_TAIL = 'M162 162C176 176 190 176 198 166'


def inline(kind, cls='', label=None):
    aria = f'role="img" aria-label="{label}"' if label else 'aria-hidden="true"'
    c = f' class="{cls}"' if cls else ''
    p = lambda d: f'<path pathLength="1" d="{d}"/>'
    if kind == 'flourish':
        return f'<svg{c} viewBox="0 0 220 28" {aria} {W} stroke="currentColor">{p(FLOURISH)}</svg>'
    if kind == 'fork':
        return f'<svg{c} viewBox="0 0 40 160" {aria} {W} stroke="currentColor">{p(FORK)}</svg>'
    if kind == 'knife':
        return f'<svg{c} viewBox="0 0 42 160" {aria} {W} stroke="currentColor">{p(KNIFE)}</svg>'
    if kind == 'plate':
        return f'<svg{c} viewBox="0 0 210 200" {aria} {W} stroke="currentColor">{p(PLATE_OUT)}{p(PLATE_IN)}{p(PLATE_TAIL)}</svg>'
    if kind == 'setting':  # fork | plate | knife, joined by loops, like the logo without its lettering
        return (f'<svg{c} viewBox="0 0 420 170" {aria} {W} stroke="currentColor">'
                f'<g transform="translate(70 5)">{p(FORK)}</g>'
                f'<g transform="translate(130 0) scale(.8)">{p(PLATE_OUT)}{p(PLATE_IN)}</g>'
                f'<g transform="translate(305 5)">{p(KNIFE)}</g>'
                f'{p("M2 96C20 96 30 84 26 76C22 68 12 74 16 84C20 94 40 98 70 92")}'
                f'{p("M348 92C376 98 396 94 400 84C404 74 394 68 390 76C386 84 396 96 418 96")}'
                f'{p("M262 140C280 150 300 140 318 110")}'
                f'</svg>')
    raise ValueError(kind)


def write_files(root):
    d = os.path.join(root, 'img', 'orn')
    os.makedirs(d, exist_ok=True)
    def svg(name, vb, paths, color, width=1.4):
        body = ''.join(f'<path d="{x}"/>' for x in paths)
        open(os.path.join(d, name), 'w').write(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">{body}</svg>\n')
    svg('curl.svg', '0 0 64 26', [CURL], '#121212')
    svg('tendril.svg', '0 0 240 26', [TENDRIL], '#121212')
    svg('tendril-white.svg', '0 0 240 26', [TENDRIL], '#FFFFFF')
    svg('plate.svg', '0 0 210 200', [PLATE_OUT, PLATE_IN, PLATE_TAIL], '#121212', 1.2)
    svg('plate-faint.svg', '0 0 210 200', [PLATE_OUT, PLATE_IN, PLATE_TAIL], '#CFCBC2', 1)
    svg('plate-white.svg', '0 0 210 200', [PLATE_OUT, PLATE_IN, PLATE_TAIL], '#FFFFFF', 1)
    svg('plate-night.svg', '0 0 210 200', [PLATE_OUT, PLATE_IN, PLATE_TAIL], '#3A3A3A', 1)


if __name__ == '__main__':
    write_files(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
