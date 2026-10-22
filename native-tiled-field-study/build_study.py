"""Self-initiated, code-authored 32px Tiled study; no client/external art.

Field Crossing is a small format/capability study, not a commissioned village,
hand-painted asset, engine integration, fitted collision system, or paid work.
Run with existing Python/Pillow. All outputs stay beside this source.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
S, COLS, WIDTH, HEIGHT = 32, 8, 16, 12
N, E, SOUTH, W = 1, 2, 4, 8
DIRS = ((N, 0, -1), (E, 1, 0), (SOUTH, 0, 1), (W, -1, 0))
G = (103, 137, 83, 255)
GRASS_LOW = (96, 130, 78, 255)
GRASS_HIGH = (115, 149, 91, 255)
SOIL = (115, 99, 65, 255)
PATH = (191, 167, 112, 255)
PATH_LIGHT = (204, 181, 130, 255)
SAND_OUT = (150, 151, 93, 255)
SAND_IN = (187, 178, 115, 255)
WATER_EDGE = (67, 111, 116, 255)
WATER = (85, 139, 151, 255)
WATER_LIGHT = (139, 180, 175, 255)
PROVENANCE = "Self-initiated/code-authored pixel-format study; no client or third-party art."


def prop(name, value, kind="string"):
    return {"name": name, "type": kind, "value": value}


def grass(variant=0):
    im = Image.new("RGBA", (S, S), G)
    d = ImageDraw.Draw(im)
    # The outer three pixels stay canonical so unrelated variants can tile.
    for y in range(4, 28):
        for x in range(4, 28):
            h = (x * 47 + y * 83 + x * y * 7 + variant * 29) % 131
            if h < 4:
                d.point((x, y), fill=GRASS_LOW)
            elif h in (37, 38):
                d.point((x, y), fill=GRASS_HIGH)
    return im


def connected_shape(mask, lo, hi):
    a = [[False] * S for _ in range(S)]
    for y in range(S):
        for x in range(S):
            a[y][x] = ((lo <= x <= hi and lo <= y <= hi)
                       or bool(mask & N and lo <= x <= hi and y < lo)
                       or bool(mask & E and lo <= y <= hi and x > hi)
                       or bool(mask & SOUTH and lo <= x <= hi and y > hi)
                       or bool(mask & W and lo <= y <= hi and x < lo))
    return a


def dilate(a, radius):
    b = [[False] * S for _ in range(S)]
    for y in range(S):
        for x in range(S):
            if not a[y][x]:
                continue
            for yy in range(max(0, y-radius), min(S, y+radius+1)):
                for xx in range(max(0, x-radius), min(S, x+radius+1)):
                    b[yy][xx] = True
    return b


def set_ports(im, mask, lo, hi, fringe):
    """A port's border colors are invariant to the other three mask bits."""
    p = im.load()
    for bit, side in ((N, "n"), (E, "e"), (SOUTH, "s"), (W, "w")):
        colors = [G] * S
        if mask & bit:
            for t in range(lo, hi+1):
                colors[t] = fringe[0]
            for delta, color in fringe[1:]:
                colors[lo-delta] = color
                colors[hi+delta] = color
        for t, color in enumerate(colors):
            xy = {"n": (t, 0), "e": (31, t), "s": (t, 31), "w": (0, t)}[side]
            p[xy] = color


def path_tile(mask):
    im = grass(0)
    a = connected_shape(mask, 10, 21)
    b = dilate(a, 1)
    p = im.load()
    for y in range(S):
        for x in range(S):
            if b[y][x]:
                p[x, y] = SOIL
            if a[y][x]:
                p[x, y] = PATH
                if 3 < x < 28 and 3 < y < 28 and (x*29+y*43+mask*3) % 83 < 3:
                    p[x, y] = PATH_LIGHT
    set_ports(im, mask, 10, 21, [PATH, (1, SOIL)])
    return im, a


