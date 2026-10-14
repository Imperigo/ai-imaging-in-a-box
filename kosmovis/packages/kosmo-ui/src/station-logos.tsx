import { useId, type CSSProperties, type ReactNode } from 'react';
import { KosmoOrbitMarke, useMarkeBewegt } from './kosmoorbit-marke';
import { moduleHue } from './tokens';

/**
 * **Die Logo-Sammlung — ein Logo je Werkzeug, eine Quelle** (Owner 30.09.2026:
 * «eine klare grafische logosammlung und soals fixe regel immer gleich
 * eingesetzt … das es nur ein KosmoOrbit logo überall gibt und jedes tool ihr
 * richtiges logo auch wirklich überall hat … das kosmoorbit logo ist ja schon
 * gut … bitte die anderen auch in diesem stil schöner und grafischer
 * ausgearbeitet und qualitätsvoller»).
 *
 * **Die Bauart kommt vom KosmoOrbit-Logo «6a»** (`logo-6a.tsx`, unverändert):
 * 48er-Raster, gestrichelte Umlaufbahn (r 17), ein Trabant als Viertelbogen
 * mit Punkt oben rechts — und in der Mitte das Zeichen. Bei 6a ist das Zeichen
 * das Neun-Quadrat; hier ist es das Bildzeichen des Werkzeugs. (Das
 * KosmoOrbit-Logo selbst ist seit 30.09.2026 die Marke mit dem A, s. unten.) Bahn und
 * Trabant sitzen bei jedem Werkzeug an DERSELBEN Stelle: das macht die Familie
 * auf einen Blick als eine erkennbar. Unterscheiden tun sich die Werkzeuge
 * durch das Bildzeichen und die Farbe (die Stationsfarbe `moduleHue`).
 *
 * **Farbe in beiden Welten.** Die Stationsfarben sind eine Garnitur für beide
 * Themen; Graphit (Draw) verschwindet auf dunklem Grund. Striche in der
 * Stationsfarbe laufen darum über `color-mix` mit der Tinte (`--k-ink`): im
 * hellen Thema wird die Farbe etwas tiefer, im dunklen etwas heller — derselbe
 * Farbton, lesbar auf beiden Gründen. Flächen tragen die Farbe halbtransparent.
 *
 * **Klein (≤ 22 px)** wie bei 6a: gröbere Striche, feine Hilfslinien weg, damit
 * das Zeichen in der Kopfzeile nicht zu Matsch verläuft.
 *
 * **KosmoOrbit** ist die Marke mit dem A (`kosmoorbit-marke.tsx`, Owner
 * 30.09.2026), animiert. **Kosmo** steht seit 30.09.2026 in derselben Familie
 * wie die Werkzeuge: flach, in coolem Rot, Version A «Schallwelle» — er zeigt,
 * ob er ruhig ist, zuhoert, denkt oder spricht (`kosmoZustand`). Beide laufen
 * über diese Komponente, damit es genau EINEN Weg zu einem Logo gibt.
 */

export type LogoId =
  | 'orbit'
  | 'kosmo'
  | 'design'
  | 'draw'
  | 'vis'
  | 'publish'
  | 'spez'
  | 'climate'
  | 'energy'
  | 'ing'
  | 'data'
  | 'prepare'
  | 'reference'
  | 'asset'
  | 'speak'
  | 'sketch'
  | 'train'
  | 'dev'
  | 'doc'
  | 'trust'
  | 'paket'
  | 'office';

/** Name je Logo — der Produktname, wie er in der Zentrale steht. */
export const LOGO_NAME: Readonly<Record<LogoId, string>> = {
  orbit: 'KosmoOrbit',
  kosmo: 'Kosmo',
  design: 'KosmoDesign',
  draw: 'KosmoDraw',
  vis: 'KosmoVis',
  publish: 'KosmoPublish',
  spez: 'KosmoSpez',
  climate: 'KosmoClimate',
  energy: 'KosmoEnergy',
  ing: 'KosmoIng',
  data: 'KosmoData',
  prepare: 'KosmoPrepare',
  reference: 'KosmoReference',
  asset: 'KosmoAsset',
  speak: 'Speak',
  sketch: 'Sketch',
  train: 'Train',
  dev: 'Dev',
  doc: 'Doc',
  trust: 'Trust',
  paket: 'Package',
  office: 'KosmoOffice',
};

