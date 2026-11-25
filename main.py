#!/usr/bin/env python3
"""news-image 20261124 ronde 3 — koran harian "WORLD NEWS", resep monocle-magazine.

Entry Make Fun news-image-20261124 ronde 3: 24 berita (5 utama + 19 ringkas),
7+ region, tanggal gambar TETAP "TUESDAY, 24 NOVEMBER 2026".

Stdlib-only, deterministik (render 2x -> sha256 identik), tanpa font/emoji/aset
eksternal, tanpa network, tanpa model gambar AI. Font bitmap 5x7 digambar kode.

Determinisme dijamin tiga lapis: tidak ada jam dinding/acak/urutan dict yang
bergantung pada hash; kompresi zlib selalu level 9; semua koordinat berasal
dari konstanta + panjang teks, bukan dari keadaan luar. Render ulang kapan pun
menghasilkan byte yang identik — dibuktikan sha256 ganda di laporan produksi.

Pemakaian:
    python3 main.py            # varian A -> output/entry.png
    python3 main.py B variants/variant-b.png
    python3 main.py C variants/variant-c.png
"""

import binascii
import hashlib
import math
import struct
import sys
import zlib

W = 1024
H = 1024

# --- Palet monocle-magazine (aksen merah editorial TUNGGAL) -----------------
PAPER = (242, 239, 231)   # kertas krem #F2EFE7
INK = (26, 26, 26)        # tinta #1A1A1A
RED = (199, 50, 46)       # aksen merah editorial #C7322E
HAIR = (200, 194, 176)    # hairline #C8C2B0

MX = 24                   # margin kiri/kanan
CW = W - 2 * MX           # lebar kolom konten = 976

# --- Font bitmap 5x7 (satu keluarga font; '#' = piksel menyala) --------------
# Setiap glyph: 7 baris, masing-masing 5 karakter. Ditulis dari nol untuk job ini.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    "-": ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ";": ["00000", "01100", "01100", "00000", "01100", "00100", "01000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "?": ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "$": ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
    '"': ["01010", "01010", "00000", "00000", "00000", "00000", "00000"],
    "*": ["00000", "10101", "01110", "11111", "01110", "10101", "00000"],
}

# --- Data edisi (riset-r3.md; semua teks UPPERCASE, karakter ASCII saja) ------
DATE_LINE = "TUESDAY, 24 NOVEMBER 2026"
MASTHEAD = "WORLD NEWS"

HERO = {
    "kicker": "MIDDLE EAST - STRAIT OF HORMUZ - IRAN SAYS",
    "headline": "FOURTH TANKER HITS MINE IN STRAIT OF HORMUZ",
    "dek": "IRAN SAYS A FOURTH TANKER EXPLODED TUESDAY AFTER HITTING A MINE EAST "
            "OF THE STRAIT, BRINGING ITS CLAIMED TOTAL TO FOUR. THE US IS PROBING "
            "SUSPECTED IRANIAN CYBERATTACKS ON UP TO 50 SHIPS. BRENT $88.97 A BARREL.",
}

# Grid 2x2: kicker, headline (1-2 baris), body (2 baris skala 1x).
# Catatan akurasi: angka TAIEX 3,310/40,122 dibulatkan dari 3,310.46/40,122.35
# (Focus Taiwan/CNA); NT$2,230 adalah harga buka limit-up TSMC, bukan tutup.
GRID = [
    {
        "kicker": "ASIA - TAIWAN - TUESDAY",
        "headline": "HUANG RETURNS, TAIEX SOARS 8.99%",
        "body": "TAIWAN'S TAIEX JUMPS A RECORD 3,310 POINTS (+8.99%) TO 40,122 TUESDAY "
                "AS HUANG RETURNS AS CEO. TSMC OPENS LIMIT-UP AT NT$2,230.",
    },
    {
        "kicker": "BUSINESS - FRANCE/US - TUESDAY",
        "headline": "SANOFI BUYS INSMED $41BN",
        "body": "$175 A SHARE TUESDAY IN 2026'S BIGGEST PHARMA DEAL; SANOFI GAINS TWO "
                "DRUGS, CLOSES FIRST HALF OF 2027. INSMED SHARES JUMP 14%.",
    },
    {
        "kicker": "ASIA - CHINA - TUESDAY",
        "headline": "CHINA PROBES CHEN JINING",
        "body": "SHANGHAI PARTY CHIEF, 62, UNDER INVESTIGATION TUESDAY; FOURTH "
                "POLITBURO MEMBER PROBED SINCE 2025, XINHUA SAYS.",
    },
    {
        "kicker": "AFRICA - SPORT - TUESDAY",
        "headline": "SENEGAL WIN BACK AFCON TITLE",
        "body": "CAS UNANIMOUSLY RESTORES SENEGAL AS 2025 CHAMPIONS TUESDAY, "
                "REINSTATING 1-0 EXTRA-TIME WIN OVER MOROCCO.",
    },
]

