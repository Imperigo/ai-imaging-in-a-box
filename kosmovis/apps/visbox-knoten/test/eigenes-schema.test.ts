import { describe, expect, it, vi } from 'vitest';
import { bridgeBescheid } from '../../kosmo-orbit/src/modules/vis/bridge-bescheid';
import { BridgeHttpError } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import {
  aufDemVisboxServer,
  brueckeSagtDenSatz,
  brueckenAdresse,
  imEigenenSchema,
  koerperAlsBytes,
} from '../src/mappe';

/**
 * VISBOX-EIGEN («Visbox eigenständig», Schritt 1, 20.10.2026): Die Mac-App lädt die Knoten aus
 * ihrem Bündel über `visbox://app/knoten/`. Die Seite erkennt den Pfad wie am Heim-PC, baut die
 * Brücke aus ihrer eigenen Adresse (nicht aus `location.origin`) und schickt Rümpfe als Bytes.
 */
describe('eigenes Adressschema der Mac-App', () => {
  it('erkennt den Pfad der Knoten wie am Heim-PC', () => {
    expect(aufDemVisboxServer(new URL('visbox://app/knoten/').pathname)).toBe(true);
    expect(aufDemVisboxServer(new URL('https://heim.example:8443/knoten/').pathname)).toBe(true);
  });

  it('baut die Brücke aus der Adresse der Seite', () => {
    expect(brueckenAdresse('visbox://app/knoten/')).toBe('visbox://app/bruecke');
    expect(brueckenAdresse('visbox://app/knoten/index.html?ordner=x')).toBe('visbox://app/bruecke');
    // Am Heim-PC dasselbe wie bisher (`location.origin + '/bruecke'`).
    expect(brueckenAdresse('https://heim.example:8443/knoten/')).toBe('https://heim.example:8443/bruecke');
  });

  it('kennt das Schema', () => {
    expect(imEigenenSchema('visbox:')).toBe(true);
    expect(imEigenenSchema('https:')).toBe(false);
  });

  it('macht aus einem Formular Bytes mit seinem Typ samt boundary', async () => {
    const roh = vi.fn(async (_e: RequestInfo | URL, _i?: RequestInit) => new Response('{}'));
    const umschlag = koerperAlsBytes(roh as unknown as typeof fetch);
    const formular = new FormData();
    formular.append('scene', '{"a":1}');
    formular.append('model', new Blob([new Uint8Array([103, 108, 84, 70])], { type: 'model/gltf-binary' }), 'model.glb');
    await umschlag('visbox://app/bruecke/jobs', { method: 'POST', body: formular, headers: { 'X-Kosmo-Token': 't' } });
    const init = roh.mock.calls[0][1] as RequestInit;
    expect(init.body).toBeInstanceOf(ArrayBuffer);
    const koepfe = new Headers(init.headers);
    expect(koepfe.get('content-type')).toMatch(/^multipart\/form-data; boundary=/);
    expect(koepfe.get('x-kosmo-token')).toBe('t');
    expect(init.method).toBe('POST');
    // Der Heim-PC kann die Bytes wieder als Formular lesen.
    const zurueck = await new Response(init.body as ArrayBuffer, { headers: koepfe }).formData();
    expect(zurueck.get('scene')).toBe('{"a":1}');
    const modell = zurueck.get('model') as File;
    expect(new Uint8Array(await modell.arrayBuffer())).toEqual(new Uint8Array([103, 108, 84, 70]));
  });

  it('lässt Text, Bytes und Anfragen ohne Rumpf unverändert', async () => {
    const roh = vi.fn(async () => new Response('{}'));
    const umschlag = koerperAlsBytes(roh as unknown as typeof fetch);
    const text = { method: 'POST', body: '{"graphen":[]}', headers: { 'Content-Type': 'application/json' } };
    await umschlag('./graph', text);
    await umschlag('./mappe');
    expect(roh.mock.calls[0][1]).toBe(text);
    expect(roh.mock.calls[1][1]).toBeUndefined();
  });
});

/**
 * Schritt 2 (Entscheid 103b): Ohne Rechner antwortet die App auf die Render-Wege mit 503/502 und
 * einem Satz. Am Render-Knoten soll dieser Satz stehen, nicht «Bridge antwortet mit: 503».
 */