/**
 * Farbe je Logo — die Stationsfarbe (`moduleHue`), seit 30.09.2026 knallig
 * (Owner: «die farbpalette allgemein darf knalliger wieder sein … nutze
 * popige farben, darf auch neon inhalte haben»; Kosmo «ein cooles rot»).
 * EINE Quelle fuer Logos und Oberflaeche. Werkzeuge ohne eigene Station
 * erben die ihrer Gruppe: Climate/Energy/Ing von KosmoSpez, Reference von
 * KosmoData; KosmoOffice (kommend) traegt ein ruhiges Grau.
 */
export const LOGO_FARBE: Readonly<Record<LogoId, string>> = {
  orbit: moduleHue.orbit,
  kosmo: moduleHue.kosmo,
  design: moduleHue.design,
  draw: moduleHue.draw,
  vis: moduleHue.vis,
  publish: moduleHue.publish,
  spez: moduleHue.spez,
  climate: moduleHue.spez,
  energy: moduleHue.spez,
  ing: moduleHue.spez,
  data: moduleHue.data,
  prepare: moduleHue.prepare,
  reference: moduleHue.data,
  asset: moduleHue.asset,
  speak: moduleHue.speak,
  sketch: moduleHue.sketch,
  train: moduleHue.train,
  dev: moduleHue.dev,
  doc: moduleHue.doc,
  trust: moduleHue.trust,
  paket: moduleHue.paket,
  office: '#9aa3b5',
};

export const LOGO_IDS = Object.keys(LOGO_NAME) as LogoId[];

/** Bis zu dieser Kantenlänge die gröbere Klein-Zeichnung (wie `logo-6a.tsx`). */
export const LOGO_KLEIN_BIS = 22;

interface Stift {
  /** Tinte (Umriss). */
  tinte: string;
  /** Strich in Stationsfarbe, auf beiden Gründen lesbar. */
  farbe: string;
  /** Fläche in Stationsfarbe, halbtransparent. */
  flaeche: string;
  /** Umriss-Strichstärke. */
  sw: number;
  klein: boolean;
}

const s = (stroke: string, strokeWidth: number, extra: CSSProperties = {}): CSSProperties => ({ stroke, strokeWidth, ...extra });
const RUND: CSSProperties = { strokeLinecap: 'round', strokeLinejoin: 'round' };

/** Das Planblatt (Publish): Blatt mit Eselsohr und Schriftfeld. */
function Planblatt(p: Stift) {
  return (
    <>
      <path d="M17 15.5H28L31.5 19V32.5H17Z" style={s(p.tinte, p.sw, RUND)} fill="none" />
      <path d="M28 15.5V19H31.5" style={s(p.tinte, p.sw * 0.7, RUND)} fill="none" />
      <rect x="23" y="26.5" width="8.5" height="6" style={s(p.farbe, p.sw * 0.9, { fill: p.flaeche })} />
      {!p.klein && <path d="M19.5 20.5H25M19.5 23.5H28" style={s(p.tinte, 1, { ...RUND, opacity: 0.6 })} />}
    </>
  );
}

function Blende(p: Stift) {
  // Sechs Lamellen: jede liegt tangential an einem Sechseck (r 4.2) und
  // endet am Aussenkreis (r 9) — die Irisblende einer Kamera.
  const lamellen: string[] = [];
  for (let i = 0; i < 6; i++) {
    const w = ((30 + i * 60) * Math.PI) / 180;
    const px = 24 + 4.2 * Math.cos(w);
    const py = 24 + 4.2 * Math.sin(w);
    const t = Math.sqrt(81 - 4.2 * 4.2);
    const qx = px + t * Math.cos(w + Math.PI / 2);
    const qy = py + t * Math.sin(w + Math.PI / 2);
    lamellen.push(`M${px.toFixed(2)} ${py.toFixed(2)}L${qx.toFixed(2)} ${qy.toFixed(2)}`);
  }
  const sechseck = Array.from({ length: 6 }, (_, i) => {
    const w = ((30 + i * 60) * Math.PI) / 180;
    return `${(24 + 4.2 * Math.cos(w)).toFixed(2)} ${(24 + 4.2 * Math.sin(w)).toFixed(2)}`;
  });
  return (
    <>
      <path d={`M${sechseck.join('L')}Z`} style={s(p.farbe, p.sw * 0.8, { fill: p.flaeche, ...RUND })} />
      {!p.klein && <path d={lamellen.join('')} style={s(p.tinte, 1.1, RUND)} fill="none" />}
      <circle cx="24" cy="24" r="9" style={s(p.tinte, p.sw)} fill="none" />
    </>
  );
}