# Blok MORE: 19 berita ringkas, 1 headline + 1 baris fakta tiap item.
MORE = [
    ("RUSSIAN DRONE BRIEFLY ENTERS POLISH AIRSPACE",
     "WARSAW CALLS IT DELIBERATE; POLAND HELD FIRE OVER CIVILIAN RISK."),
    ("LUKASHENKO INVITES ZELENSKYY TO FLY TO MOSCOW",
     "BELARUS LEADER PROPOSES JOINT TRIP FOR TALKS WITH PUTIN."),
    ("EISENKOT CLINCHES FIRST ISRAEL COALITION DEAL",
     "YASHAR (21 SEATS) JOINS LIEBERMAN (7); DEADLINE TO FORM GOVERNMENT 6 DEC."),
    ("SAUDI COALITION SAYS RIYADH TOWER TARGETED",
     "'TERRORIST ATTACK' TARGETED FINANCE-DISTRICT TOWER, NO DETAILS GIVEN."),
    ("NATO VOWS TO DEFEND SPACE AFTER NUKE SATELLITE REPORT",
     "RUTTE'S REMARKS REPORTED TUESDAY; RUSSIA COULD LAUNCH WITHIN 60 DAYS."),
    ("MALAYSIA TO REPATRIATE 6,803 MYANMAR NATIONALS",
     "DECEMBER RETURNS COME DAYS AFTER ICJ GENOCIDE RULING ON ROHINGYA."),
    ("HASINA SETS RETURN DATE: 16 DECEMBER ON BIMAN",
     "EX-PM PLANS FIRST TRIP HOME SINCE EXILE; DHAKA SAYS ONLY VIA EXTRADITION."),
    ("UN: 47,000 WOMEN KILLED BY PARTNERS OR FAMILY IN 2025",
     "FIVE PER HOUR WORLDWIDE; AFRICA HIGHEST WITH 22,100 VICTIMS."),
    ("WORLD CHESS: GUKESH VS SINDAROV OPENS WITH DRAW",
     "GAME 1 DRAWN IN 38 MOVES IN GENEVA; YOUNGEST TITLE MATCH EVER."),
    ("ABOUT 175 MIGRANTS UNACCOUNTED AFTER BOAT CONTACT LOST",
     "BOAT LEFT DAKAR FOR EUROPE ABOUT TWO WEEKS AGO, OFFICIALS SAY."),
    ("HOUTHI FORCES 60 KM FROM ADEN; CITY 'WILL NOT FALL'",
     "YEMENI GOVERNMENT FORCES SAY ADEN WILL HOLD DESPITE REBEL ADVANCE."),
    ("BANGLADESH GARMENT WORKERS CLASH WITH POLICE",
     "PAY PROTESTS SHUT DOZENS OF FACTORIES; WORKERS DEMAND 30,000 TAKA."),
    ("MEXICO INFLATION HITS SIX-MONTH HIGH OF 3.96%",
     "FIRST-HALF NOVEMBER RATE UP FROM 3.62%; CORE EASES TO 3.68%."),
    ("ABREGO GARCIA TO LEAVE US VOLUNTARILY FOR EUROPE",
     "SALVADORAN MIGRANT FLIES OUT TUESDAY ON COMMERCIAL FLIGHT."),
    ("TRUMP READY TO UNVEIL NEW TARIFFS AFTER PROBE",
     "SECTION 301 FINDINGS ON 16 TRADING PARTNERS DUE TUESDAY OR WEDNESDAY."),
    ("ITALY: NOT TOLD OF UKRAINE STRIKES IN LIBYA",
     "TAJANI WARNS KYIV NOT TO SPREAD WAR TO MEDITERRANEAN."),
    ("GAZA WARNS OF MENINGITIS EPIDEMIC: 272 CASES IN OCTOBER",
     "OCTOBER CASES ABOUT 8X THE MONTHLY AVERAGE; 15 DEAD THIS YEAR."),
    ("UK AND MI5 WARN FIRMS SUPPLYING UKRAINE OF SABOTAGE",
     "RUSSIAN SABOTAGE EFFORTS RISING, USING PROXIES AND ARSON, WARNING SAYS."),
    ("QUAKE 5.6 SHAKES EASTERN NEPAL NEAR TIBET BORDER",
     "NEPAL SAYS 5.6; USGS 5.3. NO MAJOR CASUALTIES REPORTED."),
]

