"""Turns map outlines (GeoJSON) into SVG paths for the homepage maps.

    python3 scripts/map-paths.py poland wojewodztwa-min.geojson          → scripts/wojewodztwa.json
    python3 scripts/map-paths.py world  ne_110m_admin_0_countries.geojson → scripts/swiat.json
    python3 scripts/map-paths.py globe  ne_110m_admin_0_countries.geojson → js/world-globe.json

Sources:
- "Smaki regionów": GUGiK's register of boundaries (PRG), simplified, from
  https://github.com/ppatrzyk/polska-geojson (wojewodztwa/wojewodztwa-min.geojson).
- "Smaki świata": Natural Earth 1:110m countries (public domain), from
  https://github.com/nvkelso/natural-earth-vector (geojson/ne_110m_admin_0_countries.geojson);
  Polish names come from its NAME_PL field. Antarctica is left out. "world" is the flat map
  (Equal Earth projection, used until the globe loads); "globe" keeps longitude/latitude for js/globe.js.

Run once per source; build.py reads the JSON. Stdlib only.
"""
import json
import math
import sys
from pathlib import Path

POLAND_NAMES = {     # GeoJSON names → the names used on the site
    'dolnośląskie': 'Dolnośląskie', 'kujawsko-pomorskie': 'Kujawsko-pomorskie', 'lubelskie': 'Lubelskie',
    'lubuskie': 'Lubuskie', 'łódzkie': 'Łódzkie', 'małopolskie': 'Małopolskie', 'mazowieckie': 'Mazowieckie',
    'opolskie': 'Opolskie', 'podkarpackie': 'Podkarpackie', 'podlaskie': 'Podlaskie', 'pomorskie': 'Pomorskie',
    'śląskie': 'Śląskie', 'świętokrzyskie': 'Świętokrzyskie', 'warmińsko-mazurskie': 'Warmińsko-mazurskie',
    'wielkopolskie': 'Wielkopolskie', 'zachodniopomorskie': 'Zachodniopomorskie',
}
MAPS = {
    # name: (output file, viewBox width, Douglas–Peucker tolerance in viewBox units)
    'poland': ('wojewodztwa.json', 600, 0.9),
    'world': ('swiat.json', 1000, 0.7),
}


def poland_projection():
    k = math.cos(math.radians(52))
    return lambda lon, lat: (lon * k, -lat)


def equal_earth(lon, lat):
    """Equal Earth projection (Šavrič, Patterson, Jenny 2018); y grows downwards."""
    a1, a2, a3, a4 = 1.340264, -0.081106, 0.000893, 0.003796
    m = math.sqrt(3) / 2
    t = math.asin(m * math.sin(math.radians(lat)))
    t2, t6 = t * t, t ** 6
    x = 2 * math.sqrt(3) * math.radians(lon) * math.cos(t) / (3 * (9 * a4 * t6 * t2 + 7 * a3 * t6 + 3 * a2 * t2 + a1))
    y = t * (a4 * t6 * t2 + a3 * t6 + a2 * t2 + a1)
    return x, -y


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


def area(ring):
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1])) / 2


def centroid(ring):
    a = cx = cy = 0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        f = x0 * y1 - x1 * y0
        a += f; cx += (x0 + x1) * f; cy += (y0 + y1) * f
    return cx / (3 * a), cy / (3 * a)


def globe(src):
    """Countries as small GeoJSON for the spinning globe: simplified in degrees, rounded to 0.1°."""
    feats = json.loads(Path(src).read_text(encoding='utf-8'))['features']
    out = []
    for f in feats:
        if f['properties']['ADM0_A3'] == 'ATA':
            continue
        g = f['geometry']
        polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        rings = []
        for poly in polys:
            r = [simplify([tuple(pt) for pt in ring], 0.2) for ring in poly]
            r = [[[round(x, 1), round(y, 1)] for x, y in ring] for ring in r if len(ring) >= 4]
            if r:
                rings.append(r)
        out.append({'type': 'Feature', 'properties': {'n': f['properties']['NAME_PL']},
                    'geometry': {'type': 'MultiPolygon', 'coordinates': rings}})
    dest = Path(__file__).resolve().parent.parent / 'js' / 'world-globe.json'
    dest.write_text(json.dumps({'type': 'FeatureCollection', 'features': out}, ensure_ascii=False, separators=(',', ':')),
                    encoding='utf-8')
    print(dest, len(out), 'countries,', dest.stat().st_size // 1024, 'KB')


def main(kind, src):
    if kind == 'globe':
        return globe(src)
    out_name, width, tol = MAPS[kind]
    feats = json.loads(Path(src).read_text(encoding='utf-8'))['features']
    if kind == 'poland':
        project = poland_projection()
        named = [(POLAND_NAMES[f['properties']['nazwa']], f['geometry']) for f in feats]
    else:
        project = equal_earth
        named = [(f['properties']['NAME_PL'], f['geometry']) for f in feats if f['properties']['ADM0_A3'] != 'ATA']
    polys = {}
    for name, g in named:
        rings = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        polys[name] = [[[project(lon, lat) for lon, lat in ring] for ring in poly] for poly in rings]
    xs = [x for p in polys.values() for poly in p for ring in poly for x, _ in ring]
    ys = [y for p in polys.values() for poly in p for ring in poly for _, y in ring]
    s = width / (max(xs) - min(xs))
    x0, y0 = min(xs), min(ys)
    height = round((max(ys) - y0) * s)
    out = {'viewBox': f'0 0 {width} {height}', 'regions': {}}
    for name, p in sorted(polys.items()):
        d, biggest = [], []
        for poly in p:
            for ring in poly:
                pts = simplify([((x - x0) * s, (y - y0) * s) for x, y in ring], tol)
                if len(pts) < 4:
                    continue
                if abs(area(pts[:-1])) > abs(area(biggest[:-1] or [(0, 0)])):
                    biggest = pts
                d.append('M' + 'L'.join(f'{x:.0f},{y:.0f}' for x, y in pts[:-1]) + 'Z')
        if not d:
            continue
        cx, cy = centroid(biggest[:-1])
        out['regions'][name] = {'d': ''.join(d), 'x': round(cx, 1), 'y': round(cy, 1)}
    dest = Path(__file__).with_name(out_name)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(dest, out['viewBox'], len(out['regions']), 'shapes,',
          sum(len(r['d']) for r in out['regions'].values()), 'chars of path data')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
