import { useId } from 'react';
import type { CSSProperties } from 'react';
import { KosmoOrbitMarke } from './kosmoorbit-marke';
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

/**
 * **OrbitKern — die EINE Orb-Zeichnung (Owner-Abnahme 21.09.2026).**
 *
 * Der Owner, wörtlich: «der kosmoorbit orb ist aktuell nicht derselbe wie der
 * in den tools selbst..dito und beide vielleicht schoener oder? und nicht soo
 * gross wie jetzt». Gemeint sind zwei Zeichnungen desselben Dings: das
 * statische Zeichen der Zentrale (`OrbitMark module="kosmo"`, bis hierher
 * Ring + Achskreuz + Kern + Halo im 32er-Raster) und der lebende Orb im
 * Gespräch (`apps/kosmo-orbit/src/shell/KosmoOrb.tsx`).
 *
 * Dieses Bauteil ist die abgenommene Zeichnung, **einmal**, im 100er-Raster:
 * Schein → Bahn A (−24°, Trabant in der Akzentfarbe) → Bahn B (46°,
 * gegenläufig, Trabant in `moduleHue.kosmo`) → Kern. Bahn und Trabant liegen
 * je in DERSELBEN Gruppe, die Gruppe trägt die Drehung — sonst liefe der
 * Trabant der Bahn davon.
 *
 * **Zwei Grössen, eine Zeichnung.** `bewegt` entscheidet allein über die
 * Bewegung, nicht über die Form: der grosse Orb dreht (Bahn A 34 s, Bahn B
 * 52 s gegenläufig, Kern atmet 5.2 s, Schein 7 s), der kleine in der
 * Kopfzeile steht still. Vorgabe ist `size >= ORBITKERN_BEWEGT_AB` — beide
 * heutigen `module="kosmo"`-Aufrufer (24 px im KosmoPanel-Kopf, 26 px in
 * `ErsteStartFrage`) liegen darunter und stehen damit still, wie verlangt.
 *
 * **Klein-Variante (`size <= ORBITKERN_KLEIN_BIS`).** Nachgemessen an einem
 * echten Anstrich (Chromium-Raster des gerenderten Bauteils, nicht am
 * Quelltext geschätzt): im 100er-Raster ist ein Strich von 1.6 bei 24 px
 * Kantenlänge 0.38 px breit — die Bahnen verschwinden, und der weiche Schein
 * legt sich als Nebel über den Rest. Das ist dasselbe Problem, das
 * `logo-6a.tsx` schon kennt («Rasterlinien weg, gröbere Striche, damit die
 * Konstruktion bei winzigen Grössen nicht zu Matsch verläuft») — und darum
 * dieselbe Antwort: gröbere Striche, grössere Trabanten, engerer Schein. Die
 * Konstruktion selbst bleibt Strich für Strich dieselbe.
 *
 * **prefers-reduced-motion:** KEINE eigene Regel. Das Haus hat dafür genau
 * eine Konvention — den globalen Riegel in `aura.css`
 * (`@media (prefers-reduced-motion: reduce)` auf `*`, der jede
 * `animation-duration`/`-delay` kappt). `logo-6a.tsx` verlässt sich im selben
 * Paket schon darauf («kein Sonderfall hier nötig»); eine zweite Media-Query
 * hier wäre die zweite Quelle für dieselbe Frage.
 *
 * Dass das hier gefahrlos ist, liegt an der Wahl der Keyframes und ist kein
 * Zufall: beide Bahnen drehen um GENAU eine volle Umdrehung (−24° → 336°,
 * 46° → −314°). Der Riegel kappt die Dauer auf 0.01 ms, die Bahn steht damit
 * faktisch — und zwar auf demselben Winkel, auf dem sie ohne Bewegung stünde,
 * weil Anfang und Ende modulo 360° derselbe Winkel sind. Ein reduced-motion-
 * Anstrich sieht darum aus wie die stille Klein-Variante, nicht wie eine
 * eingefrorene Zufallsstellung.
 *
 * **Warum die Keyframes in einem `<style>`-Block und nicht in `aura.css`:**
 * `aura.css` lag ausserhalb des Dateikreises dieses Pakets. Der scoped
 * `<style>`-Block ist die im Haus bereits benutzte Ausweichform für genau
 * diesen Fall (`modules/design/ViewportChrome.tsx`,
 * `ViewportKontextmenue.tsx`). Die Namen tragen das `k-orbitkern-`-Präfix,
 * kollidieren also mit keinem bestehenden Keyframe.
 */
