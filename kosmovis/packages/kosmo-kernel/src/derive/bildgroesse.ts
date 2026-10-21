/**
 * Video-Demolauf 20.10.2026, L3-A4 / L4-16: Pixelgroesse eines eingebetteten Bilds, GELESEN aus
 * dem Dateikopf (PNG: IHDR, JPEG: SOF-Segment) — ohne Bibliothek, ohne DOM, laeuft im Worker und
 * in Node. Erkannt wird an den Kopfbytes, nicht am angegebenen MIME-Typ; ein Format, das hier
 * nicht gelesen wird, bleibt unbekannt (`null`) — nie geraten.
 *
 * Die base64-Daten werden nur dort dekodiert, wo gelesen wird (ein JPEG springt von Segment zu
 * Segment ueber eine grosse EXIF-Vorschau, ohne sie zu dekodieren).
 */

const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
const B64_WERT = new Map<string, number>([...B64].map((c, i) => [c, i]));

/** Liest einzelne Bytes aus base64, ohne alles zu dekodieren. */
function byteLeser(base64: string): { laenge: number; at: (i: number) => number } {
  const daten = base64.replace(/=+$/, '');
  const laenge = Math.floor((daten.length * 3) / 4);
  let quadIdx = -1;
  let quad: [number, number, number] = [0, 0, 0];
  return {
    laenge,
    at(i: number): number {
      if (i < 0 || i >= laenge) return -1;
      const q = Math.floor(i / 3);
      if (q !== quadIdx) {
        let v = 0;
        for (let k = 0; k < 4; k++) {
          const c = daten[q * 4 + k];
          const w = c === undefined ? 0 : B64_WERT.get(c);
          if (w === undefined) return -1;
          v = (v << 6) | w;
        }
        quad = [(v >> 16) & 255, (v >> 8) & 255, v & 255];
        quadIdx = q;
      }
      return quad[i % 3]!;
    },
  };
}

/** SOF-Marker mit Abmessungen (Baseline, Progressiv, Lossless, arithmetisch); C4/C8/CC sind keine. */
const SOF = new Set([0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf]);

export function bildGroesseAusBase64(base64: string): { width: number; height: number } | null {
  const b = byteLeser(base64);
  const u16 = (i: number): number => {
    const hi = b.at(i);
    const lo = b.at(i + 1);
    return hi < 0 || lo < 0 ? -1 : (hi << 8) | lo;
  };
  const u32 = (i: number): number => {
    const hi = u16(i);
    const lo = u16(i + 2);
    return hi < 0 || lo < 0 ? -1 : hi * 65536 + lo;
  };
  // PNG: Signatur 89 50 4E 47 0D 0A 1A 0A, danach der IHDR-Chunk (Breite/Hoehe ab Byte 16).
  const PNG_SIG = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
  if (PNG_SIG.every((v, i) => b.at(i) === v)) {
    if (b.at(12) !== 0x49 || b.at(13) !== 0x48 || b.at(14) !== 0x44 || b.at(15) !== 0x52) return null;
    const width = u32(16);
    const height = u32(20);
    return width > 0 && height > 0 ? { width, height } : null;
  }
  // JPEG: FF D8, dann Segmente bis zum ersten SOF.
  if (b.at(0) === 0xff && b.at(1) === 0xd8) {
    let pos = 2;
    while (pos < b.laenge) {
      if (b.at(pos) !== 0xff) return null;
      while (b.at(pos) === 0xff) pos++; // Fuellbytes
      const marker = b.at(pos);
      pos++;
      if (marker < 0) return null;
      if ((marker >= 0xd0 && marker <= 0xd7) || marker === 0x01) continue; // ohne Laenge
      if (marker === 0xd9 || marker === 0xda) return null; // Ende/Bilddaten vor einem SOF
      const len = u16(pos);
      if (len < 2) return null;
      if (SOF.has(marker)) {
        const height = u16(pos + 3);
        const width = u16(pos + 5);
        return width > 0 && height > 0 ? { width, height } : null;
      }
      pos += len;
    }
    return null;
  }
  return null;
}
