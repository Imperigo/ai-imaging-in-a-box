import { GLYPHEN_PUNKT, type WerkzeugGlyphenArt } from './werkzeug-glyphen';
import type { CursorZustand, ZonenForm } from '../state/cursor-zustand';

/**
 * Zeigerbilder — HARDWARE-Zeiger statt gezeichneter DOM-Ebene.
 *
 * OWNER-ENTSCHEID 24.09.2026 (wörtlich): «Ziel: eigener zeiger haben aber
 * wechsel kürzen ja, es kann ja nicht sein das drüberzeichnen muss also es
 * gibt ja basically jede webseite wo zeiger ändert auf irgendeinen spez
 * zeiger...alle zeichenprogramme haben ja auch eigenen...und die sind
 * snappy». Hintergrund: ein IM SEITENINHALT gezeichneter Zeiger (die frühere
 * `CursorEbene`-Architektur, s. Git-Historie) hängt immer mindestens ein Bild
 * hinter der echten Maus und steht still, sobald der Hauptthread beschäftigt
 * ist — belegt in `docs/O-T12-ZEIGER-MESSUNG.md` (53–123 ms Ereignis→Bild,
 * 0/27 Phasen erreichten 120 Hz). Ein HARDWARE-Zeiger (CSS
 * `cursor: url(bild) x y, fallback`) wird vom Compositor/Betriebssystem
 * gezeichnet, unabhängig vom Hauptthread — genau das, was «snappy» macht.
 *
 * Diese Datei erzeugt für jeden `CursorZustand`/jede `ZonenForm` ein
 * Kosmo-Zeigerbild als data-URL (SVG, base64) — 32×32. Hotspot je Form
 * (`zeigerHotspot`, seit v0.1.6): (16,4) fuer die Spitzen-Formen (Pfeil,
 * Haende — Spec §8 «Spitze = Hotspot»), (16,16) fuer alle Formen mit einem
 * Mittelpunkt und die Werkzeug-Glyphen, damit sie ganz im Bild liegen. Der
 * Hotspot ist unabhängig vom Massstab (`--k-zeiger-mass`): der Massstab wird
 * INNERHALB der Zeichnung um genau diesen Punkt herum angewendet (`<g
 * transform="translate(hx hy) scale(f) translate(-16 -4)">`), statt wie
 * früher über eine äussere CSS-`transform-origin`-Box — ein Hardware-Cursor
 * hat keine DOM-Box, die man skalieren könnte. Ergebnis: der Hotspot-Wert in
 * der `cursor`-CSS-Erklärung ist je Form eine Konstante — für jeden
 * Massstab dieselbe (s. `zeiger-bilder.test.ts`).
 *
 * Kontur (Auftrag Punkt 1, «ein Zeiger mit Kontur, der auf beiden Gründen
 * lesbar ist»): JEDE Form bekommt automatisch zwei Halo-Durchgänge UNTER der
 * eigentlichen Zeichnung — ein breiter dunkler und ein mittlerer heller Saum
 * (`mitKontur()`) — dieselbe Technik, mit der praktisch jeder System-Zeiger
 * (weisse Füllung + schwarzer 1px-Rand) auf JEDEM Untergrund lesbar bleibt,
 * unabhängig vom App-Theme darunter. Die Formen/Farben selbst bleiben Kosmo
 * (dieselben Pfad-Daten wie die frühere gezeichnete Ebene, siehe Kommentare
 * je Funktion — «Aussehen bleibt Kosmo», Auftrag Kopf).
 *
 * Hell/Dunkel (Auftrag Punkt 1): zusätzlich zur Kontur bleiben die zwei
 * Theme-Token erhalten, die die alte Ebene schon kannte — `--kcur-fill`
 * (Pfeil-Füllung) und `--k-danger` (gesperrt) sind je Theme verschieden,
 * `--k-signal` (fast alle anderen Formen) ist themeninvariant. Weil ein
 * Hardware-Cursor-Bild ein EIGENSTÄNDIGES Bildschirm-Dokument ist (kein Teil
 * der Haupt-DOM-Kaskade), lösen `var(...)`-Referenzen dort NICHT auf — die
 * Werte stehen darum hier als LITERALE Kopie, gegen `aura.css`/
 * `cursor-ebene.css` geprüft (`zeiger-bilder-farben.test.ts`, Muster
 * `cursor-ebene-mass.test.tsx`: liest die echten Dateien, keine Behauptung).
 *
 * `tool`-Zustand (Werkzeug-Glyphe je Station, 14 Arten × bis zu 9 Rollen):
 * `WERKZEUG_PFADE` unten trägt dieselben Pfad-Daten wie `werkzeug-glyphen.
 * tsx`s `GRUND`-Tabelle (Zentrum-Koordinaten des Akzent-Punkts kommen direkt
 * von dort — `GLYPHEN_PUNKT` ist bereits öffentlich, «keine Zweitquelle» für
 * DIESEN Teil). Die GRUND-Pfade selbst sind nicht exportiert; ein erster
 * Anlauf rendered `<WerkzeugGlyphe>` hier per `renderToStaticMarkup` — das
 * lud `react-dom/server` aber STATISCH in JEDEN Import dieser Datei (auch
 * wenn nie ein `tool`-Zeiger vorkommt) und kostete beim Modul-Transform
 * messbar mehrere Sekunden je Testdatei (Ursache benannt, nicht vermutet:
 * mehrere `cursor-ebene-*`-Testdateien liefen dadurch nahe am
 * Standard-Timeout). Die Pfad-Daten stehen darum hier als literale Kopie —
 * mit einer eigenen Gegenprobe (`zeiger-bilder-werkzeug.test.tsx`), die
 * `renderToStaticMarkup(<WerkzeugGlyphe>)` NUR IM TEST gegen diese Tabelle
 * vergleicht (kein Produktionscode lädt `react-dom/server`), damit ein
 * künftiger Formwechsel an der Werkzeugleiste hier nicht still auseinander-
 * läuft.
 */

