import { wartetAbholerText, formatDauer } from './vis-runtime';

/**
 * Fortschritt eines Render-Laufs in Worten und, wo es ihn gibt, als echte Zahl — EINE Quelle für den
 * Render-Knoten (KosmoVis, `NodeCanvas.tsx`, Form «Fläche») und den Render-Block der KosmoDesign-Insel
 * (`s-panels.tsx` `ViewportRenderBlock`, Form «Leiste»). Owner 06.10.2026: «für sämtliche dinge im node ui
 * für prozesse … eine progressbar».
 *
 * Regel G6 (U13/B2): gefüllt wird nur aus echtem Fortschritt. Die Brücke liefert drei Arten:
 * * **fein** — der Bild-Rechner schreibt je Kamera `rendert <Kamera>` mit einem Anteil, der mit jedem Schritt
 *   wächst. Das ist eine echte Zahl; sie füllt, und die Kamera steht im Text.
 * * **etappe** — Blender und der Probe-Rechner schreiben nur `rendern` mit 0,5 und `fertig` mit 1,0. Das ist
 *   keine Messung, sondern eine Wegmarke. Der Text sagt darum «Phase …» ohne Prozentzahl, und der Balken
 *   springt ehrlich von Marke zu Marke, statt eine Feinheit vorzutäuschen.
 * * **unbestimmt** — noch nichts gemeldet (unterwegs, wartet auf den Rechner, rechnet ohne Angabe). Dann
 *   atmet der Platzhalter, und beim Warten steht die Wartezeit dabei.
 *
 * **R37 (Video L5-14/16/19/20, Nr. 63/71):** meldet der Abholer `kamera_i`/`kamera_n`, ist das die echte Zahl
 * über alle Kameras — die Zeile sagt «Kamera 2 von 4 · 37 %» samt Etappe (Blender, Bildmodell, Prüfung), und mit
 * `rest_s` die geschätzte Restzeit. Vor der ersten fertigen Kamera meldet der Heim-PC `null` (er rechnet die
 * Restzeit nur aus gemessenen Dauern desselben Laufs) — dann steht «Restzeit wird geschätzt …», nie eine
 * erfundene Zahl (Owner-Entscheid 104b, Blatt 29). Bis 20.10. stand hier «Restzeit ab der zweiten Kamera»: das
 * stimmte bei einer einzigen Kamera nie, und es war nicht der Wortlaut des Blatts. `vorschau` (Artefakt des letzten fertigen Zwischenbilds) reicht die Anzeige durch; den Bildweg baut
 * der Knoten. Ohne diese Felder bleibt alles wie vorher; die Kamera-Zahl wird nie aus dem Anteil zurückgerechnet.
 */
export interface RenderWarteAnzeige {
  text: string;
  /** 0…1 nur bei echter Zahl; fehlt bei «unbestimmt». */
  fortschritt?: number;
  art: 'unbestimmt' | 'etappe' | 'fein';
  /** Artefaktname des letzten fertigen Zwischenbilds (R37 `progress.vorschau`), wenn gemeldet. */
  vorschau?: string;
  /** Blatt 29 (B): Beschriftung des Zwischenbilds, «Zwischenbild — Kamera 1, fertig». */
  vorschauText?: string;
}

/** Blatt 29 (B): der Satz am Zwischenbild. */
export const ZWISCHENBILD_BLEIBT = 'Das Zwischenbild bleibt beim Abbrechen.';

/** Blatt 29 (A): die Etappen eines Laufs in Reihe. Die Grundlage hat keinen KI-Schritt. */
const ETAPPEN_REIHE: readonly { phase: string; name: string }[] = [
  { phase: 'blender', name: 'Grundlage' },
  { phase: 'bildmodell', name: 'KI-Bild' },
  { phase: 'pruefung', name: 'Prüfung' },
];

/** «Grundlage ✓ · KI-Bild … · Prüfung»: fertig mit ✓, die laufende mit …, die offenen ohne Zeichen. `null` bei
 *  einer unbekannten Phase (die Brücke darf neue erfinden; dann steht das Wort wie bisher). */
