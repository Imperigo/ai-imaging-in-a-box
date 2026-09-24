import type { CSSProperties } from 'react';

/**
 * Logo «6a» (v0.7.2 «Visuelles Update» §2, Paket 01) — die exakte
 * Vollversion aus der Bau-Spezifikation (`docs/V072-VISUELLES-UPDATE-SPEZ.md`
 * §2): Umlaufbahn (gestrichelter Ring) + Satellit (Signal-Punkt auf einem
 * Teal-Viertelbogen) + Zentrum (Neun-Quadrat-Raster mit Mittelpunkt) — «rund
 * statt Block» (Spec §0 Regel 1): das Neun-Quadrat behält als EINZIGE
 * Ausnahme weiche Ecken (rx ≈ 30 %), alles andere sind Kreise/Kreisbögen.
 * Farben laufen NICHT über Hex-Literale, sondern über Tokens: «Weiss» ist
 * `var(--k-ink)` (in paper/ink dunkler = korrekt — der Ring liest sich dort
 * als Tusche-Zeichnung), «Teal» ist `var(--k-signal)` (die themeninvariante
 * Markenfarbe, siehe `aura.css`/`tokens.ts`).
 *
 * `Logo.tsx`/`OrbitMark` rendert dieses Symbol intern für `module="orbit"`
 * (die App-Identität selbst); alle anderen Modul-Werte behalten die
 * bisherige Orbit-Konstruktion aus `Logo.tsx` unverändert (deren API/Optik
 * ist ein bestehender Vertrag ausserhalb des Streams W1-A-Auftrags).
 */

export type Logo6aZustand = 'bereit' | 'laeuft' | 'fertig' | 'fehler';

export interface Logo6aProps {
  /** Kantenlänge (Breite=Höhe) in px. ≤ 22 aktiviert die vereinfachte
   *  Klein-Variante (Spec §2: Rasterlinien weg, gröbere Striche). */
  size?: number;
  zustand?: Logo6aZustand;
  /** Shell-Kontext-Feintuning der Klein-Variante (Spec §2: «Im
   *  Shell-Kontext ≤ 22 px»: Quadrat 14×14 rx4.5 sw2, Punkt r2.5 statt der
   *  generischen 13×13 rx4 sw1.8–2, Punkt r2.1). Nur wirksam bei size ≤ 22. */
  shellKontext?: boolean;
  style?: CSSProperties;
  className?: string;
  title?: string;
}

const REDUZIERT_DAUER = {
  drehen: '1.6s',
  blinken: '1.2s',
  haken: '400ms',
} as const;

/** Vollversion (> 22 px) — exakt die Spec-§2-Konstruktion. */
function VollVersion({ zustand }: { zustand: Logo6aZustand }) {
  const laeuft = zustand === 'laeuft';
  const fertig = zustand === 'fertig';
  const fehler = zustand === 'fehler';

  const ringFarbe = fertig ? 'var(--k-success)' : 'var(--k-ink)';
  const punktFarbe = fehler ? 'var(--k-danger)' : 'var(--k-signal)';

  return (
    <>
      {/* Umlaufbahn — gestrichelter Ring; `fertig` schliesst ihn zur vollen,
          erfolgsgrünen Linie (Spec: «Ring voll --k-success»). */}
      <circle
        cx="24"
        cy="24"
        r="17"
        stroke={ringFarbe}
        strokeWidth={fertig ? 2 : 1.5}
        strokeDasharray={fertig ? undefined : '2 4'}
        strokeLinecap="round"
        opacity={fertig ? 1 : 0.5}
      />
      {/* Satellit: Teal-Viertelbogen + Punkt — bei `laeuft` rotiert die
          Gruppe kontinuierlich um den Mittelpunkt (globaler reduced-motion-
          Riegel in aura.css friert JEDE Animation automatisch ein, kein
          Sonderfall hier nötig). `fertig`/`fehler` blenden den Satelliten
          aus (Ring bzw. Mittelpunkt tragen dort die eigene Aussage). */}
      {!fertig && (
        <g
          style={
            laeuft
              ? { transformOrigin: '24px 24px', animation: `k-logo6a-drehen ${REDUZIERT_DAUER.drehen} linear infinite` }
              : undefined
          }
        >
          <path d="M 24 7 A 17 17 0 0 1 41 24" stroke="var(--k-signal)" strokeWidth="2.2" strokeLinecap="round" />
          <circle cx="40.3" cy="9.9" r="1.7" fill="var(--k-signal)" />
        </g>
      )}
      {fertig && (
        // Haken — gezeichnet mit einer einmaligen Stroke-Draw-Animation
        // (< 700 ms, Feedback-Obergrenze aus Spec §0 Regel 4).
        <path
          d="M 15.5 24.5 L 21 30 L 32.5 17.5"
          stroke="var(--k-success)"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
          pathLength={1}
          style={{
            strokeDasharray: 1,
            strokeDashoffset: 0,
            animation: `k-logo6a-haken ${REDUZIERT_DAUER.haken} var(--k-ease-standard, ease-out) both`,
          }}
        />
      )}
      {/* Zentrum — Neun-Quadrat-Raster (einzige Ausnahme von der Rund-Regel,
          Spec §0 Regel 1: rx ≈ 30 % der Kantenlänge = 4/13). */}
      <rect x="17.5" y="17.5" width="13" height="13" rx="4" stroke="var(--k-ink)" strokeWidth="1.4" />
      <path
        d="M 21.8 17.5 V 30.5 M 26.2 17.5 V 30.5 M 17.5 21.8 H 30.5 M 17.5 26.2 H 30.5"
        stroke="var(--k-ink)"
        strokeWidth="1"
        opacity=".7"
      />
      <circle
        cx="24"
        cy="24"
        r="1.6"
        fill={punktFarbe}
        style={fehler ? { animation: `k-logo6a-blinken ${REDUZIERT_DAUER.blinken} ease-in-out infinite` } : undefined}
      />
    </>
  );
}