export const ZEIGER_HOTSPOT_X = 16;
export const ZEIGER_HOTSPOT_Y = 4;

/**
 * v0.1.6 (Geraete-Rundgang 30.09.2026, Befund A: «Ring im Plan und die
 * Wand-Verschiebe-Form sind oben abgeschnitten») — der Hotspot ist NICHT mehr
 * fuer jede Form (16,4). Die Pfad-Daten unten sind alle um (16,4) gezeichnet;
 * das passt fuer die Formen, die von einer Spitze aus nach UNTEN wachsen (der
 * Pfeil, die zwei Haende). Die Formen mit einem MITTELPUNKT (Ring, Fadenkreuz,
 * Pfeilpaare, Kante, Knoten, Gesperrt, Kosmo, Laden) und alle
 * Werkzeug-Glyphen reichen aber gleich weit nach oben wie nach unten — um
 * (16,4) gezeichnet ragten sie bis y≈−7 aus dem 32-px-Bild, und was ausserhalb
 * liegt, schneidet das Betriebssystem ab. Sie sitzen darum jetzt um die
 * Bildmitte (16,16); der Hotspot zieht mit (derselbe Wert steht im
 * `cursor`-Kurzwert und in der Zeichnung, `zeigerHotspot()`), damit der
 * Klickpunkt weiter genau auf ihrem Mittelpunkt liegt. Belegt mit
 * `e2e/zeiger-bilder-rand.spec.ts` (jedes Bild im echten Chromium gemalt:
 * Rand leer, Hotspot auf der Zeichnung).
 */
export const ZEIGER_MITTE_X = 16;
export const ZEIGER_MITTE_Y = 16;

/** Formen, die von ihrer Spitze aus nach unten wachsen und darum am
 *  Hotspot (16,4) bleiben. Alle anderen sitzen um die Bildmitte. */
const SPITZEN_FORMEN: ReadonlySet<CursorZustand> = new Set<CursorZustand>(['default', 'greifen', 'greift']);

/** Der Hotspot je Form (im 32er-Raster, fuer 1x und 2x gleich). */
export function zeigerHotspot(form: CursorZustand): { x: number; y: number } {
  return SPITZEN_FORMEN.has(form)
    ? { x: ZEIGER_HOTSPOT_X, y: ZEIGER_HOTSPOT_Y }
    : { x: ZEIGER_MITTE_X, y: ZEIGER_MITTE_Y };
}

/** Owner: «wechsel kürzen» — das Fenster, in dem sehr schnell aufeinander
 *  folgende Formwechsel zu EINEM zusammengefasst werden dürfen (Auftrag
 *  Punkt 2: «hoechstens ein kurzes Zusammenfassen bei sehr schnellem
 *  Streifen (<= 60 ms)»). Der ERSTE Wechsel nach einer ruhigen Phase wendet
 *  IMMER sofort an — dieses Fenster greift nur, wenn der VORHERIGE Wechsel
 *  weniger als `ZEIGER_WECHSEL_FENSTER_MS` her ist (s. CursorEbene.tsx).
 *  Bewusst NUR EIN Wert, KEINE zweite Zeitgrösse und KEIN Geschwindigkeits-
 *  Riegel mehr (anders als die frühere `MORPH_DEBOUNCE_MS`/
 *  `ZEIGER_TEMPO_SCHWELLE_PX_S`-Kaskade, s. Git-Historie 949/955/1067/1069):
 *  jene Kaskade existierte AUSSCHLIESSLICH, um eine mehrstufige CSS-Morph-
 *  Animation (Kollaps→Entfalten, 320 ms) vor Unterbrechung zu schützen. Ein
 *  Hardware-Cursor-Bild wird ohne Animation GETAUSCHT (Auftrag Punkt 2:
 *  «Hardware-Zeiger lassen sich nicht animieren») — es gibt nichts mehr, das
 *  „mitten drin“ stehen bleiben könnte, also auch keinen Grund mehr für die
 *  zweite Zeitgrösse oder den Geschwindigkeits-Riegel.
 */
