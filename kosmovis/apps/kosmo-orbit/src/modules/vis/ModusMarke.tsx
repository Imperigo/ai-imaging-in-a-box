import { KTooltip } from '@kosmo/ui';
import { MODUS_MARKE_TEXT, MODUS_NICHT_GEMELDET_HINWEIS, MODUS_NICHT_GEMELDET_TEXT, modusAus, modusMarkeArt, modusTooltip } from './modus-marke';
import './vis-visual.css';

/**
 * Vermerk «Ohne Grundlagenbild» / «Anders gerechnet» an einem Render-Bild (Blatt 21.10.2026), gleiche Familie
 * wie die Plakette «Vorschau» (`GueteMarke`). Gelesen wird `lauf.modus` bzw. der Hinweissatz (`modus-marke.ts`).
 * Formen wie bei `GueteMarke`: «bild» (im Bild, in der `vis-marken-leiste` neben «Vorschau»), «abzeichen»
 * (Abzeichenreihe), «zeile» (Vorbehaltszeile). «Rechenweg nicht gemeldet» steht nur in der Zeile, nie im Bild.
 */
export function ModusMarke({
  lauf,
  testid,
  form = 'bild',
  kamera,
}: {
  lauf: unknown;
  testid: string;
  form?: 'bild' | 'abzeichen' | 'zeile';
  kamera?: string;
}) {
  const v = modusAus(lauf);
  const art = modusMarkeArt(v, kamera);
  if (art === null) return null;
  const lage = form === 'bild' ? 'oben' : 'unten';
  if (art === 'nicht-gemeldet') {
    if (form !== 'zeile') return null;
    return (
      <KTooltip text={MODUS_NICHT_GEMELDET_HINWEIS} className="vis-modus-marke-huelle vis-modus-marke-huelle--zeile" lage={lage}>
        <span tabIndex={0} className="vis-modus-marke-still" data-testid={testid} data-modus={art} data-form={form}>
          {MODUS_NICHT_GEMELDET_TEXT}
        </span>
      </KTooltip>
    );
  }
  return (
    <KTooltip text={modusTooltip(v, kamera)} className={`vis-modus-marke-huelle vis-modus-marke-huelle--${form}`} lage={lage}>
      <span tabIndex={0} className="vis-modus-marke" data-testid={testid} data-modus={art} data-form={form}>
        {MODUS_MARKE_TEXT[art]}
      </span>
    </KTooltip>
  );
}