const ORBITKERN_KEYFRAMES = `
@keyframes k-orbitkern-bahn-a { from { transform: rotate(-24deg); } to { transform: rotate(336deg); } }
@keyframes k-orbitkern-bahn-b { from { transform: rotate(46deg); } to { transform: rotate(-314deg); } }
@keyframes k-orbitkern-atem { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.04); } }
@keyframes k-orbitkern-schein { 0%, 100% { opacity: .78; } 50% { opacity: 1; } }
`;

/** Ab dieser Kantenlänge dreht der Orb (darunter: still — die Kopfzeile). */
export const ORBITKERN_BEWEGT_AB = 44;

/** Bis zu dieser Kantenlänge greift die gröbere Klein-Variante (s.o.). */
export const ORBITKERN_KLEIN_BIS = 32;

export interface OrbitKernProps {
  size?: number;
  /** Akzentfarbe `a` — Schein, Bahn A, ihr Trabant und der Kern. */
  akzent?: string;
  /** Erzwingt Bewegung an/aus. Ohne Angabe: `size >= ORBITKERN_BEWEGT_AB`. */
  bewegt?: boolean;
}

export function OrbitKern({ size = 28, akzent = moduleHue.kosmo, bewegt }: OrbitKernProps) {
  // Eigene Verlaufs-IDs je Instanz: zwei Orbs auf derselben Seite dürfen sich
  // die `url(#…)`-Referenzen nicht gegenseitig wegnehmen. React 19s `useId`
  // liefert Zeichen, die in einem Fragment-Bezeichner nichts zu suchen haben
  // («r0»-Form) — darum hier auf [A-Za-z0-9_-] eingedampft.
  const roh = useId().replace(/[^a-zA-Z0-9_-]/g, '');
  const glut = `k-orbitkern-glut-${roh}`;
  const kern = `k-orbitkern-kern-${roh}`;
  const laeuft = bewegt ?? size >= ORBITKERN_BEWEGT_AB;
  const klein = size <= ORBITKERN_KLEIN_BIS;
  const bahnStrich = klein ? 4 : 1.6;
  const dreh = (name: string, dauer: string): CSSProperties =>
    laeuft ? { transformOrigin: '50px 50px', animation: `${name} ${dauer} linear infinite` } : { transformOrigin: '50px 50px' };

  return (
    <>
      {laeuft ? <style>{ORBITKERN_KEYFRAMES}</style> : null}
      <defs>
        <radialGradient id={glut}>
          <stop offset="0%" stopColor={akzent} stopOpacity="0.55" />
          <stop offset="55%" stopColor={akzent} stopOpacity="0.12" />
          <stop offset="100%" stopColor={akzent} stopOpacity="0" />
        </radialGradient>
        <radialGradient id={kern} cx="36%" cy="32%">
          <stop offset="0%" stopColor="var(--k-raised, #fff)" />
          <stop offset="100%" stopColor={akzent} />
        </radialGradient>
      </defs>

      {/* Schein */}
      <circle
        cx="50"
        cy="50"
        r={klein ? 33 : 41}
        fill={`url(#${glut})`}
        style={laeuft ? { animation: 'k-orbitkern-schein 7s ease-in-out infinite' } : undefined}
      />

      {/* Bahn A (−24°) samt Trabant — EINE Gruppe, die Gruppe dreht. */}
      <g style={dreh('k-orbitkern-bahn-a', '34s')} transform={laeuft ? undefined : 'rotate(-24 50 50)'}>
        <ellipse cx="50" cy="50" rx="40" ry="14.5" fill="none" stroke={akzent} strokeWidth={bahnStrich} opacity={klein ? 0.6 : 0.45} />
        <circle cx="90" cy="50" r={klein ? 5 : 3.4} fill={akzent} />
      </g>

      {/* Bahn B (46°, gegenläufig) samt Trabant in Kosmos Karmin-Rosé. */}
      <g style={dreh('k-orbitkern-bahn-b', '52s')} transform={laeuft ? undefined : 'rotate(46 50 50)'}>
        <ellipse cx="50" cy="50" rx="29" ry="10" fill="none" stroke={akzent} strokeWidth={bahnStrich} opacity={klein ? 0.45 : 0.3} />
        <circle cx="21" cy="50" r={klein ? 4 : 2.6} fill={moduleHue.kosmo} />
      </g>

      {/* Kern */}
      <circle
        cx="50"
        cy="50"
        r="15"
        fill={`url(#${kern})`}
        style={
          laeuft
            ? { transformOrigin: '50px 50px', animation: 'k-orbitkern-atem 5.2s ease-in-out infinite' }
            : undefined
        }
      />
    </>
  );
}

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
  // Owner 30.09.2026: «das aktuelle kosmoorbit logo ist noch falsch, ich
  // möchte das mit dem A in der mitte» — die App-Identität (`module="orbit"`)
  // ist jetzt die Marke mit dem A (`kosmoorbit-marke.tsx`), animiert. Bis
  // dahin stand hier Logo «6a» (v0.7.2); `logo-6a.tsx` bleibt fuer den
  // Schaukasten stehen, wird aber von keinem KosmoOrbit-Logo mehr gezeigt.
  if (module === 'orbit') {
    return (
      <KosmoOrbitMarke
        size={size}
        {...(title !== undefined ? { beschriftung: title } : {})}
        {...(style !== undefined ? { style } : {})}
        {...(className !== undefined ? { className } : {})}
      />
    );
  }
  const hue = moduleHue[module];
  const a = (orbitAngle[module] * Math.PI) / 180;
  const R = 11;
  const cx = 16 + R * Math.cos(a);
  const cy = 16 + R * Math.sin(a);
  const isKosmo = module === 'kosmo';
  // Owner-Abnahme 21.09.2026: das Zeichen der Zentrale (`module="kosmo"`) ist
  // jetzt `OrbitKern` — dieselbe, EINE Orb-Zeichnung, im 100er-Raster. Die
  // API (module/size/stroke/style/className/title) und der DOM-Vertrag
  // ringsum (`role="img"`, `aria-label`, optionales `<title>`) bleiben exakt;
  // nur die Zeichnung im `kosmo`-Zweig wechselt, und mit ihr die ViewBox.
  // Die übrigen 16 Modul-Werte behalten ihre Ring+Trabant-Konstruktion mit
  // der modul-eigenen Bahnposition (`orbitAngle`) unverändert — sie war nicht
  // Teil der Abnahme, und ihre Bahnposition ist das Unterscheidungsmerkmal
  // der Familie.
  return (
    <svg
      width={size}
      height={size}
      viewBox={isKosmo ? '0 0 100 100' : '0 0 32 32'}
      fill="none"
      role="img"
      aria-label={title ?? `Kosmo ${module}`}
      style={style}
      className={className}
    >
      {title ? <title>{title}</title> : null}
      {isKosmo ? (
        <OrbitKern size={size} akzent={hue} />
      ) : (
        <>
          <circle cx="16" cy="16" r={R} stroke={stroke} strokeWidth="1.4" />
          {/* Achskreuz der Konstruktion — hauchfein, wie Vorzeichnung */}
          <path d="M16 3.4v4.2M16 24.4v4.2M3.4 16h4.2M24.4 16h4.2" stroke={stroke} strokeWidth="0.7" opacity="0.45" />
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
