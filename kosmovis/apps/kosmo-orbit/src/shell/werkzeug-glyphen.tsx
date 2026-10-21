import type { ReactNode } from 'react';
import type { StationModulId } from './stations-werkzeuge';

/**
 * V0.7.2 W1-B (Paket 02) — die neue Werkzeug-Glyphen-Bibliothek, exakt nach
 * `docs/V072-VISUELLES-UPDATE-SPEZ.md` §3. Norm (§0 Grundregel 1 «Rund statt
 * Block» + §3-Kopf): 24er-ViewBox, Stroke `var(--k-ink)` opacity .9, sw 1.75,
 * runde Kappen/Joins, fill none — plus GENAU EIN Akzent-Punkt (`<circle
 * r={1.7}>`) in Rollenfarbe (oder `currentColor`, wenn keine Rolle übergeben
 * — einfarbig-fähig). Einzige Ausnahme: `orbit` trägt ein Quadrat (3.2 rx1)
 * statt eines Punkts + ein Teal-Viertel (`var(--k-signal)`), siehe Spec-Zeile
 * «orbit».
 *
 * Diese Datei ist NEU (verdrahtet nur an `orbit-icons.tsx`,
 * `modules/design/werkzeug-icons.tsx` und `EntwurfsDock.tsx` — Spec §3
 * «Verträge»). `aura.css`/Tokens (die `--k-ink`/`--k-signal`/`--k-rolle-*`-
 * Variablen selbst) gehören Stream A (W1-A) und werden hier NICHT angelegt —
 * nur referenziert.
 */

/** Die 12 Stations-Glyphen aus Spec-§3 + die 2 Fable-Erweiterungen
 *  (`skizze`/`lernen`) für Stationen ohne eigene Handoff-Glyphe. */
export type WerkzeugGlyphenArt =
  | 'chat'
  | 'pipeline'
  | 'draw'
  | 'data'
  | 'viz'
  | 'publish'
  | 'prepare'
  | 'connect'
  | 'office'
  | 'zentrale'
  | 'odysseus'
  | 'orbit'
  | 'skizze'
  | 'lernen';

interface Punkt {
  cx: number;
  cy: number;
}

/** Grundform je Glyphe (ohne den Akzent-Punkt) — Pfade/Attribute exakt aus
 *  der Spec-§3-Tabelle übernommen (Zentrum-Koordinaten, keine Erfindung). */
