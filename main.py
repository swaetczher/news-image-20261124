#!/usr/bin/env python3
"""news-image 20261124 ronde 4 FINAL - koran harian 1024x1024 stdlib-only.

Ditulis dari nol untuk ronde 4 FINAL (Make Fun, kompetisi news-image-20261124).
Resep visual: monocle-magazine (kertas krem, tinta, SATU aksen merah editorial,
hairline) - dipertahankan dari ronde 3 karena skor naik 453.824 -> 525.243.
Komposisi Mode C: editorial-cover + banner-grid-2x2 + dense-explainer.
Template pola poster-generator-layout: TEMPLATE dict + DATA edisi, anchors,
positioning relatif (below / right_of / center_in), layer background ->
content -> foreground. Render deterministik: sha256 identik antar-run.
32 berita (5 utama + 27 ringkas), 8 region. Tanggal gambar tetap
"TUESDAY, 24 NOVEMBER 2026"; perkembangan Rabu dilabeli "Wednesday".

Penggunaan: python3 main.py --variant A|B|C --out <file.png>
           python3 main.py --all   (render ketiga varian ke variants/)
Hanya stdlib: sys, zlib, struct, hashlib, os.
"""

import hashlib
import os
import struct
import sys
import zlib

W = 1024
H = 1024
PAPER = (242, 239, 231)   # monocle kertas krem #F2EFE7
INK = (26, 26, 26)        # tinta #1A1A1A
ACCENT = (199, 50, 46)    # aksen merah editorial #C7322E, TUNGGAL
HAIR = (200, 194, 176)    # hairline #C8C2B0

# ---------------------------------------------------------------- font 5x7
# Satu keluarga font bitmap 5x7, huruf kapital + angka + tanda baca.
# Setiap glyph: 7 baris x 5 kolom, '#' = piksel tinta.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '*': ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '>': ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    '<': ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
}

