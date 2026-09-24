import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

/**
 * FUENF handgepflegte Aufzaehlungen desselben Backbones, quer durch drei
 * Pakete — und keine leitet sich aus der anderen ab:
 *
 *  1. `packages/kosmo-contracts/src/render-scene.ts` — der Vertrag zur
 *     HomeStation (`RenderScene.vis.backbone`); die einzige Liste, die
 *     tatsaechlich verlaesst, was wir bestellen.
 *  2. `packages/kosmo-kernel/src/commands/vis.ts` — die Parameter des
 *     `vis.render`-Befehls, aus denen zugleich Kosmos Werkzeug-Schema faellt.
 *  3. `packages/kosmo-kernel/src/model/doc.ts` — der Typ `VisRenderWunsch`,
 *     der den Auftrag im Doc traegt.
 *  4./5. `apps/kosmo-orbit/src/modules/vis/vis-jobs.ts` — zweimal: die
 *     Job-Parameter und die Optionen von `sendeGraphRenderAuftrag`.
 *
 * **Warum es diesen Test gibt.** Der Kopfkommentar an (2) behauptete bis zum
 * 19.08.2026 «kein Duplikat-Risiko: beide Seiten sind additiv». Additiv sein
 * schuetzt vor Bruch, nicht vor Drift — und die Listen waren auseinander:
 * `z-image-turbo`, seit dem 18.08. die Vorgabe der Bildlane, stand in keiner
 * von ihnen, waehrend die gemeinsame Vorgabe `'qwen'` am Geraet gemessen die
 * Tiefenkonditionierung gar nicht kann (HomeStation-Befund 12). Gefunden hat
 * es ein Nutzerdurchgang, keine Wache. **Und der Kommentar zaehlte zu tief:
 * es waren nie zwei Seiten, es sind fuenf Orte** — die vierte und fuenfte
 * kamen erst ans Licht, als die Typpruefung ueber ihnen brach.
 *
 * Dasselbe Muster wie beim «Draw»-Fund und bei den vier Massstabsreihen
 * desselben Tages: mehrere handgepflegte Listen, eine Aenderung muss
 * mehrfach ankommen. Solange die Orte verschiedene Formen brauchen
 * (zod-Enum mit Vorgabe, optionales zod-Enum, TypeScript-Unions), ist die
 * Ableitung nicht umsonst zu haben — dieser Test ist die Klammer dafuer.
 *
 * **Er prueft ausdruecklich auch, dass er die Listen ueberhaupt FINDET, und
 * WIE VIELE es sind.** Eine Zusicherung, die nur die Gleichheit einer leeren
 * Menge belegt, ist immer gruen und beweist nichts (die Falle aus ROADMAP
 * 1004). Und faellt oder waechst die Zahl, ist das ein Signal: entweder ist
 * eine sechste Handschrift entstanden, oder jemand hat sie endlich
 * abgeleitet — beides gehoert angesehen, nicht ueberschrieben.
 */

const ORTE: readonly { name: string; pfad: string; erwarteteListen: number }[] = [
  { name: 'Vertrag (render-scene.ts)', pfad: '../../../packages/kosmo-contracts/src/render-scene.ts', erwarteteListen: 1 },
  { name: 'Befehl (commands/vis.ts)', pfad: '../../../packages/kosmo-kernel/src/commands/vis.ts', erwarteteListen: 1 },
  { name: 'Doc-Typ (model/doc.ts)', pfad: '../../../packages/kosmo-kernel/src/model/doc.ts', erwarteteListen: 1 },
  { name: 'Job-Weg (vis-jobs.ts)', pfad: '../src/modules/vis/vis-jobs.ts', erwarteteListen: 2 },
];

/** Die Vorgabe, die tatsaechlich hinausgeht, wenn niemand etwas waehlt. */
const VORGABE = 'z-image-turbo';

/** Kein Wert darf verschwinden — bestehende Auftraege muessen weiter parsen. */
const NIE_ENTFERNEN = ['qwen', 'flux2-klein', 'flux-krea', 'sdxl'] as const;

const lies = (relPfad: string) => readFileSync(fileURLToPath(new URL(relPfad, import.meta.url)), 'utf8');

