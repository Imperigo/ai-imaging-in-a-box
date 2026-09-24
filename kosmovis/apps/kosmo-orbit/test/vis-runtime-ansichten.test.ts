import { afterEach, describe, expect, it } from 'vitest';
import { ANSICHT_SLOTS, useVisRuntime, waehleAufnahme, type Aufnahme } from '../src/modules/vis/vis-runtime';

/**
 * v0.8.1 / P8 (0.7.2-Rest «Viz gespeicherte Ansichten + Review-Pins», Spec
 * §6.2, B-92/B-105) — die additiven `vis-runtime.ts`-Erweiterungen: drei
 * feste Slots (ISO/NORD/DETAIL) über `Aufnahme`-Zeiger + Kommentar-Pins auf
 * einer Aufnahme. Reiner Store-Test (kein DOM nötig, Muster
 * `vis-lebenszyklus.test.ts`).
 */

function aufnahme(id: string, zeit = Date.now()): Aufnahme {
  return { id, dataUrl: `data:image/png;base64,${id}`, zeit, kamera: 'aktuell' };
}

afterEach(() => {
  useVisRuntime.setState({ aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {} });
});

describe('vis-runtime — gespeicherte Ansichten (ISO/NORD/DETAIL)', () => {
  it('kennt genau die drei Slots ISO/NORD/DETAIL', () => {
    expect(ANSICHT_SLOTS).toEqual(['iso', 'nord', 'detail']);
  });

  it('speichert einen Slot mit Version 1 beim ersten Mal, zählt bei erneutem Speichern hoch', () => {
    useVisRuntime.getState().fuegeAufnahmeHinzu(aufnahme('a1'));
    useVisRuntime.getState().speichereAnsicht('iso', 'a1');
    expect(useVisRuntime.getState().gespeicherteAnsichten.iso).toMatchObject({ aufnahmeId: 'a1', version: 1 });

    useVisRuntime.getState().fuegeAufnahmeHinzu(aufnahme('a2'));
    useVisRuntime.getState().speichereAnsicht('iso', 'a2');
    expect(useVisRuntime.getState().gespeicherteAnsichten.iso).toMatchObject({ aufnahmeId: 'a2', version: 2 });

    // NORD bleibt unberührt — jeder Slot zählt unabhängig.
    expect(useVisRuntime.getState().gespeicherteAnsichten.nord).toBeUndefined();
  });

  it('entferneAnsicht löscht genau den einen Slot', () => {
    useVisRuntime.getState().fuegeAufnahmeHinzu(aufnahme('a1'));
    useVisRuntime.getState().speichereAnsicht('detail', 'a1');
    useVisRuntime.getState().entferneAnsicht('detail');
    expect(useVisRuntime.getState().gespeicherteAnsichten.detail).toBeUndefined();
  });

  it('waehleAufnahme(ohne kamera) liefert die jüngste — Basis für «aktuelle Ansicht speichern»', () => {
    const aeltere = aufnahme('alt', 1000);
    const neuere = aufnahme('neu', 2000);
    expect(waehleAufnahme({ alt: aeltere, neu: neuere })?.id).toBe('neu');
  });
});

describe('vis-runtime — Review-Pins', () => {
  it('legt einen Pin mit vergebener id/zeit an, an der übergebenen normierten Position', () => {
    const pin = useVisRuntime.getState().fuegeReviewPinHinzu('a1', { x: 0.25, y: 0.6, text: 'Fenster prüfen', wer: 'Du' });
    expect(pin.id).toMatch(/^pin-/);
    expect(pin.text).toBe('Fenster prüfen');
    expect(useVisRuntime.getState().reviewPins.a1).toEqual([pin]);
  });

  it('mehrere Pins auf verschiedenen Aufnahmen bleiben getrennt', () => {
    useVisRuntime.getState().fuegeReviewPinHinzu('a1', { x: 0.1, y: 0.1, text: 'eins', wer: 'Du' });
    useVisRuntime.getState().fuegeReviewPinHinzu('a2', { x: 0.2, y: 0.2, text: 'zwei', wer: 'Du' });
    expect(useVisRuntime.getState().reviewPins.a1).toHaveLength(1);
    expect(useVisRuntime.getState().reviewPins.a2).toHaveLength(1);
  });

  it('entferneReviewPin entfernt genau den einen Pin, lässt andere stehen', () => {
    const p1 = useVisRuntime.getState().fuegeReviewPinHinzu('a1', { x: 0.1, y: 0.1, text: 'eins', wer: 'Du' });
    const p2 = useVisRuntime.getState().fuegeReviewPinHinzu('a1', { x: 0.3, y: 0.3, text: 'zwei', wer: 'Du' });
    useVisRuntime.getState().entferneReviewPin('a1', p1.id);
    expect(useVisRuntime.getState().reviewPins.a1).toEqual([p2]);
  });

  it('entferneReviewPin auf unbekannter Aufnahme wirft nicht, ändert nichts', () => {
    expect(() => useVisRuntime.getState().entferneReviewPin('unbekannt', 'pin-x')).not.toThrow();
  });
});
