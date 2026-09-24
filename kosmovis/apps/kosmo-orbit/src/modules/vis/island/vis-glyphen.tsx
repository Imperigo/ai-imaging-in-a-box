import type { ComponentType, ReactNode } from 'react';

/**
 * Vis-Glyphen-Bibliothek (PA4, `docs/V085-SPEZ.md` §3 E6 + §7 C-13) — 13
 * echte SVG-Icons für den kompletten `vis-island-katalog.ts`-Werkzeugsatz
 * (GRAPH 3 / ANSICHT 4 / STIMMUNG 1 / AUSTAUSCH 5), bisher reine
 * Zwei-Buchstaben-Text-Kürzel (`'NO'`, `'AR'`, …). v0.8.9 §9 E11 (PBL2,
 * `docs/V089-SPEZ.md`): additiv um ein 14. Icon für die neue SONNE-Insel
 * (Sonnenstunden, 1) erweitert. v0.8.10 E3-Nachtrag (Owner-Entscheid
 * 20.07.2026, `docs/V0810-SPEZ.md` §2 E3): AUSTAUSCH's `manuell`-Icon
 * wieder entfernt (der Insel-Rückweg ist entfallen, s. `vis-island-
 * katalog.ts`) — zurück auf 13 Icons total.
 *
 * **Bauvorschrift (BINDEND, identisch zu `design/werkzeug-icons.tsx:1-31` +
 * `design/island/island-glyphen.tsx` — dieselbe 24er-Norm, hier für den
 * Vis-Namensraum fortgeschrieben):**
 * - `viewBox="0 0 24 24"`, `strokeWidth="1.75"`, runde Kappen/Joins.
 * - GENAU EIN Akzentpunkt-Kreis pro Icon (`r="1.13"`, `fill="var(--k-accent)"`,
 *   `stroke="none"`) — einziger Ort mit einer Farbe ausserhalb `currentColor`.
 * - Alles andere ist `currentColor`/`fill="none"` (vom `<svg>`-Wurzelelement
 *   vererbt).
 * - `aria-hidden="true"`, `focusable={false}`, KEIN `<text>`-Kind.
 *
 * Motive fachlich an den Vis-Werkzeugen orientiert: Node-Palette (Raster aus
 * Bausteinen), Ausrichten (Fluchtlinie), Verbinden (zwei Knoten + Leitung),
 * Zoom (Lupe), Raster-Snap (Gitter), Kanten-Routing (Knick-Leitung),
 * Stimmung (Sonne/Wolke), Render senden
 * (Papierflieger), Aufs Plakat (Blatt mit Reisszwecke), Kamera vorschlagen
 * (echte Kamera), Report (Dokument mit Balken).
 *
 * v0.8.11 P-B1/E4 (`docs/V0811-SPEZ.md` §2 E4): additiv um 2 Icons für die
 * neuen ANSICHT-Insel-Werkzeuge «Gespeicherte Ansichten» + «Legende»
 * erweitert — 13→15. Gespeicherte Ansichten (zwei versetzte Bild-Rahmen mit
 * Häkchen — «gespeicherter Schnappschuss»), Legende (drei Zeilen aus
 * Punkt+Strich — 1:1 das Listen-Motiv der echten Legende, `vis-visual.css`
 * `.vis-legende-zeile`).
 */

const WURZEL_ATTRIBUTE = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.75,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
  focusable: false,
} as const;

interface GlyphProps {
  size?: number;
}

function glyphe(inhalt: ReactNode): ComponentType<GlyphProps> {
  function Glyphe({ size = 18 }: GlyphProps) {
    return (
      <svg {...WURZEL_ATTRIBUTE} width={size} height={size}>
        {inhalt}
      </svg>
    );
  }
  return Glyphe;
}

/** Der eine erlaubte Akzentpunkt (r=1.13, `var(--k-accent)`, kein Stroke). */
function akzent(cx: number, cy: number) {
  return <circle cx={cx} cy={cy} r={1.13} fill="var(--k-accent)" stroke="none" />;
}

