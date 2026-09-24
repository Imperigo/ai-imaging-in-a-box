import type { ReactNode, SVGProps } from 'react';

/**
 * KIcon (W0, UI-KONZEPT-065 §3) — Registry von selbstgezeichneten Zeichen,
 * ein 16×16-Raster, 1.75px-Stroke, `currentColor`, kein Fremd-SVG. Ersetzt die
 * Emoji-Zeichen (👍 👎 ⚙ ⚠ ✕ ★ 🔍 ⚑ 🎙 …) überall dort, wo sie BEDIENELEMENT
 * sind; Emoji in Meldungs-TEXTEN dürfen bleiben (unberührt von dieser Datei).
 *
 * Jeder Registry-Eintrag ist reines Pfad-Markup (kein <svg>-Wrapper) — der
 * Wrapper (Grösse, Viewbox, Stroke-Defaults, aria) sitzt einmal in `KIcon`.
 */

export type KIconName =
  | 'zahnrad'
  | 'warnung'
  | 'schliessen'
  | 'stern'
  | 'stern-voll'
  | 'daumen-hoch'
  | 'daumen-runter'
  | 'plus'
  | 'minus'
  | 'lupe'
  | 'pfeil-links'
  | 'pfeil-rechts'
  | 'pfeil-oben'
  | 'pfeil-unten'
  | 'auge'
  | 'ebenen'
  | 'export'
  | 'kopieren'
  | 'kamera'
  | 'fit'
  | 'zoom-plus'
  | 'zoom-minus'
  | 'haken'
  | 'mikrofon'
  | 'fahne'
  | 'ordner'
  | 'dokument'
  | 'schloss'
  | 'stift'
  | 'hand'
  | 'mehr'
  | 'schweben'
  | 'andocken'
  | 'wuerfel'
  | 'auge-aus'
  | 'palette'
  | 'ueberlagerung'
  | 'ruecksetzen'
  | 'scan';

