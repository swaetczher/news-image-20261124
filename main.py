"""Ringkasan berita dunia Selasa 24 November 2026 dalam satu gambar 1024x1024.

Program mandiri: hanya pustaka standar, tanpa jaringan, tanpa membaca
lingkungan, tanpa impor dinamis, tanpa mengeksekusi apa pun selain kodenya
sendiri. Keluaran deterministik: byte PNG yang sama pada setiap eksekusi.

Determinisme dijaga tiga lapis: (1) tidak ada jam, acak, atau lingkungan
yang dibaca; (2) urutan gambar selalu mengikuti urutan daftar STORIES;
(3) encoder PNG memakai kompresi zlib level 9 yang sama tiap run, tanpa
chunk waktu. Dua run berurutan wajib menghasilkan sha256 yang identik.

Pemakaian:  python3 main.py [A|B] [path-output]
  Varian A = koran (masthead + pita tanggal + hero + grid 2x2).
  Varian B = baris bertumpuk (nomor besar + headline + bodi pendek).
  Tanpa argumen: varian A ke /output/entry.png (jalur run kit).
"""

import struct
import sys
import zlib

W = 1024
H = 1024

PAPER = (253, 251, 244)
WHITE = (255, 255, 255)
INK = (17, 17, 17)
NAVY = (20, 38, 77)
RED = (176, 30, 36)
GRAY = (122, 118, 110)
LIGHT = (233, 229, 217)
TEAL = (46, 107, 79)
ORANGE = (179, 64, 42)
DARK = (51, 51, 51)
GOLD = (214, 164, 32)
STONE = (200, 198, 190)
STONE_DARK = (160, 158, 150)

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}

STORIES = [
    {
        "kicker": "UKRAINE - DYMER, NEAR KYIV - MONDAY",
        "headline": "DYMER TOLL RISES TO 11",
        "body_a": "RESCUERS PULL AN 11TH BODY FROM THE DYMER FLATS MONDAY. "
                  "A 7-YEAR-OLD BOY IS PULLED OUT ALIVE. KYIV REGION MOURNS "
                  "AS THE WEEKEND TOLL HITS 15. TWO STILL MISSING.",
        "body_b": "11TH BODY PULLED FROM DYMER FLATS MONDAY. "
                  "A 7-YEAR-OLD BOY PULLED OUT ALIVE.",
    },
    {
        "kicker": "UKRAINE - LIBYA - MONDAY",
        "headline": "UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA",
        "body_a": "ZELENSKYY SAYS 7 SEA DRONES SANK THE CORVETTE MERKURY "
                  "SUNDAY. CARGO SHIP ANGARA ALSO HIT, 2,400 KM FROM THE FRONT.",
        "body_b": "ZELENSKYY SAYS 7 SEA DRONES SANK THE MERKURY SUNDAY. "
                  "ANGARA ALSO HIT.",
    },
    {
        "kicker": "CLIMATE - COP31 - MONDAY",
        "headline": "AFTER COP31 COLLAPSES",
        "body_a": "AUSTRALIA'S OPPOSITION WANTS THE MINISTER OUT. PACIFIC "
                  "ISLANDS SAY 'LET DOWN ON ALL SIDES'. "
                  "NEXT TALKS: ADDIS ABABA 2027.",
        "body_b": "OPPOSITION WANTS THE MINISTER OUT. "
                  "PACIFIC ISLANDS SAY 'LET DOWN'.",
    },
    {
        "kicker": "INDONESIA - BANTEN - MONDAY",
        "headline": "FACTORY FIRE KILLS 24 IN INDONESIA",
        "body_a": "24 DEAD AT CANDY PLANT IN BANTEN. ABOUT 30 MISSING. "
                  "CAUSE UNDER INVESTIGATION, SUSPECTED AC SHORT CIRCUIT.",
        "body_b": "24 DEAD AT CANDY PLANT IN BANTEN. ABOUT 30 STILL MISSING.",
    },
    {
        "kicker": "USA - WASHINGTON - MONDAY",
        "headline": "COURT OPENS PATH TO ERASE TRUMP CONVICTION",
        "body_a": "COURT OPENS PATH TO MOVE HUSH-MONEY CASE TO FEDERAL COURT. "
                  "TRUMP COULD SEEK DISMISSAL. CONVICTION STANDS.",
        "body_b": "COURT OPENS PATH TO MOVE CASE TO FEDERAL COURT. "
                  "CONVICTION STANDS.",
    },
]

MASTHEAD = "WORLD NEWS"
DATE_LINE = "TUESDAY, 24 NOVEMBER 2026"
FOOTER = "FIVE STORIES FROM AROUND THE WORLD - SOURCES: REUTERS, AP, UN NEWS"


def check_font():
    for ch, rows in FONT.items():
        if len(rows) != 7:
            raise ValueError("glyph " + ch + " must have 7 rows")
        for row in rows:
            if len(row) != 5:
                raise ValueError("glyph " + ch + " rows must be 5 wide")
            for bit in row:
                if bit not in "01":
                    raise ValueError("glyph " + ch + " has bad bit")


