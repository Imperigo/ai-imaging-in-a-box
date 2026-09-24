import { describe, expect, it } from 'vitest';
import { messeBildGroesse, platziereBildAufsBlatt } from '../src/modules/vis/vis-jobs';

/**
 * **Owner-Entscheid 04.09.2026: der Bilddeckel faellt.**
 *
 * Diese Datei bewachte von v0.9.55 bis zum 04.09.2026 die MELDUNG eines
 * Tors, das Bilder ueber 1 048 576 Base64-Zeichen abgewiesen hat (ROADMAP
 * 1270, Owner-Entscheid 02.09.: «Meldung verbessern, Deckel nicht
 * anfassen»). Das Tor ist jetzt weg — fuer die Zahl gab es keinen
 * auffindbaren technischen Grund, und die Meldung verglich Base64-ZEICHEN,
 * waehrend sie MEGABYTE anzeigte.
 *
 * **Warum die Datei bleibt und nicht geloescht wird.** Ein entfernter Deckel
 * hinterlaesst sonst genau das, was hier nie stehen soll: Faelle, die still
 * gruen bleiben, weil sie nichts mehr pruefen. Die Auflage zum Entscheid
 * lautete woertlich, die Probe muesse MITWANDERN. Sie prueft darum jetzt
 * zwei Dinge, die es wirklich gibt:
 *
 *  1. **Die Messung stimmt** — sie ist geblieben, nur das Tor ist weg.
 *  2. **Das Tor ist wirklich weg** — eine Groesse, die frueher abgewiesen
 *     wurde, wird nicht mehr wegen ihrer Groesse abgewiesen.
 *
 * **Was jetzt die Grenze ist, gemessen:** der Yjs-Sync-Server deckelt die
 * einzelne Nachricht auf `KOSMO_SYNC_MAX_BYTES`, Vorgabe 8 MiB
 * (`tools/sync-server/src/server.mjs:49`, als `maxPayload` an die
 * ws-Bibliothek gereicht, Zeile 143). Rund achtmal hoeher als das gefallene
 * Tor — und haerter, denn dort bricht die Verbindung, statt zu melden.
 */
function dataUrlMitBase64Zeichen(zeichen: number): string {
  return `data:image/png;base64,${'A'.repeat(zeichen)}`;
}

/** Die Zahl, die das gefallene Tor benutzt hat — nur noch als Bezugsgroesse. */
const FRUEHERES_TOR_ZEICHEN = 1_048_576;

describe('Bildgroesse: gemessen wird weiter, abgewiesen nicht mehr', () => {
  it('rechnet Base64-Zeichen korrekt in Bytes um (vier Zeichen je drei Bytes)', () => {
    // 2 MiB Base64-Zeichen -> 1.5 MiB echte Bilddaten. Diese Umrechnung war
    // schon vor dem Entscheid richtig und bleibt es; sie ist der Grund, aus
    // dem die alte Meldung zwei Einheiten in einem Satz mischen KONNTE.
    const gemessen = messeBildGroesse(dataUrlMitBase64Zeichen(2 * FRUEHERES_TOR_ZEICHEN));
    expect(gemessen.base64Zeichen).toBe(2 * FRUEHERES_TOR_ZEICHEN);
    expect(gemessen.bytes).toBe(1_572_864);
    expect(gemessen.mbText).toBe('1.5');
  });

  it('zieht die «=»-Auffuellung ab, statt sie als Bilddaten zu zaehlen', () => {
    // Gegenprobe mit Widerspruchsmoeglichkeit: ohne Abzug kaemen 3 Bytes
    // heraus, nicht 1.
    expect(messeBildGroesse('data:image/png;base64,QQ==').bytes).toBe(1);
    expect(messeBildGroesse('data:image/png;base64,QUE=').bytes).toBe(2);
    expect(messeBildGroesse('data:image/png;base64,QUFB').bytes).toBe(3);
  });

  it('kommt auch ohne dataURL-Kopf zurecht (roher Base64-Text)', () => {
    expect(messeBildGroesse('QUFB').bytes).toBe(3);
  });

  it('DAS TOR IST WEG: ein frueher abgewiesenes Bild faellt nicht mehr an seiner Groesse', () => {
    // Der eigentliche Waechter dieses Entscheids. Frueher warf
    // `platziereBildAufsBlatt` fuer genau diese Groesse VOR jedem
    // Store-Zugriff «zu gross für das Blatt». In dieser Umgebung fehlt der
    // Store, ein Wurf ist also weiterhin erlaubt — aber er darf NICHT mehr
    // der Deckel sein. Kaeme das Tor zurueck, faellt dieser Fall.
    let meldung = '';
    try {
      platziereBildAufsBlatt(dataUrlMitBase64Zeichen(2 * FRUEHERES_TOR_ZEICHEN), 'Probe');
    } catch (err) {
      meldung = err instanceof Error ? err.message : String(err);
    }
    expect(meldung).not.toMatch(/zu gross für das Blatt/);
    expect(meldung).not.toMatch(/Kantenlänge/);
  });
});