/** Node-Palette — Raster aus vier Bausteinen (verfügbare Node-Typen), Akzent im Zentrum. */
const palette = glyphe(
  <>
    <rect x="4" y="4" width="7" height="7" rx="1" />
    <rect x="13" y="4" width="7" height="7" rx="1" />
    <rect x="4" y="13" width="7" height="7" rx="1" />
    <rect x="13" y="13" width="7" height="7" rx="1" />
    {akzent(7.5, 7.5)}
  </>,
);

/** Ausrichten — Fluchtlinie mit drei linksbündigen Balken, Akzent an der Linie oben. */
const ausrichten = glyphe(
  <>
    <path d="M4 3 V21" />
    <path d="M4 7 H18 M4 12 H14 M4 17 H20" />
    {akzent(4, 3)}
  </>,
);

/** Verbinden — zwei Knoten mit Leitung, Akzent am Zielknoten. */
const verbinden = glyphe(
  <>
    <circle cx="5" cy="12" r="2.6" />
    <circle cx="19" cy="12" r="2.6" />
    <path d="M7.6 12 H16.4" />
    {akzent(19, 12)}
  </>,
);

/** Zoom — Lupe mit Plus, Akzent am Griffende. */
const zoom = glyphe(
  <>
    <circle cx="10.5" cy="10.5" r="6.5" />
    <path d="M15.3 15.3 L21 21" />
    <path d="M10.5 7.5 V13.5 M7.5 10.5 H13.5" />
    {akzent(21, 21)}
  </>,
);

/** Raster-Snap — Gitterlinien, Akzent am ersten Kreuzungspunkt. */
const raster = glyphe(
  <>
    <path d="M4 4 H20 M4 9.3 H20 M4 14.7 H20 M4 20 H20" />
    <path d="M4 4 V20 M9.3 4 V20 M14.7 4 V20 M20 4 V20" />
    {akzent(9.3, 9.3)}
  </>,
);

/** Kanten-Routing — Knick-Leitung (orthogonale Führung), Akzent am Knick. */
const routing = glyphe(
  <>
    <path d="M3 6 H10 V18 H21" />
    <circle cx="3" cy="6" r="1.5" />
    <circle cx="21" cy="18" r="1.5" />
    {akzent(10, 6)}
  </>,
);

/* K35 (Owner-Korrekturen 2026-07, S.14): die «Minimap»-Glyphe (verschachtelter
   Rahmen) ist mitsamt dem Katalog-Werkzeug 'minimap' entfernt. */

/** Stimmung — Sonne hinter Wolke, Akzent im Sonnenkern. */
const stimmung = glyphe(
  <>
    <circle cx="9" cy="8" r="3.1" />
    <path d="M9 2.4 V4.2 M4.2 8 H6 M3.3 3.3 L4.6 4.6 M14.7 3.3 L13.4 4.6" />
    <path d="M5.6 20 C3.2 20 2.4 17.4 4.6 16.4 C4.2 13.6 8.2 12.4 10 14.4 C11.6 11.6 16.4 12.2 16.8 15.2 C19.6 15.2 20 18.4 17.2 19.6 C17 19.8 16.8 20 16.4 20 Z" />
    {akzent(9, 8)}
  </>,
);

/** Render senden — Papierflieger, Akzent an der Spitze. */
const renderSenden = glyphe(
  <>
    <path d="M3 12 L21 4 L14 21 L11 13 L3 12 Z" />
    <path d="M11 13 L21 4" />
    {akzent(21, 4)}
  </>,
);

/** Aufs Plakat — Blatt mit Reisszwecke, Akzent an der Zwecke. */
const aufsPlakat = glyphe(
  <>
    <rect x="5" y="6" width="14" height="16" rx="1" />
    <path d="M9 12 H15 M9 16 H13" />
    <path d="M12 6 V3.6" />
    {akzent(12, 3.6)}
  </>,
);