def check_stories():
    texts = [MASTHEAD, DATE_LINE, FOOTER]
    for story in STORIES:
        texts.append(story["kicker"])
        texts.append(story["headline"])
        texts.append(story["body_a"])
        texts.append(story["body_b"])
    for text in texts:
        for ch in text:
            if ch not in FONT:
                raise ValueError("character not in font: " + repr(ch))


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap_text(text, max_chars):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        cur = ""
        for word in words:
            if len(word) > max_chars:
                raise ValueError("word too long to wrap: " + word)
            if cur == "":
                cur = word
            elif len(cur) + 1 + len(word) <= max_chars:
                cur = cur + " " + word
            else:
                lines.append(cur)
                cur = word
        if cur != "":
            lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set_pixel(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = x if x > 0 else 0
        y0 = y if y > 0 else 0
        x1 = x + w if x + w < self.w else self.w
        y1 = y + h if y + h < self.h else self.h
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = color[0]
                self.px[i + 1] = color[1]
                self.px[i + 2] = color[2]

    def rect_border(self, x, y, w, h, color):
        self.fill_rect(x, y, w, 2, color)
        self.fill_rect(x, y + h - 2, w, 2, color)
        self.fill_rect(x, y, 2, h, color)
        self.fill_rect(x + w - 2, y, 2, h, color)

    def circle_fill(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            glyph = FONT[ch]
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += 6 * scale

    def draw_text_centered(self, y, text, scale, color):
        tw = text_width(text, scale)
        self.draw_text((self.w - tw) // 2, y, text, scale, color)


def png_bytes(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def draw_ship(cv, x, y):
    cv.fill_rect(x, y, 56, 56, NAVY)
    cv.fill_rect(x + 27, y + 12, 2, 20, WHITE)
    cv.fill_rect(x + 30, y + 14, 10, 4, WHITE)
    cv.fill_rect(x + 30, y + 19, 12, 4, WHITE)
    cv.fill_rect(x + 30, y + 24, 8, 4, WHITE)
    cv.fill_rect(x + 14, y + 30, 28, 4, WHITE)
    cv.fill_rect(x + 10, y + 34, 36, 8, WHITE)
    cv.fill_rect(x + 8, y + 46, 40, 2, WHITE)
    cv.fill_rect(x + 14, y + 50, 28, 2, WHITE)


def draw_globe(cv, x, y):
    cv.fill_rect(x, y, 56, 56, TEAL)
    cv.circle_fill(x + 28, y + 28, 18, WHITE)
    cv.fill_rect(x + 27, y + 10, 2, 36, TEAL)
    cv.fill_rect(x + 10, y + 27, 36, 2, TEAL)
    cv.fill_rect(x + 12, y + 18, 32, 2, TEAL)
    cv.fill_rect(x + 12, y + 36, 32, 2, TEAL)


def draw_flame(cv, x, y):
    cv.fill_rect(x, y, 56, 56, ORANGE)
    cv.fill_rect(x + 26, y + 11, 4, 5, WHITE)
    cv.fill_rect(x + 25, y + 16, 6, 6, WHITE)
    cv.fill_rect(x + 22, y + 22, 12, 6, WHITE)
    cv.fill_rect(x + 20, y + 28, 16, 6, WHITE)
    cv.fill_rect(x + 22, y + 34, 12, 12, WHITE)
    cv.fill_rect(x + 25, y + 36, 6, 8, GOLD)


def draw_court(cv, x, y):
    cv.fill_rect(x, y, 56, 56, DARK)
    cv.fill_rect(x + 12, y + 12, 32, 4, WHITE)
    cv.fill_rect(x + 16, y + 16, 24, 4, WHITE)
    cv.fill_rect(x + 20, y + 20, 16, 4, WHITE)
    cv.fill_rect(x + 12, y + 26, 5, 14, WHITE)
    cv.fill_rect(x + 25, y + 26, 5, 14, WHITE)
    cv.fill_rect(x + 38, y + 26, 5, 14, WHITE)
    cv.fill_rect(x + 10, y + 42, 36, 4, WHITE)


def draw_skyline(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, NAVY)
    cv.fill_rect(x + 100, y + 20, 8, 8, GRAY)
    cv.fill_rect(x + 116, y + 10, 6, 6, GRAY)
    cv.fill_rect(x + 12, y + 52, 20, 8, STONE)
    cv.fill_rect(x + 12, y + 60, 34, 110, STONE)
    cv.fill_rect(x + 56, y + 82, 16, 8, STONE_DARK)
    cv.fill_rect(x + 56, y + 90, 30, 80, STONE_DARK)
    cv.fill_rect(x + 96, y + 32, 18, 8, WHITE)
    cv.fill_rect(x + 96, y + 40, 36, 130, WHITE)
    cv.fill_rect(x + 142, y + 78, 30, 92, STONE_DARK)
    cv.fill_rect(x + 182, y + 100, 26, 70, STONE)
    cv.fill_rect(x + 104, y + 112, 4, 8, GOLD)
    cv.fill_rect(x + 100, y + 120, 12, 10, RED)


def draw_masthead(cv):
    cv.fill_rect(28, 28, 968, 84, NAVY)
    cv.draw_text_centered(38, MASTHEAD, 9, WHITE)
    cv.fill_rect(28, 116, 968, 40, RED)
    cv.draw_text_centered(122, DATE_LINE, 4, WHITE)


def draw_footer(cv):
    cv.draw_text_centered(984, FOOTER, 2, GRAY)


def draw_hero(cv, story):
    x, y, w, h = 28, 168, 968, 284
    cv.fill_rect(x, y, w, h, WHITE)
    cv.rect_border(x, y, w, h, GRAY)
    cv.draw_text(x + 20, y + 16, story["kicker"], 2, RED)
    head = story["headline"]
    if text_width(head, 6) > w - 40:
        raise ValueError("hero headline too wide: " + head)
    cv.draw_text(x + 20, y + 40, head, 6, INK)
    draw_skyline(cv, x + 20, y + 98, 220, 170)
    body = wrap_text(story["body_a"], 688 // 18)
    if len(body) > 6:
        raise ValueError("hero body overflows: " + str(len(body)) + " lines")
    for i, line in enumerate(body):
        cv.draw_text(x + 256, y + 98 + i * 23, line, 3, INK)


def draw_panel(cv, x, y, w, h, story, icon):
    cv.fill_rect(x, y, w, h, WHITE)
    cv.rect_border(x, y, w, h, GRAY)
    icon(cv, x + w - 16 - 56, y + 16)
    cv.draw_text(x + 16, y + 16, story["kicker"], 2, RED)
    head = wrap_text(story["headline"], (w - 32) // 18)
    if len(head) > 2:
        raise ValueError("panel headline overflows: " + story["headline"])
    hy = y + 38
    for i, line in enumerate(head):
        cv.draw_text(x + 16, hy + i * 23, line, 3, INK)
    body = wrap_text(story["body_a"], (w - 32) // 18)
    if len(body) > 5:
        raise ValueError("panel body overflows: " + story["headline"])
    by = hy + len(head) * 23 + 8
    for i, line in enumerate(body):
        cv.draw_text(x + 16, by + i * 23, line, 3, INK)


def render_a():
    cv = Canvas(W, H, PAPER)
    cv.rect_border(12, 12, 1000, 1000, GRAY)
    draw_masthead(cv)
    draw_hero(cv, STORIES[0])
    icons = [draw_ship, draw_globe, draw_flame, draw_court]
    positions = [(28, 468), (520, 468), (28, 724), (520, 724)]
    for i in range(4):
        px, py = positions[i]
        draw_panel(cv, px, py, 476, 240, STORIES[i + 1], icons[i])
    draw_footer(cv)
    return png_bytes(cv)


def draw_row(cv, y, num, story):
    cv.fill_rect(28, y, 968, 150, WHITE)
    cv.rect_border(28, y, 968, 150, GRAY)
    cv.fill_rect(28, y, 120, 150, NAVY)
    digit = str(num)
    tw = text_width(digit, 8)
    cv.draw_text(28 + (120 - tw) // 2, y + (150 - 56) // 2, digit, 8, WHITE)
    tx = 168
    cv.draw_text(tx, y + 14, story["kicker"], 2, RED)
    head = wrap_text(story["headline"], 808 // 24)
    if len(head) > 2:
        raise ValueError("row headline overflows: " + story["headline"])
    hy = y + 36
    for i, line in enumerate(head):
        cv.draw_text(tx, hy + i * 28, line, 4, INK)
    body = wrap_text(story["body_b"], 808 // 18)
    if len(body) > 2:
        raise ValueError("row body overflows: " + story["headline"])
    by = hy + len(head) * 28 + 8
    for i, line in enumerate(body):
        cv.draw_text(tx, by + i * 23, line, 3, INK)


def render_b():
    cv = Canvas(W, H, PAPER)
    cv.rect_border(12, 12, 1000, 1000, GRAY)
    draw_masthead(cv)
    y = 168
    for i, story in enumerate(STORIES):
        draw_row(cv, y, i + 1, story)
        y += 162
    draw_footer(cv)
    return png_bytes(cv)


def layout_note(variant):
    """Satu baris ringkas untuk log: varian + jumlah cerita + tanggal."""
    if variant == "A":
        shape = "koran: hero + grid 2x2"
    else:
        shape = "baris: 5 nomor + headline"
    return "news-image 20261124 variant " + variant + " (" + shape + "), " \
        + str(len(STORIES)) + " stories, " + DATE_LINE


def main(argv):
    variant = argv[1] if len(argv) > 1 else "A"
    out = argv[2] if len(argv) > 2 else "/output/entry.png"
    check_font()
    check_stories()
    if variant == "A":
        data = render_a()
    elif variant == "B":
        data = render_b()
    else:
        raise ValueError("variant must be A or B")
    with open(out, "wb") as f:
        f.write(data)
    print("OK variant=" + variant + " bytes=" + str(len(data))
          + " out=" + out)
    print(layout_note(variant))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