const GRUND: Record<WerkzeugGlyphenArt, ReactNode> = {
  chat: (
    <>
      <path d="M12 4 v5 M12 15 v5 M4 12 h5 M15 12 h5" />
      <circle cx="12" cy="12" r="2.4" />
    </>
  ),
  pipeline: (
    <>
      <circle cx="6" cy="6" r="2.4" />
      <circle cx="18" cy="12" r="2.4" />
      <path d="M8 7.5 L15.6 11 M8 17 L15.6 13" />
    </>
  ),
  draw: <path d="M5 19 L15.5 8.5 M5 19 l1-4 M5 19 l4-1" />,
  data: (
    <>
      <ellipse cx="12" cy="7" rx="7" ry="2.8" />
      <path d="M5 7 v10 c0 1.6 3.1 2.8 7 2.8 s7-1.2 7-2.8 V7" />
    </>
  ),
  viz: (
    <>
      <rect x="4" y="5.5" width="16" height="13" rx="2" />
      <path d="M4 15.5 l5-5 4 4 3-3 4 4" />
    </>
  ),
  publish: <path d="M7 20 h10 a2 2 0 0 0 2-2 V8 l-4-4 H7 a2 2 0 0 0-2 2 v12 a2 2 0 0 0 2 2 Z M15 4 v4 h4" />,
  prepare: (
    <>
      <circle cx="12" cy="12" r="8" />
      <path d="M15 9 l-2 4.4 L9 15 l2-4.4 Z" />
    </>
  ),
  connect: <path d="M4 9 h13 m0 0 -3-3 m3 3 -3 3 M20 15 H7 m0 0 3-3 m-3 3 3 3" />,
  office: <path d="M4 8 a2 2 0 0 1 2-2 h4 l2 2.5 h6 a2 2 0 0 1 2 2 V17 a2 2 0 0 1-2 2 H6 a2 2 0 0 1-2-2 Z" />,
  zentrale: (
    <>
      <rect x="5" y="4.5" width="14" height="6.4" rx="1.6" />
      <rect x="5" y="13.1" width="14" height="6.4" rx="1.6" />
      <path d="M8 7.7 h3 M8 16.3 h3" />
    </>
  ),
  odysseus: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 4.5 v2.6 M12 16.9 v2.6 M4.5 12 h2.6 M16.9 12 h2.6 M6.7 6.7 l1.8 1.8 M15.5 15.5 l1.8 1.8 M17.3 6.7 l-1.8 1.8 M8.5 15.5 l-1.8 1.8" />
    </>
  ),
  /** Ausnahme (Spec-Zeile «orbit»): Ring (dash 1.5 3) + Quadrat 3.2×3.2 rx1
   *  statt Punkt — das Teal-Viertel wird unten AUSSERHALB dieser opacity-.9-
   *  Gruppe gerendert (voller Ton, `var(--k-signal)`). */
  orbit: (
    <>
      <circle cx="12" cy="12" r="8.5" strokeDasharray="1.5 3" />
      <rect x="10.4" y="10.4" width="3.2" height="3.2" rx="1" />
    </>
  ),
  skizze: <path d="M4 16 C8 8, 12 20, 20 9" />,
  lernen: (
    <>
      <rect x="4.5" y="14" width="3" height="6" rx="1.5" />
      <rect x="10.5" y="10" width="3" height="10" rx="1.5" />
      <rect x="16.5" y="6" width="3" height="14" rx="1.5" />
    </>
  ),
};

/** Akzent-Punkt-Zentrum je Glyphe (Spec-§3-Spalte «Punkt-Zentrum») — `orbit`
 *  hat KEINEN Punkt (Quadrat-Ausnahme, siehe oben), daher hier ausgeschlossen. */
const PUNKT: Record<Exclude<WerkzeugGlyphenArt, 'orbit'>, Punkt> = {
  chat: { cx: 17.9, cy: 5.9 },
  pipeline: { cx: 5.9, cy: 17.3 },
  draw: { cx: 17.5, cy: 6.5 },
  data: { cx: 16.2, cy: 12.9 },
  viz: { cx: 16.5, cy: 9.3 },
  publish: { cx: 10.1, cy: 15.3 },
  prepare: { cx: 12, cy: 12 },
  connect: { cx: 18.7, cy: 17.7 },
  office: { cx: 17.5, cy: 13.7 },
  zentrale: { cx: 16.5, cy: 16.3 },
  odysseus: { cx: 12, cy: 12 },
  skizze: { cx: 17.5, cy: 15.5 },
  lernen: { cx: 18.5, cy: 6.5 },
};

/** Öffentlich, damit andere Besitz-Dateien (z. B. `orbit-icons.tsx`, das den
 *  ruhigen Puls `k-orbit-icon-puls` als zusätzlichen Ring um denselben
 *  Zentrum-Punkt legt) dieselbe Koordinate verwenden — keine Zweitquelle. */
export const GLYPHEN_PUNKT: Record<Exclude<WerkzeugGlyphenArt, 'orbit'>, Punkt> = PUNKT;

export interface WerkzeugGlypheProps {
  art: WerkzeugGlyphenArt;
  /** Gerenderte Kantenlänge (px); die ViewBox bleibt immer 24. Default 24. */
  size?: number;
  /** CSS-Custom-Property-NAME (z. B. `--k-rolle-manuell`), OHNE `var(...)` —
   *  die Komponente kapselt das Wrapping. Ohne Rolle erbt der Punkt
   *  `currentColor` (einfarbig-fähig, Spec-§3). Bei `art="orbit"` wirkungslos
   *  (kein Punkt, siehe Grundform-Ausnahme). */
  rolle?: string;
  /** Akzent-Punkt-Radius im 24er-Raster. Default kontextabhängig
   *  (Kritik-1-Auflage 3): 1.7 in normalen Grössen, 2.2 sobald die Glyphe
   *  klein gerendert wird (`size` ≤ 20, z. B. EntwurfsDock) — sonst ist das
   *  5-%-Signal faktisch unsichtbar. Voll deckend, kein Glow, kein Ring. */
  punktRadius?: number;
}