const REGISTRY: Record<KIconName, ReactNode> = {
  zahnrad: (
    <>
      <circle cx="8" cy="8" r="2.4" />
      <circle cx="8" cy="8" r="5.1" />
      <path d="M8 1.4V3M8 13v1.6M1.4 8H3m10 0h1.6M3.2 3.2l1.2 1.2M11.6 11.6l1.2 1.2M3.2 12.8l1.2-1.2M11.6 4.4l1.2-1.2" />
    </>
  ),
  warnung: (
    <>
      <path d="M8 2.2 14.3 13.4H1.7Z" />
      <path d="M8 6.4v3" />
      <circle cx="8" cy="11.5" r="0.75" fill="currentColor" stroke="none" />
    </>
  ),
  schliessen: <path d="M4 4l8 8M12 4l-8 8" />,
  stern: <path d="M8 2.2 9.6 6.2 14 6.5 10.6 9.3 11.7 13.6 8 11.2 4.3 13.6 5.4 9.3 2 6.5 6.4 6.2Z" />,
  'stern-voll': (
    <path
      d="M8 2.2 9.6 6.2 14 6.5 10.6 9.3 11.7 13.6 8 11.2 4.3 13.6 5.4 9.3 2 6.5 6.4 6.2Z"
      fill="currentColor"
      stroke="none"
    />
  ),
  'daumen-hoch': (
    <>
      <path d="M4 8.5h2V14H4a1 1 0 0 1-1-1V9.5a1 1 0 0 1 1-1Z" />
      <path d="M6 8.5l2.6-5c.5-.9 1.9-.5 1.9.5v2.3H12a1.3 1.3 0 0 1 1.27 1.56l-.9 4.2A1.3 1.3 0 0 1 11.1 13H6" />
    </>
  ),
  'daumen-runter': (
    <>
      <path d="M4 7.5h2V2H4a1 1 0 0 0-1 1v3.5a1 1 0 0 0 1 1Z" />
      <path d="M6 7.5l2.6 5c.5.9 1.9.5 1.9-.5V9.7H12a1.3 1.3 0 0 0 1.27-1.56l-.9-4.2A1.3 1.3 0 0 0 11.1 3H6" />
    </>
  ),
  plus: <path d="M8 3v10M3 8h10" />,
  minus: <path d="M3 8h10" />,
  lupe: (
    <>
      <circle cx="7" cy="7" r="4.3" />
      <path d="M10.2 10.2 14 14" />
    </>
  ),
  'pfeil-links': <path d="M13 8H3M7 4 3 8l4 4" />,
  'pfeil-rechts': <path d="M3 8h10M9 4l4 4-4 4" />,
  'pfeil-oben': <path d="M8 13V3M4 7l4-4 4 4" />,
  'pfeil-unten': <path d="M8 3v10M4 9l4 4 4-4" />,
  auge: (
    <>
      <path d="M1.5 8S4.2 3.3 8 3.3 14.5 8 14.5 8 11.8 12.7 8 12.7 1.5 8 1.5 8Z" />
      <circle cx="8" cy="8" r="1.9" />
    </>
  ),
  ebenen: (
    <>
      <path d="M8 1.4 13.5 4.6 8 7.8 2.5 4.6Z" />
      <path d="M8 5.4 13.5 8.6 8 11.8 2.5 8.6Z" />
      <path d="M8 9.4 13.5 12.6 8 15.8 2.5 12.6Z" />
    </>
  ),
  export: (
    <>
      <path d="M8 1.6v7.4M5 6l3-3 3 3" />
      <path d="M2.5 9.5v3.4a1 1 0 0 0 1 1h9a1 1 0 0 0 1-1V9.5" />
    </>
  ),
  /* Zwei Blaetter, das vordere ueber dem hinteren — das gelaeufige Bild fuer
     «kopieren». Es fehlte, und darum stand im Kosmo-Panel ein blosses
     Textzeichen `⧉` neben zwei echten 14-px-Symbolen. */
  kopieren: (
    <>
      <rect x="5.6" y="5.6" width="7.9" height="7.9" rx="1" />
      <path d="M10.4 5.6V3.5a1 1 0 0 0-1-1H3.5a1 1 0 0 0-1 1v5.9a1 1 0 0 0 1 1h2.1" />
    </>
  ),
  kamera: (
    <>
      <path d="M2 6h2.4l1-1.6h5.2l1 1.6H14a1 1 0 0 1 1 1v5.5a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1Z" />
      <circle cx="8" cy="9.3" r="2.4" />
    </>
  ),
  fit: <path d="M2 5.5V3a1 1 0 0 1 1-1h2.5M14 5.5V3a1 1 0 0 0-1-1h-2.5M2 10.5V13a1 1 0 0 0 1 1h2.5M14 10.5V13a1 1 0 0 1-1 1h-2.5" />,
  'zoom-plus': (
    <>
      <circle cx="7" cy="7" r="4.3" />
      <path d="M10.2 10.2 14 14" />
      <path d="M7 5v4M5 7h4" />
    </>
  ),
  'zoom-minus': (
    <>
      <circle cx="7" cy="7" r="4.3" />
      <path d="M10.2 10.2 14 14" />
      <path d="M5 7h4" />
    </>
  ),
  haken: <path d="M3 8.5 6.5 12 13 4.5" />,
  mikrofon: (
    <>
      <path d="M8 1.8a2.2 2.2 0 0 1 2.2 2.2v4.3a2.2 2.2 0 0 1-4.4 0V4a2.2 2.2 0 0 1 2.2-2.2Z" />
      <path d="M4.2 7.6v.7a3.8 3.8 0 0 0 7.6 0v-.7M8 12.1v2.1M6 14.2h4" />
    </>
  ),
  fahne: (
    <>
      <path d="M4 1.8v12.4" />
      <path d="M4 2.6h7.5l-2 2.7 2 2.7H4" />
    </>
  ),
  ordner: <path d="M1.8 4.4a1 1 0 0 1 1-1h3.3l1.2 1.6h5.9a1 1 0 0 1 1 1v6.6a1 1 0 0 1-1 1H2.8a1 1 0 0 1-1-1Z" />,
  dokument: (
    <>
      <path d="M4.5 1.8h5l3 3v9.4a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1V2.8a1 1 0 0 1 1-1Z" />
      <path d="M9.5 1.8v3h3" />
      <path d="M6 8.2h4M6 10.6h4" />
    </>
  ),
  schloss: (
    <>
      <path d="M4.6 7V5a3.4 3.4 0 0 1 6.8 0v2" />
      <path d="M3.6 7h8.8a1 1 0 0 1 1 1v5.4a1 1 0 0 1-1 1H3.6a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1Z" />
      <path d="M8 9.6v2" />
    </>
  ),
  stift: (
    <>
      <path d="M3 13l.7-3 7.6-7.6a1.6 1.6 0 0 1 2.3 2.3L6 12.3l-3 .7Z" />
      <path d="M9.6 3.3l2.3 2.3" />
    </>
  ),
  hand: (
    <path d="M5 8.6V3.6a1 1 0 1 1 2 0v4M7 7.6V2.9a1 1 0 1 1 2 0v4.7M9 7.6V3.6a1 1 0 1 1 2 0v4.7M11 8.3V5.4a1 1 0 1 1 2 0v5.2c0 2.7-1.8 4.6-4.5 4.6h-1c-1.6 0-2.4-.5-3.4-1.7L2 10.6a1.1 1.1 0 0 1 1.6-1.5l1.4 1.3" />
  ),
  mehr: (
    <>
      <circle cx="4" cy="8" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="8" cy="8" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="12" cy="8" r="1.1" fill="currentColor" stroke="none" />
    </>
  ),
  // v0.7.8 Welle 2 (P4, Dock-Pop-out): «aus dem Dock heben» — Pfeil, der
  // aus einer Ablage nach oben heraustritt.
  schweben: (
    <>
      <path d="M3 2.6h10" />
      <path d="M8 12.4V5.2M5 8l3-3 3 3" />
    </>
  ),
  // Gegenstück zu `schweben` — «zurück in den Dock legen»: Pfeil nach unten
  // auf eine Ablage.
  andocken: (
    <>
      <path d="M3 13.4h10" />
      <path d="M8 3.6v7.2M5 8l3 3 3-3" />
    </>
  ),
  // P-STUDIE (v0.9.7, Studienmodell-Viewer, HANDOFF.md §2.3): sechs neue
  // Zeichen, die das Original (`lucide-react` Box/EyeOff/Palette/Blend/
  // RotateCcw/ScanLine) in der eigenen Registry spiegeln — kein Fremd-SVG.
  wuerfel: (
    <>
      <path d="M8 1.6 13.5 4.6V11.4L8 14.4 2.5 11.4V4.6Z" />
      <path d="M2.5 4.6 8 7.6l5.5-3" />
      <path d="M8 7.6V14.4" />
    </>
  ),
  'auge-aus': (
    <>
      <path d="M1.5 8S4.2 3.3 8 3.3 14.5 8 14.5 8 11.8 12.7 8 12.7 1.5 8 1.5 8Z" />
      <circle cx="8" cy="8" r="1.9" />
      <path d="M2.5 2.5l11 11" />
    </>
  ),
  palette: (
    <>
      <path d="M8 2A6 5.4 0 1 0 8 12.8c1.1 0 1.4-1 .7-1.7-.5-.5-.2-1.3.6-1.3H11a3 3 0 0 0 3-3C14 3.8 11.3 2 8 2Z" />
      <circle cx="5.6" cy="6.4" r="0.9" fill="currentColor" stroke="none" />
      <circle cx="8" cy="5" r="0.9" fill="currentColor" stroke="none" />
      <circle cx="10.4" cy="6.4" r="0.9" fill="currentColor" stroke="none" />
    </>
  ),
  ueberlagerung: (
    <>
      <circle cx="6.2" cy="8" r="4.3" />
      <circle cx="9.8" cy="8" r="4.3" />
    </>
  ),
  ruecksetzen: (
    <>
      <path d="M3.2 8A4.8 4.8 0 1 1 4.6 11.4" />
      <path d="M3.2 4.4v3.6h3.6" />
    </>
  ),
  scan: (
    <>
      <path d="M2 5V3a1 1 0 0 1 1-1h2M14 5V3a1 1 0 0 0-1-1h-2M2 11v2a1 1 0 0 0 1 1h2M14 11v2a1 1 0 0 1-1 1h-2" />
      <path d="M2.5 8h11" />
    </>
  ),
};

