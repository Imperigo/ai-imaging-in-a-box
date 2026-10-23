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
/** Der Vorbehalt am Anfang der Kurzhilfe (Visbox-Ergebnis auf-20261023-346): Die Vorschau rechnet ohne das Grundbild als
 *  Bildeingang; am Testhaus übermalte sie das Fensterband im OG und die Bäume, während die volle Güte beides hielt. Die
 *  Fensterprüfung und die Deckung melden das erst im Befund — der Satz sagt es schon an der Marke. */
export const GUETE_VORBEHALT = 'Vorschau — Fenster und Form nicht gesichert';
export const GUETE_MARKE_HINWEIS =
  `${GUETE_VORBEHALT}: schnell gerechnet (Z-Image Turbo, weniger Schritte, kleineres KI-Bild, ohne das Grundbild als Bildeingang) — sie kann Fenster übermalen und von der Form abweichen; kein fertiger Render. Für das fertige Bild am Knoten «Güte: Voll» wählen und die Variante neu rechnen.`;

/** Alles, was ein Bild beschreibt (Lauf, Verlaufseintrag, Kuratier-Quelle); Quellen ohne `guete` (z. B. ein
 *  eingefügtes Bild) gelten als voll. */
export type MitGuete = { guete?: Guete | undefined } | object | null | undefined;

export function istVorschau(lauf: MitGuete): boolean {
  return typeof lauf === 'object' && lauf !== null && (lauf as { guete?: unknown }).guete === 'vorschau';
}

/** Zusatz für Knopfnamen und Alternativtexte: «, Vorschau» oder nichts. */
export function gueteZusatz(lauf: MitGuete): string {
  return istVorschau(lauf) ? `, ${GUETE_MARKE_TEXT}` : '';
}

/**
 * `form`: «bild» (Vorgabe) liegt unten links IM Bild; «abzeichen» steht in einer Abzeichenreihe wie «FAVORIT»
 * (Kuratier-Karte, Vergleich); «zeile» steht als Vorbehaltszeile unter dem Bild wie die Lizenz-Marke (Inspektor,
 * Bildkachel, Blatt-Knoten).
 */
export function GueteMarke({
  lauf,
  testid,
  form = 'bild',
}: {
  lauf: MitGuete;
  testid: string;
  form?: 'bild' | 'abzeichen' | 'zeile';
}) {
  if (!istVorschau(lauf)) return null;
  return (
    <KTooltip text={GUETE_MARKE_HINWEIS} className={`vis-guete-marke-huelle vis-guete-marke-huelle--${form}`} lage={form === 'bild' ? 'oben' : 'unten'}>
      <span tabIndex={0} className="vis-guete-marke" data-testid={testid} data-guete="vorschau" data-form={form}>
        {GUETE_MARKE_TEXT}
      </span>
    </KTooltip>
  );
}
