// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { type VisGraph, type VisNode } from '@kosmo/kernel';
import { KuratierInspektor, type VorbildWahl } from '../src/modules/vis/KuratierInspektor';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import type { KuratierKartenDaten } from '../src/modules/vis/varianten-diff';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

/**
 * A10 · ZEILE 54 AN DER OBERFLAECHE — «Aus einem Referenzbild einzelne,
 * benannte Eigenschaften uebernehmen, und nur diese.»
 *
 * WAS SIE BEWACHT:
 *
 *  1. DASS ES DEN GRIFF UEBERHAUPT GIBT — und dass er NICHT da ist, wenn es
 *     kein Vorbild gibt. Die Gegenprobe steht zuerst: ohne sie waere «der
 *     Knopf ist da» kein Beleg, sondern ein Zufallstreffer.
 *  2. DASS DIE AUSWAHL WIRKT. Ein Kaestchen, das nur orange wird, ist die
 *     Attrappe aus Muster 11 der Anleitung. Hier wird gemessen, dass das
 *     Umschalten des Bereichs den VORBEHALT mitzieht und dass ohne Kreuz der
 *     Knopf aus ist.
 *  3. DASS DAS ERGEBNIS EINEN NEUAUFBAU UEBERLEBT. Genau das konnte die
 *     Belichtung bis zum 17.09.2026 nicht — sie lag in einem `useState` des
 *     Inspektors, und wer das Feld schloss und wieder oeffnete, stand ohne
 *     sein Ergebnis da. Die Uebernahme liegt darum von Anfang an in einer
 *     Ablage ausserhalb der Komponente.
 *  4. DASS DIE SCHICHTEN STIMMEN. Uebernahme und Farbangleich sitzen in
 *     DERSELBEN Schicht (die Uebernahme ist die Berichtigung des
 *     Farbangleichs), die Belichtung darueber.
 *
 * WAS SIE NICHT MISST: die Rechnung. Die braucht `<img>` und `<canvas>`, die
 * es in jsdom nicht gibt; sie ist im Kern mit 36 Proben bewacht
 * (`packages/kosmo-kernel/test/a10-uebernahme.test.ts`). Hier wird die NAHT
 * gemessen. Und sie misst NICHT, ob ein echtes Renderbild danach richtig
 * aussieht — dafuer braucht es ein Renderbild, und im Repo liegt keines.
 *
 * WARUM ECHTES ZEICHNEN UND NICHT `renderToStaticMarkup`: das statische
 * Zeichnen sieht Store-Aenderungen GRUNDSAETZLICH nicht (Muster 16, am
 * 17.09.2026 einmal in dieser Datei-Familie schon passiert) — die Probe waere
 * rot, obwohl der Code stimmt.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const NODE: VisNode = { id: 'node-54', typ: 'render', x: 0, y: 0, params: {} } as VisNode;

const KARTE: KuratierKartenDaten = {
  node: NODE,
  quelle: { dataUrl: 'data:image/png;base64,iVBORw0KGgo=' },
  kur: { markiert: false, verworfen: false },
};

const VORBILDER: readonly VorbildWahl[] = [
  { id: 'ref-1', label: 'Bild-Referenz', quelle: { dataUrl: 'data:image/png;base64,AAAA' } },
];

const GRAPH = { id: 'g1', typ: 'VisGraph', name: 'P', nodes: [NODE], edges: [] } as unknown as VisGraph;

const BERICHT = [
  'Bild 700 × 540, Vorbild 512 × 384',
  'Sättigung aus «Deckenholz (oben und warm)»: 13.9 % der Fläche erfasst',
  'Unangetastet: 74.8 % der Fläche liegt in keinem Bereich, 76.6 % der Bildpunkte sind Byte für Byte gleich',
];

let root: Root | null = null;
let container: HTMLDivElement | null = null;

function zeichne(vorbilder: readonly VorbildWahl[] = VORBILDER): HTMLDivElement {
  if (root) act(() => root!.unmount());
  if (container) container.remove();
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(
      <KuratierInspektor
        graph={GRAPH}
        karte={KARTE}
        id="pruef"
        onMarkieren={() => {}}
        onVerwerfen={() => {}}
        onInsProjekt={() => {}}
        vorbilder={vorbilder}
      />,
    );
  });
  return container;
}

function finde(testid: string): HTMLElement | null {
  return container?.querySelector<HTMLElement>(`[data-testid="${testid}"]`) ?? null;
}

beforeEach(() => {
  useVisRuntime.setState({ gerechneteBilder: {}, gehobeneBilder: {} });
  useVisRuntime.setState({ gerechneteBilder: {}, gehobeneBilder: {} });
});

afterEach(() => {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (container) {
    container.remove();
    container = null;
  }
});

describe('Zeile 54 — der Griff steht im Kurations-Inspektor', () => {
  it('OHNE Vorbild gibt es den Griff NICHT — und der Grund steht da', () => {
    // Die Gegenprobe zuerst. Ein Knopf, der immer da ist, belegt nichts.
    zeichne([]);
    expect(finde('vis-kuratier-uebernahme')).toBeNull();
    expect(finde('vis-kuratier-uebernehmen')).toBeNull();
    const grund = finde('vis-kuratier-kein-vorbild');
    expect(grund).not.toBeNull();
    expect(grund!.textContent).toContain('Übernahme');
  });

  it('MIT Vorbild stehen die zwei Achsen der Auswahl da: WAS und WO', () => {
    zeichne();
    expect(finde('vis-kuratier-uebernahme')).not.toBeNull();
    // WAS — drei Kaestchen, und zwar genau die drei Groessen, die sich aus
    // einem fertigen Bild einzeln holen lassen.
    for (const e of ['farbton', 'saettigung', 'helligkeit']) {
      const kasten = finde(`vis-kuratier-uebernahme-eigenschaft-${e}`) as HTMLInputElement | null;
      expect(kasten, e).not.toBeNull();
      expect(kasten!.type).toBe('checkbox');
    }
    // Die Vorgabe ist der Zuruf selbst: «die saettigung und farbe der decke».
    expect((finde('vis-kuratier-uebernahme-eigenschaft-farbton') as HTMLInputElement).checked).toBe(true);
    expect((finde('vis-kuratier-uebernahme-eigenschaft-saettigung') as HTMLInputElement).checked).toBe(true);
    expect((finde('vis-kuratier-uebernahme-eigenschaft-helligkeit') as HTMLInputElement).checked).toBe(false);
    // WO — vier Bereiche, «deckenholz» vorgewaehlt.
    const liste = finde('vis-kuratier-uebernahme-bereich') as HTMLSelectElement;
    expect(liste.value).toBe('deckenholz');
    expect([...liste.options].map((o) => o.value)).toEqual([
      'deckenholz',
      'bewuchs',
      'helleFlaechen',
      'ganzesBild',
    ]);
    // «eigeneMaske» wird NICHT angeboten: es gibt in dieser Oberflaeche keine
    // Quelle fuer eine Maske. Ein Eintrag, der nur den Ablehnungstext des
    // Kerns vorfuehrte, waere eine Attrappe.
    expect([...liste.options].map((o) => o.value)).not.toContain('eigeneMaske');
    // Und der Knopf ist AN, weil zwei Kaestchen gesetzt sind.
    expect((finde('vis-kuratier-uebernehmen') as HTMLButtonElement).disabled).toBe(false);
  });

  it('der Vorbehalt haengt wirklich am gewaehlten Bereich', () => {
    // WIRKUNG STATT AUGENSCHEIN: der Text muss sich mit der Liste aendern.
    // Ein fest eingetippter Satz saehe im Bild genauso aus.
    const c = zeichne();
    const liste = finde('vis-kuratier-uebernahme-bereich') as HTMLSelectElement;
    const vorher = finde('vis-kuratier-uebernahme-vorbehalt')!.textContent ?? '';
    expect(vorher).toContain('warm getönt');

    act(() => {
      liste.value = 'helleFlaechen';
      liste.dispatchEvent(new Event('change', { bubbles: true }));
    });
    const nachher = c.querySelector('[data-testid="vis-kuratier-uebernahme-vorbehalt"]')!.textContent ?? '';
    expect(nachher).not.toBe(vorher);
    // Die gemessene Zahl aus `belichtung.ts` steht beim Nutzer auf dem Schirm,
    // nicht nur im Quelltext: «helle Flaechen» ist keine Kuechenfront.
    expect(nachher).toContain('83.2 %');
    expect(nachher).toContain('Kein Bauteil');
  });

  it('ohne Kreuz ist der Knopf AUS — und sagt warum', () => {
    // Der Kern lehnt eine leere Bestellung ab. Einen Knopf zu lassen, der
    // diese Ablehnung vorfuehrt, waere Muster 11.
    zeichne();
    expect(finde('vis-kuratier-uebernahme-nichts-benannt')).toBeNull();
    for (const e of ['farbton', 'saettigung']) {
      const kasten = finde(`vis-kuratier-uebernahme-eigenschaft-${e}`) as HTMLInputElement;
      act(() => {
        kasten.click();
      });
    }
    expect((finde('vis-kuratier-uebernahme-eigenschaft-farbton') as HTMLInputElement).checked).toBe(false);
    expect((finde('vis-kuratier-uebernehmen') as HTMLButtonElement).disabled).toBe(true);
    expect(finde('vis-kuratier-uebernahme-nichts-benannt')!.textContent).toContain('Nichts angekreuzt');
  });

  it('die Inhaltsspalte traegt die Zeilenvorgabe, die sie rollen laesst', () => {
    // EHRLICH, WAS DIESE PROBE IST: ein Riegel gegen das ENTFERNEN der Zeile,
    // nicht ein Beleg ihrer Wirkung. jsdom hat keine Layout-Rechnung — hier
    // ist jedes Element 0 Bildpunkte gross, und «ueberdeckt» hat keinen Sinn.
    //
    // DIE WIRKUNG IST EINMAL IM ECHTEN FENSTER GEMESSEN (17.09.2026,
    // 1500x950, eigener Bau, kopfloser Chromium): ohne die Zeile ragte die
    // Vorschau 160.2 Bildpunkte in die naechste Rasterzeile,
    // `document.elementFromPoint` auf die Mitte des zweiten Kaestchens traf
    // das Vorschaubild, ein echter Klick lief in die Zeitueberschreitung, und
    // die Spalte meldete `scrollHeight` 777 bei `clientHeight` 777. Mit der
    // Zeile: 1015 gegen 777, Ueberlappung -16 (die Fuge), und der Klick
    // trifft das Kaestchen. Die Zahlen stehen im Kommentar an der Stelle
    // selbst.
    //
    // 17.09.2026, NACHGEZOGEN: die Zeile stand vorlaeufig als Stil AM ELEMENT,
    // weil `vis-visual.css` dem Erbauer nicht gehoerte. Sie steht jetzt dort,
    // wo sie hingehoert — bei `.vis-inspektor-inhalt`, samt der Messreihe.
    // Darum liest diese Probe seither die STILDATEI statt das Element: jsdom
    // wendet Stilblaetter nicht auf `element.style` an, eine Probe am Element
    // waere nach dem Umzug still gruen geblieben und haette nichts mehr
    // bewacht. Die Klasse selbst wird weiter am gezeichneten Baum geprueft —
    // sonst bewachte die Datei-Lesung eine Regel fuer ein Element, das es
    // vielleicht gar nicht mehr gibt.
    const c = zeichne();
    const inhalt = c.querySelector<HTMLElement>('.vis-inspektor-inhalt');
    expect(inhalt, 'die Inhaltsspalte traegt die Klasse noch').not.toBeNull();

    const css = readFileSync(resolve(__dirname, '../src/modules/vis/vis-visual.css'), 'utf8');
    const block = css.slice(css.indexOf('.vis-inspektor-inhalt {'));
    const regel = block.slice(0, block.indexOf('}'));
    expect(regel, 'die Zeilenvorgabe fehlt in .vis-inspektor-inhalt').toContain('grid-auto-rows: min-content');
  });

  it('was NICHT geht, steht auch da — und nicht nur in einem Bericht anderswo', () => {
    zeichne();
    const text = finde('vis-kuratier-uebernahme-was-fehlt')!.textContent ?? '';
    expect(text).toContain('Vorhang');
    expect(text).toContain('Durchlässigkeit');
    expect(text).toContain('Textur');
  });
});

describe('Zeile 54 — das Ergebnis ueberlebt einen Neuaufbau', () => {
  it('ohne Ergebnis zeigt der Inspektor KEINEN Uebernahme-Bericht (Gegenprobe zuerst)', () => {
    zeichne();
    expect(finde('vis-kuratier-uebernahme-bericht')).toBeNull();
    expect(finde('vis-kuratier-uebernommenes-bild')).toBeNull();
  });

  it('liegt ein Ergebnis in der Ablage, zeigt JEDER neue Aufbau es wieder', () => {
    useVisRuntime.getState().setzeGerechnetesBild('node-54', {
      art: 'uebernahme',
      nodeId: 'node-54',
      dataUrl: 'data:image/png;base64,UUU',
      bericht: BERICHT,
      zusage: 'nur die benannten Eigenschaften',
      kopfzeile: 'Sättigung aus «Bild-Referenz», nur im Bereich «Deckenholz (oben und warm)» — gerechnet, nicht erzeugt.',
    });
    // Dreimal frisch gezeichnet = dreimal eine NEUE Komponenteninstanz. Genau
    // das war der Fall, der bei der Belichtung das Ergebnis verlor.
    for (let i = 0; i < 3; i++) {
      zeichne();
      expect(finde('vis-kuratier-uebernahme-bericht'), `Aufbau ${i + 1}`).not.toBeNull();
      expect(finde('vis-kuratier-uebernahme-bericht')!.textContent).toContain(
        '76.6 % der Bildpunkte sind Byte für Byte gleich',
      );
      const bild = finde('vis-kuratier-uebernommenes-bild') as HTMLImageElement;
      expect(bild.getAttribute('src')).toBe('data:image/png;base64,UUU');
      expect(finde('vis-kuratier-uebernahme-zuruecksetzen')).not.toBeNull();
    }
  });

  it('«zuruecknehmen» nimmt wirklich zurueck — das Original liegt wieder oben', () => {
    useVisRuntime.getState().setzeGerechnetesBild('node-54', {
      art: 'uebernahme',
      nodeId: 'node-54',
      dataUrl: 'data:image/png;base64,UUU',
      bericht: BERICHT,
      zusage: 'nur die benannten Eigenschaften',
      kopfzeile: 'Sättigung aus «Bild-Referenz» — gerechnet, nicht erzeugt.',
    });
    zeichne();
    const knopf = finde('vis-kuratier-uebernahme-zuruecksetzen') as HTMLButtonElement;
    act(() => {
      knopf.click();
    });
    expect(finde('vis-kuratier-uebernommenes-bild')).toBeNull();
    expect(finde('vis-kuratier-uebernahme-bericht')).toBeNull();
    expect(useVisRuntime.getState().gerechneteBilder['node-54']).toBeUndefined();
  });

  it('ein Ergebnis einer FREMDEN Karte zeigt hier nichts', () => {
    // Diese Komponente wird beim Kartenwechsel nicht neu aufgebaut; ohne die
    // Wache zeigte das Bild der vorigen Karte an der naechsten weiter — und
    // zwar als deren Bild.
    useVisRuntime.getState().setzeGerechnetesBild('node-54', {
      art: 'uebernahme',
      nodeId: 'eine-andere-karte',
      dataUrl: 'data:image/png;base64,FREMD',
      bericht: BERICHT,
      zusage: 'x',
      kopfzeile: 'x',
    });
    zeichne();
    expect(finde('vis-kuratier-uebernommenes-bild')).toBeNull();
    expect(finde('vis-kuratier-uebernahme-bericht')).toBeNull();
  });
});

describe('Zeile 54 — die Schichten', () => {
  it('die Belichtung liegt DARUEBER und nennt die Uebernahme als ihre Grundlage', () => {
    useVisRuntime.getState().setzeGerechnetesBild('node-54', {
      art: 'uebernahme',
      nodeId: 'node-54',
      dataUrl: 'data:image/png;base64,UUU',
      bericht: BERICHT,
      zusage: 'x',
      kopfzeile: 'x',
    });
    useVisRuntime.getState().setzeGehobenesBild('node-54', {
      nodeId: 'node-54',
      dataUrl: 'data:image/png;base64,HELLER',
      bericht: ['Bild 700 × 540, Hebung 1.080'],
      zusage: 'nur die Helligkeit',
      grundlage: 'die Übernahme',
    });
    zeichne();
    // Das gehobene Bild gewinnt die Anzeige — es ist der zuletzt gerechnete
    // Griff.
    const bild = finde('vis-kuratier-belichtetes-bild') as HTMLImageElement;
    expect(bild.getAttribute('src')).toBe('data:image/png;base64,HELLER');
    expect(finde('vis-kuratier-uebernommenes-bild')).toBeNull();
    // Und die Kopfzeile sagt, worauf gerechnet wurde.
    expect(finde('vis-kuratier-belichtung-bericht')!.textContent).toContain('Belichtung auf die Übernahme');
  });

  it('«Nachbearbeiten» raeumt die Uebernahme weg — sie sitzen in derselben Schicht', () => {
    // Beide sind Griffe ins ORIGINAL. Blieben beide stehen, zeigte der
    // Inspektor ein Bild mit dem Bericht eines anderen.
    useVisRuntime.getState().setzeGerechnetesBild('node-54', {
      art: 'uebernahme',
      nodeId: 'node-54',
      dataUrl: 'data:image/png;base64,UUU',
      bericht: BERICHT,
      zusage: 'x',
      kopfzeile: 'x',
    });
    zeichne();
    expect(finde('vis-kuratier-uebernommenes-bild')).not.toBeNull();
    const knopf = finde('vis-kuratier-nachbearbeiten') as HTMLButtonElement;
    act(() => {
      knopf.click();
    });
    // Die Rechnung selbst scheitert in jsdom (kein Canvas) und meldet sich;
    // das WEGRAEUMEN passiert davor und ist genau das, was hier gemessen wird.
    expect(useVisRuntime.getState().gerechneteBilder['node-54']).toBeUndefined();
    expect(finde('vis-kuratier-uebernommenes-bild')).toBeNull();
  });
});
