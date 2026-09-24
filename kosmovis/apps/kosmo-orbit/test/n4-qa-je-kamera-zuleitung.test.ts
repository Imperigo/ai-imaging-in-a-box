import { beforeEach, describe, expect, it } from 'vitest';
import { useVisRuntime, type JobQaJeKamera } from '../src/modules/vis/vis-runtime';
import { kameraQaZeilen } from '../src/modules/vis/varianten-diff';

/**
 * N4 — die Zuleitung. N2 hat die Anzeige fuer `qa_je_kamera` gebaut und dabei
 * SELBST gemeldet, dass sie in der echten App leer bleibt: `NodeCanvas.tsx`
 * reichte nur `qa: j.result.qa` weiter, das Geschwisterfeld `qa_je_kamera`
 * fiel unterwegs weg. Eine Anzeige ohne Zuleitung ist genau die Klasse
 * «gebaut und nicht bestellt» (ROADMAP 1063).
 *
 * Diese Datei bewacht die zwei Glieder, die sich in einer Probe fassen
 * lassen: der Laufzeit-Zustand traegt das Feld durch `patchLauf`, und die
 * Anzeige-Funktion liest genau die Form, die dort ankommt. Das dritte Glied
 * — die drei Stellen in `NodeCanvas.tsx` selbst — ist hier NICHT gepruefet
 * (kein Render der Datei in dieser Suite); dass es dieselbe Form benutzt,
 * haelt `npm run typecheck` fest, nicht diese Datei.
 */

const EINTRAEGE: JobQaJeKamera[] = [
  { kamera: 'eingang', geometry: { passed: true, method: 'depth-anything-v2' } },
  { kamera: 'uebersicht', geometry: { passed: false, method: 'depth-anything-v2' } },
];

beforeEach(() => {
  useVisRuntime.setState({ laeufe: {} });
});

/** Legt einen fertigen Lauf ab und gibt zurueck, was `NodeCanvas.tsx` daraus
 *  als `quelle.qaJeKamera` weiterreichen wuerde — die Probe liest also den
 *  Wert AUS dem Laufzeit-Zustand, statt ihn danebenzulegen. */
function useProbeLauf(): JobQaJeKamera[] | undefined {
  useVisRuntime.getState().setzeLauf('nq', { status: 'gesendet' });
  useVisRuntime.getState().patchLauf('nq', {
    status: 'fertig',
    jobId: 'j1',
    bild: 'data:image/png;base64,AA',
    qaJeKamera: EINTRAEGE,
  });
  return useVisRuntime.getState().laeufe['nq']?.qaJeKamera;
}

describe('N4 — qa_je_kamera kommt vom Job bis in die Anzeige', () => {
  it('patchLauf traegt qaJeKamera durch den Laufzeit-Zustand', () => {
    // `patchLauf` MISCHT nur in einen VORHANDENEN Lauf und tut ohne ihn still
    // gar nichts (`vis-runtime.ts`: `if (!alt) return s;`) — beim Schreiben
    // dieser Probe zuerst uebersehen und am roten Lauf gelernt. `NodeCanvas.tsx`
    // trifft das nie, weil dort `setzeLauf` beim Absenden vorausgeht.
    useVisRuntime.getState().setzeLauf('n1', { status: 'gesendet' });
    useVisRuntime.getState().patchLauf('n1', {
      status: 'fertig',
      jobId: 'j1',
      bild: 'data:image/png;base64,AA',
      qaJeKamera: EINTRAEGE,
    });

    const lauf = useVisRuntime.getState().laeufe['n1'];
    expect(lauf?.qaJeKamera).toHaveLength(2);
    expect(lauf?.qaJeKamera?.[0]?.kamera).toBe('eingang');
  });

  it('was im Lauf steht, liest die Anzeige-Funktion unveraendert', () => {
    // Genau die Form, die `patchLauf` im Fall darueber ablegt und die
    // `NodeCanvas.tsx` als `quelle.qaJeKamera` weiterreicht.
    const zeilen = kameraQaZeilen(useProbeLauf());

    expect(zeilen).toHaveLength(2);
    expect(zeilen[0]?.kamera).toBe('eingang');
    expect(zeilen[0]?.bestanden).toBe(true);
    expect(zeilen[1]?.kamera).toBe('uebersicht');
    expect(zeilen[1]?.bestanden).toBe(false);
  });

  it('ohne qaJeKamera bleibt alles wie vor diesem Paket — kein erfundener Eintrag', () => {
    useVisRuntime.getState().setzeLauf('n2', { status: 'gesendet' });
    useVisRuntime.getState().patchLauf('n2', {
      status: 'fertig',
      jobId: 'j2',
      bild: 'data:image/png;base64,AA',
    });

    expect(useVisRuntime.getState().laeufe['n2']?.qaJeKamera).toBeUndefined();
    expect(kameraQaZeilen(undefined)).toHaveLength(0);
  });
});