export const ZEIGER_WECHSEL_FENSTER_MS = 60;

export type ZeigerThema = 'orbit' | 'paper';

interface ZeigerFarben {
  signal: string;
  danger: string;
  pfeilFuellung: string;
  ink: string;
  rollen: Record<string, string>;
}

/**
 * LITERALE Kopie der Theme-Token aus `packages/kosmo-ui/src/aura.css` (fremder
 * Dateibesitz — hier nur GELESEN, per Test gegengeprüft, nie geändert) und
 * `shell/cursor-ebene.css` (`--kcur-fill`). Grund für die Kopie s. Datei-Kopf.
 */
export const ZEIGER_FARBEN: Record<ZeigerThema, ZeigerFarben> = {
  orbit: {
    signal: '#57b6c2',
    // orbit ist das dunkle Theme (Standard) — `aura.css` überschreibt
    // `--k-ink`/`--k-danger` extra für `[data-theme='orbit']` (Zeilen
    // ~1254/1314), WEIL sie sich vom gemeinsamen `:root,[data-theme=
    // 'paper']`-Grundblock unterscheiden (hell statt dunkel, s. `zeiger-
    // bilder.test.ts`).
    danger: '#cd7670',
    pfeilFuellung: '#eaf6f8',
    ink: '#f4f6fa',
    rollen: {
      '--k-rolle-manuell': '#74c2a0',
      '--k-rolle-pn': '#6f9bcf',
      '--k-rolle-pna': '#c082b4',
      '--k-rolle-agent': '#cbb06a',
      '--k-rolle-memory': '#cf9466',
      '--k-rolle-generator': '#cd7670',
      '--k-rolle-ak': '#b08a6e',
      '--k-rolle-office': '#8a7b5a',
      '--k-rolle-doc': '#5d7489',
    },
  },
  paper: {
    signal: '#57b6c2',
    // paper teilt den gemeinsamen `:root,[data-theme='paper']`-Grundblock
    // (`aura.css` Zeilen 27ff) — hier stehen `--k-ink`/`--k-danger` OHNE
    // eigene Überschreibung, das sind also zugleich die Vorgabe-Werte.
    danger: '#a33d31',
    pfeilFuellung: '#0b0d12',
    ink: '#1a1815',
    rollen: {
      '--k-rolle-manuell': '#5a977d',
      '--k-rolle-pn': '#5779a1',
      '--k-rolle-pna': '#96658c',
      '--k-rolle-agent': '#9e8953',
      '--k-rolle-memory': '#a17350',
      '--k-rolle-generator': '#a05c57',
      '--k-rolle-ak': '#896c56',
      '--k-rolle-office': '#6c6046',
      '--k-rolle-doc': '#495a6b',
    },
  },
};

/** Liest das aktive Theme direkt vom DOM (Muster `eigencursorAktiv()`: kein
 *  eigener Store, reiner Lesehelfer) — `App.tsx` schreibt `data-theme` als
 *  einzige Quelle (`'orbit'` Vorgabe, `'paper'` der einzige zweite Wert,
 *  `packages/kosmo-ui/src/tokens.ts` `ThemeName`). Ein unbekannter/fehlender
 *  Wert fällt auf `'orbit'` zurück (der App-Standard). */
export function aktuellesZeigerThema(): ZeigerThema {
  try {
    const wert = typeof document !== 'undefined' ? document.documentElement.dataset['theme'] : undefined;
    return wert === 'paper' ? 'paper' : 'orbit';
  } catch {
    return 'orbit';
  }
}

export interface Strich {
  d: string;
  breite: number;
}

export interface Punkt {
  cx: number;
  cy: number;
  r: number;
}

export interface FormZeichnung {
  /** Reine Linienzüge (Kosmo-Formen: 1.75er- bzw. 1.3er-Strich, wie die
   *  frühere `cursor-ebene.css`-Familie). */
  striche: Strich[];
  /** GENAU EIN Akzent-Punkt sitzt bei den meisten Formen auf dem Hotspot
   *  selbst — mehrere sind trotzdem als Liste erlaubt (Pfeil braucht keinen,
   *  Fadenkreuz/Greifen je einen). */
  punkte?: Punkt[];
  /** Gefüllte Silhouette (nur der Pfeil) — eigene Randfarbe/-breite. */
  fuellungPfad?: string;
  /** `true`: die Striche/Punkte/Füllung nutzen `--k-danger` statt
   *  `--k-signal` (bislang nur `gesperrt`). */
  gefahr?: boolean;
}

const RING_ARC = (r: number) => `M ${16 - r} 4 A ${r} ${r} 0 1 0 ${16 + r} 4 A ${r} ${r} 0 1 0 ${16 - r} 4`;