/** Das Bildzeichen je Werkzeug, im 48er-Raster, Mitte 24/24, etwa 15…33. */
const ZEICHEN: Readonly<Record<Exclude<LogoId, 'orbit' | 'kosmo'>, (p: Stift) => ReactNode>> = {
  // KosmoDesign — der Würfel: das Modell, aus dem alles abgeleitet wird.
  design: (p) => (
    <>
      <path d="M24 15L31.8 19.5L24 24L16.2 19.5Z" style={{ fill: p.flaeche }} />
      <path d="M24 15L31.8 19.5V28.5L24 33L16.2 28.5V19.5Z" style={s(p.tinte, p.sw, RUND)} fill="none" />
      <path d="M16.2 19.5L24 24L31.8 19.5M24 24V33" style={s(p.farbe, p.sw * 0.9, RUND)} fill="none" />
    </>
  ),
  // KosmoDraw — der Grundriss: Raum mit Trennwand und Türschlag.
  draw: (p) => (
    <>
      <rect x="16" y="24" width="16" height="8" style={{ fill: p.flaeche }} />
      <rect x="16" y="16" width="16" height="16" rx="1.5" style={s(p.tinte, p.sw, RUND)} fill="none" />
      <path d="M16 24H21M26.5 24H32" style={s(p.tinte, p.sw, RUND)} fill="none" />
      <path d="M21 24V18.5" style={s(p.farbe, p.sw, RUND)} fill="none" />
      {!p.klein && <path d="M21 18.5A5.5 5.5 0 0 1 26.5 24" style={s(p.farbe, 1, { ...RUND, strokeDasharray: '1.4 1.6' })} fill="none" />}
    </>
  ),
  // KosmoVis — die Blende: das Bild, das entsteht.
  vis: Blende,
  // KosmoPublish — das Planblatt mit Schriftfeld.
  publish: Planblatt,
  // KosmoSpez — Sonne über der Welle: Energie und Klima.
  spez: (p) => (
    <>
      <circle cx="24" cy="21" r="3.6" style={s(p.farbe, p.sw * 0.8, { fill: p.flaeche })} />
      {!p.klein && (
        <path
          d={Array.from({ length: 8 }, (_, i) => {
            const w = (i * 45 * Math.PI) / 180;
            return `M${(24 + 5.6 * Math.cos(w)).toFixed(2)} ${(21 + 5.6 * Math.sin(w)).toFixed(2)}L${(24 + 7.4 * Math.cos(w)).toFixed(2)} ${(21 + 7.4 * Math.sin(w)).toFixed(2)}`;
          }).join('')}
          style={s(p.farbe, 1.1, RUND)}
          fill="none"
        />
      )}
      <path d="M15.5 30.5q2.12-2.2 4.25 0t4.25 0t4.25 0t4.25 0" style={s(p.tinte, p.sw, RUND)} fill="none" />
    </>
  ),
  // KosmoClimate — Wind: drei Züge, zwei davon eingerollt.
  climate: (p) => (
    <>
      <path d="M16 20.5H26.5A3 3 0 1 0 23.5 17.5" style={s(p.farbe, p.sw, RUND)} fill="none" />
      <path d="M16 25H29.5A2.8 2.8 0 1 1 26.7 27.8" style={s(p.tinte, p.sw, RUND)} fill="none" />
      {!p.klein && <path d="M16 29.5H22.5" style={s(p.tinte, 1.1, { ...RUND, opacity: 0.7 })} fill="none" />}
    </>
  ),
  // KosmoEnergy (kommend) — der Blitz.
  energy: (p) => <path d="M26 15L18.5 25.5H23.5L22 33L29.5 22.5H24.5Z" style={s(p.farbe, p.sw * 0.9, { fill: p.flaeche, ...RUND })} />,
  // KosmoIng (kommend) — das Doppel-T des Tragwerks.
  ing: (p) => (
    <path
      d="M17 16.5H31V19.5H25.6V28.5H31V31.5H17V28.5H22.4V19.5H17Z"
      style={s(p.tinte, p.sw * 0.9, { fill: p.flaeche, ...RUND })}
    />
  ),
  // KosmoData — der Speicher: drei Schichten Wissen.
  data: (p) => (
    <>
      <ellipse cx="24" cy="17.5" rx="8" ry="3" style={s(p.farbe, p.sw * 0.9, { fill: p.flaeche })} />
      <path d="M16 17.5V30.5A8 3 0 0 0 32 30.5V17.5" style={s(p.tinte, p.sw, RUND)} fill="none" />
      {!p.klein && <path d="M16 22A8 3 0 0 0 32 22M16 26.3A8 3 0 0 0 32 26.3" style={s(p.tinte, 1, { ...RUND, opacity: 0.6 })} fill="none" />}
    </>
  ),
  // KosmoPrepare — das Klemmbrett: Grundlagen, geprüft.
  prepare: (p) => (
    <>
      <rect x="17" y="17" width="14" height="16" rx="2" style={s(p.tinte, p.sw, RUND)} fill="none" />
      <rect x="21" y="15" width="6" height="3.6" rx="1.2" style={s(p.farbe, p.sw * 0.8, { fill: p.flaeche })} />
      <path d="M19.4 23.2L20.6 24.4L22.6 22.2M19.4 28.2L20.6 29.4L22.6 27.2" style={s(p.farbe, p.sw * 0.9, RUND)} fill="none" />
      {!p.klein && <path d="M24.6 23.4H28.8M24.6 28.4H28.8" style={s(p.tinte, 1, { ...RUND, opacity: 0.6 })} fill="none" />}
    </>
  ),
  // KosmoReference — das offene Buch mit Lesezeichen.
  reference: (p) => (
    <>
      <path d="M24 19.5C21.3 17.6 18.7 17.2 16 17.8V30.3C18.7 29.7 21.3 30 24 31.8C26.7 30 29.3 29.7 32 30.3V17.8C29.3 17.2 26.7 17.6 24 19.5Z" style={s(p.tinte, p.sw, RUND)} fill="none" />
      <path d="M24 19.5V31.8" style={s(p.tinte, p.sw * 0.8, RUND)} fill="none" />
      <path d="M27.4 17.6V23.4L28.9 22.1L30.4 23.4V17.4" style={s(p.farbe, p.sw * 0.8, { fill: p.flaeche, ...RUND })} />
    </>
  ),
  // KosmoAsset — die Bibliothek der Dinge: drei Grundkörper.
  asset: (p) => (
    <>
      <path d="M24 15.5L28.3 22.5H19.7Z" style={s(p.tinte, p.sw, RUND)} fill="none" />
      <rect x="16.5" y="25" width="6.4" height="6.4" rx="1.2" style={s(p.tinte, p.sw, RUND)} fill="none" />
      <circle cx="28.2" cy="28.2" r="3.4" style={s(p.farbe, p.sw * 0.9, { fill: p.flaeche })} />
    </>
  ),
  // Speak — die Sprechblase mit Stimme.
  speak: (p) => (
    <>
      <path d="M19 15.8H29A3 3 0 0 1 32 18.8V25.3A3 3 0 0 1 29 28.3H22.5L18.5 32V28.3A3 3 0 0 1 16 25.3V18.8A3 3 0 0 1 19 15.8Z" style={s(p.tinte, p.sw, RUND)} fill="none" />
      <path d="M20.5 20.8V23.3M23 19.2V24.9M25.5 20.2V23.9M28 21.3V22.8" style={s(p.farbe, p.sw * 1.1, RUND)} fill="none" />
    </>
  ),
  // Sketch — der freie Strich mit der Stiftspitze.
  sketch: (p) => (
    <>
      <path d="M15.8 30C18.2 22.5 21 31.2 23.6 24.4S28.2 16.6 31 19.2" style={s(p.tinte, p.sw, RUND)} fill="none" />
      {!p.klein && <path d="M17 32.6H26" style={s(p.tinte, 1, { ...RUND, opacity: 0.45 })} fill="none" />}
      <circle cx="31" cy="19.2" r="1.9" style={{ fill: p.farbe }} />
    </>
  ),
  // Train — Schicht um Schicht: die Stufen des Lernens.
  train: (p) => (
    <>
      <path d="M16 32V27.5H21V23H26V18.5H31.5V32Z" style={s(p.tinte, p.sw, { fill: p.flaeche, ...RUND })} />
      <circle cx="28.7" cy="15.6" r="1.9" style={{ fill: p.farbe }} />
    </>
  ),
  // Dev — die Werkstatt an der Software: Klammern und Schrägstrich.
  dev: (p) => (
    <>
      <path d="M20.3 18L15.5 24L20.3 30M27.7 18L32.5 24L27.7 30" style={s(p.tinte, p.sw * 1.1, RUND)} fill="none" />
      <path d="M25.8 16.5L22.2 31.5" style={s(p.farbe, p.sw * 1.2, RUND)} fill="none" />
    </>
  ),
  // Doc — Diagnose und Berichte: das Blatt mit dem Puls.
  doc: (p) => (
    <>
      <rect x="17" y="15.5" width="14" height="17" rx="2" style={s(p.tinte, p.sw, RUND)} fill="none" />
      <path d="M17 25H20.2L21.8 21L24.4 29L26.4 23.6L27.4 25H31" style={s(p.farbe, p.sw, RUND)} fill="none" />
    </>
  ),
  // Trust — das Siegel: Schild mit Haken.
  trust: (p) => (
    <>
      <path d="M24 15L31 17.8V23.5C31 28 28 31.2 24 33C20 31.2 17 28 17 23.5V17.8Z" style={s(p.tinte, p.sw, { fill: p.flaeche, ...RUND })} />
      <path d="M20.6 24L23 26.4L27.6 21.6" style={s(p.farbe, p.sw * 1.1, RUND)} fill="none" />
    </>
  ),
  // Package — das Bündel: Kiste mit Band.
  paket: (p) => (
    <>
      <path d="M16.5 20.5H31.5V32H16.5Z" style={s(p.tinte, p.sw, RUND)} fill="none" />
      <path d="M15.5 17.2H32.5V20.5H15.5Z" style={s(p.tinte, p.sw, { fill: p.flaeche, ...RUND })} />
      <path d="M24 17.2V32" style={s(p.farbe, p.sw * 1.2, RUND)} fill="none" />
      {!p.klein && <path d="M24 17.2C21.8 14 19.3 15.4 21.4 17.2M24 17.2C26.2 14 28.7 15.4 26.6 17.2" style={s(p.farbe, 1.1, RUND)} fill="none" />}
    </>
  ),
  // KosmoOffice (kommend) — das Haus der Büroarbeit.
  office: (p) => (
    <>
      <path d="M17.5 32.5V19L24.5 15.5V32.5Z" style={s(p.tinte, p.sw, { fill: p.flaeche, ...RUND })} />
      <path d="M24.5 22.5H31V32.5M15 32.5H33" style={s(p.tinte, p.sw, RUND)} fill="none" />
      {!p.klein && <path d="M20 22.5H22M20 26H22M27 26H28.6M27 29.2H28.6" style={s(p.farbe, 1.3, RUND)} fill="none" />}
    </>
  ),
};