/** `<WerkzeugGlyphe art size rolle?>` — die 14 Grundformen aus Spec-§3 (12 +
 *  2 Fable-Erweiterungen), gerendert nach der «Rund statt Block»-Grundregel:
 *  IMMER ein `<circle>` als Akzent (r 1.7, in Klein-Kontexten 2.2 —
 *  Quadrat-Ausnahme nur bei `orbit`). */
export function WerkzeugGlyphe({ art, size = 24, rolle, punktRadius }: WerkzeugGlypheProps) {
  const punktFarbe = rolle ? `var(${rolle})` : 'currentColor';
  const punktR = punktRadius ?? (size <= 20 ? 2.2 : 1.7);
  const punkt = art === 'orbit' ? null : PUNKT[art as Exclude<WerkzeugGlyphenArt, 'orbit'>];
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <g stroke="var(--k-ink)" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" fill="none" opacity={0.9}>
        {GRUND[art]}
      </g>
      {art === 'orbit' && (
        <path
          d="M12 3.5 A 8.5 8.5 0 0 1 20.5 12"
          fill="none"
          stroke="var(--k-signal)"
          strokeWidth={2}
          strokeLinecap="round"
        />
      )}
      {punkt && <circle cx={punkt.cx} cy={punkt.cy} r={punktR} fill={punktFarbe} stroke="none" />}
    </svg>
  );
}

/** Station → Glyphe → Rollenfarbe, exakt nach Spec-§3-Tabelle (nur die 12
 *  echten Stationen — `orbit`/`kosmo` sind keine `StationModulId`, s.
 *  `stations-werkzeuge.ts`; die Zeilen «Sync/Koppeln»/«Hauptwerkzeug
 *  orbit»/«Hauptwerkzeug office» dort sind keine Stationen und leben
 *  ausserhalb dieser Tabelle). */
export const STATION_GLYPHE: Record<StationModulId, { art: WerkzeugGlyphenArt; rolle: string }> = {
  design: { art: 'draw', rolle: '--k-rolle-manuell' },
  sketch: { art: 'skizze', rolle: '--k-rolle-manuell' },
  draw: { art: 'zentrale', rolle: '--k-rolle-pn' },
  data: { art: 'data', rolle: '--k-rolle-pn' },
  vis: { art: 'viz', rolle: '--k-rolle-generator' },
  publish: { art: 'publish', rolle: '--k-rolle-agent' },
  prepare: { art: 'prepare', rolle: '--k-rolle-memory' },
  asset: { art: 'office', rolle: '--k-rolle-ak' },
  dev: { art: 'pipeline', rolle: '--k-rolle-pna' },
  speak: { art: 'chat', rolle: '--k-signal' },
  doc: { art: 'odysseus', rolle: '--k-rolle-office' },
  train: { art: 'lernen', rolle: '--k-rolle-memory' },
  trust: { art: 'connect', rolle: '--k-rolle-office' },
  // v0.8.1 / P14 (C-28/C-30): KosmoPackage teilt sich `office` mit `doc`/
  // `trust` (Büro-/Meta-Rolle) — reine Bündel-/Export-Übersicht, kein neuer
  // Glyphen-Typ nötig.
  paket: { art: 'connect', rolle: '--k-rolle-office' },
  // P-SPEZ: KosmoSpez teilt sich `viz` mit `vis` (Licht-/Ergebnis-Thema passt
  // fachlich — Sonnenstunden-Heatmaps, Falschfarben-Overlays) — eigene
  // Rolle `--k-rolle-doc` (bislang von keiner Station belegt) hält die
  // Zentrale-Kachel trotzdem farblich unterscheidbar von KosmoVis.
  spez: { art: 'viz', rolle: '--k-rolle-doc' },
};
