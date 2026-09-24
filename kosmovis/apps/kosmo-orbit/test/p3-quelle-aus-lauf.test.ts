import { describe, expect, it } from 'vitest';
import { quelleAusLauf, type JobQaJeKameraEintrag } from '../src/modules/vis/varianten-diff';
import type { NodeLauf } from '../src/modules/vis/vis-runtime';
import type { JobQa } from '../src/modules/vis/vis-jobs';

/**
 * P3 (ROADMAP 1340) — die Wache fuer die «Zuleitung», die N4 gebaut und
 * selbst als unbewacht gemeldet hat: `NodeCanvas.tsx` faedelte `qaJeKamera`
 * an drei Stellen ein, ohne dass irgendeine Probe das je gepruefet haette
 * (die Datei wird in dieser Suite nicht gerendert, die Felder sind optional,
 * `typecheck` sieht ihr Fehlen also nicht — Gegenprobe vor diesem Paket
 * belegt: alle drei Stellen entfernt, Probe UND typecheck blieben gruen).
 *
 * Statt eines E2E-Falls (Weg a) ist die Abbildung «fertiger Lauf →
 * Kuratier-Quelle» aus `NodeCanvas.tsx` herausgezogen (Weg b,
 * `varianten-diff.ts:quelleAusLauf`) — `bildQuelle()` UND die
 * `renderKarten`-Zuordnung rufen jetzt beide NUR NOCH diese eine Funktion.
 * Eine Probe hier bewacht damit direkt beide frueheren Konsumenten, ohne
 * die `.tsx` zu rendern (`npm run e2e` bricht seit dem 26.08. schon bei der
 * Sammlung ab — B61-Bericht, ein fremder Strang repariert das).
 */

const QA_MINIMAL: JobQa = { verdict: { passed: true } };

const KAMERA_EINTRAEGE: JobQaJeKameraEintrag[] = [
  { kamera: 'eingang', geometry: { passed: true, method: 'depth-anything-v2' } },
  { kamera: 'uebersicht', geometry: { passed: false, method: 'depth-anything-v2' } },
];

function fertigerLauf(patch: Partial<NodeLauf> = {}): NodeLauf {
  return {
    status: 'fertig',
    jobId: 'j1',
    bild: 'data:image/png;base64,AA',
    qa: QA_MINIMAL,
    memoKey: 'k1',
    ...patch,
  };
}

describe('P3 — quelleAusLauf: die Wache fuer die Zuleitung (ROADMAP 1340)', () => {
  it('reicht qaJeKamera an eine fertige Quelle weiter, wenn der Lauf es traegt', () => {
    const quelle = quelleAusLauf(fertigerLauf({ qaJeKamera: KAMERA_EINTRAEGE }));

    expect(quelle).not.toBeNull();
    expect(quelle && 'jobId' in quelle ? quelle.qaJeKamera : undefined).toEqual(KAMERA_EINTRAEGE);
  });

  it('ohne qaJeKamera im Lauf bleibt das Feld weg — kein erfundener Eintrag', () => {
    const quelle = quelleAusLauf(fertigerLauf());

    expect(quelle).not.toBeNull();
    expect(quelle && 'jobId' in quelle ? quelle.qaJeKamera : 'FEHLT').toBeUndefined();
  });

  it('qa bleibt die Hauptauskunft, unveraendert weitergereicht', () => {
    const quelle = quelleAusLauf(fertigerLauf());

    expect(quelle && 'jobId' in quelle ? quelle.qa : undefined).toBe(QA_MINIMAL);
    expect(quelle && 'jobId' in quelle ? quelle.jobId : undefined).toBe('j1');
    expect(quelle && 'jobId' in quelle ? quelle.bild : undefined).toBe('data:image/png;base64,AA');
  });

  it('ohne fertiges Bild bleibt die Quelle null — kein Rendern eines leeren Laufs', () => {
    // `jobId`/`bild` bewusst GANZ WEGGELASSEN statt auf `undefined` gesetzt:
    // `NodeLauf` traegt sie ohne `| undefined` im Typ (exactOptionalPropertyTypes).
    const ohneJobId: NodeLauf = { status: 'fertig', bild: 'x', qa: QA_MINIMAL, memoKey: 'k1' };
    const ohneBild: NodeLauf = { status: 'fertig', jobId: 'j1', qa: QA_MINIMAL, memoKey: 'k1' };

    expect(quelleAusLauf(undefined)).toBeNull();
    expect(quelleAusLauf(fertigerLauf({ status: 'rendert' }))).toBeNull();
    expect(quelleAusLauf(ohneJobId)).toBeNull();
    expect(quelleAusLauf(ohneBild)).toBeNull();
  });
});