export interface KIconProps extends Omit<SVGProps<SVGSVGElement>, 'children'> {
  name: KIconName;
  size?: 14 | 16 | 20;
  /** Wenn gesetzt: `role="img"` + sichtbarer `<title>` (das Icon TRÄGT dann
   * Bedeutung, z.B. als einziger Inhalt eines Icon-Buttons). Sonst
   * `aria-hidden` — der Regelfall, wenn ein sichtbares Text-Label daneben
   * steht (UI-KONZEPT-065: «Text bleibt Text»). */
  title?: string;
}

export function KIcon({ name, size = 16, title, ...rest }: KIconProps) {
  return (
    <svg
      viewBox="0 0 16 16"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      /* v0.7.3 D7: 1.5 → 1.75 — dieselbe Strichstärke wie die 0.7.2-
         Werkzeug-Glyphen (`werkzeug-glyphen.tsx`, sw 1.75), damit Utility-
         und Werkzeug-Zeichen gleich kräftig wirken. KEIN Zwangs-Rollenpunkt
         hier: KIcon ist die generische Utility-Registry (Schliessen,
         Zahnrad, Chevron, …) — ohne Bezug zu «WER handelt» (Mensch/Agent/…,
         Spec §1/§3); der Rollenpunkt bleibt den 0.7.2-Werkzeug-Glyphen
         vorbehalten, die genau dafür gebaut wurden. */
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...(title !== undefined ? { role: 'img' } : { 'aria-hidden': true })}
      {...rest}
    >
      {title !== undefined && <title>{title}</title>}
      {REGISTRY[name]}
    </svg>
  );
}

/** Für Tests/Tooling: alle Registry-Namen in stabiler Reihenfolge. */
export const K_ICON_NAMES: readonly KIconName[] = Object.keys(REGISTRY) as KIconName[];
