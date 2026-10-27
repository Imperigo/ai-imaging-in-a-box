import { KTooltip } from '@kosmo/ui';
import { MODUS_MARKE_TEXT, MODUS_NICHT_GEMELDET_HINWEIS, MODUS_NICHT_GEMELDET_TEXT, modusAus, modusMarkeArt, modusTooltip } from './modus-marke';
import './vis-visual.css';

/**
 * Vermerk «Ohne Grundlagenbild» / «Anders gerechnet» an einem Render-Bild (Blatt 21.10.2026), gleiche Familie
 * wie die Plakette «Vorschau» (`GueteMarke`). Gelesen wird `lauf.modus` bzw. der Hinweissatz (`modus-marke.ts`).
 * Formen wie bei `GueteMarke`: «bild» (im Bild, in der `vis-marken-leiste` neben «Vorschau»), «abzeichen»
 * (Abzeichenreihe), «zeile» (Vorbehaltszeile). «Rechenweg nicht gemeldet» steht nur in der Zeile, nie im Bild.
 * Vierte Form «symbol» fuer die engste Flaeche, den 96 x 60-Daumen des Varianten-Knotens (Befund Geraeteprobe R73:
 * «GRUNDLAGENBILD» ist breiter als der Daumen und brach mitten im Wort). UI-Regel 2 (kein Wortbruch, nichts ueber
 * den Rand) und Regel 3 (ausgeschrieben ODER Symbol): dort steht ein Zeichen, der volle Wortlaut steht in der
 * Kurzhilfe und im aria-label. Kein Abkuerzungstext, keine Auslassungspunkte.
 */
export function ModusMarke({
  lauf,
  testid,
  form = 'bild',
  kamera,
}: {
  lauf: unknown;
  testid: string;
  form?: 'bild' | 'abzeichen' | 'zeile' | 'symbol';
  kamera?: string;
}) {
  const v = modusAus(lauf);
  const art = modusMarkeArt(v, kamera);
  if (art === null) return null;
  const lage = form === 'bild' || form === 'symbol' ? 'oben' : 'unten';
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
  if (form === 'symbol') {
    return (
      <KTooltip text={modusTooltip(v, kamera)} className="vis-modus-marke-huelle vis-modus-marke-huelle--symbol" lage={lage}>
        <span tabIndex={0} role="img" aria-label={MODUS_MARKE_TEXT[art]} className="vis-modus-marke vis-modus-marke--symbol" data-testid={testid} data-modus={art} data-form={form}>
          <svg viewBox="0 0 12 12" width="1em" height="1em" aria-hidden="true" focusable="false">
            <rect x="1.5" y="2.5" width="9" height="7" rx="1" fill="none" stroke="currentColor" strokeWidth="1.2" />
            {art === 'ohne-grundlagenbild' ? (
              <line x1="1.5" y1="10.5" x2="10.5" y2="1.5" stroke="currentColor" strokeWidth="1.2" />
            ) : (
              <path d="M3.5 5.5h5M3.5 7.5h5" stroke="currentColor" strokeWidth="1.2" fill="none" />
            )}
          </svg>
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
