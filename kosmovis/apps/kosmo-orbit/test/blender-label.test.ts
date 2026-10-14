import { describe, expect, it } from 'vitest';
import { bildLabel } from '../src/modules/vis/vis-jobs';

/**
 * E13 (`docs/V089-SPEZ.md` §9, PBL2, Matrix C-17) — Label-/Herkunftskette:
 * `bildLabel({worker?, requestedStyle?})` ersetzt die frühere feste
 * `BILD_LABEL_FAKE_RENDER`-Konstante durch eine echte Herkunftsprüfung.
 *
 * WICHTIG (Container-Grenze, wörtlich, s. `vis-jobs.ts`s Kommentar an
 * `bildLabel`): der `'echter Render'`-Zweig ist im Container-Betrieb NIE
 * erreichbar — die Fake-Bridge (`tools/homestation-bridge/kosmo_bridge/
 * main.py` `_fake_worker_step`) liefert IMMER `worker: 'fake-worker'`. Diese
 * Suite ist der EINZIGE Ort, an dem der Echt-Zweig überhaupt ausgeführt wird
 * — mit einem KÜNSTLICHEN JobRecord-Ausschnitt, nicht über einen echten
 * Bridge-Roundtrip. Bis zu einer echten HomeStation-Abnahme (0.8.10+,
 * Owner-Termin) bleibt er ein unbewiesener Live-Pfad.
 *
 * P11/B5 (V016-SPEZ) — Befund NACHGEZOGEN, 23.09.2026: `bildLabel` behauptete
 * bisher zwei falsche Herkünfte. (1) Fehlte `worker` GANZ (keine Angabe, z. B.
 * ein fehlgeschlagener Zusatz-Fetch), nannte die Funktion das Bild trotzdem
 * «Vorschau (Fake-Render)» — eine geratene Behauptung, kein gemessener
 * Befund: ein Bild ohne `worker`-Angabe könnte ebenso ein echter Render
 * gewesen sein, dessen Feld nur nicht mitkam. Jetzt: «Herkunft unbekannt».
 * (2) Ein KI-Bild (Stiltransfer über `requestedStyle: 'redux'/'ipadapter'/
 * 'lora'`, `RenderScene.style.mode` in `kosmo-contracts`) hiess «Render
 * (Cycles)» — Cycles ist der Render-KERN, die KI-Veredelung ein zusätzlicher
 * Schritt danach; beide unter demselben Namen zu zeigen verschleiert genau
 * die Unterscheidung, die der Nutzer treffen soll. Jetzt: «KI-Bild». Der
 * echte-Worker-ohne-KI-Stil-Fall selbst heisst neu «echter Render» (bleibt
 * ebenfalls Container-unerreichbar) — `'fake-worker'` UND `'lineart'` bleiben
 * UNVERÄNDERT (E2E `blender-bridge.spec.ts:247`/`vis-publish-bild.spec.ts`
 * hängen am `'fake-worker'`-Wortlaut, ausserhalb dieses Pakets, nicht
 * angefasst).
 */
describe('bildLabel — Herkunfts-Label (E13, P11/B5 nachgezogen)', () => {
  it('B5: worker fehlt GANZ → «Herkunft unbekannt», NICHT mehr geraten als Fake-Render', () => {
    expect(bildLabel({})).toBe('Herkunft unbekannt');
    expect(bildLabel({ requestedStyle: 'lineart' })).toBe('Herkunft unbekannt');
  });

  it("worker === 'fake-worker' → «Vorschau (Fake-Render)» (Container-Normalfall, jede Fake-Bridge-Antwort — unverändert, E2E hängt daran)", () => {
    expect(bildLabel({ worker: 'fake-worker' })).toBe('Vorschau (Fake-Render)');
    expect(bildLabel({ worker: 'fake-worker', requestedStyle: 'lineart' })).toBe('Vorschau (Fake-Render)');
  });

  it('echter Worker + requestedStyle "lineart" → «Strichzeichnung (Line-Art)» (Container-unerreichbar, s. Kopfkommentar)', () => {
    expect(bildLabel({ worker: 'homestation-1', requestedStyle: 'lineart' })).toBe('Strichzeichnung (Line-Art)');
  });

  it('echter Worker + requestedStyle undefined/"none" → «echter Render» (Container-unerreichbar, s. Kopfkommentar)', () => {
    expect(bildLabel({ worker: 'homestation-1' })).toBe('echter Render');
    expect(bildLabel({ worker: 'homestation-1', requestedStyle: undefined })).toBe('echter Render');
    expect(bildLabel({ worker: 'homestation-1', requestedStyle: 'none' })).toBe('echter Render');
  });

  // B5: DER KERN-BEFUND — vor der Reparatur lieferten alle drei Zeilen
  // «Render (Cycles)», obwohl «redux»/«ipadapter»/«lora» KI-Stiltransfer
  // bestellen (`RenderScene.style.mode`, kosmo-contracts). Cycles ist nur
  // der Render-KERN darunter, nicht die volle Herkunft des gezeigten Bildes.
  it('B5: echter Worker + requestedStyle "redux"/"ipadapter"/"lora" (KI-Veredelung) → «KI-Bild», NICHT «echter Render»/«Cycles»', () => {
    expect(bildLabel({ worker: 'homestation-1', requestedStyle: 'redux' })).toBe('KI-Bild');
    expect(bildLabel({ worker: 'homestation-1', requestedStyle: 'ipadapter' })).toBe('KI-Bild');
    expect(bildLabel({ worker: 'homestation-1', requestedStyle: 'lora' })).toBe('KI-Bild');
  });
});
