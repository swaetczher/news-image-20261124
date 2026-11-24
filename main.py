#!/usr/bin/env python3
"""news-image-20261124 ronde 2 — satu gambar ringkasan berita dunia.

Ditulis dari nol di sesi produksi ronde 2 (dimulai 24 Nov 2026 ~21:37 WIB).
Stdlib-only: struct, sys, zlib. Tanpa os, tanpa network, tanpa PIL.
Font bitmap 5x7 + encoder PNG pure-Python. Deterministik: output hanya
bergantung pada konstanta di file ini — run ulang menghasilkan byte yang
sama persis (dicek 3 run identik sebelum lapor).

Isi (riset-r2.md, semua peristiwa/pengumuman Selasa 24 Nov 2026):
  1 HERO  Selat Hormuz — 3 tanker kena ranjau (Iran says), AS selidiki
          dugaan serangan siber Iran ke ~50 tanker (US investigating).
  2       Ukraina bela serangan Benghazi sebagai bela diri Pasal 51;
          Zelenskyy akui serang Sparta II di Teluk Finlandia.
  3       Israel bunuh kepala keamanan internal Hamas di Gaza + 6 lainnya.
  4       Serangan Rusia ke Zaporizhzhia: 2 tewas, 22 luka (Reuters).
  5       Banten: korban naik 26 tewas, 8 hilang, penyidikan pidana
          kelalaian dibuka polisi (indikasi awal, bukan vonis).
Tanggal gambar: TUESDAY, 24 NOVEMBER 2026 (judul kompetisi).
Klaim selalu dilabeli sebagai klaim di teks gambar.
"""

import struct
import sys
import zlib

W = 1024
H = 1024

BG = (245, 242, 233)
INK = (26, 26, 26)
NAVY = (18, 34, 77)
RED = (176, 30, 40)
GREY = (90, 90, 90)
WHITE = (255, 255, 255)
PANEL = (255, 255, 255)
LINE = (120, 115, 100)
TEAL = (0, 96, 96)
RUST = (150, 62, 20)
SEA = (16, 52, 96)
FLAME = (232, 120, 20)
FLAME2 = (244, 196, 40)

# ---------------------------------------------------------------- font 5x7
# Setiap glif: 7 baris, tiap baris 5 bit (bit 4 = kolom kiri).
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    "-": (0, 0, 0, 0x1F, 0, 0, 0),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "+": (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
}


def text_w(s, scale):
    """Lebar piksel teks pada skala tertentu (advance 6 piksel per huruf)."""
    return len(s) * 6 * scale


def wrap(s, max_w, scale):
    """Bungkus kata per kata; kembalikan daftar baris (tanpa hyphen)."""
    lines = []
    cur = ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- kanvas
class Canvas:
    def __init__(self):
        self.buf = bytearray(W * H * 3)
        for i in range(W * H):
            self.buf[i * 3] = BG[0]
            self.buf[i * 3 + 1] = BG[1]
            self.buf[i * 3 + 2] = BG[2]

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(W, x + w)
        y1 = min(H, y + h)
        for yy in range(y0, y1):
            base = (yy * W + x0) * 3
            for xx in range(x0, x1):
                o = base + (xx - x0) * 3
                self.buf[o] = color[0]
                self.buf[o + 1] = color[1]
                self.buf[o + 2] = color[2]

    def border(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def text(self, x, y, s, scale, color):
        # Font hanya huruf besar: semua teks dirender kapital (gaya koran).
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch)
            if glyph is None:
                raise ValueError("glif hilang: %r" % ch)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale

    def text_center(self, y, s, scale, color):
        self.text((W - text_w(s, scale)) // 2, y, s, scale, color)

    def para(self, x, y, lines, scale, color, leading=None):
        lh = 8 * scale if leading is None else leading
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, scale, color)
        return y + len(lines) * lh


def png_bytes(c):
    """Encoder PNG RGB 8-bit, filter 0, kompresi zlib deterministik."""

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += c.buf[yy * W * 3:(yy + 1) * W * 3]
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b""))


# ---------------------------------------------------------------- konten
# CATATAN DETERMINISME RONDE 2 (baris baru, ditulis lewat edit di sesi ini):
# - Tidak ada jam dinding, tidak ada acak, tidak ada dict yang diiterasi
#   tanpa urutan tetap: PANELS adalah list berurutan, FONT hanya dibaca
#   lewat kunci eksplisit, dan zlib.compress dipanggil dengan level tetap.
# - Satu-satunya input adalah argv (varian + path output); isi gambar
#   sepenuhnya ditentukan konstanta HERO / PANELS / FOOTER di file ini.
# - Karena itu sha256 output stabil antar run di mesin yang sama, dan
#   verifikasi 3-run identik adalah bukti langsung, bukan klaim.
# - Kalau suatu hari ada yang mengubah satu huruf di HERO/PANELS, hash
#   berubah — itu yang diinginkan: gambar adalah fungsi murni dari file.
def r2_build_note():
    """Satu kalimat asal-usul build, dipakai sebagai penanda revisi ronde 2."""
    return ("r2: Hormuz hero + 4 panel Selasa 24 Nov 2026, "
            "headline panel skala 5, bodi maks 4 baris.")


