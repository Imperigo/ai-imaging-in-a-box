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
 * Die Kamera-Zahl «i von n» liefert die Brücke heute nicht (nur den Namen in der Phase); sie wird darum nicht
 * aus dem Anteil zurückgerechnet.
 */
export interface RenderWarteAnzeige {
  text: string;
  /** 0…1 nur bei echter Zahl; fehlt bei «unbestimmt». */
  fortschritt?: number;
  art: 'unbestimmt' | 'etappe' | 'fein';
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
  progress?: { phase: string; pct: number } | undefined;
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
      const fein = FEINE_PHASE.exec(p.phase);
      if (fein) {
        return {
          text: `Bild wird gerechnet · Kamera «${fein[1]}» · ${Math.round(anteil * 100)} %${zusatz}`,
          fortschritt: anteil,
          art: 'fein',
        };
      }
      return {
        text: `Phase «${ETAPPE_WORT[p.phase] ?? p.phase}» · die Brücke meldet nur Etappen${zusatz}`,
        fortschritt: anteil,
        art: 'etappe',
      };
    }
    default:
      return null;
  }
}