export interface StationLogoProps {
  logo: LogoId;
  size?: number;
  /** Beschriftung fuer Vorlesen; ohne Angabe der Produktname. `''` = schmueckend. */
  beschriftung?: string;
  style?: CSSProperties;
  className?: string;
  /** Nur KosmoOrbit und Kosmo bewegen sich. Ohne Angabe: immer, ausser bei «weniger Bewegung». */
  bewegt?: boolean;
  /** Nur Kosmo: ruhig (Vorgabe), hoert zu, denkt, spricht. */
  kosmoZustand?: KosmoZustand;
  /**
   * Werkzeug-Logos: der Trabant laeuft, solange das Werkzeug aktiv ist (und
   * beim Darueberfahren ohnehin). Owner-Entscheid 01.10.2026 (B16): «Marke und
   * Kosmo immer, Werkzeuge bei Aktivitaet».
   */
  aktiv?: boolean;
  /**
   * Nur Kosmo im Zustand «spricht»: Pegel der Stimme, 0…1 (U2, Owner-Entscheid 6).
   * Gesetzt folgen Wellen und Scheibe dem Pegel statt dem festen Silbentakt;
   * ohne Bewegung (`bewegt` aus) schwingt nichts mit.
   */
  pegel?: number;
}

/**
 * Lauf des Trabanten bei Werkzeug-Logos (B16): einmal um die Bahn in 2,4 s,
 * nur beim Darueberfahren (Logo selbst oder sein Knopf) oder wenn `aktiv`.
 * Die Regeln stehen im Logo, damit es ueberall gleich wirkt, wo es steht.
 */
