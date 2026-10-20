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
}

/** R37-Etappen des Abholers in Worten (KosmoVis-Vorschlag 20.10.2026; «KI-Bild» wie auf Blatt 29). */
const ABHOLER_ETAPPE: Record<string, string> = { blender: 'Blender', bildmodell: 'KI-Bild', pruefung: 'Prüfung' };

/** Entscheid 104b: der Satz, solange noch keine Kamera fertig ist. */
export const RESTZEIT_GESCHAETZT = 'Restzeit wird geschätzt …';

/** Restzeit in Worten: «noch etwa 1 min 20 s»; Sekunden unter einer Minute auf 5 s gerundet. */
export function restzeitText(restS: number | null | undefined): string | null {
  if (restS === undefined) return null;
  if (restS === null || !Number.isFinite(restS)) return RESTZEIT_GESCHAETZT;
  const s = Math.max(0, Math.round(restS));
  if (s < 60) return `noch etwa ${Math.max(5, Math.round(s / 5) * 5)} s`;
  const m = Math.floor(s / 60);
  const rest = s % 60;
  return rest > 0 ? `noch etwa ${m} min ${rest} s` : `noch etwa ${m} min`;
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
      const vorschau = p.vorschau !== undefined ? { vorschau: p.vorschau } : {};
      // Der Abbruch kann einen Poll lang noch als «laeuft» dastehen — dann sein Satz, keine Restzeit.
      if (p.phase === ABGEBROCHEN_PHASE) {
        return { text: `${abbruchText(p)}${zusatz}`, fortschritt: anteil, art: 'etappe', ...vorschau };
      }
      if (p.kamera_i !== undefined && p.kamera_n !== undefined) {
        const etappe = ABHOLER_ETAPPE[p.phase] ?? ETAPPE_WORT[p.phase] ?? p.phase;
        const rest = restzeitText(p.rest_s);
        return {
          text: `${etappe} · Kamera ${p.kamera_i} von ${p.kamera_n} · ${Math.round(anteil * 100)} %${rest ? ` · ${rest}` : ''}${zusatz}`,
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
