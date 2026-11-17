# Japanese text on the 8x8 OLED using the Misaki Gothic font
# (https://littlelimit.net/misaki.htm, free to use and redistribute).
#
# jpfont.bin layout: u16 N, N sorted u16 code points (big endian),
# then N glyphs of 8 bytes each (MONO_HLSB, 8x8).
# Glyphs are read from flash on demand, so only a small cache uses RAM.
#
# install(display) wraps display.text(): ASCII is drawn with the built-in
# 8x8 font as before, other characters with Misaki glyphs, 8 pixels each,
# so the Scroller line wrapping (1 char = 8 px) keeps working.

import framebuf, struct

FONTFILE = "jpfont.bin"

class JPFont:
    def __init__(self, path=FONTFILE):
        self.f = open(path, "rb")
        self.n = struct.unpack(">H", self.f.read(2))[0]
        self.glyph_base = 2 + self.n * 2
        self.cache = {}
        self.buf = bytearray(8)
        self.fb = framebuf.FrameBuffer(self.buf, 8, 8, framebuf.MONO_HLSB)

    def find(self, cp):
        lo, hi = 0, self.n - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            self.f.seek(2 + mid * 2)
            v = struct.unpack(">H", self.f.read(2))[0]
            if v == cp: return mid
            if v < cp: lo = mid + 1
            else: hi = mid - 1
        return -1

    def glyph(self, ch):
        g = self.cache.get(ch)
        if g is None:
            i = self.find(ord(ch))
            if i < 0:
                i = self.find(0x3013)  # 〓 for missing characters
            self.f.seek(self.glyph_base + i * 8)
            g = self.f.read(8)
            if len(self.cache) > 64: self.cache = {}
            self.cache[ch] = g
        return g

    def draw(self, display, ch, x, y, color):
        self.buf[:] = self.glyph(ch)
        if color:
            display.fill_rect(x, y, 8, 8, 0)
            display.blit(self.fb, x, y, 0)
        else:
            # Inverted text: draw glyph pixels with color 0.
            for row in range(8):
                b = self.buf[row]
                for col in range(8):
                    if b & (0x80 >> col): display.pixel(x + col, y + row, 0)

def install(display):
    if display is None or not hasattr(display, "blit"): return None
    try:
        font = JPFont()
    except OSError:
        print("[jpfont] jpfont.bin not found, Japanese disabled")
        return None
    ascii_text = display.text

    def text(s, x, y, color=1):
        s = str(s)
        start = 0
        for i, ch in enumerate(s):
            if ord(ch) >= 0x80:
                if i > start: ascii_text(s[start:i], x + start * 8, y, color)
                font.draw(display, ch, x + i * 8, y, color)
                start = i + 1
        if start < len(s): ascii_text(s[start:], x + start * 8, y, color)

    display.text = text
    return font