# ---------------------------------------------------------------- data edisi
# DATA edisi 24 November 2026 - 32 berita (5 utama + 27 ringkas), 8 region.
# Label tanggal/klaim dipatuhi: perkembangan Rabu = "Wednesday"; klaim IRGC =
# "Iran says"; tuduhan FRMF = "Morocco alleges"; klaim Kyiv = "Ukraine claims";
# tarif = "expected"/"sources say"; COP31 = "collapsed Sunday"; catur partai 2
# belum dimainkan saat render (mulai 21:00 WIB) -> "scheduled Wednesday".
DATA = {
    "masthead": "THE WORLD TODAY",
    "dateline": "TUESDAY, 24 NOVEMBER 2026",
    "dateline_right": "32 STORIES - 8 REGIONS",
    "hero": {
        "kicker": "MIDDLE EAST - WEDNESDAY UPDATE",
        "headline": "TWO MORE TANKERS HIT BY MINES",
        "dek": ("Iran says two more tankers hit mines in Hormuz Wednesday, "
                "its claimed total now six; Tehran warns ships to coordinate "
                "passage."),
    },
    "grid": [
        {
            "kicker": "TECH - TUESDAY",
            "headline": "HUANG'S COMEBACK RALLY FADES",
            "dek": ("Nvidia soars 31% Monday (+$952bn) then falls 5.9% Tuesday "
                    "to $155.38; US blacklists Megaspeed and an Alibaba unit."),
            "icon": "chip",
        },
        {
            "kicker": "PHARMA - TUESDAY",
            "headline": "SANOFI'S $41BN BET CHEERED BY MARKETS",
            "dek": ("Sanofi up 10% and Insmed up 14% Tuesday; biggest pharma "
                    "deal of 2026, largest biotech since Seagen in 2023."),
            "icon": "pill",
        },
        {
            "kicker": "CHINA - WEDNESDAY ANALYSIS",
            "headline": "CHINA'S POLITBURO SHRINKS FURTHER",
            "dek": ("Chen Jining is the fourth Politburo member probed since "
                    "2025, after He Weidong, Zhang Youxia and Ma Xingrui."),
            "icon": "building",
        },
        {
            "kicker": "FOOTBALL - TUESDAY",
            "headline": "SENEGAL KEEP TITLE - FOR NOW",
            "dek": ("Morocco vows Swiss court appeal, alleging contact between "
                    "a CAS judge and Senegal's federation chief."),
            "icon": "trophy",
        },
    ],
    # MORE: (headline <= 48 karakter, fakta <= 48 karakter) agar muat 3 kolom.
    "more": [
        ("IOWA ARMY TO DETONATE 9,500 LB OF LEAD AZIDE",
         "Court lifts hold; blast set for Wednesday 9am CT"),
        ("RUSSIA WARNS ESTONIA OF 'OPEN WAR'",
         "Tallinn to shut land border from 1 December"),
        ("US BLACKLISTS MEGASPEED, ALIBABA UNIT",
         "Entity List bars AI chip diversion to China"),
        ("ZELENSKYY MOCKS LUKASHENKO FLY-TOGETHER BID",
         "'Am I a suitcase?' Kyiv rejects Moscow trip"),
        ("TRUMP TARIFFS 'EXPECTED' AT 15% FOR ALLIES",
         "Sources say China stays at 20%; USTR to announce"),
        ("GAZA DEATH TOLL SINCE TRUCE HITS 1,679",
         "4 killed in 24 hours; total 74,746 since Oct 2023"),
        ("HOUTHIS CLOSE IN ON ADEN AS CIVILIANS FLEE",
         "822 civilians killed and injured since Sept"),
        ("RECORD 2,100 MIGRANTS REACH CANARY IN A DAY",
         "Wednesday arrivals set new daily record"),
        ("SAUDI NATIONAL KIDNAPPED IN NIGER",
         "Suspected IS militants seized him at weekend"),
        ("'EL CHAPO ISIDRO' TO FACE TRIAL IN MEXICO",
         "US extradition request set aside for now"),
        ("EU PROPOSES 22ND SANCTIONS PACKAGE",
         "60 banks off SWIFT; 70+ shadow fleet ships"),
        ("ABREGO GARCIA LANDS IN MADRID",
         "Self-deport ends two-year saga; 90-day visa"),
        ("SENEGAL NAVY RESCUES 974 MIGRANTS",
         "5,200+ intercepted since early November"),
        ("CHESS: GUKESH HAS WHITE IN GAME 2",
         "Game 1 drawn in 38 moves; Game 2 Wed 21:00 WIB"),
        ("ZAPORIZHZHIA TOLL RISES TO 44, LATER 50",
         "Russian strike kills 2, wounds 4 children"),
        ("COP31 COLLAPSES WITHOUT A DEAL",
         "First failed climate summit since 2009"),
        ("POLAND RENEWS PUSH FOR PERMANENT US TROOPS",
         "NATO AWACS deployed after airspace violations"),
        ("GERMANY GETS UKRAINE'S DELTA BATTLE SOFTWARE",
         "NATO allies to share battle-tested system"),
        ("UKRAINE CLAIMS 2,091 RUSSIAN TROOPS KILLED",
         "Kyiv says daily toll; total near 1.64 million"),
        ("UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA",
         "Rare strike far beyond the Black Sea"),
        ("HOUTHI STRIKE HITS RIYADH SKYSCRAPER",
         "Saudi coalition: finance district tower targeted"),
        ("EISENKOT CLINCHES FIRST COALITION DEAL",
         "Ex-army chief seeks to form Israeli government"),
        ("BAGHDAD MOVES ON KURD OIL FIELDS",
         "PM orders takeover of crossings, oilfields"),
        ("US CONSUMER CONFIDENCE NEAR 2-YEAR HIGH",
         "Confidence jumps to highest in nearly 2 years"),
        ("DEMOCRATS: NO DARK MONEY FOR 2028 DEBATES",
         "Candidates must reject dark money, party says"),
        ("EBOLA'S HIDDEN DEATH TOLL REVEALED",
         "Reuters probe finds fields of graves"),
        ("HUAWEI GUILTY OF STEALING US TRADE SECRETS",
         "New York jury convicts; reported Wednesday"),
    ],
    "footer": ("SOURCES: REUTERS - AP - CNN - EUROPEAN COMMISSION - ISW - "
               "SANOFI - CAS - FIDE - CONFERENCE BOARD - ALL CLAIMS LABELLED"),
    # Strip KPI "BY THE NUMBERS": 4 angka kunci edisi (konten nyata).
    "kpi": [
        ("6", "TANKERS CLAIMED BY IRAN"),
        ("+31%", "NVIDIA MONDAY RALLY"),
        ("$41BN", "SANOFI BUYS INSMED"),
        ("2,100", "MIGRANTS IN ONE DAY"),
    ],
}