def water_tile(mask):
    im = grass(1)
    # Corner bits NW=1, NE=2, SE=4, SW=8. Shared corners define shared
    # bilinear edge samples. In particular, mask15 is water everywhere.
    nw, ne, se, sw = (bool(mask & b) for b in (1, 2, 4, 8))
    a = [[((1-x/31)*(1-y/31)*nw + (x/31)*(1-y/31)*ne
           + (x/31)*(y/31)*se + (1-x/31)*(y/31)*sw) >= 0.5
          for x in range(S)] for y in range(S)]
    outer, inner = dilate(a, 2), dilate(a, 1)
    p = im.load()
    for y in range(S):
        for x in range(S):
            if outer[y][x]:
                p[x, y] = SAND_OUT
            if inner[y][x]:
                p[x, y] = SAND_IN
            if a[y][x]:
                boundary = any(0 <= x+dx < S and 0 <= y+dy < S and not a[y+dy][x+dx]
                               for _, dx, dy in DIRS)
                p[x, y] = WATER_EDGE if boundary else WATER
    # Quiet, pixel-aligned ripples stay away from connection borders.
    for y in (11, 20):
        for x in range(10 + (mask % 3), 17 + (mask % 3)):
            if a[y][x] and all(a[y+dy][x+dx] for _, dx, dy in DIRS):
                p[x, y] = WATER_LIGHT
    # Boundary shading must also depend only on the two shared corners,
    # never on the other two corners of a neighboring tile.
    for side, first, last in ((N, nw, ne), (E, ne, se), (SOUTH, sw, se), (W, nw, sw)):
        for t in range(S):
            if first == last:
                color = WATER if first else G
            else:
                distance = (t-15) if first else (16-t)
                color = WATER if distance < 0 else WATER_EDGE if distance == 0 else SAND_IN if distance == 1 else SAND_OUT if distance == 2 else G
            xy = {N: (t, 0), E: (31, t), SOUTH: (t, 31), W: (0, t)}[side]
            p[xy] = color
    return im, a


def decoration(kind):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if kind.startswith("flowers"):
        dots = [(9, 20), (21, 11), (24, 25)] if kind == "flowers-white" else [(11, 12), (19, 23)]
        petal = (235, 226, 187, 255) if kind == "flowers-white" else (191, 128, 135, 255)
        for x, y in dots:
            d.line((x, y+1, x, y+5), fill=(64, 108, 67, 255))
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                d.point((x+dx, y+dy), fill=petal)
            d.point((x, y), fill=(216, 180, 92, 255))
    elif kind == "rock":
        d.polygon(ROCK_POLYGON, fill=(91, 106, 98, 255))
        d.polygon([(7, 17), (12, 11), (21, 10), (25, 17), (18, 20), (10, 20)], fill=(151, 162, 140, 255))
        d.line([(12, 13), (20, 12), (22, 15)], fill=(183, 188, 161, 255))
        d.line([(10, 25), (22, 25), (25, 20)], fill=(66, 85, 79, 255))
    elif kind == "sign":
        d.rectangle((14, 13, 17, 30), fill=(101, 82, 55, 255))
        d.polygon([(6, 7), (22, 7), (27, 12), (22, 17), (6, 17)], fill=(96, 78, 52, 255))
        d.polygon([(7, 8), (21, 8), (25, 12), (21, 15), (7, 15)], fill=(192, 160, 104, 255))
        d.line((9, 10, 19, 10), fill=(220, 190, 127, 255))
        d.line((11, 13, 19, 13), fill=(128, 105, 66, 255))
    elif kind == "canopy":
        d.polygon([(2, 12), (5, 6), (11, 4), (16, 1), (24, 5), (29, 11), (30, 20),
                   (26, 27), (19, 30), (9, 28), (3, 22)], fill=(53, 86, 60, 255))
        d.polygon([(4, 12), (8, 7), (14, 6), (19, 3), (25, 8), (28, 15), (24, 23),
                   (18, 26), (9, 23), (4, 19)], fill=(76, 119, 69, 255))
        for x, y in ((9, 10), (17, 8), (21, 15), (11, 18)):
            d.rectangle((x, y, x+3, y+1), fill=(110, 146, 83, 255))
    elif kind == "trunk":
        d.ellipse((8, 25, 25, 30), fill=(63, 99, 63, 180))
        d.polygon([(13, 0), (19, 0), (20, 24), (24, 28), (9, 28), (13, 23)], fill=(107, 86, 57, 255))
        d.line((15, 2, 15, 25), fill=(156, 123, 75, 255))
    return im


ROCK_POLYGON = [(7, 17), (12, 11), (21, 10), (27, 17), (25, 26), (9, 27), (5, 23)]


def polygon_outline(a):
    """Exact pixel-union outer boundary of the single simply connected port shape."""
    edges = {}
    for y in range(S):
        for x in range(S):
            if not a[y][x]:
                continue
            for outside, start, end in (
                (y == 0 or not a[y-1][x], (x, y), (x+1, y)),
                (x == 31 or not a[y][x+1], (x+1, y), (x+1, y+1)),
                (y == 31 or not a[y+1][x], (x+1, y+1), (x, y+1)),
                (x == 0 or not a[y][x-1], (x, y+1), (x, y)),
            ):
                if outside:
                    assert start not in edges
                    edges[start] = end
    start = min(edges)
    points, here = [], start
    while True:
        points.append(here)
        here = edges[here]
        if here == start:
            break
        assert len(points) <= len(edges)
    assert len(points) == len(edges), "Unexpected hole or disconnected water shape"
    simple = []
    for n, p in enumerate(points):
        before, after = points[n-1], points[(n+1) % len(points)]
        if (p[0]-before[0])*(after[1]-p[1]) != (p[1]-before[1])*(after[0]-p[0]):
            simple.append(p)
    return simple


