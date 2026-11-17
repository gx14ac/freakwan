# Convert misaki_gothic.bdf to jpfont.bin: u16 N, N x u16 codepoints (sorted, BE), N x 8 bytes MONO_HLSB 8x8 glyphs.
import sys, struct
src, dst = sys.argv[1], sys.argv[2]
ASCENT = 6
glyphs = {}
cp = None
with open(src, encoding='ascii', errors='replace') as f:
    lines = iter(f)
    for line in lines:
        if line.startswith('ENCODING'): cp = int(line.split()[1])
        elif line.startswith('BBX'): w, h, xo, yo = map(int, line.split()[1:])
        elif line.startswith('BITMAP'):
            rows = []
            for l in lines:
                if l.startswith('ENDCHAR'): break
                rows.append(int(l.strip(), 16) << (8 - 4*len(l.strip())) if len(l.strip()) < 2 else int(l.strip()[:2], 16))
            if cp is None or cp < 0x80 or cp > 0xFFFF: continue
            cell = [0]*8
            top = ASCENT - h - yo
            for i, r in enumerate(rows):
                y = top + i
                if 0 <= y < 8: cell[y] = (r >> xo) & 0xFF
            glyphs[cp] = bytes(cell)
keys = sorted(glyphs)
with open(dst, 'wb') as o:
    o.write(struct.pack('>H', len(keys)))
    o.write(b''.join(struct.pack('>H', k) for k in keys))
    o.write(b''.join(glyphs[k] for k in keys))
print(len(keys), 'glyphs')