# Varian = hierarki/spacing, BUKAN ganti resep (semua monocle-magazine).
# A: hero-dominan, MORE 3 kolom, rapat. B: seimbang, MORE 2 kolom.
# C: hero-dominan, MORE 3 kolom, lapang.
VARIANTS = {
    "A": dict(masthead=10, hero=6, grid=4, cols=3, more_pitch=40,
              sec_gap=14, hero_gap=10, grid_gap=12),
    "B": dict(masthead=9, hero=5, grid=4, cols=2, more_pitch=28,
              sec_gap=12, hero_gap=8, grid_gap=10),
    "C": dict(masthead=10, hero=6, grid=4, cols=3, more_pitch=36,
              sec_gap=18, hero_gap=12, grid_gap=14),
}

# TEMPLATE: skema poster-generator-layout (pola saja) - anchors + layer.
TEMPLATE = {
    "schema": "1.0",
    "settings": {"width": W, "height": H, "background_color": "#F2EFE7"},
    "anchors": {"masthead_bottom": (0, 120), "hero_top": (24, 150),
                "grid_top": (24, 560)},
    "layers": ["background", "content", "foreground"],
    "groups": ["headers", "hero", "grid", "more", "footer"],
}

# ---------------------------------------------------------------- kanvas
class Canvas:
    def __init__(self):
        self.px = bytearray(PAPER * (W * H))

    def set(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color):
        for xx in range(x, x + w):
            self.set(xx, y, color)

    def vline(self, x, y, h, color):
        for yy in range(y, y + h):
            self.set(x, yy, color)

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def text(self, x, y, s, scale, color):
        for ci, ch in enumerate(s):
            glyph = FONT.get(ch) or FONT.get(ch.upper())
            if glyph is None:
                raise ValueError("glyph hilang untuk karakter: %r" % ch)
            ox = x + ci * 6 * scale
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '1':
                        for dy in range(scale):
                            for dx in range(scale):
                                self.set(ox + col * scale + dx,
                                         y + row * scale + dy, color)

    def text_w(self, s, scale):
        return len(s) * 6 * scale

    def text_centered(self, y, s, scale, color):
        self.text((W - self.text_w(s, scale)) // 2, y, s, scale, color)


def wrap(text, max_chars):
    """Wrap greedy per kata; baris terakhir JANGAN orphan 1 kata."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    for line in lines:
        if len(line) > max_chars:
            raise ValueError("baris melebihi lebar: %r" % line)
    while len(lines) > 1 and len(lines[-1].split()) == 1:
        prev = lines[-2].split()
        if len(prev) <= 1:
            break
        lines[-2] = " ".join(prev[:-1])
        lines[-1] = prev[-1] + " " + lines[-1]
    return lines


def below(y, height, gap):
    return y + height + gap


def center_in(x, w, content_w):
    return x + (w - content_w) // 2


# ---------------------------------------------------------------- ilustrasi
def draw_tanker(cv, x, y, w, h):
    """Adegan hero: tanker di laut + ranjau (geometris, tinta + aksen)."""
    cv.rect(x, y, w, h, INK)
    # langit krem di dalam kotak: biarkan tinta sebagai laut malam
    sea_y = y + int(h * 0.62)
    cv.rect(x, sea_y, w, h - int(h * 0.62), (58, 58, 54))
    # lambung kapal
    hull_y = sea_y - 26
    cv.rect(x + 18, hull_y, w - 36, 26, PAPER)
    cv.rect(x + 18, hull_y + 26, w - 36, 6, ACCENT)
    # kontainer
    for i in range(4):
        cx = x + 30 + i * 52
        cv.rect(cx, hull_y - 22, 44, 22, ACCENT if i % 2 == 0 else PAPER)
    # cerobong + asap
    cv.rect(x + w - 70, hull_y - 40, 26, 40, PAPER)
    cv.circle(x + w - 57, hull_y - 48, 7, ACCENT)
    cv.circle(x + w - 44, hull_y - 58, 5, ACCENT)
    # ranjau: lingkaran berduri
    for mx, my in ((x + 34, sea_y + 26), (x + w - 52, sea_y + 34)):
        cv.circle(mx, my, 9, ACCENT)
        for dx, dy in ((-11, 0), (11, 0), (0, -11), (0, 11),
                       (-8, -8), (8, -8), (-8, 8), (8, 8)):
            cv.set(mx + dx, my + dy, ACCENT)
    # gelombang
    for gx in range(x + 8, x + w - 8, 26):
        cv.hline(gx, sea_y + 52, 14, PAPER)


def draw_icon(cv, x, y, kind):
    """Ikon geometris kecil per panel grid (1 adegan per panel)."""
    s = 34  # ukuran kotak ikon
    cv.rect(x, y, s, s, INK)
    if kind == "chip":
        cv.rect(x + 9, y + 9, 16, 16, PAPER)
        cv.rect(x + 13, y + 13, 8, 8, ACCENT)
        for i in range(3):
            cv.hline(x + 2, y + 12 + i * 6, 5, PAPER)
            cv.hline(x + s - 7, y + 12 + i * 6, 5, PAPER)
    elif kind == "pill":
        cv.rect(x + 6, y + 13, 22, 9, ACCENT)
        cv.rect(x + 6, y + 13, 11, 9, PAPER)
    elif kind == "building":
        cv.rect(x + 8, y + 6, 18, 22, PAPER)
        for r in range(3):
            for c in range(2):
                cv.rect(x + 11 + c * 7, y + 9 + r * 7, 4, 4, ACCENT)
    elif kind == "trophy":
        cv.rect(x + 11, y + 6, 12, 12, ACCENT)
        cv.rect(x + 14, y + 18, 6, 6, PAPER)
        cv.rect(x + 9, y + 24, 16, 4, PAPER)


# ---------------------------------------------------------------- render
def render(variant):
    cfg = VARIANTS[variant]
    cv = Canvas()
    margin = 24
    content_w = W - 2 * margin
    y = 20

    # -- layer background: kertas sudah jadi latar; hairline atas masthead
    # -- grup headers: masthead + dateline
    ms = cfg["masthead"]
    cv.text_centered(y, DATA["masthead"], ms, INK)
    y = below(y, 7 * ms, 8)
    cv.hline(margin, y, content_w, INK)
    y += 3
    cv.hline(margin, y, content_w, HAIR)
    y += 8
    cv.text(margin, y, DATA["dateline"], 2, INK)
    right = DATA["dateline_right"]
    cv.text(W - margin - cv.text_w(right, 1), y + 4, right, 1, ACCENT)
    y = below(y, 14, cfg["sec_gap"])
    cv.hline(margin, y, content_w, HAIR)
    y += cfg["sec_gap"]

    # -- grup hero: ilustrasi kiri + teks kanan
    hero_top = y
    ill_w = 300
    hero_text_x = margin + ill_w + 16
    hero_text_w = W - margin - hero_text_x
    hs = cfg["hero"]
    hero = DATA["hero"]
    cv.text(hero_text_x, y, hero["kicker"], 1, ACCENT)
    y = below(y, 7, 6)
    head_lines = wrap(hero["headline"], hero_text_w // (6 * hs))
    for line in head_lines:
        cv.text(hero_text_x, y, line, hs, INK)
        y += 7 * hs
    y += 6
    dek_lines = wrap(hero["dek"], hero_text_w // 6)
    assert len(dek_lines) <= 3, "dek hero > 3 baris: %r" % (dek_lines,)
    for line in dek_lines:
        cv.text(hero_text_x, y, line, 1, INK)
        y += 10
    hero_h = y - hero_top
    draw_tanker(cv, margin, hero_top, ill_w, hero_h)
    y = below(hero_top, hero_h, cfg["sec_gap"])
    cv.hline(margin, y, content_w, HAIR)
    y += cfg["sec_gap"]

    # -- grup grid 2x2
    grid_top = y
    gs = cfg["grid"]
    gutter = 16
    panel_w = (content_w - gutter) // 2
    panel_h = 0
    for row in range(2):
        row_y = y
        row_h = 0
        for col in range(2):
            item = DATA["grid"][row * 2 + col]
            px = margin + col * (panel_w + gutter)
            cv.text(px, row_y, item["kicker"], 1, ACCENT)
            ly = below(row_y, 7, 5)
            maxc = (panel_w - 14) // (6 * gs)
            lines = wrap(item["headline"], maxc)
            assert len(lines) <= 3, "headline grid > 3 baris: %r" % (lines,)
            for line in lines:
                cv.text(px, ly, line, gs, INK)
                ly += 7 * gs
            ly += 4
            dek = wrap(item["dek"], (panel_w - 14) // 6)
            assert len(dek) <= 2, "dek grid > 2 baris: %r" % (dek,)
            for line in dek:
                cv.text(px, ly, line, 1, INK)
                ly += 10
            # ikon kecil di kanan kicker
            draw_icon(cv, px + panel_w - 34, row_y, item["icon"])
            row_h = max(row_h, ly - row_y)
        if row == 0:
            cv.hline(margin, row_y + row_h + cfg["grid_gap"] // 2,
                     content_w, HAIR)
        y = row_y + row_h + (cfg["grid_gap"] if row == 0 else 0)
        panel_h += row_h
    y += cfg["sec_gap"]
    cv.hline(margin, y, content_w, HAIR)
    y += cfg["sec_gap"]

    # -- strip KPI "BY THE NUMBERS": 4 angka kunci edisi
    kpi_top = y
    cv.text(margin, y, "BY THE NUMBERS", 1, ACCENT)
    y = below(y, 7, 6)
    cell_w = content_w // 4
    for i, (num, label) in enumerate(DATA["kpi"]):
        kx = margin + i * cell_w
        cv.text(kx, y, num, 3, ACCENT if i % 2 == 0 else INK)
        cv.text(kx, y + 25, label, 1, INK)
        if i > 0:
            cv.vline(kx - 8, kpi_top, 48, HAIR)
    y = kpi_top + 48 + cfg["sec_gap"]
    cv.hline(margin, y, content_w, HAIR)
    y += cfg["sec_gap"]

    # -- grup more: header + kolom berita ringkas
    cv.text(margin, y, "MORE FROM TUESDAY - 27 STORIES", 2, INK)
    y = below(y, 14, 6)
    cv.hline(margin, y, content_w, HAIR)
    y += 8
    cols = cfg["cols"]
    col_w = (content_w - (cols - 1) * 16) // cols
    max_chars = col_w // 6 - 2
    per_col = (len(DATA["more"]) + cols - 1) // cols
    more_top = y
    for ci in range(cols):
        cx = margin + ci * (col_w + 16)
        cy = more_top
        for item in DATA["more"][ci * per_col:(ci + 1) * per_col]:
            head, fact = item
            assert len(head) <= max_chars, "headline MORE kepanjangan: %r" % head
            assert len(fact) <= max_chars, "fakta MORE kepanjangan: %r" % fact
            cv.rect(cx, cy + 1, 5, 5, ACCENT)
            cv.text(cx + 10, cy, head, 1, INK)
            cy += 10
            cv.text(cx + 10, cy, fact, 1, (94, 88, 78))
            cy += cfg["more_pitch"] - 10
        if ci < cols - 1:
            cv.vline(cx + col_w + 8, more_top, per_col * cfg["more_pitch"], HAIR)
    y = more_top + per_col * cfg["more_pitch"]
    y += 2
    cv.hline(margin, y, content_w, HAIR)
    y += 8

    # -- grup footer
    footer = DATA["footer"]
    assert cv.text_w(footer, 1) <= content_w, "footer kepanjangan"
    cv.text(margin, y, footer, 1, INK)
    footer_end = y + 7
    assert footer_end <= 1010, "footer keluar kanvas: end y=%d" % footer_end
    print("varian %s: hero_h=%d grid_top=%d more_top=%d footer_end=%d "
          "berita=%d" % (variant, hero_h, grid_top, more_top, footer_end,
                         5 + len(DATA["more"])))
    return encode_png(cv.px)


def encode_png(px):
    raw = bytearray()
    stride = W * 3
    for row in range(H):
        raw.append(0)
        raw += px[row * stride:(row + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def main(argv):
    build = os.path.dirname(os.path.abspath(__file__))
    if "--all" in argv:
        os.makedirs(os.path.join(build, "variants"), exist_ok=True)
        for v in ("A", "B", "C"):
            data = render(v)
            path = os.path.join(build, "variants", "variant-%s.png" % v.lower())
            with open(path, "wb") as f:
                f.write(data)
            print("%s -> %s sha256=%s" % (v, path, sha256_hex(data)))
        return 0
    variant = "A"
    out = None
    i = 0
    while i < len(argv):
        if argv[i] == "--variant":
            variant = argv[i + 1]
            i += 2
        elif argv[i] == "--out":
            out = argv[i + 1]
            i += 2
        else:
            i += 1
    if variant not in VARIANTS:
        print("varian tidak dikenal: %s (pilih A/B/C)" % variant)
        return 2
    data = render(variant)
    if out is None:
        out = os.path.join(build, "output", "entry.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    print("%s -> %s sha256=%s" % (variant, out, sha256_hex(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