def polygon_outlines(a):
    # Saddle cases5/10 have two separate water components. Keep separate
    # polygons rather than bridging dry space with a false collision region.
    todo = {(x, y) for y in range(S) for x in range(S) if a[y][x]}
    result = []
    while todo:
        seed = todo.pop()
        component, q = {seed}, deque([seed])
        while q:
            x, y = q.popleft()
            for _, dx, dy in DIRS:
                n = (x+dx, y+dy)
                if n in todo:
                    todo.remove(n); component.add(n); q.append(n)
        isolated = [[(x, y) in component for x in range(S)] for y in range(S)]
        polygon = polygon_outline(isolated)
        area2 = sum(x*polygon[(n+1) % len(polygon)][1]-polygon[(n+1) % len(polygon)][0]*y
                    for n, (x, y) in enumerate(polygon))
        assert area2 == 2*len(component), "Collision polygon does not equal occupied water pixels"
        result.append(polygon)
    return result


def edge(im, side):
    p = im.load()
    return tuple(p[t, 0] if side == N else p[31, t] if side == E
                 else p[t, 31] if side == SOUTH else p[0, t] for t in range(S))


def component_count(cells):
    todo, count = set(cells), 0
    while todo:
        count += 1
        start = todo.pop()
        q = deque([start])
        while q:
            x, y = q.popleft()
            for _, dx, dy in DIRS:
                n = (x+dx, y+dy)
                if n in todo:
                    todo.remove(n)
                    q.append(n)
    return count


def layer(lid, name, data):
    return {"id": lid, "name": name, "type": "tilelayer", "x": 0, "y": 0,
            "width": WIDTH, "height": HEIGHT, "opacity": 1, "visible": True, "data": data}