FOOTER = ("SOURCES: REUTERS, AP, UN NEWS, SANOFI, CAS - "
          "ALL STORIES FROM TUESDAY, 24 NOVEMBER 2026")

# --- Varian: SATU resep + template, beda hierarki/spacing -------------------
# A = seimbang | B = hero-dominan | C = lapang
VARIANTS = {
    "A": dict(masthead=9, hero_head=5, grid_head=4, gutter=16,
              sec_gap=18, more_gap=18, hero_pad=12, grid_pad=12),
    "B": dict(masthead=10, hero_head=6, grid_head=4, gutter=12,
              sec_gap=16, more_gap=16, hero_pad=12, grid_pad=12),
    "C": dict(masthead=8, hero_head=4, grid_head=3, gutter=20,
              sec_gap=20, more_gap=22, hero_pad=14, grid_pad=14),
}

BODY_SCALE = 1      # body/dek skala 1x (agate type; pipeline §2.2)
KICKER_SCALE = 1    # kicker skala 1x, letter-spaced
DATE_SCALE = 2      # pita tanggal skala 2x
LINE_H = 9          # tinggi baris body 1x (7 glyph + 2 leading)


# --- Kanvas ------------------------------------------------------------------
class Canvas:
    def __init__(self):
        self.px = bytearray(bytes(PAPER) * (W * H))

    def fill_rect(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        assert 0 <= x and x + w <= W and 0 <= y and y + h <= H, \
            "fill_rect keluar kanvas: x=%d y=%d w=%d h=%d" % (x, y, w, h)
        row = bytes(color) * w
        for yy in range(y, y + h):
            off = (yy * W + x) * 3
            self.px[off:off + w * 3] = row

    def hline(self, x, y, w, color, thick=1):
        self.fill_rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill_rect(x, y, thick, h, color)

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)


def text_w(s, scale, spacing=0):
    return len(s) * (5 * scale + spacing) - spacing if s else 0


def draw_text(cv, x, y, s, scale, color, spacing=0):
    """Gambar teks; karakter tak dikenal = ERROR (fail-loud, bukan diam)."""
    cx = x
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is None:
            raise ValueError("karakter tanpa glyph di font 5x7: %r" % ch)
        for row_i, row in enumerate(glyph):
            for col_i, bit in enumerate(row):
                if bit == "1":
                    cv.fill_rect(cx + col_i * scale, y + row_i * scale,
                                 scale, scale, color)
        cx += 5 * scale + spacing
    return cx


def wrap(text, max_w, scale, spacing=0):
    """Word-wrap greedy; satu kata yang lebih lebar dari max_w = ERROR."""
    cell = 5 * scale + spacing
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        if text_w(word, scale, spacing) > max_w:
            raise ValueError("kata terlalu lebar untuk kolom: %r" % word)
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale, spacing) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def center_in(x0, w, s, scale, spacing=0):
    return x0 + (w - text_w(s, scale, spacing)) // 2