const WERKZEUG_LAUF = `
@keyframes k-logo-umlauf { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
svg[data-logo]:hover .k-logo-trabant,
:hover > svg[data-logo] .k-logo-trabant,
svg[data-logo][data-aktiv="ja"] .k-logo-trabant {
  transform-box: view-box;
  transform-origin: 24px 24px;
  animation: k-logo-umlauf 2.4s linear infinite;
}
`;

/**
 * Das Logo eines Werkzeugs — der EINE Weg, ein Werkzeug zu zeigen. Überall,
 * wo ein Werkzeug als Werkzeug erscheint (Zentrale, Palette, Kopf, Dock,
 * Einstellungen, Neuigkeiten …), steht diese Komponente — keine eigene
 * Zeichnung daneben (Regel: `docs/LOGO-REGEL.md`).
 */
/**
 * Was Kosmo gerade tut — das Logo zeigt es (Owner: «ein orb der mit jemandem
 * sprechen kann und animiert ist wenn er spricht»). `denkt` deckt auch
 * Schreiben und Werkzeug-Aufrufe ab (`kosmoZustandAusStatus` in der App).
 */
export type KosmoZustand = 'ruhig' | 'hoert' | 'denkt' | 'spricht';

const KOSMO_KEYFRAMES = `
@keyframes k-kosmo-welle { from { transform: scale(.72); opacity: .9; } to { transform: scale(1.35); opacity: 0; } }
@keyframes k-kosmo-sog { from { transform: scale(1.4); opacity: 0; } 55% { opacity: .85; } to { transform: scale(.7); opacity: 0; } }
@keyframes k-kosmo-atem { 0%, 100% { transform: scale(.95); } 50% { transform: scale(1.05); } }
@keyframes k-kosmo-silbe { 0%, 100% { transform: scale(1); } 30% { transform: scale(1.14); } 60% { transform: scale(.97); } }
@keyframes k-kosmo-kreisen { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
`;

