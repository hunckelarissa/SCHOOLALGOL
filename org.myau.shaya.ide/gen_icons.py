#!/usr/bin/env python3
"""Generate crisp Eclipse toolbar icons (16x16 / 32x32), transparent PNG, no fonts."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / "icons"
S = 4  # draw scale (64 -> 16)


def blank(logical: int = 16) -> Image.Image:
    return Image.new("RGBA", (logical * S, logical * S), (0, 0, 0, 0))


def save(img: Image.Image, name: str, logical: int = 16) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    out = img.resize((logical, logical), Image.Resampling.LANCZOS)
    path = OUT / name
    out.save(path, format="PNG")
    print(f"  {path.name} ({path.stat().st_size} B)")


def icon_run() -> None:
    """Green play — Run."""
    im = blank()
    d = ImageDraw.Draw(im)
    d.polygon([(14, 8), (14, 56), (56, 32)], fill=(46, 160, 67, 255))
    save(im, "run.png")


def icon_check() -> None:
    """Clipboard + green check — Check."""
    im = blank()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 12, 50, 56), radius=5, fill=(245, 250, 255, 255), outline=(35, 95, 160, 255), width=3)
    d.rounded_rectangle((20, 6, 40, 16), radius=3, fill=(35, 95, 160, 255))
    d.line([(18, 34), (28, 46), (46, 20)], fill=(25, 145, 65, 255), width=6)
    save(im, "check.png")


def icon_transpile() -> None:
    """Page + arrow + C — Transpile to C."""
    im = blank()
    d = ImageDraw.Draw(im)
    # .alg page
    d.rounded_rectangle((4, 8, 26, 56), radius=3, fill=(250, 252, 255, 255), outline=(55, 75, 110, 255), width=2)
    for y in (18, 28, 38):
        d.line([(9, y), (21, y)], fill=(100, 120, 150, 255), width=2)
    # arrow
    d.rectangle((27, 28, 36, 36), fill=(40, 110, 200, 255))
    d.polygon([(34, 20), (34, 44), (48, 32)], fill=(40, 110, 200, 255))
    # C tile (drawn, not font)
    d.rounded_rectangle((46, 10, 62, 54), radius=4, fill=(30, 70, 140, 255))
    # letter C as thick arc
    d.arc((48, 16, 60, 48), start=40, end=320, fill=(255, 255, 255, 255), width=5)
    save(im, "transpile.png")


def icon_step() -> None:
    """Amber bug — Step Debug."""
    im = blank()
    d = ImageDraw.Draw(im)
    body = (230, 155, 35, 255)
    edge = (130, 80, 10, 255)
    d.ellipse((16, 22, 48, 50), fill=body, outline=edge, width=2)
    d.ellipse((22, 10, 42, 28), fill=(245, 185, 60, 255), outline=edge, width=2)
    for y in (28, 36, 44):
        d.line([(8, y - 2), (18, y + 2)], fill=edge, width=2)
        d.line([(56, y - 2), (46, y + 2)], fill=edge, width=2)
    d.line([(26, 12), (18, 4)], fill=edge, width=2)
    d.line([(38, 12), (46, 4)], fill=edge, width=2)
    # eyes
    d.ellipse((26, 16, 30, 20), fill=(40, 30, 10, 255))
    d.ellipse((34, 16, 38, 20), fill=(40, 30, 10, 255))
    save(im, "step.png")
    save(im, "debug.png")


def icon_last() -> None:
    """Replay circle + play — Run Last."""
    im = blank()
    d = ImageDraw.Draw(im)
    col = (125, 65, 185, 255)
    d.arc((8, 8, 56, 56), start=45, end=310, fill=col, width=8)
    d.polygon([(44, 6), (58, 16), (42, 22)], fill=col)
    d.polygon([(24, 22), (24, 42), (42, 32)], fill=(95, 45, 155, 255))
    save(im, "last.png")


def _draw_a(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    # A as thick strokes
    mid = x0 + w // 2
    d.line([(x0 + 2, y1 - 2), (mid, y0 + 2)], fill=fill, width=max(3, w // 5))
    d.line([(x1 - 2, y1 - 2), (mid, y0 + 2)], fill=fill, width=max(3, w // 5))
    bar_y = y0 + int(h * 0.58)
    d.line([(x0 + w // 4, bar_y), (x1 - w // 4, bar_y)], fill=fill, width=max(3, w // 6))


def icon_alg(logical: int, name: str) -> None:
    """Blue badge with A — brand."""
    im = blank(logical)
    d = ImageDraw.Draw(im)
    side = logical * S
    pad = max(2, side // 14)
    d.rounded_rectangle(
        (pad, pad, side - pad - 1, side - pad - 1),
        radius=max(4, side // 5),
        fill=(35, 90, 165, 255),
        outline=(15, 45, 100, 255),
        width=max(2, side // 28),
    )
    inset = side // 5
    _draw_a(d, (inset, inset, side - inset, side - inset), (255, 255, 255, 255))
    save(im, name, logical=logical)


def icon_currentline() -> None:
    """Orange right arrow — current debug line gutter."""
    im = blank()
    d = ImageDraw.Draw(im)
    d.polygon(
        [(4, 32), (30, 12), (30, 24), (52, 24), (52, 40), (30, 40), (30, 52)],
        fill=(255, 150, 25, 255),
    )
    d.rectangle((52, 16, 58, 48), fill=(220, 110, 0, 255))
    save(im, "currentline.png")


def main() -> None:
    print(f"Writing icons -> {OUT}")
    icon_run()
    icon_check()
    icon_transpile()
    icon_step()
    icon_last()
    icon_alg(16, "alg.png")
    icon_alg(16, "alg16.png")
    icon_alg(32, "alg32.png")
    icon_currentline()
    print("done")


if __name__ == "__main__":
    main()