/**
 * Die 13 festen Formen — Pfad-Daten 1:1 aus der früheren gezeichneten Ebene
 * übernommen (Git-Historie `CursorEbene.tsx` vor diesem Paket: `FadenkreuzSvg`/
 * `GreifenSvg`/`ResizeSvg`/`KanteSvg`/`KnotenSvg`/`DiagonaleSvg`/`GesperrtSvg`/
 * der Pfeil-Pfad/`ZeichneForm`) — «Aussehen bleibt Kosmo» (Auftrag Kopf).
 *
 * ANIMATION ENTFÄLLT (Auftrag Punkt 2 — Hardware-Zeiger lassen sich nicht
 * animieren): `loading` (früher ein rotierender Ring) und `kosmo` (früher ein
 * pulsierender Kern) sind jetzt STATISCHE Formen — derselbe Ring/Kern, ohne
 * die CSS-Keyframes. Reine Darstellungs-Reduktion, keine neue Geometrie.
 */
const GRUNDFORMEN: Record<Exclude<CursorZustand, 'tool'>, FormZeichnung> = {
  default: {
    striche: [],
    fuellungPfad: 'M16 4 L25 26 Q16 21.5 7 26 Z',
  },
  loading: {
    striche: [{ d: RING_ARC(11), breite: 2 }],
  },
  kosmo: {
    striche: [{ d: RING_ARC(13), breite: 1.3 }],
    // Der frühere Kern pulsierte (`k-cursor-kosmo-puls`) — jetzt ein
    // statischer voller Kreis derselben Grösse (r 7, Auftrag Punkt 2:
    // Hardware-Zeiger lassen sich nicht animieren).
    punkte: [{ cx: 16, cy: 4, r: 7 }],
  },
  precision: {
    striche: [
      { d: 'M16 4 m -9 0 a 9 9 0 1 0 18 0 a 9 9 0 1 0 -18 0', breite: 1.3 },
      { d: 'M16 -7 v4 M16 11 v4 M5 4 h4 M23 4 h4', breite: 1.3 },
    ],
    punkte: [{ cx: 16, cy: 4, r: 1.5 }],
  },
  fadenkreuz: {
    striche: [
      { d: 'M16 4 m -9 0 a 9 9 0 1 0 18 0 a 9 9 0 1 0 -18 0', breite: 1.3 },
      { d: 'M16 -7 v4 M16 11 v4 M5 4 h4 M23 4 h4', breite: 1.3 },
    ],
    punkte: [{ cx: 16, cy: 4, r: 1.5 }],
  },
  greifen: {
    striche: [
      { d: 'M10 12 V7 M14 12 V4 M18 12 V4 M22 12 V7', breite: 1.75 },
      { d: 'M8 12 v3 a8 8 0 0 0 8 8 a8 8 0 0 0 8 -8 v-3', breite: 1.75 },
    ],
    punkte: [{ cx: 16, cy: 4, r: 1.7 }],
  },
  greift: {
    striche: [
      { d: 'M9 10 h3 M13 8 h3 M17 8 h3 M21 10 h3', breite: 1.75 },
      { d: 'M8 12 v3 a8 8 0 0 0 8 8 a8 8 0 0 0 8 -8 v-3', breite: 1.75 },
    ],
    punkte: [{ cx: 16, cy: 4, r: 1.7 }],
  },
  spalte: {
    striche: [{ d: 'M6 4 h20 M6 4 l4 -4 M6 4 l4 4 M26 4 l-4 -4 M26 4 l-4 4', breite: 1.75 }],
    punkte: [{ cx: 16, cy: 4, r: 1.7 }],
  },
  zeile: {
    striche: [{ d: 'M16 -6 v20 M16 -6 l-4 4 M16 -6 l4 4 M16 14 l-4 -4 M16 14 l4 -4', breite: 1.75 }],
    punkte: [{ cx: 16, cy: 4, r: 1.7 }],
  },
  gesperrt: {
    striche: [
      { d: 'M16 4 m -9 0 a 9 9 0 1 0 18 0 a 9 9 0 1 0 -18 0', breite: 1.75 },
      { d: 'M10 -2 L22 10', breite: 1.75 },
    ],
    punkte: [{ cx: 16, cy: 4, r: 1.7 }],
    gefahr: true,
  },
  kante: {
    striche: [
      { d: 'M5 4 h22', breite: 1.75 },
      { d: 'M16 -4 v4 M13 -1 l3 -3 l3 3 M16 12 v-4 M13 9 l3 3 l3 -3', breite: 1.75 },
    ],
    punkte: [{ cx: 16, cy: 4, r: 1.7 }],
  },
  // Vereinfachung gegenüber der Vorlage (`<rect rx={1.5}>`): scharfe statt
  // gerundete Ecken — eine Pfad-Kontur (dieselbe Struktur wie alle anderen
  // Formen, s. `Strich`) statt eines Sonderfalls nur für dieses eine Rechteck.
  // Erkennbar bleibt die Form («offenes Quadrat um den Hotspot») unverändert.
  knoten: {
    striche: [{ d: 'M10 -2 h12 v12 h-12 Z', breite: 1.75 }],
    punkte: [{ cx: 16, cy: 4, r: 1.7 }],
  },
  // Dieselbe Resize-Geometrie wie `spalte`, ±45° um den Hotspot gedreht
  // (`DIAGONALE_DREHUNG` unten) — exakt wie die frühere `DiagonaleSvg`.
  'diagonale-ab': {
    striche: [{ d: 'M6 4 h20 M6 4 l4 -4 M6 4 l4 4 M26 4 l-4 -4 M26 4 l-4 4', breite: 1.75 }],
    punkte: [{ cx: 16, cy: 4, r: 1.7 }],
  },
  'diagonale-auf': {
    striche: [{ d: 'M6 4 h20 M6 4 l4 -4 M6 4 l4 4 M26 4 l-4 -4 M26 4 l-4 4', breite: 1.75 }],
    punkte: [{ cx: 16, cy: 4, r: 1.7 }],
  },
};

