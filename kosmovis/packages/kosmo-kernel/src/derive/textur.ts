/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  ABNAHMEZEILE 6 — «…oder selber generieren und maps hinzufuegen»
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Der Zuruf: «bitte entweder hochaufloesende texturen im interner gratis
 * finden mit allen maps oder selber generieren und maps hinzufuegen».
 *
 * ## Der Befund, an dem es bisher gebrochen ist
 *
 * `derive/gltf.ts` hat am 11.09.2026 vermessen, was einer Textur in der
 * Ausfuhr fehlt, und drei Dinge genannt. Zwei waren keine Huerde (Behaelter,
 * UV-Koordinaten). Beim dritten steht woertlich: **«BILDPUNKTE. HIER BRICHT
 * ES.»** Die einzigen echten Karten im Haus sind prozedural und
 * BROWSER-GEBUNDEN — `modules/design/texturen.ts` zeichnet auf ein
 * `document.createElement`-Canvas. Der Kern hat weder DOM noch three.js.
 *
 * Diese Datei ist die fehlende Bildquelle: Kacheln als reine Bytes, gezeichnet
 * mit vier Grundformen auf einem Zahlenfeld, ohne Canvas, ohne neue
 * Abhaengigkeit — und darum auch unter Node in jeder Probe lauffaehig.
 *
 * ## Warum 256 Bildpunkte und nicht 2048
 *
 * «Hochaufloesend» ist keine Eigenschaft der Datei, sondern der FLAECHE. Eine
 * Kachel deckt hier EINEN Meter ab (dieselbe Regel wie im 3D-Fenster: 1 UV =
 * 1 m). 256 Punkte je Meter sind rund 6500 Punkte je Zoll bei Massstab 1:1 —
 * mehr, als jeder Druck aufloest.
 *
 * Und die Gegenrechnung, die den Ausschlag gibt: Der PNG-Schreiber unten
 * komprimiert NICHT (s. dort, mit Grund). Eine 256er-Kachel wiegt damit rund
 * 197 KB, eine 1024er rund 3,1 MB. Bei zwei Karten je Material waeren das
 * 6 MB fuer EIN Material — fuer eine Datei, die jemand verschickt, ist das
 * der falsche Handel.
 *
 * ## Welche Karten — und welche ausdruecklich NICHT
 *
 *   FARBE      ja. Was man sieht.
 *   RAUHEIT    ja. Die Karte, die Beton von Kunststoff unterscheidet — eine
 *              gleichmaessige Rauheit laesst jede Flaeche wie Plastik wirken.
 *   NORMALE    NEIN, und das ist ein Entscheid: Eine Normalenkarte braucht
 *              TANGENTEN je Eckpunkt, und die fuehrt `MeshData` nicht. Sie
 *              hier zu schreiben hiesse, die Ausfuhr um Daten zu vergroessern,
 *              die kein Betrachter richtig deuten kann — genau der Fehler,
 *              vor dem der Kopf von `gltf.ts` bei den UVs warnt.
 */

import { materialkatalog } from '@kosmo/data';

/** Kantenlaenge einer Kachel in Bildpunkten. S. Dateikopf. */
export const KACHEL_PX = 256;

/** Eine Kachel: RGB, Zeile fuer Zeile, drei Byte je Bildpunkt. */
export interface Kachel {
  breite: number;
  hoehe: number;
  /** `breite * hoehe * 3` Byte. */
  rgb: Uint8Array;
}

export interface MaterialKarten {
  /** Was man sieht. */
  farbe: Kachel;
  /**
   * Rauheit als Graustufe im gruenen Kanal — dieselbe Belegung wie glTF sie
   * fuer `metallicRoughnessTexture` verlangt (Rauheit gruen, Metall blau).
   * Die Kachel ist darum schon so gebaut, dass sie unveraendert in die Datei
   * kann; eine Umsortierung beim Schreiben waere eine zweite Stelle, an der
   * sich jemand vertun kann.
   */
  rauheit: Kachel;
  /** Welche SIA-Klasse das Rezept geliefert hat. */
  rezept: string;
}

// ───────────────────────────────────────────────────────────────────────────
// 1 · Zeichnen auf einem Zahlenfeld — vier Formen, mehr braucht kein Rezept
// ───────────────────────────────────────────────────────────────────────────