/** Klein-Variante (≤ 22 px, Spec §2) — Rasterlinien weg, gröbere Striche,
 *  damit die Konstruktion bei winzigen Grössen nicht zu Matsch verläuft. */
function KleinVersion({ zustand, shellKontext }: { zustand: Logo6aZustand; shellKontext: boolean }) {
  const laeuft = zustand === 'laeuft';
  const fertig = zustand === 'fertig';
  const fehler = zustand === 'fehler';

  const ringFarbe = fertig ? 'var(--k-success)' : 'var(--k-ink)';
  const punktFarbe = fehler ? 'var(--k-danger)' : 'var(--k-signal)';
  // «Im Shell-Kontext ≤22px»: Quadrat 14×14 rx4.5 sw2, Punkt r2.5 — sonst
  // die generische Klein-Konstruktion 13×13 rx4 sw1.8–2, Punkt r2.1.
  const quadratSeite = shellKontext ? 14 : 13;
  const quadratRx = shellKontext ? 4.5 : 4;
  const quadratSw = shellKontext ? 2 : 1.9;
  const punktR = shellKontext ? 2.5 : 2.1;
  const quadratXY = 24 - quadratSeite / 2;

  return (
    <>
      <circle
        cx="24"
        cy="24"
        r="17"
        stroke={ringFarbe}
        strokeWidth={fertig ? 2.2 : 2}
        strokeDasharray={fertig ? undefined : '2.4 4'}
        strokeLinecap="round"
        opacity={fertig ? 1 : 0.6}
      />
      {!fertig && (
        <g
          style={
            laeuft
              ? { transformOrigin: '24px 24px', animation: `k-logo6a-drehen ${REDUZIERT_DAUER.drehen} linear infinite` }
              : undefined
          }
        >
          <path d="M 24 7 A 17 17 0 0 1 41 24" stroke="var(--k-signal)" strokeWidth="2.4" strokeLinecap="round" />
          <circle cx="40.3" cy="9.9" r="2" fill="var(--k-signal)" />
        </g>
      )}
      <rect x={quadratXY} y={quadratXY} width={quadratSeite} height={quadratSeite} rx={quadratRx} stroke="var(--k-ink)" strokeWidth={quadratSw} />
      <circle
        cx="24"
        cy="24"
        r={punktR}
        fill={punktFarbe}
        style={fehler ? { animation: `k-logo6a-blinken ${REDUZIERT_DAUER.blinken} ease-in-out infinite` } : undefined}
      />
    </>
  );
}

export function Logo6a({ size = 48, zustand = 'bereit', shellKontext = false, style, className, title }: Logo6aProps) {
  const klein = size <= 22;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      role="img"
      aria-label={title ?? 'KosmoOrbit'}
      style={style}
      className={className}
    >
      {title ? <title>{title}</title> : null}
      {klein ? <KleinVersion zustand={zustand} shellKontext={shellKontext} /> : <VollVersion zustand={zustand} />}
    </svg>
  );
}
