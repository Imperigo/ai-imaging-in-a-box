import { describe, expect, it } from 'vitest';
import { bridgeBescheid, type BescheidLage } from '../src/modules/vis/bridge-bescheid';

/**
 * KosmoVis-Messung am Geraet (06.10.2026, Integrator-Auftrag zu E156): in der
 * Desktop-App meldete der Render-Knoten «Bridge nicht erreichbar», obwohl der
 * Auftrag auf der Bruecke ANGEKOMMEN war. WARUM: der Browser schickt den POST
 * ab, die Bruecke nimmt ihn an, aber ohne CORS-Freigabe fuer die Herkunft der
 * App (`tauri://localhost`) verwirft der Browser die Antwort — der `fetch`
 * endet als TypeError, und auch die Gegenprobe `/health` scheitert aus
 * demselben Grund. «Offline» ist dann eine Behauptung, keine Messung, und sie
 * verleitet zum erneuten Senden (doppelter Auftrag).
 *
 * Dazu UI-Befund C3: der 401 soll mit dem Satz beginnen, der sagt, was zu tun
 * ist und WO.
 */

const GRUNDLAGE: BescheidLage = { netzfehler: false, tokenGesetzt: false, cspVerdacht: false };
const lage = (teil: Partial<BescheidLage>): BescheidLage => ({ ...GRUNDLAGE, ...teil });

describe('Bridge-Bescheid nach einem schreibenden Ruf (CORS-Befund E156)', () => {
  it('POST mit Netzfehler, Health-Probe stumm: NICHT «nicht erreichbar», sondern «kann angekommen sein»', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, healthErreichbar: false, schreibRuf: true }), 'Failed to fetch');
    expect(b.art).toBe('antwort-unlesbar');
    expect(b.text).not.toMatch(/nicht erreichbar/);
    expect(b.text).not.toMatch(/\(Offline\)/);
    expect(b.text).toMatch(/angekommen sein/);
    expect(b.text, 'nennt die wahrscheinliche Ursache').toMatch(/CORS/);
    expect(b.text, 'warnt vor dem doppelten Senden').toMatch(/nicht erneut senden|bevor .* erneut/i);
    expect(b.text, 'nennt den anderen Fall ehrlich mit').toMatch(/HomeStation-Bridge/);
  });

  it('POST mit Netzfehler ohne Gegenprobe: ebenso ehrlich unklar', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, schreibRuf: true }), 'x');
    expect(b.art).toBe('antwort-unlesbar');
    expect(b.text).not.toMatch(/nicht erreichbar/);
  });

  it('GEGENPROBE: ein lesender Ruf mit stummer Health-Probe bleibt «offline»', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, healthErreichbar: false }), 'x');
    expect(b.art).toBe('offline');
  });

  it('GEGENPROBE: POST, aber Health antwortet — es bleibt der Token-/CORS-Fall', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, healthErreichbar: true, schreibRuf: true }), 'x');
    expect(b.art).toBe('token-fehlt');
  });

  it('GEGENPROBE: CSP-Verdacht behaelt Vorrang, auch nach einem POST', () => {
    expect(bridgeBescheid(lage({ netzfehler: true, cspVerdacht: true, schreibRuf: true }), 'x').art).toBe('csp');
  });
});

describe('UI-Befund C3 — 401 ohne Token sagt zuerst, was zu tun ist', () => {
  it('beginnt mit «Bridge-Token fehlt — in Einstellungen ▸ HomeServer eintragen»', () => {
    const b = bridgeBescheid(lage({ status: 401 }), 'x');
    expect(b.art).toBe('token-fehlt');
    expect(b.text.startsWith('Bridge-Token fehlt — in Einstellungen ▸ HomeServer eintragen')).toBe(true);
  });

  it('GEGENPROBE: ein hinterlegter, falscher Token heisst NICHT «fehlt»', () => {
    const b = bridgeBescheid(lage({ status: 401, tokenGesetzt: true }), 'x');
    expect(b.text).not.toMatch(/^Bridge-Token fehlt/);
  });
});