export function etappenReihe(phase: string, stufe: 'grundlage' | 'variante' | undefined): string | null {
  const reihe = ETAPPEN_REIHE.filter((e) => stufe !== 'grundlage' || e.phase !== 'bildmodell');
  const i = reihe.findIndex((e) => e.phase === phase);
  if (i < 0) return null;
  return reihe.map((e, j) => (j < i ? `${e.name} ✓` : j === i ? `${e.name} …` : e.name)).join(' · ');
}

/** Blatt 29 (B): welche Kamera das Zwischenbild zeigt. Der Heim-PC legt es ab, sobald Blender eine Kamera fertig hat:
 *  während «blender» von Kamera i ist es die vorige, danach die eigene. */
export function zwischenbildText(p: { phase: string; kamera_i?: number | undefined }): string {
  const nr = p.kamera_i === undefined ? undefined : p.phase === 'blender' ? p.kamera_i - 1 : p.kamera_i;
  return nr !== undefined && nr >= 1 ? `Zwischenbild — Kamera ${nr}, fertig` : 'Zwischenbild — letzte fertige Kamera';
}

/** R37-Etappen des Abholers in Worten (KosmoVis-Vorschlag 20.10.2026; «KI-Bild» wie auf Blatt 29). */
const ABHOLER_ETAPPE: Record<string, string> = { blender: 'Blender', bildmodell: 'KI-Bild', pruefung: 'Prüfung' };

/** Entscheid 104b: der Satz, solange noch keine Kamera fertig ist. */
export const RESTZEIT_GESCHAETZT = 'Restzeit wird geschätzt …';

/** Restzeit in Hausschreibung wie auf Blatt 29 (D): «noch etwa 3 Min», auf ganze Minuten gerundet; darunter
 *  «noch weniger als 1 Min»; ab einer Stunde «noch etwa 1 h 5 min» (wie `formatDauer`). */
export function restzeitText(restS: number | null | undefined): string | null {
  if (restS === undefined) return null;
  if (restS === null || !Number.isFinite(restS)) return RESTZEIT_GESCHAETZT;
  const m = Math.round(Math.max(0, restS) / 60);
  if (m < 1) return 'noch weniger als 1 Min';
  if (m < 60) return `noch etwa ${m} Min`;
  const h = Math.floor(m / 60);
  return m % 60 === 0 ? `noch etwa ${h} h` : `noch etwa ${h} h ${m % 60} min`;
}

/**
 * Visbox de5e6bd: nach einem Abbruch schreibt der Heim-PC `progress.phase = "abgebrochen"` (pct bleibt,
 * `rest_s` null). Die Zeile dafuer — nie der Rohwert und nie eine Restzeit: «abgebrochen bei Kamera 2 von 3».
 * Ohne Kamera-Zahl nur «abgebrochen».
 */
export const ABGEBROCHEN_PHASE = 'abgebrochen';
export function abbruchText(p: RenderLaufAusschnitt['progress']): string {
  return p && p.kamera_i !== undefined && p.kamera_n !== undefined
    ? `abgebrochen bei Kamera ${p.kamera_i} von ${p.kamera_n}`
    : 'abgebrochen';
}

/** Ein Bild-Rechner meldet seine Kamera als «rendert <Name>» (Bild-Rechner der HomeStation). */
const FEINE_PHASE = /^rendert\s+(.+)$/;

/** Bekannte Etappen in Worten; unbekannte stehen wörtlich da (die Brücke darf neue erfinden). */
const ETAPPE_WORT: Record<string, string> = {
  rendern: 'rendern',
  fertig: 'fertig, Bild wird abgelegt',
  'an ComfyUI übergeben': 'an den Bild-Rechner übergeben',
  // KosmoVis 0.3.2: nach einem Abbruch schreibt der Abholer diese Phase (pct bleibt stehen, rest_s wird null).
  abgebrochen: 'abgebrochen',
};

