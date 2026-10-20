import { KTooltip } from '@kosmo/ui';
import type { Guete } from './guete';
import './vis-visual.css';

/**
 * Vermerk «Vorschau» an einem Render-Bild (Entscheide 104/104a, Absprache UI/KosmoVis 20.10.2026):
 * ein Vorschaubild darf nirgends wie ein volles aussehen — gleich wie bei der `LizenzOffenMarke`.
 *
 * Gelesen wird, was das ERGEBNIS meldet (`NodeLauf.guete` aus `result.guete`), nicht was bestellt war;
 * fehlt das Feld, gilt voll, und es steht nichts da. Die Plakette liegt IM Bild (unten links; oben links
 * stehen die Abzeichen «LAUF n»), damit der Knoten nicht wächst (KV-B5-Register). Sie nimmt keinen Zeiger
 * ausser für die Kurzhilfe und sperrt nichts.
 *
 * Am Verlaufs-Daumen (32 px hoch) passt das Wort nicht in seine Box (UI-Regel 2), eine Abkürzung verbietet
 * Regel 3: dort trägt der Daumen den gestrichelten Rahmen (`vis-verlauf-daumen--vorschau`) als Zeichen, und
 * der Knopfname sagt «Vorschau» (`gueteZusatz`).
 */

export const GUETE_MARKE_TEXT = 'Vorschau';
export const GUETE_MARKE_HINWEIS =
  'Vorschau: schnell gerechnet (Z-Image Turbo, weniger Schritte, kleineres KI-Bild) — kein fertiger Render. Für das fertige Bild am Knoten «Güte: Voll» wählen und die Variante neu rechnen.';

export function istVorschau(lauf: { guete?: Guete | undefined } | null | undefined): boolean {
  return lauf?.guete === 'vorschau';
}

/** Zusatz für Knopfnamen und Alternativtexte: «, Vorschau» oder nichts. */
export function gueteZusatz(lauf: { guete?: Guete | undefined } | null | undefined): string {
  return istVorschau(lauf) ? `, ${GUETE_MARKE_TEXT}` : '';
}

export function GueteMarke({ lauf, testid }: { lauf: { guete?: Guete | undefined } | null | undefined; testid: string }) {
  if (!istVorschau(lauf)) return null;
  return (
    <KTooltip text={GUETE_MARKE_HINWEIS} className="vis-guete-marke-huelle" lage="oben">
      <span tabIndex={0} className="vis-guete-marke" data-testid={testid} data-guete="vorschau">
        {GUETE_MARKE_TEXT}
      </span>
    </KTooltip>
  );
}
