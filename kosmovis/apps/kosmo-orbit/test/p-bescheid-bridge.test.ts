import { describe, expect, it } from 'vitest';
import { bridgeBescheid, type BescheidLage } from '../src/modules/vis/bridge-bescheid';

/**
 * P-BESCHEID (B43 Teil 2 §10) — «ein 401 ist kein Offline».
 *
 * Gemessen am laufenden System: die App meldete «Bridge nicht erreichbar
 * (Offline)», während `/health` mit 200 antwortete und die Render-Routen
 * 401 gaben. Die Meldung schickte den Nutzer die Bridge neustarten statt
 * den Token prüfen.
 */

const GRUNDLAGE: BescheidLage = {
  netzfehler: false,
  tokenGesetzt: false,
  cspVerdacht: false,
};

const lage = (teil: Partial<BescheidLage>): BescheidLage => ({ ...GRUNDLAGE, ...teil });

describe('P-BESCHEID — die App misst, statt zu raten', () => {
  it('DER BEFUND: Netzfehler, aber /health antwortet → nicht «offline», sondern Token', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, healthErreichbar: true }), 'Failed to fetch');
    expect(b.art).toBe('token-fehlt');
    expect(b.text).toMatch(/ANTWORTET/);
    expect(b.text, 'die Meldung darf NICHT zum Neustart raten').toMatch(/[Nn]icht die Bridge neustarten/);
    expect(b.text).not.toMatch(/\(Offline\)/);
  });

  it('derselbe Fall mit hinterlegtem Token nennt den Token als verdächtig, nicht sein Fehlen', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, healthErreichbar: true, tokenGesetzt: true }), 'x');
    expect(b.art).toBe('token-abgelehnt');
    expect(b.text).toMatch(/passt der hinterlegte Bridge-Token nicht/);
  });

  it('sie behauptet nicht, welche der zwei Ursachen es ist — Token oder CORS bleiben beide genannt', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, healthErreichbar: true }), 'x');
    expect(b.text).toMatch(/CORS/);
    expect(b.text).toMatch(/Token/i);
  });

  it('ein GESEHENER 401 braucht keine Gegenprobe — er ist eindeutig', () => {
    const b = bridgeBescheid(lage({ status: 401 }), 'x');
    expect(b.art).toBe('token-fehlt');
    expect(b.text).toMatch(/401/);
    expect(b.text).toMatch(/Neustart der Bridge hilft hier nicht/);
  });

  it('403 wird wie 401 behandelt — abgelehnt ist abgelehnt', () => {
    expect(bridgeBescheid(lage({ status: 403, tokenGesetzt: true }), 'x').art).toBe('token-abgelehnt');
  });

  it('Netzfehler UND stumme Health-Probe → jetzt ist «offline» eine Messung', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, healthErreichbar: false }), 'x');
    expect(b.art).toBe('offline');
    expect(b.text).toMatch(/auch die Health-Probe antwortet nicht/);
  });

  it('ohne Gegenprobe bleibt es beim alten, vorsichtigeren Wortlaut', () => {
    const b = bridgeBescheid(lage({ netzfehler: true }), 'x');
    expect(b.art).toBe('offline');
    expect(b.text).not.toMatch(/Health-Probe/);
  });

  it('der CSP-Verdacht behält Vorrang — er erklärt den Netzfehler vollständig', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, cspVerdacht: true, healthErreichbar: true }), 'x');
    expect(b.art).toBe('csp');
  });

  it('ein Fehler ohne Netzfehler und ohne Status bleibt der Rohtext — keine erfundene Erklärung', () => {
    const b = bridgeBescheid(lage({}), 'Irgendein anderer Fehler');
    expect(b.art).toBe('roh');
    expect(b.text).toBe('Irgendein anderer Fehler');
  });

  it('ein 500 ist kein Auth-Fall und wird nicht als Token-Problem ausgegeben', () => {
    expect(bridgeBescheid(lage({ status: 500 }), 'Job x: 500').art).toBe('roh');
  });

  // Nachtrag zu auf-orbit-20260824-06.md Punkt 1 («Luecke bleibt» oben in
  // diesem Auftrag): die 401/403-Meldungen nannten den Namen der
  // Umgebungsvariable nicht, die auf der BRUECKEN-Seite die Token-Pflicht
  // erst einschaltet (`KOSMO_BRIDGE_TOKEN`, s. `main.py:183,264`). Ein
  // Nutzer erfuhr nur «Token in den Einstellungen hinterlegen», nicht dass
  // er die Variable auf dem Home-PC auch ENTFERNEN koennte.
  it('401 (kein Token gesetzt) nennt KOSMO_BRIDGE_TOKEN und beide Wege', () => {
    const b = bridgeBescheid(lage({ status: 401 }), 'x');
    expect(b.text, 'nennt den Variablennamen der Bruecken-Seite').toMatch(/KOSMO_BRIDGE_TOKEN/);
    expect(b.text, 'Weg 1: Token in den Einstellungen hinterlegen').toMatch(/Einstellungen/);
    expect(b.text, 'Weg 2: Variable auf dem Home-PC entfernen').toMatch(/entfernt/);
    // Der scheinbare Widerspruch («Neustart hilft nicht» vs. «Neustart
    // noetig») muss aufgeloest bleiben: ein Neustart OHNE eine der beiden
    // Aenderungen hilft nicht — WIRD die Variable entfernt, ist er
    // Pflicht. Beide Haelften muessen im selben Text stehen.
    expect(b.text).toMatch(/Neustart der Bridge hilft hier nicht/);
    expect(b.text, 'Neustart ist Pflicht, WENN die Variable entfernt wird').toMatch(/danach neu starten/);
  });

  it('401 mit hinterlegtem, falschem Token nennt KOSMO_BRIDGE_TOKEN ebenso', () => {
    const b = bridgeBescheid(lage({ status: 401, tokenGesetzt: true }), 'x');
    expect(b.art).toBe('token-abgelehnt');
    expect(b.text).toMatch(/KOSMO_BRIDGE_TOKEN/);
    expect(b.text).toMatch(/entfernt/);
  });

  it('Netzfehler+Health-Probe (kein Token) nennt KOSMO_BRIDGE_TOKEN ebenfalls', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, healthErreichbar: true }), 'x');
    expect(b.text).toMatch(/KOSMO_BRIDGE_TOKEN/);
    expect(b.text).toMatch(/entfernt/);
    // Die alte Warnung «Nicht die Bridge neustarten» bleibt woertlich
    // stehen — sie gilt fuer den Weg «Token in den Einstellungen pruefen»,
    // nicht fuer den Weg «Variable entfernen».
    expect(b.text).toMatch(/Nicht die Bridge neustarten/);
  });

  it('GEGENPROBE: CSP-Meldung nennt KOSMO_BRIDGE_TOKEN NICHT — falscher Fall', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, cspVerdacht: true }), 'x');
    expect(b.art).toBe('csp');
    expect(b.text).not.toMatch(/KOSMO_BRIDGE_TOKEN/);
  });

  it('GEGENPROBE: reiner Offline-Fall (Health-Probe stumm) nennt es NICHT', () => {
    const b = bridgeBescheid(lage({ netzfehler: true, healthErreichbar: false }), 'x');
    expect(b.art).toBe('offline');
    expect(b.text).not.toMatch(/KOSMO_BRIDGE_TOKEN/);
  });

  it('keine Meldung ist so kurz, dass sie nur ein Symptom nennt', () => {
    const faelle: BescheidLage[] = [
      lage({ netzfehler: true, healthErreichbar: true }),
      lage({ status: 401 }),
      lage({ netzfehler: true, healthErreichbar: false }),
      lage({ netzfehler: true, cspVerdacht: true }),
    ];
    for (const f of faelle) {
      const b = bridgeBescheid(f, 'x');
      expect(b.text.length, `zu knapp fuer «${b.art}»`).toBeGreaterThan(60);
    }
  });
});