/** Was die Anzeige vom Lauf braucht — bewusst schmal, damit Knoten (Status als Text) und Insel (`NodeLauf`)
 *  denselben Weg nehmen. */
export interface RenderLaufAusschnitt {
  status: string;
  gestartetUm?: number | undefined;
  progress?: { phase: string; pct: number; kamera_i?: number | undefined; kamera_n?: number | undefined; vorschau?: string | undefined; rest_s?: number | null | undefined } | undefined;
  worker?: string | undefined;
  wartetGrund?: string | undefined;
  bridgeHinweis?: string | undefined;
  /** Nr. 85: Grundlage (ohne KI-Schritt) oder Variante. */
  stufe?: 'grundlage' | 'variante' | undefined;
  /** Entscheid 104 (Antwort KosmoVis 20.10.): die am Knoten bestellte Güte — steht schon während des Laufs da. */
  bestellteGuete?: 'vorschau' | 'voll' | undefined;
}

export function renderWarteAnzeige(
  lauf: RenderLaufAusschnitt | undefined,
  jetzt: number,
): RenderWarteAnzeige | null {
  if (!lauf) return null;
  const zusatz = `${lauf.worker ? ` · ${lauf.worker}` : ''}${lauf.bridgeHinweis ? ` · ${lauf.bridgeHinweis}` : ''}`;
  const seit = lauf.gestartetUm !== undefined ? ` · seit ${formatDauer(jetzt - lauf.gestartetUm)}` : '';
  switch (lauf.status) {
    case 'gesendet':
      return { text: `Auftrag geht an die Brücke${zusatz}`, art: 'unbestimmt' };
    case 'wartetGpu':
      return { text: `${wartetAbholerText(lauf.gestartetUm, jetzt, lauf.wartetGrund)}${zusatz}`, art: 'unbestimmt' };
    case 'rendert': {
      const p = lauf.progress;
      if (!p || !Number.isFinite(p.pct)) return { text: `Bild wird gerechnet${seit}${zusatz}`, art: 'unbestimmt' };
      const anteil = Math.min(1, Math.max(0, p.pct));
      const vorschau = p.vorschau !== undefined ? { vorschau: p.vorschau, vorschauText: zwischenbildText(p) } : {};
      // Vorschau gilt nur für den KI-Schritt — also nur bei einer Variante; eine Grundlage hat keinen, und bei
      // unbekannter Stufe behaupten wir keine Vorschau.
      const guete = lauf.bestellteGuete === 'vorschau' && lauf.stufe === 'variante' ? 'Vorschau · ' : '';
      // Der Abbruch kann einen Poll lang noch als «laeuft» dastehen — dann sein Satz, keine Restzeit.
      if (p.phase === ABGEBROCHEN_PHASE) {
        return { text: `${abbruchText(p)}${zusatz}`, fortschritt: anteil, art: 'etappe', ...vorschau };
      }
      if (p.kamera_i !== undefined && p.kamera_n !== undefined) {
        const etappe = etappenReihe(p.phase, lauf.stufe) ?? ABHOLER_ETAPPE[p.phase] ?? ETAPPE_WORT[p.phase] ?? p.phase;
        const rest = restzeitText(p.rest_s);
        return {
          text: `${guete}${etappe} · Kamera ${p.kamera_i} von ${p.kamera_n} · ${Math.round(anteil * 100)} %${rest ? ` · ${rest}` : ''}${zusatz}`,
          fortschritt: anteil,
          art: 'fein',
          ...vorschau,
        };
      }
      const fein = FEINE_PHASE.exec(p.phase);
      if (fein) {
        return {
          text: `Bild wird gerechnet · Kamera «${fein[1]}» · ${Math.round(anteil * 100)} %${zusatz}`,
          fortschritt: anteil,
          art: 'fein',
          ...vorschau,
        };
      }
      return {
        text: `Phase «${ETAPPE_WORT[p.phase] ?? p.phase}» · die Brücke meldet nur Etappen${zusatz}`,
        fortschritt: anteil,
        art: 'etappe',
        ...vorschau,
      };
    }
    default:
      return null;
  }
}