/** Die zwei Diagonalen sind dieselbe Resize-Geometrie wie `spalte`, ±45°
 *  um den Hotspot gedreht (exakt wie die frühere `DiagonaleSvg` — statisches
 *  SVG-Attribut, keine Laufzeit-Rotation). */
const DIAGONALE_DREHUNG: Partial<Record<CursorZustand, number>> = {
  'diagonale-ab': 45,
  'diagonale-auf': -45,
};

/**
 * Teil C (Owner 07.10.2026: «gib denen auch die gleichen funktionen und
 * animationen wie die kosmoorbit maus selbst»): dieselbe Geometrie für die
 * Figuren von Claude und Kosmo (`shell/kosmo-maus/AgentFigur.tsx`), die sie
 * als eigenes SVG in ihrer Farbe zeichnen — und, anders als der
 * Hardware-Zeiger, beim Wechsel animieren dürfen. Angelegt um (16,4) wie
 * alle Formen; `tool` fällt auf den Pfeil zurück (die Figur hat kein
 * Werkzeug in der Hand).
 */
export function formZeichnung(form: CursorZustand): { zeichnung: FormZeichnung; drehungGrad: number } {
  const zeichnung = form === 'tool' ? GRUNDFORMEN.default : GRUNDFORMEN[form];
  return { zeichnung, drehungGrad: DIAGONALE_DREHUNG[form] ?? 0 };
}

/** Fallback-CSS-Schlüsselwort je Form — greift nur, wenn ein Browser WEDER
 *  `image-set()` NOCH `url()` im `cursor`-Kurzwert akzeptiert (Auftrag: «CSS
 *  cursor-Wert … mit Hotspot», ein Kurzwert trägt IMMER einen nativen
 *  Rückfall als letztes Glied, Spec-übliche Praxis). */
const FALLBACK_KEYWORD: Record<CursorZustand, string> = {
  default: 'default',
  loading: 'progress',
  kosmo: 'pointer',
  tool: 'pointer',
  precision: 'crosshair',
  fadenkreuz: 'crosshair',
  greifen: 'grab',
  greift: 'grabbing',
  spalte: 'col-resize',
  zeile: 'row-resize',
  gesperrt: 'not-allowed',
  kante: 'crosshair',
  knoten: 'cell',
  'diagonale-ab': 'nwse-resize',
  'diagonale-auf': 'nesw-resize',
};

export function fallbackFuer(form: CursorZustand): string {
  return FALLBACK_KEYWORD[form];
}

/** Kontur-Halo (Auftrag Punkt 1) — zwei zusätzliche Durchgänge UNTER der
 *  eigentlichen Zeichnung, dieselben Pfade mit breiterem Strich: ein
 *  dunkler Aussen- und ein heller Innen-Saum. Macht die Form auf JEDEM
 *  Untergrund lesbar, unabhängig vom App-Theme darunter — dieselbe Technik
 *  wie bei den meisten System-Zeigern (helle Füllung, dunkler Rand). */
function konturDurchgaenge(striche: Strich[], fuellungPfad: string | undefined): string {
  const aussen = striche
    .map((s) => `<path d="${s.d}" fill="none" stroke="rgba(7,11,14,0.55)" stroke-width="${s.breite + 3}" stroke-linecap="round" stroke-linejoin="round" />`)
    .join('');
  const innen = striche
    .map((s) => `<path d="${s.d}" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="${s.breite + 1.4}" stroke-linecap="round" stroke-linejoin="round" />`)
    .join('');
  // Kein `transform-origin`-Attribut (in älteren SVG-Renderern, u. a.
  // WebKitGTK — s. Auftrag «Beispielprojekt … Owner nutzt Linux/WebKitGTK» —
  // nicht zuverlässig unterstützt): der Aussen-/Innen-Saum der gefüllten
  // Pfeil-Silhouette entsteht stattdessen als dicke, ungefüllte STRICH-Kontur
  // ENTLANG desselben Pfades (`fill="none"`, breiter Strich) — universell
  // unterstützte SVG-1.1-Mechanik, kein Skalieren um einen Punkt nötig.
  const fuellungHalo = fuellungPfad
    ? `<path d="${fuellungPfad}" fill="none" stroke="rgba(7,11,14,0.55)" stroke-width="3.4" stroke-linejoin="round" transform="rotate(-22.25 16 4)" />` +
      `<path d="${fuellungPfad}" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="1.8" stroke-linejoin="round" transform="rotate(-22.25 16 4)" />`
    : '';
  return `${fuellungHalo}${aussen}${innen}`;
}