function leer(breite: number, hoehe: number): Kachel {
  return { breite, hoehe, rgb: new Uint8Array(breite * hoehe * 3) };
}

const klemme = (v: number): number => (v < 0 ? 0 : v > 255 ? 255 : v | 0);

function setze(k: Kachel, x: number, y: number, r: number, g: number, b: number): void {
  if (x < 0 || y < 0 || x >= k.breite || y >= k.hoehe) return;
  const i = (y * k.breite + x) * 3;
  k.rgb[i] = klemme(r);
  k.rgb[i + 1] = klemme(g);
  k.rgb[i + 2] = klemme(b);
}

/** Mischen statt Ersetzen — `anteil` 0..1. */
function mische(k: Kachel, x: number, y: number, r: number, g: number, b: number, anteil: number): void {
  if (x < 0 || y < 0 || x >= k.breite || y >= k.hoehe) return;
  const i = (y * k.breite + x) * 3;
  const t = anteil < 0 ? 0 : anteil > 1 ? 1 : anteil;
  k.rgb[i] = klemme(k.rgb[i]! * (1 - t) + r * t);
  k.rgb[i + 1] = klemme(k.rgb[i + 1]! * (1 - t) + g * t);
  k.rgb[i + 2] = klemme(k.rgb[i + 2]! * (1 - t) + b * t);
}

function fuelle(k: Kachel, r: number, g: number, b: number): void {
  for (let y = 0; y < k.hoehe; y++) for (let x = 0; x < k.breite; x++) setze(k, x, y, r, g, b);
}

function rechteck(k: Kachel, x0: number, y0: number, w: number, h: number,
                  r: number, g: number, b: number): void {
  for (let y = y0; y < y0 + h; y++) for (let x = x0; x < x0 + w; x++) setze(k, x, y, r, g, b);
}

/**
 * Waagrechte Linie mit weicher Kante.
 *
 * `staerke` ist die halbe Breite; der Rand wird anteilig gemischt, sonst
 * saehe jede Fuge nach Treppe aus — bei 256 Punkten je Meter faellt das auf.
 */
function linieH(k: Kachel, y: number, staerke: number, r: number, g: number, b: number): void {
  const von = Math.floor(y - staerke), bis = Math.ceil(y + staerke);
  for (let yy = von; yy <= bis; yy++) {
    const d = Math.abs(yy + 0.5 - y);
    const anteil = d <= staerke ? 1 : Math.max(0, 1 - (d - staerke));
    if (anteil <= 0) continue;
    for (let x = 0; x < k.breite; x++) mische(k, x, yy, r, g, b, anteil);
  }
}

/** Kreisscheibe, weiche Kante — dieselbe Begruendung wie bei `linieH`. */
function scheibe(k: Kachel, cx: number, cy: number, radius: number,
                 r: number, g: number, b: number, deckung = 1): void {
  const von = Math.floor(cy - radius - 1), bis = Math.ceil(cy + radius + 1);
  for (let y = von; y <= bis; y++) {
    for (let x = Math.floor(cx - radius - 1); x <= Math.ceil(cx + radius + 1); x++) {
      const d = Math.hypot(x + 0.5 - cx, y + 0.5 - cy);
      const anteil = d <= radius ? 1 : Math.max(0, 1 - (d - radius));
      if (anteil > 0) mische(k, x, y, r, g, b, anteil * deckung);
    }
  }
}