/** Kamera vorschlagen — echte Kamera (Körper + Objektiv), Akzent als Linsen-Reflex. */
const kameraVorschlagen = glyphe(
  <>
    <path d="M4 8 H8 L10 6 H14 L16 8 H20 V19 H4 Z" />
    <circle cx="12" cy="13.5" r="3.6" />
    {akzent(10.4, 12)}
  </>,
);

/** Report — Dokument mit Balkendiagramm, Akzent an der gefalteten Ecke. */
const report = glyphe(
  <>
    <path d="M6 3 H15 L19 7 V21 H6 Z" />
    <path d="M15 3 V7 H19" />
    <path d="M9 12 V17 M12.5 10 V17 M16 13.5 V17" />
    {akzent(15, 3)}
  </>,
);

/**
 * Sonnenstunden — Sonnenscheibe mit acht Strahlen (Sonnenuhr-Motiv, bewusst
 * verschieden vom «Sonne-hinter-Wolke»-Motiv von `stimmung`), Akzent im
 * Zentrum. v0.8.9 §9 E11 (PBL2, `docs/V089-SPEZ.md`) — SONNE-Insel
 * (`vis-island-katalog.ts`).
 */
const sonnenstunden = glyphe(
  <>
    <circle cx="12" cy="12" r="4.2" />
    <path d="M12 3 V5.4 M12 18.6 V21 M3 12 H5.4 M18.6 12 H21 M5.9 5.9 L7.6 7.6 M16.4 16.4 L18.1 18.1 M5.9 18.1 L7.6 16.4 M16.4 7.6 L18.1 5.9" />
    {akzent(12, 12)}
  </>,
);

/**
 * Gespeicherte Ansichten — zwei versetzte Bild-Rahmen (Schnappschuss-Stapel,
 * Muster des früheren Minimap-Rahmens, aber ÜBERLAPPEND statt verschachtelt), Häkchen im
 * vorderen Rahmen («gespeichert»), Akzent an der hinteren Rahmen-Ecke. v0.8.11
 * P-B1/E4 (`docs/V0811-SPEZ.md` §2 E4) — Insel-Äquivalent zu
 * `GespeicherteAnsichten.tsx`.
 */
const ansichten = glyphe(
  <>
    <rect x="4" y="7" width="13" height="10" rx="1.3" />
    <rect x="7.6" y="4" width="13" height="10" rx="1.3" />
    <path d="M7.8 12.2 L10.4 14.8 L14.4 9.4" />
    {akzent(20.6, 4)}
  </>,
);

/**
 * Legende — drei Listenzeilen aus Punkt+Strich, 1:1 das echte Legende-Motiv
 * (`vis-visual.css` `.vis-legende-zeile`: Punkt + Text je Porttyp), Akzent
 * auf dem ersten Punkt. v0.8.11 P-B1/E4 (`docs/V0811-SPEZ.md` §2 E4) —
 * Insel-Äquivalent zur Porttyp-Legende (bisher NUR `NodeCanvas.tsx`).
 */
const legende = glyphe(
  <>
    <path d="M9 6 H20 M9 12 H20 M9 18 H20" />
    <circle cx="4.5" cy="6" r="1.6" />
    <circle cx="4.5" cy="12" r="1.6" />
    <circle cx="4.5" cy="18" r="1.6" />
    {akzent(4.5, 6)}
  </>,
);

/** Die Vis-Werkzeug-Icons, geschlüsselt nach `vis-island-katalog.ts`s `IslandWerkzeug.id`. */
export const VIS_GLYPHEN: Record<string, ComponentType<GlyphProps>> = {
  palette,
  ausrichten,
  verbinden,
  zoom,
  raster,
  routing,
  stimmung,
  'render-senden': renderSenden,
  'aufs-plakat': aufsPlakat,
  'kamera-vorschlagen': kameraVorschlagen,
  report,
  sonnenstunden,
  ansichten,
  legende,
};