# --- Ilustrasi hero: tanker + ranjau, geometris, palet resep saja ------------
def draw_hero_art(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, INK)
    # Bintang-bintang kecil (kertas).
    for sx, sy in ((18, 14), (52, 26), (96, 10), (150, 20), (196, 12), (128, 34)):
        cv.fill_rect(x + sx, y + sy, 2, 2, PAPER)
    # Bulan kecil.
    cv.fill_rect(x + w - 34, y + 14, 14, 14, PAPER)
    # Ranjau laut (lingkaran kertas + duri).
    mx, my, mr = x + w - 52, y + 52, 9
    cv.fill_circle(mx, my, mr, PAPER)
    for dx, dy in ((-14, 0), (14, 0), (0, -14), (0, 14),
                   (-10, -10), (10, -10), (-10, 10), (10, 10)):
        cv.fill_rect(mx + dx - 1, my + dy - 1, 3, 3, PAPER)
    cv.fill_circle(mx, my, 3, INK)
    # Api merah di atas cerobong.
    fx = x + 118
    cv.fill_rect(fx, y + h - 108, 8, 22, RED)
    cv.fill_rect(fx + 12, y + h - 96, 6, 12, RED)
    cv.fill_rect(fx - 10, y + h - 92, 6, 10, RED)
    # Kapal tanker: lambung kertas + cerobong.
    hy = y + h - 62
    cv.fill_rect(x + 18, hy, 150, 26, PAPER)
    cv.fill_rect(x + 168, hy + 6, 22, 20, PAPER)   # haluan bertingkat
    cv.fill_rect(x + 118, hy - 30, 18, 30, PAPER)  # cerobong
    cv.fill_rect(x + 118, hy - 30, 18, 8, RED)     # pita merah cerobong
    cv.fill_rect(x + 40, hy - 16, 10, 16, PAPER)   # anjungan
    # Gelombang laut (garis kertas).
    for gy in (hy + 34, hy + 44, hy + 54):
        cv.fill_rect(x + 10, gy, w - 20, 2, PAPER)
        cv.fill_rect(x + 30, gy + 5, 60, 2, PAPER)


