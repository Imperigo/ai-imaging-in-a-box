import { describe, expect, it, vi } from 'vitest';
import { aufDemVisboxServer, brueckenAdresse, imEigenenSchema, koerperAlsBytes } from '../src/mappe';

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