/**
 * Kosmo — **Version A «Schallwelle»** (Owner 30.09.2026: «version A ist
 * schönstes»; vorher: «die kugel wird wieder 2d, nicht diesen 3d effekt»).
 * Flach, in coolem Rot, mit derselben Bahn und demselben Trabanten wie die
 * Werkzeuge. In der Mitte eine Scheibe mit zwei ruhigen Ringen.
 *
 * * **ruhig** — alles steht still, die Ringe leise (Owner G1, 01.10.2026: in Ruhe bewegt sich nichts).
 * * **hoert** — Ringe laufen von aussen in die Scheibe hinein: Kosmo saugt die
 *   Information auf (Owner 30.09.2026: «beim hört zu … die animationsströmung
 *   vom orb nach innen, als würde er info aufsaugen»).
 * * **denkt** — ein gestrichelter Ring kreist, die Scheibe atmet schneller.
 * * **spricht** — Ringe laufen rasch nach aussen, die Scheibe schlaegt im Silbentakt.
 */
function KosmoZeichen({ p, laeuft, zustand, pegel }: { p: Stift; laeuft: boolean; zustand: KosmoZustand; pegel?: number }) {
  const wellen = laeuft && (zustand === 'hoert' || zustand === 'spricht');
  const dauer = zustand === 'spricht' ? 1.4 : 2.4;
  // Der Pegel kommt alle ~50 ms neu; er wird direkt gesetzt, ohne Uebergang,
  // damit die Scheibe der Stimme folgt und ihr nicht nachlaeuft.
  const stimme =
    laeuft && zustand === 'spricht' && pegel !== undefined && Number.isFinite(pegel) ? Math.min(1, Math.max(0, pegel)) : undefined;
  const kernAnimation = !laeuft
    ? undefined
    : zustand === 'spricht'
      ? stimme !== undefined
        ? undefined
        : 'k-kosmo-silbe .5s ease-in-out infinite'
      : zustand === 'denkt'
        ? 'k-kosmo-atem 1.6s ease-in-out infinite'
        : // «ruhig» steht still (Owner-Abstimmung G1, 01.10.2026): Bewegung
          // heisst immer «da passiert etwas». Vorher atmete er in 4,8 s.
          undefined;
  return (
    <>
      {wellen ? (
        <g data-kosmo-wellen="" style={stimme !== undefined ? { transformOrigin: '24px 24px', transform: `scale(${(0.8 + 0.5 * stimme).toFixed(3)})` } : undefined}>
        {[0, 1, 2].map((i) => (
          <circle
            key={i}
            cx="24"
            cy="24"
            r="10"
            fill="none"
            style={{
              stroke: p.farbe,
              strokeWidth: zustand === 'spricht' ? 1.6 : 1.1,
              transformOrigin: '24px 24px',
              animation: `${zustand === 'hoert' ? 'k-kosmo-sog' : 'k-kosmo-welle'} ${dauer}s ${zustand === 'hoert' ? 'ease-in' : 'ease-out'} ${(-i * dauer) / 3}s infinite`,
            }}
          />
        ))}
        </g>
      ) : (
        <>
          <circle cx="24" cy="24" r="10.5" fill="none" style={{ stroke: p.farbe, strokeWidth: p.klein ? 1.6 : 1.1, opacity: 0.45 }} />
          {!p.klein && <circle cx="24" cy="24" r="13.4" fill="none" style={{ stroke: p.farbe, strokeWidth: 0.9, opacity: 0.2 }} />}
        </>
      )}
      {laeuft && zustand === 'denkt' ? (
        <circle
          cx="24"
          cy="24"
          r="12.2"
          fill="none"
          style={{ stroke: p.farbe, strokeWidth: 1.2, strokeDasharray: '3 5', strokeLinecap: 'round', transformOrigin: '24px 24px', animation: 'k-kosmo-kreisen 2.4s linear infinite' }}
        />
      ) : null}
      <circle
        data-kosmo-kern=""
        cx="24"
        cy="24"
        r="7"
        style={{
          fill: p.farbe,
          transformOrigin: '24px 24px',
          ...(kernAnimation ? { animation: kernAnimation } : {}),
          ...(stimme !== undefined ? { transform: `scale(${(0.94 + 0.28 * stimme).toFixed(3)})` } : {}),
        }}
      />
    </>
  );
}

