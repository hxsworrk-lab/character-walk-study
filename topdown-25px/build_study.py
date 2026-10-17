"""Render three original vector-pixel key poses, not a commissioned walk cycle.

The source is a 25-cell coordinate grid. No reference-image pixels are inputs.
PNG exports use exactly the same grid as SVG; no image resampling or AI raster
generation is used for the artwork. Pillow is only the export renderer.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
PALETTE = {
    ".": None,
    "o": "#182a32", "h": "#44342f", "H": "#775b48",
    "s": "#d7a07a", "S": "#a86d51", "c": "#317d88",
    "C": "#62a9ae", "p": "#697889", "P": "#3f5364",
    "b": "#303039",
}


def pose(phase):
    grid = [["."] * 25 for _ in range(25)]
    def rect(x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                grid[y][x] = color
    # Foreshortened legs. Body/pelvis and the head retain identical positions.
    lengths = [(16, 16), (17, 15), (15, 17)][phase]
    for x0, end in zip((10, 13), lengths):
        rect(x0, 14, x0 + 1, end - 1, "P")
        rect(x0, 14, x0, max(14, end - 1), "p")
        rect(x0 - (phase == 2 and x0 == 13), end, x0 + 1, end, "b")
    # Opposite shoulder/hand swing, kept within the common frame.
    hands = [(14, 14), (13, 15), (15, 13)][phase]
    for left, hand_y in zip((True, False), hands):
        x0 = 7 if left else 16
        rect(x0, 11, x0 + 1, hand_y - 2, "o")
        rect(x0, 11, x0, hand_y - 2, "c")
        rect(x0, hand_y - 1, x0 + 1, hand_y, "S")
        rect(x0, hand_y - 1, x0, hand_y - 1, "s")
    rect(9, 10, 15, 13, "o")
    rect(10, 10, 14, 13, "c")
    rect(9, 11, 9, 12, "C")
    rect(10, 11, 10, 12, "C")
    rect(11, 14, 13, 14, "P")
    # Crown/back of head: no face drawn on a north-facing figure.
    rect(10, 9, 14, 11, "h")
    rect(11, 8, 13, 8, "h")
    rect(11, 12, 13, 12, "h")
    rect(10, 9, 12, 10, "H")
    rect(11, 11, 11, 11, "H")
    rect(12, 7, 12, 7, "S")
    return ["".join(row) for row in grid]


def rgba_grid(rows):
    im = Image.new("RGBA", (25, 25), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, key in enumerate(row):
            color = PALETTE[key]
            if color:
                im.putpixel((x, y), tuple(bytes.fromhex(color[1:])) + (255,))
    return im


def svg_grid(rows):
    pixels = []
    for y, row in enumerate(rows):
        for x, key in enumerate(row):
            if PALETTE[key]:
                pixels.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{PALETTE[key]}"/>')
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 25 25" width="25" height="25" shape-rendering="crispEdges"><title>Hx Works self-initiated north-facing key pose</title>' + ''.join(pixels) + '</svg>\n'


def build():
    rows = [pose(i) for i in range(3)]
    frames = [rgba_grid(r) for r in rows]
    results = []
    for i, (data, im) in enumerate(zip(rows, frames)):
        im.save(ROOT / f"pose-{i}.png")
        (ROOT / f"pose-{i}.svg").write_text(svg_grid(data), encoding="utf-8")
        actual = {im.getpixel((x, y)) for y in range(25) for x in range(25)}
        assert im.size == (25, 25)
        assert {p[3] for p in actual} == {0, 255}
        assert len([p for p in actual if p[3]]) <= 12
        results.append({"name": f"pose-{i}", "size": list(im.size), "bbox": im.getbbox(), "opaque_colors": len([p for p in actual if p[3]]), "alpha_values": [0, 255], "sha256": hashlib.sha256((ROOT / f"pose-{i}.png").read_bytes()).hexdigest()})
    # Exact shared head/torso cells are compared on the canonical grid.
    for y in range(8, 13):
        for x in range(10, 15):
            assert len({r[y][x] for r in rows}) == 1
    sheet = Image.new("RGBA", (75, 25), (0, 0, 0, 0))
    for i, im in enumerate(frames):
        sheet.paste(im, (i * 25, 0))
    sheet.save(ROOT / "three-key-poses.png")
    indices = {key: i for i, key in enumerate(PALETTE)}
    rgb_palette = [0, 0, 0]
    for color in list(PALETTE.values())[1:]:
        rgb_palette.extend(bytes.fromhex(color[1:]))
    rgb_palette.extend([0] * (768 - len(rgb_palette)))
    gif_frames = []
    sequence = [0, 1, 0, 2]
    for index in sequence:
        frame = Image.new("P", (25, 25))
        frame.putpalette(rgb_palette)
        frame.putdata([indices[key] for row in rows[index] for key in row])
        gif_frames.append(frame)
    gif_frames[0].save(ROOT / "key-pose-loop.gif", save_all=True,
                       append_images=gif_frames[1:], duration=180,
                       loop=0, transparency=0, disposal=2, optimize=False)
    with Image.open(ROOT / "key-pose-loop.gif") as exported:
        assert exported.n_frames == 4
        for i, expected in enumerate(sequence):
            exported.seek(i)
            assert exported.convert("RGBA").tobytes() == frames[expected].tobytes()
    font = ImageFont.load_default(size=16)
    board = Image.new("RGB", (640, 360), "#eceff1")
    draw = ImageDraw.Draw(board)
    draw.text((20, 16), "Hx Works / 25px key-pose study", font=font, fill="#182a32")
    draw.text((20, 42), "Three poses only - not a finished walk cycle", font=font, fill="#45535a")
    for i, im in enumerate(frames):
        x = 28 + i * 204
        draw.rectangle((x, 90, x + 179, 269), fill="#263640" if i == 1 else "#ffffff")
        board.paste(im.resize((150, 150), Image.Resampling.NEAREST), (x + 15, 105), im.resize((150, 150), Image.Resampling.NEAREST))
        draw.text((x, 282), ["Neutral", "Left leg back", "Right leg back"][i], font=font, fill="#182a32")
        board.paste(im, (x + 72, 312), im)
    board.save(ROOT / "preview.png")
    manifest = {"self_initiated": True, "client_work": False, "source": "Original coordinate grid and named color-role palette; no imported art", "facing": "north-facing interpretation; buyer acceptance unverified", "unique_key_poses": 3, "completed_8_frame_walk": False, "all_animations_or_directions": False, "palette": PALETTE, "frames": results, "root": [12, 13], "checks": {"head_region_identical": True, "binary_alpha_only": True, "no_antialiasing_or_gradients": True}, "limitations": "Readability and perceived top-down angle/motion need actual visual and buyer review; structural checks are not artistic acceptance."}
    (ROOT / "grid-source.json").write_text(json.dumps({"palette": PALETTE, "poses": rows}, indent=2) + "\n", encoding="utf-8")
    (ROOT / "metrics.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    build()