/** Rendert eine `FormZeichnung` als eigenständiges 32×32-SVG-Dokument.
 *  `dichte` skaliert NUR das Ausgabe-Canvas (1 oder 2, `image-set()`-2x-
 *  Fassung) — die viewBox bleibt `0 0 32 32`, der Hotspot bleibt darum in
 *  BEIDEN Fassungen `16 4` (dieselbe Koordinatenbasis, s. Datei-Kopf). */
function renderFormSvg(
  zeichnung: FormZeichnung,
  opts: { thema: ZeigerThema; masse: number; dichte: 1 | 2; hotspot: { x: number; y: number }; drehungGrad?: number },
): string {
  const farben = ZEIGER_FARBEN[opts.thema];
  const linienFarbe = zeichnung.gefahr ? farben.danger : farben.signal;
  const punktFarbe = zeichnung.gefahr ? farben.danger : farben.signal;
  const drehung = opts.drehungGrad ? ` rotate(${opts.drehungGrad} 16 4)` : '';

  const konturen = konturDurchgaenge(zeichnung.striche, zeichnung.fuellungPfad);
  const striche = zeichnung.striche
    .map((s) => `<path d="${s.d}" fill="none" stroke="${linienFarbe}" stroke-width="${s.breite}" stroke-linecap="round" stroke-linejoin="round" />`)
    .join('');
  const fuellung = zeichnung.fuellungPfad
    ? `<path d="${zeichnung.fuellungPfad}" fill="${farben.pfeilFuellung}" stroke="${farben.signal}" stroke-width="1.5" stroke-linejoin="round" transform="rotate(-22.25 16 4)" />`
    : '';
  const punkte = (zeichnung.punkte ?? [])
    .map((p) => `<circle cx="${p.cx}" cy="${p.cy}" r="${p.r}" fill="${punktFarbe}" />`)
    .join('');

  const kante = 32 * opts.dichte;
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${kante}" height="${kante}" viewBox="0 0 32 32">` +
    // Die Zeichnung ist um (16,4) angelegt; `translate(hx hy) … translate(-16
    // -4)` legt diesen Punkt auf den Hotspot der Form und skaliert um genau
    // ihn (s. `zeigerHotspot`).
    `<g transform="translate(${opts.hotspot.x} ${opts.hotspot.y}) scale(${opts.masse}) translate(-16 -4)${drehung}">` +
    konturen +
    striche +
    fuellung +
    punkte +
    `</g></svg>`
  );
}

function zuDatenUrl(svg: string): string {
  const base64 = typeof btoa === 'function' ? btoa(svg) : Buffer.from(svg, 'utf8').toString('base64');
  return `data:image/svg+xml;base64,${base64}`;
}

/**
 * Grundform je Werkzeug-Glyphe — LITERALE Kopie der `GRUND`-Tabelle aus
 * `werkzeug-glyphen.tsx` (Begründung/Grenzen s. Datei-Kopf «keine
 * react-dom/server-Kosten»), als rohe SVG-Element-Strings statt JSX.
 * `orbit` trägt seinen Teal-Viertelring separat (`ORBIT_RING` unten) — exakt
 * die dortige Ausnahme («Quadrat statt Punkt», Spec §3-Zeile «orbit»).
 */
const WERKZEUG_GRUND: Record<WerkzeugGlyphenArt, string> = {
  chat: '<path d="M12 4 v5 M12 15 v5 M4 12 h5 M15 12 h5" /><circle cx="12" cy="12" r="2.4" />',
  pipeline: '<circle cx="6" cy="6" r="2.4" /><circle cx="18" cy="12" r="2.4" /><path d="M8 7.5 L15.6 11 M8 17 L15.6 13" />',
  draw: '<path d="M5 19 L15.5 8.5 M5 19 l1-4 M5 19 l4-1" />',
  data: '<ellipse cx="12" cy="7" rx="7" ry="2.8" /><path d="M5 7 v10 c0 1.6 3.1 2.8 7 2.8 s7-1.2 7-2.8 V7" />',
  viz: '<rect x="4" y="5.5" width="16" height="13" rx="2" /><path d="M4 15.5 l5-5 4 4 3-3 4 4" />',
  publish: '<path d="M7 20 h10 a2 2 0 0 0 2-2 V8 l-4-4 H7 a2 2 0 0 0-2 2 v12 a2 2 0 0 0 2 2 Z M15 4 v4 h4" />',
  prepare: '<circle cx="12" cy="12" r="8" /><path d="M15 9 l-2 4.4 L9 15 l2-4.4 Z" />',
  connect: '<path d="M4 9 h13 m0 0 -3-3 m3 3 -3 3 M20 15 H7 m0 0 3-3 m-3 3 3 3" />',
  office: '<path d="M4 8 a2 2 0 0 1 2-2 h4 l2 2.5 h6 a2 2 0 0 1 2 2 V17 a2 2 0 0 1-2 2 H6 a2 2 0 0 1-2-2 Z" />',
  zentrale: '<rect x="5" y="4.5" width="14" height="6.4" rx="1.6" /><rect x="5" y="13.1" width="14" height="6.4" rx="1.6" /><path d="M8 7.7 h3 M8 16.3 h3" />',
  odysseus:
    '<circle cx="12" cy="12" r="3" /><path d="M12 4.5 v2.6 M12 16.9 v2.6 M4.5 12 h2.6 M16.9 12 h2.6 M6.7 6.7 l1.8 1.8 M15.5 15.5 l1.8 1.8 M17.3 6.7 l-1.8 1.8 M8.5 15.5 l-1.8 1.8" />',
  orbit: '<circle cx="12" cy="12" r="8.5" stroke-dasharray="1.5 3" /><rect x="10.4" y="10.4" width="3.2" height="3.2" rx="1" />',
  skizze: '<path d="M4 16 C8 8, 12 20, 20 9" />',
  lernen: '<rect x="4.5" y="14" width="3" height="6" rx="1.5" /><rect x="10.5" y="10" width="3" height="10" rx="1.5" /><rect x="16.5" y="6" width="3" height="14" rx="1.5" />',
};

