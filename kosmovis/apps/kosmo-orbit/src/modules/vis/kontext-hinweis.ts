/**
 * KONTEXT BEIM BESTELLEN (Visbox-Video-Befund L4-5, 21.10.2026; Blatt «Grossansicht und Vergleich», Feld 5).
 *
 * WARUM: Im Demolauf wurden Bestand und Gelaende als Ausweg ausgeblendet — die Varianten standen danach ohne Kontext
 * im Bild, «ein Riegel im Leeren», und das fiel erst am fertigen Bild auf. Ein Entwurf des Varianten-Knotens ist eine
 * Ebenenkombination (E222); gesendet wird nur, was in ihr sichtbar ist (`docFuerEbenen`). Blendet sie jeden
 * Bestandskoerper aus, den das Modell hat, sagt das jetzt eine Meldung BEIM BESTELLEN — bestellt wird trotzdem.
 *
 * NICHT HIER: die Standard-Ebene «Bestand fern» und eine Auto-Kamera, die die nahen Nachbarn einschliesst — beides
 * gehoert zur 3D-Ansicht von KosmoOrbit und steht als Bitte im Meldeblatt.
 */
import { docFuerEbenen, istBestandVolumen, type KosmoDoc, type MassBody, type VariantenEntwurf } from '@kosmo/kernel';

/** Wie viele Bestandskoerper (Volumen im Programm «Bestand») ein Dokument traegt. */
export function bestandAnzahl(doc: KosmoDoc): number {
  return doc.byKind<MassBody>('mass').filter((m) => istBestandVolumen(m)).length;
}

/**
 * Die Entwuerfe, die den Bestand des Modells ganz ausblenden. Leer, wenn das Modell keinen Bestand hat (dann gibt es
 * nichts zu verlieren) oder jeder Entwurf mindestens einen Bestandskoerper zeigt. Ein Entwurf ohne Kombination ist das
 * ganze Modell und blendet nichts aus.
 */
export function entwuerfeOhneBestand(doc: KosmoDoc, entwuerfe: readonly VariantenEntwurf[]): VariantenEntwurf[] {
  if (bestandAnzahl(doc) === 0) return [];
  return entwuerfe.filter((e) => e.kombination !== undefined && bestandAnzahl(docFuerEbenen(doc, e.kombination)) === 0);
}

/** Die Meldung beim Bestellen; `null`, wenn kein Entwurf den Bestand ausblendet. */
export function ohneBestandSatz(ohne: readonly Pick<VariantenEntwurf, 'name'>[]): string | null {
  if (ohne.length === 0) return null;
  const namen = ohne.map((e) => `«${e.name}»`).join(', ');
  return (
    `${ohne.length === 1 ? 'Entwurf' : 'Entwürfe'} ${namen} ${ohne.length === 1 ? 'blendet' : 'blenden'} den ganzen Bestand aus — ` +
    'die Bilder zeigen den Entwurf ohne Nachbarn. Für Kontext in der Ebenenkombination die Ebene «Bestand» ' +
    '(oder eine Ebene mit den nahen Bauten) einblenden. Bestellt ist trotzdem.'
  );
}

/** Wie lange die Meldung steht (ms) — laenger als eine gewoehnliche, sie verlangt ein Lesen. */
export const OHNE_BESTAND_MELDUNG_MS = 9000;
