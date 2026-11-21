"""Eldara -- a travel poster for a place that isn't there.

A program that draws one travel poster (1024x1024 PNG) for Eldara, an
invented island above a sea of clouds, and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Python standard library only: no Pillow, no network, no randomness.
Every run writes the exact same bytes.

The place: Eldara, an island whose cliffs rise out of a sea of clouds.
A striped lighthouse stands on the western cliff and its beam sweeps
over the cloud sea at dusk; a cable car descends from the cliff into
the clouds. The poster's promise: a stay above the weather, where the
sea ends in sky.
"""

import hashlib
import math
import os
import struct
import sys
import zlib

# ------------------------------------------------------------------ font --
# A 5x7 pixel font, drawn from scratch for this entry. Each glyph is
# seven rows of five pixels; "#" is on, "." is off. Capitals, digits
# and a small set of punctuation. Lowercase input is folded to upper
# case (the font is capitals-only).

FONT = {
    "A": ("..#..", ".#.#.", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", ".#.#.", ".#.#.", "..#..", "..#..", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "*": (".....", ".#.#.", ".###.", "#####", ".###.", ".#.#.", "....."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
}

# --------------------------------------------------------------- colours --
INDIGO = (36, 30, 74)      # dusk sky, top
VIOLET = (96, 64, 124)     # dusk sky, middle
ROSE = (196, 96, 110)      # dusk sky, low
GOLD = (250, 182, 110)     # horizon glow
SUN = (255, 222, 150)      # setting sun
BEAM = (255, 228, 158)     # lighthouse beam
CREAM = (252, 244, 228)    # poster type
CLOUD = (246, 224, 204)    # sea of clouds
CLOUD_SH = (236, 212, 204)  # cloud shadow
CLIFF = (28, 22, 46)       # cliff silhouette
SEA = (38, 30, 62)         # dark sea strip at the foot
RED = (178, 52, 52)        # lighthouse bands
WHITE = (250, 244, 230)    # lighthouse tower
DARK = (20, 16, 36)        # lamp room, gondola


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Canvas:
    """An RGB pixel buffer with tiny drawing primitives."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color):
        for deg in range(360):
            a = math.radians(deg)
            self.set(cx + int(r * math.cos(a)), cy + int(r * math.sin(a)),
                     color)

    def polyfill(self, pts, color):
        """Scanline fill of a polygon given as [(x, y), ...]."""
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for xx in range(int(xs[j]), int(xs[j + 1]) + 1):
                    self.set(xx, y, color)

    def text_width(self, text, scale):
        return len(text) * (5 * scale + scale)

    def text(self, text, x, y, scale, color):
        cx = x
        for ch in text.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale

    def text_centred(self, text, cx, y, scale, color):
        self.text(text, cx - self.text_width(text, scale) // 2, y, scale,
                  color)


# ---------------------------------------------------------------- content --
def sky(cv, w, h, horizon):
    """Vertical dusk gradient, indigo to gold, down to the horizon."""
    stops = [(0.00, INDIGO), (0.38, VIOLET), (0.66, ROSE), (0.88, GOLD),
             (1.00, (255, 205, 130))]
    for y in range(horizon):
        t = y / horizon
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                color = lerp(c0, c1, (t - t0) / (t1 - t0))
                break
        else:
            color = stops[-1][1]
        cv.hline(0, y, w, color)


def stars(cv, w):
    """A sparse, deterministic scatter of stars in the upper sky."""
    for i in range(70):
        x = (i * 173 + 61) % w
        y = (i * 97 + 23) % 260
        if (i * 37) % 5 == 0:
            cv.disc(x, y, 2, (240, 230, 255))
        else:
            cv.set(x, y, (235, 228, 250))


def bird(cv, cx, cy, s, color):
    cv.line(cx - s, cy, cx, cy - s // 2, color)
    cv.line(cx, cy - s // 2, cx + s, cy, color)


def lighthouse(cv, x, base_y):
    """Striped lighthouse standing on the cliff top."""
    # tower: white with two red bands
    cv.rect(x, base_y - 150, 56, 150, WHITE)
    cv.rect(x, base_y - 118, 56, 22, RED)
    cv.rect(x, base_y - 66, 56, 22, RED)
    # gallery + lamp room
    cv.rect(x - 8, base_y - 168, 72, 8, DARK)
    cv.rect(x + 6, base_y - 196, 44, 28, DARK)
    cv.disc(x + 28, base_y - 182, 10, SUN)
    cv.rect(x - 2, base_y - 206, 60, 8, DARK)
    # beam sweeping right across the dusk sky, narrow and low
    cv.polyfill([(x + 50, base_y - 190), (1024, base_y - 246),
                 (1024, base_y - 176), (x + 50, base_y - 174)], BEAM)
    cv.polyfill([(x + 50, base_y - 186), (1024, base_y - 232),
                 (1024, base_y - 190), (x + 50, base_y - 178)], SUN)


def cable_car(cv):
    """A cable line descending from the cliff into the cloud sea."""
    cv.line(280, 540, 780, 800, DARK)
    cv.line(280, 548, 780, 808, DARK)
    # gondola hanging from the line, mid-descent (on the cable at x=596)
    gx, gy = 596, 704
    cv.line(gx, gy - 26, gx, gy, DARK)
    cv.rect(gx - 34, gy, 68, 44, DARK)
    cv.rect(gx - 28, gy + 8, 56, 20, GOLD)
    cv.rect(gx - 34, gy, 68, 6, RED)


def clouds(cv, w, top):
    """A sea of clouds: billowing scallops over a cream field."""
    cv.rect(0, top + 40, w, 1024 - top - 40, CLOUD)
    # shadow scallops, slightly lower and offset
    for cx, r in ((80, 90), (260, 120), (470, 100), (680, 130),
                  (880, 110), (1010, 80)):
        cv.disc(cx, top + 66, r, CLOUD_SH)
    # bright scallops on top
    for cx, r in ((0, 70), (150, 110), (350, 90), (540, 120), (740, 100),
                  (930, 120), (1024, 70)):
        cv.disc(cx, top + 40, r, CLOUD)
    for cx, r in ((60, 90), (280, 110), (500, 95), (720, 115),
                  (940, 100)):
        cv.disc(cx, top + 190, r, CLOUD)


def draw():
    W, H = 1024, 1024
    cv = Canvas(W, H, INDIGO)
    horizon = 660

    # ------------------------------------------------------------ sky ------
    sky(cv, W, H, horizon)
    stars(cv, W)

    # ------------------------------------------------------------ sun ------
    sun_cx, sun_cy = 660, 560
    cv.disc(sun_cx, sun_cy, 104, (255, 196, 120))
    cv.disc(sun_cx, sun_cy, 82, (255, 208, 132))
    cv.disc(sun_cx, sun_cy, 62, SUN)

    # birds crossing the dusk
    bird(cv, 470, 210, 16, CLIFF)
    bird(cv, 540, 176, 12, CLIFF)
    bird(cv, 830, 300, 14, CLIFF)
    bird(cv, 900, 262, 10, CLIFF)

    # ---------------------------------------------------------- clouds -----
    clouds(cv, W, horizon)

    # dark sea strip at the foot
    cv.rect(0, 950, W, 74, SEA)

    # ----------------------------------------------------------- cliff -----
    cv.polyfill([(0, 1024), (0, 430), (120, 418), (220, 470), (300, 560),
                 (330, 700), (300, 1024)], CLIFF)
    # a pale edge where the dusk catches the cliff (two pixels wide)
    for dy in (0, 1):
        cv.line(0, 430 + dy, 120, 418 + dy, ROSE)
        cv.line(120, 418 + dy, 220, 470 + dy, ROSE)
        cv.line(220, 470 + dy, 300, 560 + dy, ROSE)

    # ------------------------------------------------------ lighthouse -----
    lighthouse(cv, 150, 470)
    cable_car(cv)

    # ------------------------------------------------------------ type -----
    # the name leads the eye; the landmark and the horizon follow it
    cv.text_centred("ELDARA", W // 2, 84, 12, CREAM)
    cv.text_centred("ISLE ABOVE THE CLOUDS", W // 2, 196, 2, CREAM)
    cv.hline(W // 2 - 150, 232, 300, CREAM)
    cv.text_centred("WHERE THE SEA ENDS IN SKY", W // 2, 968, 2, CREAM)

    # thin poster frame
    cv.rect(20, 20, W - 40, 3, CREAM)
    cv.rect(20, H - 23, W - 40, 3, CREAM)
    cv.rect(20, 20, 3, H - 40, CREAM)
    cv.rect(W - 23, 20, 3, H - 40, CREAM)
    return cv


# -------------------------------------------------------------------- png --
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def to_png(cv):
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = draw()
    png = to_png(cv)
    assert png[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG magic"
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes, sha256 %s)"
          % (path, len(png), hashlib.sha256(png).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