# --- Layout (template + data; positioning relatif, layer background->foreground)
def render(variant):
    v = VARIANTS[variant]
    cv = Canvas()
    log = []

    # Lapisan background: kertas sudah jadi latar kanvas.
    y = 16
    # --- Grup headers: masthead + pita tanggal -------------------------------
    ms = v["masthead"]
    draw_text(cv, center_in(MX, CW, MASTHEAD, ms), y, MASTHEAD, ms, INK)
    y += 7 * ms
    log.append(("masthead", y))
    y += 10
    cv.hline(MX, y, CW, RED, 3)
    y += 12
    draw_text(cv, center_in(MX, CW, DATE_LINE, DATE_SCALE), y,
              DATE_LINE, DATE_SCALE, RED)
    y += 7 * DATE_SCALE
    log.append(("dateline", y))
    y += 8
    cv.hline(MX, y, CW, HAIR, 1)
    y += v["sec_gap"]

    # --- Grup hero ------------------------------------------------------------
    hero_y = y
    art_w, art_gap = 220, 16
    text_x = MX + art_w + art_gap
    text_wd = MX + CW - text_x
    pad = v["hero_pad"]
    hx = hero_y + pad
    draw_text(cv, text_x, hx, HERO["kicker"], KICKER_SCALE, RED, spacing=1)
    hx += 7 + 8
    hero_lines = wrap(HERO["headline"], text_wd, v["hero_head"])
    for ln in hero_lines:
        draw_text(cv, text_x, hx, ln, v["hero_head"], INK)
        hx += 7 * v["hero_head"] + 4
    hx += 6
    dek_lines = wrap(HERO["dek"], text_wd, BODY_SCALE)
    for ln in dek_lines:
        draw_text(cv, text_x, hx, ln, BODY_SCALE, INK)
        hx += LINE_H
    hero_h = (hx - hero_y) + pad
    draw_hero_art(cv, MX, hero_y + pad, art_w, hero_h - 2 * pad)
    y = hero_y + hero_h
    log.append(("hero_h=%d lines=%d dek=%d" % (hero_h, len(hero_lines),
                                               len(dek_lines)), y))
    cv.hline(MX, y, CW, HAIR, 1)
    y += v["sec_gap"]

    # --- Grup grid 2x2 ---------------------------------------------------------
    gut = v["gutter"]
    pw = (CW - gut) // 2
    grid_y = y
    row_hs = []
    for row in range(2):
        panels = GRID[row * 2:(row + 1) * 2]
        # Hitung tinggi baris dari panel tertinggi (headline + body).
        heights = []
        for p in panels:
            hl = wrap(p["headline"], pw - 2 * v["grid_pad"], v["grid_head"])
            bl = wrap(p["body"], pw - 2 * v["grid_pad"], BODY_SCALE)
            heights.append((len(hl), len(bl)))
        rh = (v["grid_pad"] + 7 + 6
              + max(h[0] for h in heights) * (7 * v["grid_head"] + 3)
              + 6 + max(h[1] for h in heights) * LINE_H + v["grid_pad"])
        row_hs.append(rh)
        for i, p in enumerate(panels):
            px = MX + i * (pw + gut)
            py = grid_y
            # Hairline vertikal antar-kolom (Monocle: kolom dipisah hairline).
            if i == 1:
                cv.vline(px - gut // 2, py, rh, HAIR, 1)
            tx = px + v["grid_pad"]
            tw = pw - 2 * v["grid_pad"]
            ty = py + v["grid_pad"]
            draw_text(cv, tx, ty, p["kicker"], KICKER_SCALE, RED, spacing=1)
            ty += 7 + 6
            for ln in wrap(p["headline"], tw, v["grid_head"]):
                draw_text(cv, tx, ty, ln, v["grid_head"], INK)
                ty += 7 * v["grid_head"] + 3
            ty += 3
            for ln in wrap(p["body"], tw, BODY_SCALE):
                draw_text(cv, tx, ty, ln, BODY_SCALE, INK)
                ty += LINE_H
        grid_y += rh
        if row == 0:
            cv.hline(MX, grid_y, CW, HAIR, 1)
            grid_y += gut
    y = grid_y
    log.append(("grid rows=%s" % (row_hs,), y))
    cv.hline(MX, y, CW, HAIR, 1)
    y += v["sec_gap"]

    # --- Grup MORE: 19 berita ringkas, 2 kolom -------------------------------
    draw_text(cv, MX, y, "MORE FROM TUESDAY - 19 STORIES", DATE_SCALE, RED)
    y += 7 * DATE_SCALE + 8
    cv.hline(MX, y, CW, HAIR, 1)
    y += 10
    more_y = y
    col_w = (CW - gut) // 2
    left = MORE[:10]
    right = MORE[10:]
    max_items = max(len(left), len(right))
    item_h = 2 * LINE_H + v["more_gap"]
    for col_i, items in enumerate((left, right)):
        cx0 = MX + col_i * (col_w + gut)
        iy = more_y
        for head, fact in items:
            h_lines = wrap(head, col_w - 12, BODY_SCALE)
            f_lines = wrap(fact, col_w - 12, BODY_SCALE)
            assert len(h_lines) == 1, "headline MORE >1 baris: %r" % head
            assert len(f_lines) == 1, "fakta MORE >1 baris: %r" % fact
            cv.fill_rect(cx0, iy + 1, 5, 5, RED)  # bullet merah
            draw_text(cv, cx0 + 12, iy, h_lines[0], BODY_SCALE, INK)
            draw_text(cv, cx0 + 12, iy + LINE_H, f_lines[0], BODY_SCALE, INK)
            iy += item_h
    y = more_y + max_items * item_h
    log.append(("more items=%d item_h=%d" % (len(MORE), item_h), y))

    # --- Grup footer -----------------------------------------------------------
    y += 8
    cv.hline(MX, y, CW, HAIR, 1)
    y += 10
    draw_text(cv, center_in(MX, CW, FOOTER, BODY_SCALE), y,
              FOOTER, BODY_SCALE, INK)
    y += 7
    log.append(("footer_end", y))
    assert y <= 1010, "layout overflow: footer berakhir y=%d" % y
    return cv, log, y


def png_bytes(cv):
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += cv.px[yy * W * 3:(yy + 1) * W * 3]

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main(argv):
    variant = (argv[1] if len(argv) > 1 else "A").upper()
    if variant not in VARIANTS:
        raise SystemExit("varian tidak dikenal: %s (pilih A/B/C)" % variant)
    out = argv[2] if len(argv) > 2 else "output/entry.png"
    cv, log, end_y = render(variant)
    data = png_bytes(cv)
    with open(out, "wb") as f:
        f.write(data)
    print("varian %s -> %s" % (variant, out))
    print("  sha256: %s" % hashlib.sha256(data).hexdigest())
    print("  bytes: %d  footer_end_y=%d" % (len(data), end_y))
    for name, yy in log:
        print("  %-28s y=%d" % (name, yy))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