/** Deterministischer Zufall — dieselbe Kachel ueber alle Laeufe. */
function lcg(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function rauschen(k: Kachel, basis: readonly [number, number, number],
                  rnd: () => number, staerke: number): void {
  for (let y = 0; y < k.hoehe; y++) {
    for (let x = 0; x < k.breite; x++) {
      const d = (rnd() - 0.5) * 2 * staerke;
      setze(k, x, y, basis[0] + d, basis[1] + d, basis[2] + d);
    }
  }
}

/** Eine Rauheitskachel aus einem Grundwert plus Streuung. */
function rauheitskachel(grund: number, rnd: () => number, streuung: number): Kachel {
  const k = leer(KACHEL_PX, KACHEL_PX);
  for (let y = 0; y < k.hoehe; y++) {
    for (let x = 0; x < k.breite; x++) {
      const v = klemme((grund + (rnd() - 0.5) * 2 * streuung) * 255);
      // Gruen traegt die Rauheit, blau das Metall (hier null) — glTF-Belegung.
      setze(k, x, y, 0, v, 0);
    }
  }
  return k;
}

// ───────────────────────────────────────────────────────────────────────────
// 2 · Die Rezepte — je SIA-Klasse eines
//
// Sie sind die Uebersetzung der Canvas-Rezepte aus `modules/design/
// texturen.ts` auf ein Zahlenfeld. GLEICHE BILDER SIND NICHT DAS ZIEL und
// waeren auch nicht pruefbar: Dort zeichnet ein Browser mit seiner eigenen
// Kantenglaettung. Gleich ist, was ein Mensch benennen wuerde — eine
// Schalungsfuge mit vier Ankerloechern, ein halbversetzter Steinverband.
// ───────────────────────────────────────────────────────────────────────────

function betonKachel(basis: readonly [number, number, number], rnd: () => number): MaterialKarten {
  const f = leer(KACHEL_PX, KACHEL_PX);
  rauschen(f, basis, rnd, 10);
  // Schalungsstoss auf halber Hoehe plus vier Ankerloecher — Sichtbeton.
  linieH(f, KACHEL_PX / 2, 0.8, 0, 0, 0);
  const r = rauheitskachel(0.9, rnd, 0.04);
  linieH(r, KACHEL_PX / 2, 0.8, 0, 255, 0);        // die Fuge ist rauer
  for (const [x, y] of [[64, 64], [192, 64], [64, 192], [192, 192]] as const) {
    scheibe(f, x, y, 4, 0, 0, 0, 0.18);
    scheibe(r, x, y, 4, 0, 255, 0, 0.5);
  }
  return { farbe: f, rauheit: r, rezept: 'beton' };
}

function mauerwerkKachel(basis: readonly [number, number, number], rnd: () => number): MaterialKarten {
  const f = leer(KACHEL_PX, KACHEL_PX);
  // Moertel zuerst, dann die Steine darauf — vier Schichten, halbversetzt.
  fuelle(f, basis[0] - 30, basis[1] - 30, basis[2] - 30);
  const r = leer(KACHEL_PX, KACHEL_PX);
  fuelle(r, 0, Math.round(0.95 * 255), 0);          // Moertel ist rauer
  const schicht = KACHEL_PX / 4;
  for (let i = 0; i < 4; i++) {
    const versatz = i % 2 === 0 ? 0 : KACHEL_PX / 4;
    for (let j = -1; j < 3; j++) {
      const x = j * (KACHEL_PX / 2) + versatz;
      const d = (rnd() - 0.5) * 16;
      rechteck(f, x + 2, i * schicht + 2, KACHEL_PX / 2 - 4, schicht - 4,
               basis[0] + d, basis[1] + d, basis[2] + d);
      rechteck(r, x + 2, i * schicht + 2, KACHEL_PX / 2 - 4, schicht - 4,
               0, Math.round(0.82 * 255), 0);
    }
  }
  return { farbe: f, rauheit: r, rezept: 'mauerwerk' };
}

function holzKachel(basis: readonly [number, number, number], rnd: () => number): MaterialKarten {
  const f = leer(KACHEL_PX, KACHEL_PX);
  rauschen(f, basis, rnd, 6);
  // Bretter laengs, dazwischen die Stossfuge; darin die Adern.
  const brett = KACHEL_PX / 4;
  const r = rauheitskachel(0.75, rnd, 0.05);
  for (let i = 0; i < 4; i++) {
    const d = (rnd() - 0.5) * 26;
    for (let y = i * brett; y < (i + 1) * brett; y++) {
      for (let x = 0; x < KACHEL_PX; x++) mische(f, x, y, basis[0] + d, basis[1] + d, basis[2] + d, 0.5);
    }
    // Adern: feine, leicht gewellte Linien im Brett.
    const adern = 3 + Math.floor(rnd() * 3);
    for (let a = 0; a < adern; a++) {
      const y0 = i * brett + 4 + rnd() * (brett - 8);
      const welle = 1.5 + rnd() * 2;
      for (let x = 0; x < KACHEL_PX; x++) {
        const y = y0 + Math.sin((x / KACHEL_PX) * Math.PI * 2 + a) * welle;
        mische(f, x, Math.round(y), basis[0] - 40, basis[1] - 40, basis[2] - 40, 0.35);
      }
    }
    if (i > 0) linieH(f, i * brett, 0.6, basis[0] - 55, basis[1] - 55, basis[2] - 55);
    if (i > 0) linieH(r, i * brett, 0.6, 0, Math.round(0.9 * 255), 0);
  }
  return { farbe: f, rauheit: r, rezept: 'holz' };
}

function daemmungKachel(basis: readonly [number, number, number], rnd: () => number): MaterialKarten {
  const f = leer(KACHEL_PX, KACHEL_PX);
  rauschen(f, basis, rnd, 18);
  const r = rauheitskachel(1, rnd, 0.02);
  // Faserflocken — sie machen die Rauheit ungleichmaessig, nicht die Farbe.
  for (let i = 0; i < 500; i++) {
    scheibe(r, rnd() * KACHEL_PX, rnd() * KACHEL_PX, 1 + rnd() * 2.5, 0, 235, 0, 0.6);
  }
  return { farbe: f, rauheit: r, rezept: 'daemmung' };
}

function putzKachel(basis: readonly [number, number, number], rnd: () => number): MaterialKarten {
  const f = leer(KACHEL_PX, KACHEL_PX);
  rauschen(f, basis, rnd, 7);
  const r = rauheitskachel(0.95, rnd, 0.03);
  // Feiner Kellenschlag: einzelne Punkte, sonst nichts.
  for (let i = 0; i < 1800; i++) {
    const x = Math.floor(rnd() * KACHEL_PX), y = Math.floor(rnd() * KACHEL_PX);
    mische(r, x, y, 0, 255, 0, 0.5);
  }
  return { farbe: f, rauheit: r, rezept: 'putz' };
}

const REZEPTE: Record<string, (b: readonly [number, number, number], rnd: () => number) => MaterialKarten> = {
  beton: betonKachel,
  mauerwerk: mauerwerkKachel,
  holz: holzKachel,
  daemmung: daemmungKachel,
  putz: putzKachel,
};

/** Welche SIA-Klassen ein Rezept haben — zum Nachzaehlen, nicht zum Glauben. */
export const REZEPT_KLASSEN: readonly string[] = Object.keys(REZEPTE);

/**
 * Der Katalog fuehrt die Farbe als ZAHL (`0xc9c5bc`), nicht als Zeichenkette
 * — nachgesehen in `materialkatalog.ts`, nicht angenommen. Mein erster Anlauf
 * nahm eine Hex-Zeichenkette an; der Typpruefer hat es sofort gemeldet.
 */
function ausZahl(n: number): [number, number, number] {
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

/**
 * **Die Karten zu einem Katalogschluessel** — oder `null`, wenn es fuer seine
 * SIA-Klasse kein Rezept gibt.
 *
 * `null` heisst «fuer dieses Material gibt es keine Kachel» und ist eine
 * Aussage ueber das MATERIAL. Anders als im 3D-Fenster gibt es hier keinen
 * zweiten Fall («der Canvas hat gerade nicht geliefert») — ohne Canvas kann
 * er nicht eintreten, und darum darf das Ergebnis gemerkt werden.
 */
export function materialTextur(key: string): MaterialKarten | null {
  const gecacht = merker.get(key);
  if (gecacht !== undefined) return gecacht;
  const eintrag = materialkatalog.find((m) => m.key === key);
  const bau = eintrag ? REZEPTE[eintrag.sia as string] : undefined;
  const karten = bau && eintrag
    ? bau(ausZahl(eintrag.pbr.color), lcg([...key].reduce((s, c) => s * 31 + c.charCodeAt(0), 7) >>> 0))
    : null;
  merker.set(key, karten);
  return karten;
}

const merker = new Map<string, MaterialKarten | null>();

// ───────────────────────────────────────────────────────────────────────────
// 3 · PNG — ohne Abhaengigkeit, ohne Kompression
// ───────────────────────────────────────────────────────────────────────────

function crc32(daten: Uint8Array): number {
  let c = 0xffffffff;
  for (let i = 0; i < daten.length; i++) {
    c ^= daten[i]!;
    for (let k = 0; k < 8; k++) c = c & 1 ? (c >>> 1) ^ 0xedb88320 : c >>> 1;
  }
  return (c ^ 0xffffffff) >>> 0;
}

function adler32(daten: Uint8Array): number {
  let a = 1, b = 0;
  for (let i = 0; i < daten.length; i++) {
    a = (a + daten[i]!) % 65521;
    b = (b + a) % 65521;
  }
  return ((b << 16) | a) >>> 0;
}

function block(typ: string, inhalt: Uint8Array): Uint8Array {
  const out = new Uint8Array(12 + inhalt.length);
  const dv = new DataView(out.buffer);
  dv.setUint32(0, inhalt.length);
  for (let i = 0; i < 4; i++) out[4 + i] = typ.charCodeAt(i);
  out.set(inhalt, 8);
  dv.setUint32(8 + inhalt.length, crc32(out.subarray(4, 8 + inhalt.length)));
  return out;
}

/**
 * Eine Kachel als PNG-Bytes.
 *
 * **OHNE KOMPRESSION, und das ist eine Entscheidung mit Preis.** Ein
 * zlib-Strom darf aus lauter «gespeicherten» Bloecken bestehen; der Aufbau
 * ist eine Laengenangabe je Block und sonst nichts. Echtes Deflate haette
 * hier eine Abhaengigkeit oder rund vierhundert Zeilen Huffman-Kodierung
 * bedeutet — und `zlib` gibt es im Browser nicht, `CompressionStream` nur
 * asynchron, was jede aufrufende Stelle ansteckte.
 *
 * DER PREIS STEHT IM DATEIKOPF: 197 KB je 256er-Kachel statt rund 20 KB.
 * Genau deshalb sind die Kacheln 256 Punkte gross und nicht 1024 — die
 * Aufloesung ist an dieser Zahl gewaehlt worden, nicht umgekehrt.
 */
export function alsPng(k: Kachel): Uint8Array {
  const roh = new Uint8Array(k.hoehe * (1 + k.breite * 3));
  for (let y = 0; y < k.hoehe; y++) {
    const ziel = y * (1 + k.breite * 3);
    roh[ziel] = 0;                                   // Filter 0 = keiner
    roh.set(k.rgb.subarray(y * k.breite * 3, (y + 1) * k.breite * 3), ziel + 1);
  }
  // zlib-Rahmen: Kopf 0x78 0x01, gespeicherte Bloecke, Adler-32 am Schluss.
  const MAX = 65535;
  const bloecke = Math.ceil(roh.length / MAX) || 1;
  const z = new Uint8Array(2 + bloecke * 5 + roh.length + 4);
  z[0] = 0x78; z[1] = 0x01;
  let p = 2, q = 0;
  for (let i = 0; i < bloecke; i++) {
    const n = Math.min(MAX, roh.length - q);
    z[p++] = i === bloecke - 1 ? 1 : 0;
    z[p++] = n & 255; z[p++] = (n >> 8) & 255;
    z[p++] = ~n & 255; z[p++] = (~n >> 8) & 255;
    z.set(roh.subarray(q, q + n), p);
    p += n; q += n;
  }
  new DataView(z.buffer).setUint32(p, adler32(roh));
  const ihdr = new Uint8Array(13);
  const dv = new DataView(ihdr.buffer);
  dv.setUint32(0, k.breite);
  dv.setUint32(4, k.hoehe);
  ihdr[8] = 8;                                       // 8 Bit je Kanal
  ihdr[9] = 2;                                       // Farbtyp 2 = RGB
  const teile = [
    new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    block('IHDR', ihdr),
    block('IDAT', z),
    block('IEND', new Uint8Array(0)),
  ];
  const gesamt = teile.reduce((s, t) => s + t.length, 0);
  const out = new Uint8Array(gesamt);
  let o = 0;
  for (const t of teile) { out.set(t, o); o += t.length; }
  return out;
}
