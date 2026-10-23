"""Turns voivodeship borders (GeoJSON) into SVG paths for the "Smaki regionów" map.

Source: GUGiK's register of boundaries (PRG), simplified, from
https://github.com/ppatrzyk/polska-geojson (wojewodztwa/wojewodztwa-min.geojson).

    python3 scripts/map-paths.py wojewodztwa-min.geojson   → writes scripts/wojewodztwa.json

Run once; build.py reads the JSON. Stdlib only.
"""
import json
import math
import sys
from pathlib import Path

WIDTH = 600          # viewBox width; height follows the country's shape
TOLERANCE = 0.9      # Douglas–Peucker tolerance in viewBox units
NAMES = {            # GeoJSON names → the names used on the site
    'dolnośląskie': 'Dolnośląskie', 'kujawsko-pomorskie': 'Kujawsko-pomorskie', 'lubelskie': 'Lubelskie',
    'lubuskie': 'Lubuskie', 'łódzkie': 'Łódzkie', 'małopolskie': 'Małopolskie', 'mazowieckie': 'Mazowieckie',
    'opolskie': 'Opolskie', 'podkarpackie': 'Podkarpackie', 'podlaskie': 'Podlaskie', 'pomorskie': 'Pomorskie',
    'śląskie': 'Śląskie', 'świętokrzyskie': 'Świętokrzyskie', 'warmińsko-mazurskie': 'Warmińsko-mazurskie',
    'wielkopolskie': 'Wielkopolskie', 'zachodniopomorskie': 'Zachodniopomorskie',
}


def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy) or 1e-9
    far, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / norm if (dx or dy) else math.hypot(x - x1, y - y1)
        if d > far:
            far, idx = d, i
    if far <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def centroid(ring):
    a = cx = cy = 0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        f = x0 * y1 - x1 * y0
        a += f; cx += (x0 + x1) * f; cy += (y0 + y1) * f
    return cx / (3 * a), cy / (3 * a)


def main(src):
    feats = json.loads(Path(src).read_text(encoding='utf-8'))['features']
    k = math.cos(math.radians(52))
    polys = {}
    for f in feats:
        g = f['geometry']
        polys[NAMES[f['properties']['nazwa']]] = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
    xs = [lon * k for p in polys.values() for poly in p for ring in poly for lon, _ in ring]
    ys = [-lat for p in polys.values() for poly in p for ring in poly for _, lat in ring]
    s = WIDTH / (max(xs) - min(xs))
    x0, y0 = min(xs), min(ys)
    height = round((max(ys) - y0) * s)
    out = {'viewBox': f'0 0 {WIDTH} {height}', 'regions': {}}
    for name, p in sorted(polys.items()):
        d, biggest = [], []
        for poly in p:
            for ring in poly:
                pts = [((lon * k - x0) * s, (-lat - y0) * s) for lon, lat in ring]
                pts = simplify(pts, TOLERANCE)
                if len(pts) < 4:
                    continue
                if len(pts) > len(biggest):
                    biggest = pts
                d.append('M' + 'L'.join(f'{x:.0f},{y:.0f}' for x, y in pts[:-1]) + 'Z')
        cx, cy = centroid(biggest[:-1])
        out['regions'][name] = {'d': ''.join(d), 'x': round(cx, 1), 'y': round(cy, 1)}
    dest = Path(__file__).with_name('wojewodztwa.json')
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(dest, out['viewBox'], sum(len(r['d']) for r in out['regions'].values()), 'chars of path data')


if __name__ == '__main__':
    main(sys.argv[1])