HERO = {
    "kicker": "MIDDLE EAST - STRAIT OF HORMUZ - TUESDAY",
    "headline": "TANKERS HIT IN HORMUZ",
    "body": ("Iran says three tankers caught fire after hitting mines Monday. "
             "The US is probing suspected Iranian cyberattacks on up to 50 "
             "tankers, announced Tuesday."),
}

PANELS = [
    {
        "kicker": "UKRAINE - LIBYA - TUESDAY",
        "headline": "UKRAINE DEFENDS LIBYA STRIKE",
        "body": ("Kyiv cites UN Charter Article 51. Zelenskyy also claims "
                 "the Sparta II hit."),
        "short": ("Kyiv cites UN Charter Article 51. Zelenskyy claims a "
                  "second strike on the Sparta II."),
        "accent": NAVY,
    },
    {
        "kicker": "GAZA - TUESDAY",
        "headline": "ISRAEL KILLS HAMAS SECURITY CHIEF",
        "body": ("Hamas security chief Naeem Abu Nahel killed with six "
                 "others, medics say."),
        "short": ("Hamas security chief Naeem Abu Nahel killed with six "
                  "others, medics say."),
        "accent": RED,
    },
    {
        "kicker": "ZAPORIZHZHIA - TUESDAY",
        "headline": "RUSSIAN STRIKE KILLS 2 IN ZAPORIZHZHIA",
        "body": ("Overnight attack wounds 22, including two children. "
                 "An apartment block was hit."),
        "short": ("Overnight attack wounds 22, including two children. "
                  "An apartment block was hit."),
        "accent": TEAL,
    },
    {
        "kicker": "BANTEN - TUESDAY",
        "headline": "BANTEN FIRE TOLL RISES TO 26",
        "body": ("Confirmed Tuesday. Eight still missing. Police open a "
                 "criminal negligence probe."),
        "short": ("Confirmed Tuesday. Eight still missing. Police open a "
                  "criminal negligence probe."),
        "accent": RUST,
    },
]

FOOTER = "FIVE STORIES FROM AROUND THE WORLD - SOURCES: REUTERS, AP"


# ---------------------------------------------------------------- gambar
def draw_masthead(c):
    c.rect(16, 12, 992, 88, NAVY)
    c.text_center(26, "WORLD NEWS", 9, WHITE)
    c.rect(16, 104, 992, 42, RED)
    c.text_center(110, "TUESDAY, 24 NOVEMBER 2026", 5, WHITE)


def draw_tanker_art(c, x, y, w, h):
    """Seni hero: tanker di Selat Hormuz, langit malam + api + ranjau."""
    c.rect(x, y, w, h, SEA)
    # langit malam + bintang
    c.rect(x, y, w, 52, NAVY)
    for sx, sy in ((18, 12), (52, 26), (96, 10), (150, 22), (196, 12),
                   (228, 28), (70, 34), (176, 36)):
        c.rect(x + sx, y + sy, 4, 4, WHITE)
    # bulan
    c.rect(x + w - 52, y + 10, 30, 30, (240, 236, 210))
    c.rect(x + w - 44, y + 16, 14, 14, NAVY)
    # laut
    c.rect(x, y + 96, w, 4, (120, 170, 220))
    c.rect(x, y + 116, w, 3, (90, 140, 200))
    # lambung tanker
    c.rect(x + 18, y + 78, 196, 22, (30, 30, 34))
    c.rect(x + 18, y + 78, 196, 4, (70, 70, 78))
    c.rect(x + 150, y + 56, 26, 22, (60, 60, 68))
    c.rect(x + 154, y + 50, 18, 6, RED)
    # cerobong + api di geladak
    c.rect(x + 60, y + 62, 14, 16, (200, 200, 200))
    c.rect(x + 58, y + 44, 6, 18, FLAME)
    c.rect(x + 64, y + 38, 6, 24, FLAME2)
    c.rect(x + 70, y + 48, 6, 14, FLAME)
    c.rect(x + 40, y + 30, 44, 6, (150, 150, 150))
    c.rect(x + 52, y + 22, 20, 8, (130, 130, 130))
    # ranjau laut mengambang
    mx, my = x + w - 46, y + 104
    c.rect(mx, my, 16, 16, (20, 20, 20))
    c.rect(mx + 6, my - 6, 4, 6, (20, 20, 20))
    c.rect(mx + 6, my + 16, 4, 6, (20, 20, 20))
    c.rect(mx - 6, my + 6, 6, 4, (20, 20, 20))
    c.rect(mx + 16, my + 6, 6, 4, (20, 20, 20))


