# Courier walk study — Hx Works

A self-initiated character-animation study: one 12-frame walk, transparent 128 × 128 PNG exports, and editable SVG paths. This is a portfolio exercise, not a client commission or a completed game character set.

## Walk preview

<img src="walk-loop.webp" width="128" height="128" alt="Courier walk at its 128-pixel export size"> <img src="walk-loop.webp" width="64" height="64" alt="The same courier walk at 64 pixels">

The animated WebP contains the same twelve PNG frames, at 83 ms per frame. It is a viewing preview; the PNGs and SVGs are the working files.

## Files and workflow

- [Transparent PNG sheet](walk-sheet.png): 512 × 384, four columns and three rows, no padding.
- [Twelve individual PNG frames](https://github.com/hxsworrk-lab/character-walk-study/tree/main/frames).
- [Twelve editable SVG frames](https://github.com/hxsworrk-lab/character-walk-study/tree/main/svg-frames): seven named groups and 52 paths per frame, without an embedded bitmap.
- [Python source](build_probe.py) and [export measurements](metrics.json).

The workflow uses code-authored projected geometry and SVG cutout paths, with Pillow raster exports from that same geometry. The PNGs are rendered directly by Pillow from the shared geometry, rather than from the SVG files. Development used AI coding assistance; no customer references, stock character, generated raster image or purchased asset is included in this study.

## Scope of this example

Only one stylised walk is demonstrated. This does not establish idle, mining, building or tool-use animations, all movement directions, natural foot contact, a buyer-approved camera angle, or Unity integration. SVG editability does not establish compatibility with a buyer's preferred art application. The mathematical period-end test in the measurements does not prove a natural final-frame-to-first-frame transition.

The study is public for inspection; it is not a promise of copyright assignment or exclusive rights in a future commissioned asset.

To regenerate the PNG/SVG study locally with Python and Pillow 12.2.0, run `python build_probe.py` from this folder. This writes the frame, sheet and measurement files beside the script. The separately packaged WebP preview is not rebuilt by that command.
