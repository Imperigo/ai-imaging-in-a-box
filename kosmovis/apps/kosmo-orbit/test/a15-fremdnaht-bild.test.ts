/**
 * A15 · Die Fremdnaht Bild (Welle 5, 17.09.2026) — die Probe zur Messung.
 *
 * WAS SIE BEWACHT, IN EINEM SATZ: dass kein Bedienelement dieses Moduls eine
 * Bestellung abschickt, von der niemand gemessen hat, ob die Gegenseite sie
 * liest.
 *
 * Der Auftrag dieser Welle war zuerst eine Messung und erst danach ein Bau
 * (Bauplan §4, «Welle 5»: «Jede Zeile hier ohne Antwort zu bauen hiesse, ein
 * Feld an einen Vertrag zu haengen, das die Gegenseite nicht liest»). Die
 * Messung liegt als Tabelle `FREMDNAHT` in `vis-jobs.ts`. Eine Tabelle allein
 * altert aber genauso still wie der Satz, den sie ersetzt hat — darum diese
 * Probe.
 *
 * SIE KANN WIDERSPRECHEN, und zwar nachgestellt (Muster 3):
 *
 *  - Nimmt man `render.rauschschwelle` aus `FREMDNAHT` heraus, wird Fall 1 rot
 *    («ohne Messung an der Fremdnaht: render.rauschschwelle»).
 *  - Haengt jemand ein siebtes Bedienelement an `renderBedienungAusParams`,
 *    ohne die Messung nachzutragen, wird derselbe Fall rot — das ist der
 *    eigentliche Zweck.
 *  - Faerbt jemand `render.sun.staerke` in der Tabelle auf `'gelesen'`, ohne
 *    dass die Naht gebaut ist, wird Fall 4 rot.
 *  - Waechst der Hinweistext ueber sein Laengenbudget, wird Fall 3 rot —
 *    bevor der Knoten ihn stillschweigend abschneidet.
 *
 * WAS SIE NICHT KANN: nachsehen, ob die Gegenseite das Feld heute liest. Das
 * fremde Repo liegt ausserhalb dieses Baums, und ein Analogieschluss ist kein
 * Nachweis an fremdem Code. Die Probe bewacht die BUCHFUEHRUNG ueber die
 * Messung, nicht die Messung selbst; wer die Naht anfasst, misst neu und
 * traegt das Datum nach.
 */
import { describe, expect, it } from 'vitest';
import { RENDER_PRESETS, HIMMEL_ARTEN } from '@kosmo/kernel';
import {
  BILDWEG_OFFEN,
  BILDWERKZEUG_IDS,
  FREMDNAHT,
  fremdnahtBefund,
  fremdnahtNichtGelesen,
  fremdnahtSatz,
  renderBedienungAusParams,
  AUFLOESUNGEN,
  QUALITAETSSTUFEN,
} from '../src/modules/vis/vis-jobs';

/**
 * Eine Parameterbelegung, die JEDES der sechs Bedienelemente wirklich setzt.
 * Die Werte kommen aus den Listen des Moduls selbst, nie aus getippten
 * Konstanten: eine Probe, die ihre Eingabe erfindet, misst ihre eigene
 * Erfindung (Muster 3, der Zirkelschluss des 3DS-Lesers).
 */
function alleSechsGesetzt(): Record<string, string | number | boolean> {
  const aufl = AUFLOESUNGEN[AUFLOESUNGEN.length - 1]!.wert;
  const preset = RENDER_PRESETS.find((p) => p.render.sun.staerke !== undefined);
  expect(preset, 'kein Preset traegt Sonnendetails — dann misst diese Probe nichts').toBeDefined();
  return {
    preset: preset!.id,
    aufloesung: `${aufl[0]}x${aufl[1]}`,
    abtastungen: QUALITAETSSTUFEN[0]!.abtastungen,
    himmel: HIMMEL_ARTEN[1]!,
    umgebungDrehungGrad: 90,
    backbone: BILDWERKZEUG_IDS[0]!,
  };
}

/**
 * Der Vertragspfad zu einem erzeugten Bedienwert. Die Regel ist mechanisch
 * und steht hier, damit sie nicht zum handgepflegten Zwilling wird:
 *  - `sunDetails.X` → `render.sun.X` (der Sammelname der Oberflaeche wird
 *    im Vertrag zum Unterfeld von `sun`),
 *  - `backbone`     → `vis.backbone` (das einzige Bedienelement, das nicht
 *    unter `render` haengt),
 *  - alles Uebrige  → `render.X`.
 * Wer einen dritten Sonderfall braucht, traegt ihn HIER ein und merkt dabei,
 * dass er einen baut.
 */
