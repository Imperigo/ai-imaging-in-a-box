import { KTooltip } from '@kosmo/ui';
import { LIZENZ_OFFEN_LABEL, lizenzOffenGrund, type LizenzAngabe } from './varianten-diff';
import './vis-visual.css';

/**
 * P-LIZENZMARKE Schritt 2 (Owner-Entscheid E154 (4), 06.10.2026: «Anzeigen,
 * nicht sperren»): der Hinweis «Lizenz offen» an einem Bild, dessen Ergebnis
 * `engine_license_open: true` traegt (heute Qwen-Image-2.1, «Qwen Research
 * License Agreement»; die Lizenz ist vor einer Veroeffentlichung zu loesen,
 * E128).
 *
 * KEINE NEUE OPTIK: die Zeile traegt die Vorbehaltsklasse der Bildkachel
 * (`.vis-bild-kachel-qa-vorbehalt`, Warnfarbe, wie der Liefer-Vorbehalt aus
 * kv-lieferstatus-null) und das Warnzeichen der QA-Zeile. Der Grund steht in
 * der Kurzhilfe (`KTooltip`, kein natives `title=`): beim Darueberfahren, beim
 * Fokus per Tab und beim Tippen, und fuer die Sprachausgabe immer.
 *
 * SPERRT NICHTS: kein Knopf wird ausgegraut, kein Klick abgefangen. Ohne Marke
 * (Feld fehlt oder `false`) rendert der Baustein nichts.
 */
export function LizenzOffenMarke({
  lizenz,
  testid,
  abzeichen,
  lage,
}: {
  lizenz: LizenzAngabe | null | undefined;
  testid: string;
  /**
   * Auf einem Bild (Kuratier-Karte, Vergleich) steht die Marke als Abzeichen
   * in der Form von «FAVORIT» (`.vis-raster-karte-badge`), in der Farbe des
   * Vorbehalts; `'rechts'`/`'links'` sagt, an welcher Kante des Bildes es
   * sitzt, damit die Kurzhilfe ins Bild hinein aufgeht.
   */
  abzeichen?: 'links' | 'rechts';
  lage?: 'oben' | 'unten';
}) {
  const grund = lizenzOffenGrund(lizenz);
  if (!grund) return null;
  const klassen = [
    'vis-bild-kachel-qa-vorbehalt',
    'vis-lizenz-offen',
    abzeichen ? 'vis-raster-karte-badge vis-raster-karte-badge--lizenz' : '',
  ]
    .filter(Boolean)
    .join(' ');
  const huelle = ['vis-lizenz-offen-huelle', abzeichen ? `vis-lizenz-offen-huelle--${abzeichen}` : '']
    .filter(Boolean)
    .join(' ');
  return (
    <KTooltip text={grund} className={huelle} {...(lage !== undefined ? { lage } : {})}>
      <span tabIndex={0} className={klassen} data-testid={testid}>
        <span aria-hidden="true">⚠ </span>
        {LIZENZ_OFFEN_LABEL}
      </span>
    </KTooltip>
  );
}

/**
 * Derselbe Hinweis an einem Ablage-Knopf («Ins Projekt», «Aufs Blatt»): die
 * Marke und dahinter, ausgeschrieben, was vor dem Veroeffentlichen zu tun
 * ist. Der Knopf daneben bleibt bedienbar.
 */
export function LizenzOffenAblageHinweis({
  lizenz,
  testid,
}: {
  lizenz: LizenzAngabe | null | undefined;
  testid: string;
}) {
  const grund = lizenzOffenGrund(lizenz);
  if (!grund) return null;
  return (
    <span className="vis-bild-kachel-qa-vorbehalt vis-lizenz-offen-ablage" data-testid={testid}>
      <span aria-hidden="true">⚠ </span>
      {LIZENZ_OFFEN_LABEL} — {grund}
    </span>
  );
}