/**
 * Zieht jede Backbone-Aufzaehlung aus einer Quelldatei — beide Formen:
 * `backbone: z.enum([…])` (auch ueber mehrere Zeilen umbrochen) und die
 * TypeScript-Union `backbone?: 'a' | 'b';`. Kommentare enthalten einzelne
 * bequotierte Werte, aber nie eine dieser beiden Formen — sie fallen
 * darum nicht mit hinein.
 */
function listen(quelle: string): string[][] {
  const gefunden: string[][] = [];
  const enumForm = /backbone\??\s*:\s*z\s*(?:\r?\n\s*)?\.enum\(\[([^\]]*)\]\)/g;
  const unionForm = /backbone\??\s*:\s*((?:'[a-z0-9-]+'\s*\|\s*)+'[a-z0-9-]+')\s*;/g;
  for (const form of [enumForm, unionForm]) {
    for (const treffer of quelle.matchAll(form)) {
      const roh = treffer[1] ?? '';
      gefunden.push([...roh.matchAll(/'([a-z0-9-]+)'/g)].map((m) => m[1] as string));
    }
  }
  return gefunden;
}

describe('Backbone-Aufzaehlung: fuenf Orte, eine Liste', () => {
  const erhoben = ORTE.map((ort) => ({ ...ort, listen: listen(lies(ort.pfad)) }));

  it('findet an jedem Ort genau so viele Aufzaehlungen wie erwartet (sonst belegt der Vergleich unten nichts)', () => {
    for (const ort of erhoben) {
      expect(ort.listen.length, `${ort.name}: Aufzaehlung nicht gefunden oder Anzahl geaendert`).toBe(
        ort.erwarteteListen,
      );
      for (const liste of ort.listen) {
        expect(liste.length, `${ort.name}: leere Aufzaehlung eingelesen`).toBeGreaterThan(1);
      }
    }
  });

  it('es sind fuenf handgepflegte Orte — nicht mehr und nicht weniger', () => {
    const anzahl = erhoben.reduce((summe, ort) => summe + ort.listen.length, 0);
    expect(
      anzahl,
      'Die Zahl der handgepflegten Backbone-Listen hat sich geaendert. Ist eine sechste ' +
        'Handschrift entstanden, oder wurden sie abgeleitet? Beides gehoert angesehen — ' +
        'diese Zahl bitte bewusst nachfuehren, nicht reflexhaft.',
    ).toBe(5);
  });

  it('fuehrt an allen fuenf Orten dieselben Werte (Reihenfolge egal)', () => {
    const massstab = [...(erhoben[0]?.listen[0] ?? [])].sort();
    expect(massstab.length).toBeGreaterThan(1);
    for (const ort of erhoben) {
      for (const [i, liste] of ort.listen.entries()) {
        expect([...liste].sort(), `${ort.name} (Aufzaehlung ${i + 1}) weicht vom Vertrag ab`).toEqual(massstab);
      }
    }
  });

  it(`kennt «${VORGABE}» — den Backbone, dessen ControlNet-Naht am Geraet belegt ist`, () => {
    for (const ort of erhoben) {
      for (const liste of ort.listen) {
        expect(liste, `${ort.name} kennt «${VORGABE}» nicht`).toContain(VORGABE);
      }
    }
  });

  it('hat keinen alten Wert entfernt — bestehende Auftraege muessen weiter parsen', () => {
    for (const ort of erhoben) {
      for (const liste of ort.listen) {
        for (const alt of NIE_ENTFERNEN) {
          expect(liste, `${ort.name}: «${alt}» darf nicht verschwinden`).toContain(alt);
        }
      }
    }
  });

  it('die Vorgabe steht an BEIDEN Stellen, an denen sie wirklich entscheidet', () => {
    // Der Vertrag setzt sie beim Parsen (`.default(...)`) — der Job-Weg setzt
    // sie schon davor, per `??`-Rueckfall, und DIESE Zeile bestimmt, was
    // tatsaechlich hinausgeht, wenn niemand etwas waehlt.
    const vertrag = lies(ORTE[0]!.pfad);
    const jobWeg = lies(ORTE[3]!.pfad);
    expect(vertrag).toContain(`.default('${VORGABE}')`);
    expect(jobWeg).toContain(`params.backbone ?? '${VORGABE}'`);
    expect(jobWeg).not.toContain("params.backbone ?? 'qwen'");
  });
});
