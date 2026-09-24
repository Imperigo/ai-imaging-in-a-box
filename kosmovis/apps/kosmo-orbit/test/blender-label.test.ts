import { describe, expect, it } from 'vitest';
import { bildLabel } from '../src/modules/vis/vis-jobs';

/**
 * E13 (`docs/V089-SPEZ.md` §9, PBL2, Matrix C-17) — Label-/Herkunftskette:
 * `bildLabel({worker?, requestedStyle?})` ersetzt die frühere feste
 * `BILD_LABEL_FAKE_RENDER`-Konstante durch eine echte Herkunftsprüfung.
 *
 * WICHTIG (Container-Grenze, wörtlich, s. `vis-jobs.ts`s Kommentar an
 * `bildLabel`): der `'Render (Cycles)'`-Zweig ist im Container-Betrieb NIE
 * erreichbar — die Fake-Bridge (`tools/homestation-bridge/kosmo_bridge/
 * main.py` `_fake_worker_step`) liefert IMMER `worker: 'fake-worker'`. Diese
 * Suite ist der EINZIGE Ort, an dem der Echt-Zweig überhaupt ausgeführt wird
 * — mit einem KÜNSTLICHEN JobRecord-Ausschnitt, nicht über einen echten
 * Bridge-Roundtrip. Bis zu einer echten HomeStation-Abnahme (0.8.10+,
 * Owner-Termin) bleibt er ein unbewiesener Live-Pfad.
 */
describe('bildLabel — Herkunfts-Label (E13)', () => {
  it('worker fehlt → «Vorschau (Fake-Render)» (Default-/Rückwärtskompatibilitäts-Fall)', () => {
    expect(bildLabel({})).toBe('Vorschau (Fake-Render)');
  });

  it("worker === 'fake-worker' → «Vorschau (Fake-Render)» (Container-Normalfall, jede Fake-Bridge-Antwort)", () => {
    expect(bildLabel({ worker: 'fake-worker' })).toBe('Vorschau (Fake-Render)');
    expect(bildLabel({ worker: 'fake-worker', requestedStyle: 'lineart' })).toBe('Vorschau (Fake-Render)');
  });

  it('echter Worker + requestedStyle "lineart" → «Strichzeichnung (Line-Art)» (Container-unerreichbar, s. Kopfkommentar)', () => {
    expect(bildLabel({ worker: 'homestation-1', requestedStyle: 'lineart' })).toBe('Strichzeichnung (Line-Art)');
  });

  it('echter Worker + requestedStyle undefined → «Render (Cycles)» (Container-unerreichbar, s. Kopfkommentar)', () => {
    expect(bildLabel({ worker: 'homestation-1' })).toBe('Render (Cycles)');
    expect(bildLabel({ worker: 'homestation-1', requestedStyle: undefined })).toBe('Render (Cycles)');
  });

  it('echter Worker + requestedStyle "none"/"redux"/… (kein Line-Art) → «Render (Cycles)»', () => {
    expect(bildLabel({ worker: 'homestation-1', requestedStyle: 'none' })).toBe('Render (Cycles)');
    expect(bildLabel({ worker: 'homestation-1', requestedStyle: 'redux' })).toBe('Render (Cycles)');
  });
});