export function StationLogo({ logo, size = 28, beschriftung, style, className, bewegt: bewegtVorgabe, kosmoZustand = 'ruhig', aktiv = false, pegel }: StationLogoProps) {
  const name = beschriftung ?? LOGO_NAME[logo];
  const roh = useId().replace(/[^a-zA-Z0-9_-]/g, '');
  const kannBewegen = useMarkeBewegt();
  const bewegt = bewegtVorgabe ?? kannBewegen;
  if (logo === 'orbit') {
    return (
      <KosmoOrbitMarke
        size={size}
        beschriftung={name}
        {...(bewegtVorgabe !== undefined ? { bewegt: bewegtVorgabe } : {})}
        aktiv={aktiv}
        {...(style !== undefined ? { style } : {})}
        {...(className !== undefined ? { className } : {})}
      />
    );
  }
  const klein = size <= LOGO_KLEIN_BIS;
  const hue = LOGO_FARBE[logo];
  const stift: Stift = {
    tinte: 'var(--k-ink)',
    farbe: `color-mix(in oklab, ${hue} 84%, var(--k-ink))`,
    flaeche: `color-mix(in srgb, ${hue} 30%, transparent)`,
    sw: klein ? 2.3 : 1.45,
    klein,
  };
  const glanz = `k-logo-glanz-${roh}`;
  const istKosmo = logo === 'kosmo';
  const zeichen = istKosmo ? <KosmoZeichen p={stift} laeuft={bewegt} zustand={kosmoZustand} {...(pegel !== undefined ? { pegel } : {})} /> : ZEICHEN[logo](stift);
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      {...(name ? { role: 'img', 'aria-label': name } : { 'aria-hidden': true })}
      data-logo={logo}
      {...(istKosmo ? {} : { 'data-aktiv': aktiv ? 'ja' : 'nein' })}
      style={style}
      className={className}
    >
      {name ? <title>{name}</title> : null}
      {istKosmo && bewegt ? <style>{KOSMO_KEYFRAMES}</style> : null}
      {!istKosmo && bewegt ? <style>{WERKZEUG_LAUF}</style> : null}
      <defs>
        {/* Neon-Schein: ein weicher Hof in der Werkzeugfarbe, hinter dem
            Trabanten (und bei Kosmo hinter dem Kern). */}
        <radialGradient id={glanz}>
          <stop offset="0%" style={{ stopColor: hue, stopOpacity: 0.6 }} />
          <stop offset="100%" style={{ stopColor: hue, stopOpacity: 0 }} />
        </radialGradient>
      </defs>
      {/* Umlaufbahn — dieselbe gestrichelte Bahn bei jedem Werkzeug. */}
      <circle
        cx="24"
        cy="24"
        r="17"
        stroke="var(--k-ink)"
        strokeWidth={klein ? 2 : 1.5}
        strokeDasharray={klein ? '3 4.6' : '2 4'}
        strokeLinecap="round"
        opacity={klein ? 0.55 : 0.45}
      />
      {/* Trabant — an derselben Stelle bei jedem Werkzeug, in seiner Farbe, mit Neon-Schein. */}
      <g className="k-logo-trabant">
        <path d="M24 7A17 17 0 0 1 41 24" style={{ stroke: stift.farbe }} strokeWidth={klein ? 2.6 : 2.2} strokeLinecap="round" />
        <circle cx="40.3" cy="9.9" r={klein ? 4.6 : 4.2} fill={`url(#${glanz})`} />
        <circle cx="40.3" cy="9.9" r={klein ? 2.2 : 1.8} style={{ fill: stift.farbe }} />
      </g>
      {/* Klein: das Zeichen etwas grösser in die Bahn — sonst geht es bei 18 px
          neben Bahn und Trabant unter. */}
      {klein ? <g transform="translate(24 24) scale(1.22) translate(-24 -24)">{zeichen}</g> : zeichen}
    </svg>
  );
}