/** `orbit`s Teal-Viertelring — ausserhalb der `opacity:.9`-Ink-Gruppe,
 *  immer in `--k-signal` (Ausnahme wie in `werkzeug-glyphen.tsx`). */
const ORBIT_RING = '<path d="M12 3.5 A 8.5 8.5 0 0 1 20.5 12" fill="none" stroke-linecap="round" />';

/** Werkzeug-Icon (Auftrag Punkt 1, `tool`-Zustand) — `rolle` ohne führendes
 *  `var(...)` (Prop-Konvention von `WerkzeugGlyphe`, s. `werkzeug-glyphen.
 *  tsx`). Farben werden HIER direkt eingesetzt (keine `var()`-Referenzen zu
 *  ersetzen — anders als der frühere `renderToStaticMarkup`-Anlauf, s.
 *  Datei-Kopf, weil dieser Weg nie welche erzeugt). */
function zeichneWerkzeugSvg(
  art: WerkzeugGlyphenArt,
  rolle: string | undefined,
  opts: { thema: ZeigerThema; masse: number; dichte: 1 | 2 },
): string {
  const farben = ZEIGER_FARBEN[opts.thema];
  const punktFarbe = rolle ? farben.rollen[rolle] ?? farben.ink : farben.ink;
  const grund = WERKZEUG_GRUND[art];
  const punkt = art === 'orbit' ? '' : (() => {
    const p = GLYPHEN_PUNKT[art as Exclude<WerkzeugGlyphenArt, 'orbit'>];
    return `<circle cx="${p.cx}" cy="${p.cy}" r="1.7" fill="${punktFarbe}" />`;
  })();
  const ring = art === 'orbit' ? ORBIT_RING.replace('stroke-linecap', `stroke="${farben.signal}" stroke-width="2" stroke-linecap`) : '';
  const innen =
    `<g stroke="${farben.ink}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" fill="none" opacity="0.9">${grund}</g>` +
    ring +
    punkt;
  // Kontur-Halo (Auftrag Punkt 1): dieselbe Zeichnung als reine Strich-Kontur
  // — zweimal, dunkel/hell, wie bei den 13 festen Formen (`konturDurchgaenge`)
  // — die STROKE-BREITE kommt hier bewusst NUR von der äusseren `<g>` unten
  // (kein eigenes `stroke-width` auf `alsKontur` selbst, sonst gewinnt das
  // innerste und beide Durchgänge sähen gleich breit aus). `grund` trägt nie
  // `fill` auf seinen eigenen Elementen (`fill="none"` kommt von der Gruppe),
  // der Akzent-Punkt bekommt seine eigene, etwas grössere Kontur separat.
  const alsKontur = `${grund}${punkt ? punkt.replace(/fill="[^"]*"/, 'fill="none"').replace('r="1.7"', 'r="2.6"') : ''}`;

  const kante = 32 * opts.dichte;
  const konturHuelle =
    `<g stroke="rgba(7,11,14,0.55)" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round" fill="none">${alsKontur}</g>` +
    `<g stroke="rgba(255,255,255,0.85)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none">${alsKontur}</g>`;

  // Die Glyphe lebt im EIGENEN 24er-Raster (`WerkzeugGlyphe`, viewBox
  // "0 0 24 24"), ihr Zentrum (12,12) muss auf dem Hotspot (16,4) liegen
  // (Vorlage: `.cursor-ebene-tool { left:16px; top:4px; transform:
  // translate(-50%,-50%) }`) — UND der Massstab muss um GENAU diesen Hotspot
  // skalieren, nicht um den Icon-Mittelpunkt. `translate(16 4) scale(f)
  // translate(-12 -12)` trifft beides in einem Zug: erst rückt `translate(
  // -12 -12)` das Icon-Zentrum auf den Ursprung, dann skaliert `scale(f)` um
  // GENAU diesen (jetzt im Ursprung liegenden) Punkt, zuletzt schiebt
  // `translate(16 4)` ihn auf den echten Hotspot — bei JEDEM `f` bleibt der
  // Ursprungspunkt (0,0) fest ⇒ der Hotspot wandert nie.
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${kante}" height="${kante}" viewBox="0 0 32 32">` +
    `<g transform="translate(${ZEIGER_MITTE_X} ${ZEIGER_MITTE_Y}) scale(${opts.masse}) translate(-12 -12)">` +
    konturHuelle +
    innen +
    `</g></svg>`
  );
}