def main():
    tiles = [grass(0), grass(1)]
    names = ["grass-a", "grass-b"]
    water_shapes = {}
    for m in range(16):
        tiles.append(path_tile(m)[0]); names.append(f"path-NESW-mask-{m:02d}")
    for m in range(16):
        im, a = water_tile(m)
        tiles.append(im); names.append(f"water-corners-NW-NE-SE-SW-mask-{m:02d}")
        water_shapes[m] = a
    for kind in ("flowers-white", "flowers-rose", "rock", "sign", "canopy", "trunk"):
        tiles.append(decoration(kind)); names.append(kind)
    assert len(tiles) == 40
    atlas = Image.new("RGBA", (COLS*S, math.ceil(len(tiles)/COLS)*S))
    for tid, im in enumerate(tiles):
        atlas.paste(im, ((tid % COLS)*S, (tid//COLS)*S))

    path_cells = {(5, y) for y in range(HEIGHT)} | {(x, 7) for x in range(WIDTH)} | {(x, 3) for x in range(5, 11)}
    water_vertices = {(12, 2), (13, 2), (12, 3), (13, 3), (14, 3), (13, 4), (14, 4)}
    def water_mask_at(x, y):
        return sum(bit for bit, vertex in ((1, (x, y)), (2, (x+1, y)),
                    (4, (x+1, y+1)), (8, (x, y+1))) if vertex in water_vertices)
    water_cells = {(x, y) for y in range(HEIGHT) for x in range(WIDTH) if water_mask_at(x, y)}
    assert not (path_cells & water_cells)
    def mask_at(cells, x, y):
        return sum(bit for bit, dx, dy in DIRS if (x+dx, y+dy) in cells)
    ground, decor, above = [], [0]*(WIDTH*HEIGHT), [0]*(WIDTH*HEIGHT)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            tid = ((x*17+y*31) % 7 == 0)
            if (x, y) in path_cells:
                tid = 2 + mask_at(path_cells, x, y)
            elif (x, y) in water_cells:
                tid = 18 + water_mask_at(x, y)
            ground.append(int(tid)+1)
    flowers = [(1, 4), (2, 5), (8, 1), (9, 5), (10, 9), (13, 9), (14, 10), (7, 10), (1, 10), (8, 4)]
    for n, (x, y) in enumerate(flowers):
        decor[y*WIDTH+x] = 35 + n % 2
    rocks = [(10, 1), (14, 5), (11, 10)]
    for x, y in rocks:
        decor[y*WIDTH+x] = 37
    sign_x, sign_y = 6, 6
    decor[sign_y*WIDTH+sign_x] = 38
    for x, y in ((2, 2), (2, 9), (9, 10)):
        above[y*WIDTH+x] = 39
        decor[(y+1)*WIDTH+x] = 40

    objects = [{"id": 1, "name": "spawn", "type": "spawn", "point": True,
                "x": 4.5*S, "y": 7.5*S, "width": 0, "height": 0, "rotation": 0, "visible": True,
                "properties": [prop("purpose", "Static spawn annotation only; no engine behavior.")]},
               {"id": 2, "name": "sign-interaction", "type": "interaction", "x": sign_x*S+3,
                "y": sign_y*S+5, "width": 26, "height": 27, "rotation": 0, "visible": True,
                "properties": [prop("text", "East: the pond. West: the meadow. North: the field path."),
                               prop("purpose", "Interaction rectangle annotation, not implemented game logic.")]}]
    collisions = []
    oid = 3
    for x, y in sorted(water_cells, key=lambda p: (p[1], p[0])):
        m = water_mask_at(x, y)
        for component, polygon in enumerate(polygon_outlines(water_shapes[m])):
            collisions.append({"id": oid, "name": f"water-{x}-{y}-{component}", "type": "water-geometry",
                               "x": x*S, "y": y*S, "width": 0, "height": 0, "rotation": 0, "visible": True,
                               "polygon": [{"x": px, "y": py} for px, py in polygon],
                               "properties": [prop("purpose", "Exact occupied-water-pixel outline; geometry annotation only, no engine validation."),
                                              prop("corner_mask", m, "int")]})
            oid += 1
    for x, y in rocks:
        collisions.append({"id": oid, "name": f"rock-{x}-{y}", "type": "rock-geometry",
                           "x": x*S, "y": y*S, "width": 0, "height": 0, "rotation": 0, "visible": True,
                           "polygon": [{"x": px, "y": py} for px, py in ROCK_POLYGON],
                           "properties": [prop("purpose", "Visible rock outline annotation only; no engine validation.")]})
        oid += 1
    tsj = {"type": "tileset", "version": "1.10", "name": "field-crossing-code-study",
           "tilewidth": S, "tileheight": S, "tilecount": len(tiles), "columns": COLS,
           "margin": 0, "spacing": 0, "image": "tiles.png", "imagewidth": atlas.width,
           "imageheight": atlas.height, "properties": [prop("provenance", PROVENANCE),
           prop("path_mask_bits", "N=1,E=2,S=4,W=8; a set bit joins road in that direction."),
           prop("water_corner_bits", "NW=1,NE=2,SE=4,SW=8; bilinear threshold0.5; shared vertex occupancy defines the shoreline.")],
           "tiles": [{"id": tid, "type": "ground" if tid < 34 else "decoration",
                      "properties": [prop("study_name", name)]} for tid, name in enumerate(names)]}
    tmj = {"type": "map", "version": "1.10", "orientation": "orthogonal", "renderorder": "right-down",
           "width": WIDTH, "height": HEIGHT, "tilewidth": S, "tileheight": S, "infinite": False,
           "nextlayerid": 6, "nextobjectid": oid, "backgroundcolor": "#678953",
           "properties": [prop("title", "Field Crossing"), prop("provenance", PROVENANCE),
                          prop("limits", "Static Tiled-format study; no engine, client scene, physical test or paid delivery.")],
           "tilesets": [{"firstgid": 1, "source": "tiles.tsj"}],
           "layers": [layer(1, "ground", ground), layer(2, "decor", decor),
                      {"id": 3, "name": "objects", "type": "objectgroup", "draworder": "topdown",
                       "opacity": 1, "visible": True, "x": 0, "y": 0, "objects": objects},
                      layer(4, "above-player", above),
                      {"id": 5, "name": "collision", "type": "objectgroup", "draworder": "topdown",
                       "opacity": 0.35, "visible": False, "x": 0, "y": 0, "objects": collisions}]}

    # Exhaustive compatible ports: every mask combination in both axes.
    path_compatible_checks = 0
    for offset, family in ((2, "path"),):
        for a in range(16):
            for b in range(16):
                for sa, sb in ((E, W), (SOUTH, N)):
                    if bool(a & sa) == bool(b & sb):
                        assert edge(tiles[offset+a], sa) == edge(tiles[offset+b], sb), (family, a, b, sa)
                        path_compatible_checks += 1
        for m in range(16):
            for side in (N, E, SOUTH, W):
                if not m & side:
                    assert edge(tiles[offset+m], side) == tuple([G]*S)
    water_compatible_checks = 0
    for a in range(16):
        for b in range(16):
            if (bool(a & 2), bool(a & 4)) == (bool(b & 1), bool(b & 8)):
                assert edge(tiles[18+a], E) == edge(tiles[18+b], W), ("water-corners", a, b, "E/W")
                water_compatible_checks += 1
            if (bool(a & 8), bool(a & 4)) == (bool(b & 1), bool(b & 2)):
                assert edge(tiles[18+a], SOUTH) == edge(tiles[18+b], N), ("water-corners", a, b, "S/N")
                water_compatible_checks += 1
    assert all(all(row) for row in water_shapes[15])
    assert all(not any(row) for row in water_shapes[0])
    assert len(polygon_outlines(water_shapes[5])) == len(polygon_outlines(water_shapes[10])) == 2
    for side in (N, E, SOUTH, W):
        assert edge(tiles[0], side) == edge(tiles[1], side) == tuple([G]*S)
    map_edge_checks = 0
    for y in range(HEIGHT):
        for x in range(WIDTH):
            a = tiles[ground[y*WIDTH+x]-1]
            if x+1 < WIDTH:
                assert edge(a, E) == edge(tiles[ground[y*WIDTH+x+1]-1], W), (x, y, "horizontal")
                map_edge_checks += 1
            if y+1 < HEIGHT:
                assert edge(a, SOUTH) == edge(tiles[ground[(y+1)*WIDTH+x]-1], N), (x, y, "vertical")
                map_edge_checks += 1
    assert component_count(path_cells) == component_count(water_cells) == 1
    assert all(im.getextrema()[3] == (255, 255) for im in tiles[:34])
    assert all(im.getextrema()[3][0] == 0 and im.getextrema()[3][1] == 255 for im in tiles[34:])
    assert [l["name"] for l in tmj["layers"]] == ["ground", "decor", "objects", "above-player", "collision"]
    for l in tmj["layers"]:
        if l["type"] == "tilelayer":
            assert len(l["data"]) == WIDTH*HEIGHT and all(0 <= gid <= len(tiles) for gid in l["data"])
    assert all(0 <= o["x"] <= WIDTH*S and 0 <= o["y"] <= HEIGHT*S for o in objects+collisions)
    assert len({o["id"] for o in objects+collisions}) == len(objects+collisions)
    for o in collisions:
        poly = [(p["x"], p["y"]) for p in o["polygon"]]
        area2 = sum(x*poly[(n+1) % len(poly)][1]-poly[(n+1) % len(poly)][0]*y for n, (x, y) in enumerate(poly))
        assert area2 > 0 and len(poly) >= 4
    for obj in (tsj, tmj):
        assert json.loads(json.dumps(obj, allow_nan=False)) == obj
    ROOT.mkdir(parents=True, exist_ok=True)
    atlas.save(ROOT/"tiles.png", optimize=False)
    (ROOT/"tiles.tsj").write_text(json.dumps(tsj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (ROOT/"field-crossing.tmj").write_text(json.dumps(tmj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    # Actual saved-file round trip, dimensions and dependency resolution.
    with Image.open(ROOT/"tiles.png") as png:
        assert png.size == (256, 160) and png.mode == "RGBA"
    saved_map = json.loads((ROOT/"field-crossing.tmj").read_text(encoding="utf-8"))
    saved_ts = json.loads((ROOT/saved_map["tilesets"][0]["source"]).read_text(encoding="utf-8"))
    assert (ROOT/saved_ts["image"]).is_file()
    print(json.dumps({"provenance": PROVENANCE, "tile_count": len(tiles), "tile_px": 32,
          "atlas_px": [256, 160], "map_tiles": [WIDTH, HEIGHT], "path_compatible_edge_checks": path_compatible_checks,
          "water_corner_compatible_edge_checks": water_compatible_checks,
          "full_water_mask15_pixels": sum(sum(row) for row in water_shapes[15]),
          "map_neighbor_edge_checks": map_edge_checks, "path_components": 1, "water_components": 1,
          "water_cells": len(water_cells), "water_collision_polygons": len(collisions)-len(rocks), "rock_collision_polygons": len(rocks),
          "objects": ["spawn", "sign-interaction"], "native_editor_verified": False, "game_engine_verified": False,
          "files": [{"path": str(ROOT/f), "bytes": (ROOT/f).stat().st_size,
                     "sha256": hashlib.sha256((ROOT/f).read_bytes()).hexdigest()}
                    for f in ("build_study.py", "tiles.png", "tiles.tsj", "field-crossing.tmj")]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
