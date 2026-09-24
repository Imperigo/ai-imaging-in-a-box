import type { CSSProperties } from 'react';
import { Logo6a } from './logo-6a';
import { moduleHue, type ModuleId } from './tokens';

/**
 * KosmoOrbit — Orbital-Logo-System.
 *
 * Konstruktion: ein präziser Ring (die Umlaufbahn) mit einem Planetenpunkt und
 * einer feinen Achslinie — gezeichnet wie mit dem Zirkel auf Transparentpapier.
 * Jedes Modul erbt dieselbe Konstruktion und setzt seinen Punkt an eine andere
 * Position der Bahn; der Farbton kommt aus moduleHue. Dadurch bleibt die ganze
 * Familie erkennbar EIN System.
 */

const orbitAngle: Record<ModuleId, number> = {
  orbit: -90,
  design: -30,
  draw: 30,
  data: 90,
  vis: 150,
  publish: 210,
  prepare: 270,
  kosmo: -90,
  train: 330,
  doc: 60,
  sketch: 120,
  speak: 240,
  asset: 180,
  dev: 300,
  trust: 0,
  paket: 165,
  // P-SPEZ: freie Bahn-Position (45°), kollidiert mit keinem Bestandswinkel.
  spez: 45,
};

export interface OrbitMarkProps {
  module?: ModuleId;
  size?: number;
  /** Tintenfarbe des Rings; Standard erbt currentColor. */
  stroke?: string;
  style?: CSSProperties;
  className?: string;
  title?: string;
}

export function OrbitMark({
  module = 'orbit',
  size = 28,
  stroke = 'currentColor',
  style,
  className,
  title,
}: OrbitMarkProps) {
  // v0.7.2 §2 (Paket 01): die App-Identität selbst (`module="orbit"`) ist
  // jetzt das Logo «6a» — API (module/size/…) bleibt exakt bestehen, nur die
  // Zeichnung dahinter wechselt. Alle anderen Modul-Werte (kosmo, design,
  // draw, …) behalten die bisherige Ring+Trabant-Konstruktion unverändert
  // (eigene Modul-Identität, ausserhalb des «6a ist die Marke»-Auftrags).
  if (module === 'orbit') {
    return (
      <Logo6a
        size={size}
        {...(style !== undefined ? { style } : {})}
        {...(className !== undefined ? { className } : {})}
        {...(title !== undefined ? { title } : {})}
      />
    );
  }
  const hue = moduleHue[module];
  const a = (orbitAngle[module] * Math.PI) / 180;
  const R = 11;
  const cx = 16 + R * Math.cos(a);
  const cy = 16 + R * Math.sin(a);
  const isKosmo = module === 'kosmo';
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      role="img"
      aria-label={title ?? `Kosmo ${module}`}
      style={style}
      className={className}
    >
      {title ? <title>{title}</title> : null}
      <circle cx="16" cy="16" r={R} stroke={stroke} strokeWidth="1.4" />
      {/* Achskreuz der Konstruktion — hauchfein, wie Vorzeichnung */}
      <path d="M16 3.4v4.2M16 24.4v4.2M3.4 16h4.2M24.4 16h4.2" stroke={stroke} strokeWidth="0.7" opacity="0.45" />
      {isKosmo ? (
        // Kosmo: der Kern selbst pulsiert im Zentrum, kein Trabant
        <>
          <circle cx="16" cy="16" r="4.4" fill={hue} />
          <circle cx="16" cy="16" r="6.8" stroke={hue} strokeWidth="0.8" opacity="0.5" />
        </>
      ) : (
        <>
          <circle cx="16" cy="16" r="1.6" fill={stroke} opacity="0.8" />
          <circle cx={cx} cy={cy} r="3.1" fill={hue} />
        </>
      )}
    </svg>
  );
}

export interface WordmarkProps {
  size?: number;
  style?: CSSProperties;
  /** Versions-Exponent, z.B. «v0.6.0». Fehlt er, steht «V1» (Rückwärtskompat). */
  version?: string;
}

/** Wortmarke «KosmoOrbit» — v0.7.2 §2: Plakat-Schrift (`--k-font-titel`,
 *  Tracking .28em) statt der bisherigen feinen Grotesk-Tracking von 0.01em —
 *  API/DOM/`app-version`-Testid bleiben ein bestehender Vertrag, exakt. */
export function Wordmark({ size = 18, style, version }: WordmarkProps) {
  return (
    <span
      style={{
        fontSize: size,
        fontFamily: 'var(--k-font-titel)',
        letterSpacing: '0.28em',
        fontWeight: 'var(--k-gewicht-stark)',
        display: 'inline-flex',
        alignItems: 'baseline',
        gap: 6,
        ...style,
      }}
    >
      Kosmo<span style={{ fontWeight: 'var(--k-gewicht-normal)' }}>Orbit</span>
      <sup data-testid="app-version" style={{ fontSize: size * 0.55, opacity: 0.55, fontWeight: 'var(--k-gewicht-normal)' }}>
        {version ?? 'V1'}
      </sup>
    </span>
  );
}
