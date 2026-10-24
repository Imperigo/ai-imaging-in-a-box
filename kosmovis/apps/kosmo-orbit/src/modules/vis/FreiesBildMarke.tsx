import { KTooltip } from '@kosmo/ui';
import { FREIES_BILD_MARKE_HINWEIS, FREIES_BILD_MARKE_TEXT, istFreiesBild, type MitFreiemBild } from './freies-bild';
import './vis-visual.css';

/**
 * Marke «freies Bild» (Visbox-Entscheid 149) — dieselbe Familie und dieselben drei Formen wie die Plakette
 * «Vorschau» (`GueteMarke`): «bild» im Bild in der `vis-marken-leiste`, «abzeichen» in einer Abzeichenreihe,
 * «zeile» als Vorbehaltszeile. Gelesen wird, was das ERGEBNIS meldet (`freiesBild` am Lauf, aus
 * `result.freies_bild`). Ein freies Bild darf nirgends wie ein modelltreues aussehen.
 */
export function FreiesBildMarke({
  lauf,
  testid,
  form = 'bild',
}: {
  lauf: MitFreiemBild;
  testid: string;
  form?: 'bild' | 'abzeichen' | 'zeile';
}) {
  if (!istFreiesBild(lauf)) return null;
  return (
    <KTooltip text={FREIES_BILD_MARKE_HINWEIS} className={`vis-guete-marke-huelle vis-guete-marke-huelle--${form}`} lage={form === 'bild' ? 'oben' : 'unten'}>
      <span tabIndex={0} className="vis-guete-marke" data-testid={testid} data-freies-bild="ja" data-form={form}>
        {FREIES_BILD_MARKE_TEXT}
      </span>
    </KTooltip>
  );
}