def draw_hero(c):
    x, y, w, h = 16, 158, 992, 238
    c.rect(x, y, w, h, PANEL)
    c.border(x, y, w, h, LINE)
    c.rect(x, y, 8, h, RED)
    ix = x + 16
    iy = y + 12
    c.text(ix, iy, HERO["kicker"], 3, RED)
    head = HERO["headline"]
    assert text_w(head, 6) <= w - 32, "headline hero kepanjangan"
    c.text(ix, iy + 30, head, 6, NAVY)
    ay = iy + 30 + 48 + 8
    draw_tanker_art(c, ix, ay, 250, 136)
    bx = ix + 250 + 16
    bw = x + w - 16 - bx
    body = wrap(HERO["body"], bw, 3)
    assert len(body) <= 5, "bodi hero %d baris" % len(body)
    c.para(bx, ay, body, 3, INK)
    return y + h


def draw_panel(c, p, x, y, w, h):
    c.rect(x, y, w, h, PANEL)
    c.border(x, y, w, h, LINE)
    c.rect(x, y, 8, h, p["accent"])
    ix = x + 20
    iy = y + 12
    iw = x + w - 16 - ix
    c.text(ix, iy, p["kicker"], 3, p["accent"])
    head = wrap(p["headline"], iw, 5)
    assert len(head) <= 3, "headline panel %d baris" % len(head)
    c.para(ix, iy + 30, head, 5, NAVY)
    by = iy + 30 + len(head) * 40 + 6
    body = wrap(p["body"], iw, 3)
    assert len(body) <= 4, "bodi panel %d baris: %r" % (len(body), body)
    c.para(ix, by, body, 3, INK)


def render_a():
    """Varian A (pemenang ronde 1): koran — hero + grid 2x2.

    Perbaikan ronde 2 vs ronde 1: headline panel naik ke skala 5 (ronde 1
    skala 4) supaya tetap terbaca di downscale 300 px; bodi dipadatkan ke
    maks 4 baris supaya headline besar itu muat tanpa luapan.
    """
    c = Canvas()
    c.border(8, 8, W - 16, H - 16, LINE)
    draw_masthead(c)
    draw_hero(c)
    xs = (16, 524)
    ys = (408, 696)
    for i, p in enumerate(PANELS):
        draw_panel(c, p, xs[i % 2], ys[i // 2], 484, 276)
    c.text_center(982, FOOTER, 2, GREY)
    return c


def render_b():
    """Varian B: lima baris bernomor — headline skala 5, bodi 2 baris."""
    c = Canvas()
    c.border(8, 8, W - 16, H - 16, LINE)
    draw_masthead(c)
    stories = [dict(HERO, accent=RED, short=HERO["body"])] + PANELS
    # bodi hero dipendekkan untuk format baris (maks 2 baris skala 3)
    stories[0]["short"] = ("Iran says 3 tankers hit mines Monday. US probes "
                           "suspected cyberattacks on 50 tankers.")
    y = 158
    for i, s in enumerate(stories):
        rh = 156
        c.rect(16, y, 992, rh, PANEL)
        c.border(16, y, 992, rh, LINE)
        c.rect(16, y, 8, rh, s["accent"])
        c.text(36, y + 48, str(i + 1), 8, s["accent"])
        tx = 108
        tw = 1008 - tx
        head = wrap(s["headline"], tw, 5)
        assert len(head) <= 2, "headline B %d baris" % len(head)
        c.para(tx, y + 12, head, 5, NAVY)
        by = y + 12 + len(head) * 40 + 4
        body = wrap(s["short"], tw, 3)
        assert len(body) <= 2, "bodi B %d baris" % len(body)
        c.para(tx, by, body, 3, INK)
        y += rh + 8
    c.text_center(986, FOOTER, 2, GREY)
    return c


def main():
    _note = r2_build_note()  # penanda revisi ronde 2 (tidak memengaruhi gambar)
    variant = sys.argv[1] if len(sys.argv) > 1 else "A"
    out = sys.argv[2] if len(sys.argv) > 2 else "/output/entry.png"
    if variant == "A":
        c = render_a()
    elif variant == "B":
        c = render_b()
    else:
        raise SystemExit("varian harus A atau B")
    data = png_bytes(c)
    with open(out, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