/**
 * Welches Logo ein Hauptwerkzeug der Zentrale trägt (`ORBIT_HAUPTWERKZEUGE`,
 * `orbit-werkzeuge.ts`). Untertools laufen über ihre Station
 * (`LOGO_FUER_STATION`) — die Kennungen beider Ebenen überschneiden sich
 * (`spez` ist Hauptwerkzeug UND Untertool-Kennung von KosmoClimate), darum
 * zwei Tabellen statt einer.
 */
export const LOGO_FUER_HAUPTWERKZEUG: Readonly<Record<string, LogoId>> = {
  design: 'design',
  spez: 'spez',
  data: 'data',
  kosmo: 'kosmo',
  office: 'office',
};

/**
 * Welches Logo eine offene STATION trägt (`ModuleId`, z. B. im Kopf der
 * Insel). `design` ist die Zeichenfläche — also KosmoDraw; `data` der
 * Datenraum — also KosmoReference; `spez` heute KosmoClimate.
 */
export const LOGO_FUER_STATION: Readonly<Record<string, LogoId>> = {
  orbit: 'orbit',
  kosmo: 'kosmo',
  design: 'draw',
  draw: 'draw',
  vis: 'vis',
  publish: 'publish',
  prepare: 'prepare',
  data: 'reference',
  asset: 'asset',
  spez: 'climate',
  speak: 'speak',
  sketch: 'sketch',
  train: 'train',
  dev: 'dev',
  doc: 'doc',
  trust: 'trust',
  paket: 'paket',
};