function bestellpfade(bedienung: Record<string, unknown>): string[] {
  const pfade: string[] = [];
  for (const [schluessel, wert] of Object.entries(bedienung)) {
    if (wert === undefined) continue;
    if (schluessel === 'sunDetails') {
      for (const unter of Object.keys(wert as Record<string, unknown>)) pfade.push(`render.sun.${unter}`);
    } else if (schluessel === 'backbone') {
      pfade.push('vis.backbone');
    } else {
      pfade.push(`render.${schluessel}`);
    }
  }
  return pfade;
}

describe('A15 · Fremdnaht Bild — kein Bedienelement ohne Messung', () => {
  it('1 · jedes Feld, das die Bedienung bestellen kann, hat einen Messeintrag', () => {
    const bedienung = renderBedienungAusParams(alleSechsGesetzt());
    const pfade = bestellpfade(bedienung as Record<string, unknown>);

    // Die Probe muss zuerst beweisen, dass sie ueberhaupt etwas sieht — sonst
    // besteht sie aus dem falschen Grund (Muster 6, die Probe im falschen
    // Massstab: 0 Pfade gegen 0 Fehlende ist keine Aussage).
    expect(pfade.length, 'die Bedienung erzeugte nichts — dann prueft der Rest nichts').toBeGreaterThanOrEqual(8);

    const ohneMessung = pfade.filter((p) => fremdnahtBefund(p) === undefined);
    expect(ohneMessung, `ohne Messung an der Fremdnaht: ${ohneMessung.join(', ')}`).toEqual([]);
  });

  it('2 · jeder Messeintrag traegt Datum und Beleg — eine Behauptung ist kein Befund', () => {
    for (const eintrag of FREMDNAHT) {
      expect(eintrag.gemessenAm, `${eintrag.feld}: kein Messdatum`).toMatch(/^\d{2}\.\d{2}\.\d{4}$/);
      expect(eintrag.beleg.length, `${eintrag.feld}: Beleg zu duenn`).toBeGreaterThan(40);
      expect(eintrag.titel.length, `${eintrag.feld}: kein Anzeigename`).toBeGreaterThan(2);
    }
    // Gegenprobe zur Gegenprobe: die Tabelle ist nicht leer, sonst besteht
    // die Schleife oben, ohne einen einzigen Eintrag gesehen zu haben.
    expect(FREMDNAHT.length).toBeGreaterThanOrEqual(11);
  });

  it('3 · der Hinweistext bleibt im Laengenbudget seiner Zeile', () => {
    const satz = fremdnahtSatz();
    // 275 Zeichen war der Satz, der bis zum 17.09.2026 in `zusatz-ehrlichkeit`
    // stand und fuer den das Zeilenregister 106 px eingetragen hat. Der Zusatz
    // ueber «nur Cycles»/«Strichzeichnung» (78 Zeichen) steht im Knoten hinter
    // diesem Satz und zaehlt darum mit.
    const zusatzImKnoten = 78;
    expect(satz.length + zusatzImKnoten, `Hinweistext zu lang: ${satz.length + zusatzImKnoten} Zeichen`).toBeLessThanOrEqual(
      275,
    );
    // Und er sagt, was gemessen wurde — der alte Satz fuehrte eine erledigte
    // Pruefung weiter als offen.
    expect(satz).toContain('Gemessen');
    expect(satz).not.toContain('nicht geprüft');
    expect(satz).toContain('Sonnenstärke');
  });

  it('4 · die Sonnen-STAERKE gilt als nicht gelesen, der Sonnen-STAND als gelesen', () => {
    // Der Unterschied ist der ganze Befund der Welle: der Hinweis im Auftrag
    // lautete, Zeile 46 gehe «vielleicht schon durch», weil `sun` ein Feld
    // `staerke` traegt. Gemessen geht der STAND durch und die STAERKE nicht.
    expect(fremdnahtBefund('render.sun.azimuth')?.stand).toBe('gelesen');
    expect(fremdnahtBefund('render.sun.elevation')?.stand).toBe('gelesen');
    for (const feld of ['render.sun.staerke', 'render.sun.kelvin', 'render.sun.winkelGrad']) {
      expect(fremdnahtBefund(feld)?.stand, `${feld} gilt faelschlich als gelesen`).toBe('nicht-gelesen');
    }
    // Die Liste wird gezaehlt, nicht getippt (Muster 4).
    expect(fremdnahtNichtGelesen().length).toBe(FREMDNAHT.filter((f) => f.stand === 'nicht-gelesen').length);
  });

  it('5 · die fuenf offenen Bildzeilen stehen vollstaendig und ohne Bedienelement da', () => {
    expect(BILDWEG_OFFEN.map((o) => o.zeile)).toEqual(['50b', '53', '57', '58', '59']);
    for (const offen of BILDWEG_OFFEN) {
      expect(offen.warum.length, `Zeile ${offen.zeile}: kein Grund genannt`).toBeGreaterThan(80);
    }
  });
});