describe('ohne Rechner ein Satz am Render-Knoten', () => {
  const SATZ = 'Kein Heim-PC eingerichtet — Mappe und Rechnen gehen erst, wenn er gekoppelt ist.';
  const seite = () => 'visbox://app/knoten/';
  const antwort = (status: number, rumpf: string) => async () =>
    new Response(rumpf, { status, headers: { 'Content-Type': 'application/json' } });

  it('macht aus 503 mit Satz einen Fehler mit diesem Satz', async () => {
    const f = brueckeSagtDenSatz(antwort(503, JSON.stringify({ fehler: SATZ })) as unknown as typeof fetch, seite);
    await expect(f('visbox://app/bruecke/jobs', { method: 'POST' })).rejects.toThrow(SATZ);
    const g = brueckeSagtDenSatz(
      antwort(502, JSON.stringify({ fehler: 'Der Heim-PC ist nicht erreicht: x' })) as unknown as typeof fetch,
      seite,
    );
    await expect(g('visbox://app/bruecke/jobs/abc/artifacts/bild.png')).rejects.toThrow('Der Heim-PC ist nicht erreicht: x');
  });

  it('und genau dieser Satz steht dann am Knoten (bridgeBescheid, Art roh)', async () => {
    const f = brueckeSagtDenSatz(antwort(503, JSON.stringify({ fehler: SATZ })) as unknown as typeof fetch, seite);
    const fehler = await f('visbox://app/bruecke/jobs', { method: 'POST' }).catch((e: unknown) => e);
    // So baut `bescheidFuerBridgeFehler` die Lage aus einem Fehler, der weder Netzfehler noch
    // BridgeHttpError ist.
    expect(fehler).toBeInstanceOf(Error);
    expect(fehler).not.toBeInstanceOf(TypeError);
    expect(fehler).not.toBeInstanceOf(BridgeHttpError);
    const bescheid = bridgeBescheid(
      { netzfehler: false, tokenGesetzt: false, cspVerdacht: false, schreibRuf: true },
      (fehler as Error).message,
    );
    expect(bescheid).toEqual({ art: 'roh', text: SATZ });
    // OHNE UMSCHLAG stuende dort nur die Zahl.
    expect(bridgeBescheid({ netzfehler: false, status: 503, tokenGesetzt: false, cspVerdacht: false },
      new BridgeHttpError(503, 'Bridge antwortet mit').message).text).toBe('Bridge antwortet mit: 503');
  });

  it('Fund D: ein Auftrag, den der Heim-PC mit 400 und Satz abweist, steht mit dem Satz am Knoten', async () => {
    const abgewiesen = "Die Skizze 'ipad/skizze-20261022-1.png' steht nicht (mehr) in der Mappe «Demohaus» — verworfen oder nie abgelegt.";
    const f = brueckeSagtDenSatz(antwort(400, JSON.stringify({ fehler: abgewiesen })) as unknown as typeof fetch, seite);
    await expect(f('visbox://app/bruecke/jobs', { method: 'POST' })).rejects.toThrow(abgewiesen);
    // 409 (Grundlage fehlt) bleibt eine Antwort: die Kopie reicht dann das Modell nach.
    const g = brueckeSagtDenSatz(antwort(409, JSON.stringify({ fehler: 'Grundlage fehlt' })) as unknown as typeof fetch, seite);
    expect((await g('visbox://app/bruecke/jobs', { method: 'POST' })).status).toBe(409);
  });

  it('lässt alles andere unverändert durch', async () => {
    const satz = JSON.stringify({ fehler: SATZ });
    for (const [status, rumpf, weg] of [
      [200, '{"job_id":"j"}', 'visbox://app/bruecke/jobs'],
      [401, satz, 'visbox://app/bruecke/jobs'], // die Tür deutet bridgeBescheid selbst
      [503, satz, 'visbox://app/bruecke/health'], // die Gegenprobe zählt die Kopie selbst
      [503, satz, 'visbox://app/bruecke/gpu'],
      [503, satz, 'visbox://app/knoten/mappe'],
      [503, 'kein json', 'visbox://app/bruecke/jobs'],
      [503, '{"fehler":"  "}', 'visbox://app/bruecke/jobs'],
      [502, '{"anders":1}', 'visbox://app/bruecke/jobs'],
    ] as const) {
      const f = brueckeSagtDenSatz(antwort(status, rumpf) as unknown as typeof fetch, seite);
      const r = await f(weg);
      expect(r.status).toBe(status);
      expect(await r.text()).toBe(rumpf);
    }
  });
});
