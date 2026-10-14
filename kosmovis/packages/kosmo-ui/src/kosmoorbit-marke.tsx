import { useId, type CSSProperties } from 'react';
import { useBewegung } from './anzeige';

/**
 * **Das KosmoOrbit-Logo — die Marke mit dem A** (Owner 30.09.2026: «das
 * aktuelle kosmoorbit logo ist noch falsch, ich möchte das mit dem A in der
 * mitte, rest passt» und «animiere auch immer überall das kosmoorbit logo»).
 *
 * Die Geometrie ist die der Startsequenz (Owner-Paket 21.07.2026,
 * `docs/owner-packages/2026-07-21-startsequenz/`, bis hierher nur in
 * `shell/StartSequenz.tsx` als eigene Kopie gezeichnet): 40er-Raster, geneigte
 * Umlaufbahn (Ellipse rx 17 / ry 8.5, −24°), die A-Spitze
 * `M11 25 L20 9 L29 25`, der Knoten (r 2.4) unter der Spitze. Dazu der
 * Trabant, der auf der Bahn umläuft — **nur, wenn etwas passiert** (`aktiv`).
 * Owner-Abstimmung mit Visbox G1 (01.10.2026) ersetzt hier den Wunsch vom
 * 30.09. («immer, an jeder Stelle»): in Ruhe steht er an seinem Platz, damit
 * Bewegung immer «da läuft etwas» heisst. Wer «weniger Bewegung» eingestellt
 * hat oder einen Browser ohne Bahnen (`offset-path`) nutzt, sieht ihn auch
 * dann stehen.
 *
 * **Farbe:** Bahn, Knoten und Trabant im Neon-Türkis der Marke, gemischt mit
 * der Tinte — im hellen Thema tiefer, im dunklen leuchtend. Die A-Spitze in
 * der Tinte. Knoten und Trabant tragen einen weichen Schein (Neon-Akzent).
 */

export const KOSMOORBIT_NEON = '#12D8EA';

/** Ab dieser Kantenlänge abwärts gröbere Striche (wie die Werkzeug-Logos). */
const KLEIN_BIS = 22;

const KEYFRAMES = `
@keyframes k-marke-umlauf { from { offset-distance: 0%; } to { offset-distance: 100%; } }
@keyframes k-marke-schein { 0%, 100% { opacity: .55; } 50% { opacity: 1; } }
`;

const BAHN = "path('M 3 20 A 17 8.5 0 1 1 37 20 A 17 8.5 0 1 1 3 20')";

function bahnenBekannt(): boolean {
  try {
    return typeof CSS !== 'undefined' && CSS.supports('offset-path', "path('M0 0L1 1')");
  } catch {
    return false;
  }
}

/** `true`, wenn der Trabant umlaufen darf und kann. */
export function useMarkeBewegt(): boolean {
  // Schleifen (Umlauf, Kosmo-Zustände) nur bei voller Bewegung: «ruhig» und
  // «aus» halten sie an — Gerät oder eigener Schalter (U14, anzeige.ts).
  return useBewegung() === 'voll' && bahnenBekannt();
}

export interface KosmoOrbitMarkeProps {
  size?: number;
  /** Beschriftung fuer Vorlesen; `''` = schmueckend. */
  beschriftung?: string;
  /** Erzwingt Bewegung an/aus (Proben, Druck). Ohne Angabe: wie das Geraet («weniger Bewegung»). */
  bewegt?: boolean;
  /**
   * Es passiert gerade etwas (Start, Kosmo arbeitet, ein Auftrag laeuft): nur
   * dann laeuft der Trabant. Owner-Abstimmung mit Visbox G1 (01.10.2026):
   * «Bewegung nur, wenn etwas passiert. In Ruhe steht alles still.» Das
   * ersetzt den Wunsch vom 30.09. «animiere immer überall das Logo».
   */
  aktiv?: boolean;
  style?: CSSProperties;
  className?: string;
}

export function KosmoOrbitMarke({ size = 28, beschriftung = 'KosmoOrbit', bewegt, aktiv = false, style, className }: KosmoOrbitMarkeProps) {
  const roh = useId().replace(/[^a-zA-Z0-9_-]/g, '');
  const schein = `k-marke-schein-${roh}`;
  const kannBewegen = useMarkeBewegt();
  // `bewegt={true}` bleibt der erzwungene Lauf fuer Proben und Schaukasten.
  const laeuft = (bewegt ?? kannBewegen) && (aktiv || bewegt === true);
  const klein = size <= KLEIN_BIS;
  const neon = `color-mix(in oklab, ${KOSMOORBIT_NEON} 82%, var(--k-ink, #1a1815))`;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      {...(beschriftung ? { role: 'img', 'aria-label': beschriftung } : { 'aria-hidden': true })}
      data-logo="orbit"
      data-bewegt={laeuft ? 'ja' : 'nein'}
      style={style}
      className={className}
    >
      {beschriftung ? <title>{beschriftung}</title> : null}
      {laeuft ? <style>{KEYFRAMES}</style> : null}
      <defs>
        <radialGradient id={schein}>
          <stop offset="0%" style={{ stopColor: KOSMOORBIT_NEON, stopOpacity: 0.55 }} />
          <stop offset="100%" style={{ stopColor: KOSMOORBIT_NEON, stopOpacity: 0 }} />
        </radialGradient>
      </defs>
      <g transform="rotate(-24 20 20)">
        <ellipse cx="20" cy="20" rx="17" ry="8.5" style={{ stroke: neon }} strokeWidth={klein ? 2 : 1.4} />
        {laeuft ? (
          <g style={{ offsetPath: BAHN, animation: 'k-marke-umlauf 9s linear infinite' }}>
            <circle r={klein ? 3.4 : 3} fill={`url(#${schein})`} />
            <circle r={klein ? 2 : 1.6} style={{ fill: neon }} />
          </g>
        ) : (
          <>
            <circle cx="37" cy="20" r={klein ? 3.4 : 3} fill={`url(#${schein})`} />
            <circle cx="37" cy="20" r={klein ? 2 : 1.6} style={{ fill: neon }} />
          </>
        )}
      </g>
      <path
        d="M11 25 L20 9 L29 25"
        stroke="var(--k-ink, #1a1815)"
        strokeWidth={klein ? 2.3 : 1.6}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle
        cx="20"
        cy="16.5"
        r="5.2"
        fill={`url(#${schein})`}
        style={laeuft ? { animation: 'k-marke-schein 3.6s ease-in-out infinite' } : undefined}
      />
      <circle cx="20" cy="16.5" r={klein ? 2.8 : 2.4} style={{ fill: neon }} />
    </svg>
  );
}