export interface ZeigerCssWert {
  wert: string;
  form: CursorZustand;
}

const cache = new Map<string, string>();

function schluesselFuer(
  form: CursorZustand,
  opts: { thema: ZeigerThema; masse: number; toolArt: string | undefined; toolRolle: string | undefined },
): string {
  return `${form}|${opts.thema}|${opts.masse}|${opts.toolArt ?? ''}|${opts.toolRolle ?? ''}`;
}

/**
 * Baut den vollständigen CSS-`cursor`-Kurzwert für einen `CursorZustand` —
 * `image-set()` mit 1×/2× (Auftrag Punkt 1: «zusaetzlich 2x-Fassung ueber
 * image-set() wo unterstuetzt»), dahinter ein reiner `url()`-Rückfall für
 * Browser ohne `image-set()`-Unterstützung, zuletzt ein natives Schlüsselwort
 * (`fallbackFuer`). Der Hotspot ist in JEDEM der drei Glieder `"16 4"` (s.
 * Datei-Kopf). Memoisiert je (Form, Theme, Massstab, Werkzeug-Art/-Rolle) —
 * dieselbe Form erzeugt nie zweimal dieselbe Kodierung.
 */
export function zeigerCssWert(
  form: CursorZustand,
  opts: { thema: ZeigerThema; masse: number; tool?: { art: WerkzeugGlyphenArt; rolle: string | undefined } | null },
): string {
  const toolArt: string | undefined = form === 'tool' ? opts.tool?.art : undefined;
  const toolRolle: string | undefined = form === 'tool' ? opts.tool?.rolle : undefined;
  const schluessel = schluesselFuer(form, { thema: opts.thema, masse: opts.masse, toolArt, toolRolle });
  const vorhanden = cache.get(schluessel);
  if (vorhanden) return vorhanden;

  let daten1x: string;
  let daten2x: string;
  if (form === 'tool' && toolArt) {
    daten1x = zuDatenUrl(zeichneWerkzeugSvg(toolArt as WerkzeugGlyphenArt, toolRolle, { thema: opts.thema, masse: opts.masse, dichte: 1 }));
    daten2x = zuDatenUrl(zeichneWerkzeugSvg(toolArt as WerkzeugGlyphenArt, toolRolle, { thema: opts.thema, masse: opts.masse, dichte: 2 }));
  } else {
    const basisForm: Exclude<CursorZustand, 'tool'> = form === 'tool' ? 'default' : form;
    const zeichnung = GRUNDFORMEN[basisForm];
    const drehungGrad = DIAGONALE_DREHUNG[form];
    const hotspot = zeigerHotspot(basisForm);
    daten1x = zuDatenUrl(renderFormSvg(zeichnung, { thema: opts.thema, masse: opts.masse, dichte: 1, hotspot, ...(drehungGrad !== undefined ? { drehungGrad } : {}) }));
    daten2x = zuDatenUrl(renderFormSvg(zeichnung, { thema: opts.thema, masse: opts.masse, dichte: 2, hotspot, ...(drehungGrad !== undefined ? { drehungGrad } : {}) }));
  }

  // `tool` MIT Werkzeug-Glyphe sitzt um die Mitte; `tool` OHNE faellt auf den
  // Pfeil zurueck (s. oben) und traegt dann dessen Spitzen-Hotspot.
  const hotspotPunkt = form === 'tool' && toolArt ? { x: ZEIGER_MITTE_X, y: ZEIGER_MITTE_Y } : zeigerHotspot(form === 'tool' ? 'default' : form);
  const hs = `${hotspotPunkt.x} ${hotspotPunkt.y}`;
  const wert = `image-set(url("${daten1x}") 1x, url("${daten2x}") 2x) ${hs}, url("${daten1x}") ${hs}, ${fallbackFuer(form)}`;
  cache.set(schluessel, wert);
  return wert;
}

/** Nur für Tests: leert den Bild-Cache (Theme-/Massstab-Wechsel zwischen
 *  Testfällen dürfen keinen stehengebliebenen Wert eines anderen Tests
 *  sehen). Keine Rolle im Produktivpfad. */
export function _zeigerCacheLeerenFuerTests(): void {
  cache.clear();
}

export type { ZonenForm };
