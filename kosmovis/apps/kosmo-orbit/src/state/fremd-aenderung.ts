/**
 * P1 (v0.9.60) — Auflage aus `docs/V0955-SPEZ-IPAD.md` §3a, Entscheid E:
 * «wo nicht offensichtlich ist, was Rückgängig treffen wird, sagt es die
 * Oberfläche.» Es bleiben ZWEI getrennte Undo-Ketten (Entscheid E,
 * unverändert) — `project-sync.ts`s `remoteAnwenden` ruft `history.record`
 * bis heute NIE auf (B93-Baubericht, die benannte Stelle für einen
 * künftigen Widerruf). Was fehlte, ist eine ehrliche Anzeige: ist die
 * zuletzt SICHTBARE Änderung im Doc eine, die «Rückgängig» als nächstes gar
 * nicht trifft (weil sie über den Sync ankam, nicht lokal entstand)?
 *
 * Bewusst ein eigenes, winziges Modul statt eines neuen Felds in
 * `project-store.ts` (dessen `ProjectState`-Form viele Aufrufer kennen) oder
 * eines Eingriffs in `project-sync.ts`s Kernpfad (`remoteAnwenden` bleibt
 * unangetastet bis auf den einen Meldeaufruf unten) — reiner Lese-/
 * Schreib-Zustand, kein neuer Store, kein Yjs-Typ, kein Sync-Protokoll-
 * Eingriff (Entscheid B gilt auch hier: keine neue Protokollschicht für
 * eine Bequemlichkeit).
 */

// Monotoner Zähler statt `Date.now()`: zwei Aufrufe in derselben
// Millisekunde (real möglich — `patchListener`/`remoteAnwenden` reagieren
// synchron auf einen Yjs-Event-Batch) wären mit Wall-Clock-Zeit nicht
// unterscheidbar («neuer als» bräuchte ein ECHTES Grösser, kein Gleichstand).
// Ein Zähler ist per Konstruktion streng aufsteigend, unabhängig von der
// Systemuhr-Auflösung.
let zaehler = 0;
let letzteLokaleFolge = 0;
let letzteFremdeFolge = 0;
let letzteFremdeKurz = '';

/** Nach jeder LOKALEN Doc-Änderung (Command, Undo, Redo) aufrufen — setzt
 *  den Massstab zurück, an dem eine Fremdänderung als «neuer als das
 *  letzte lokale Tun» erkannt wird. */
export function meldeLokaleAenderung(): void {
  letzteLokaleFolge = ++zaehler;
}

/** Nach einer angewendeten FREMDänderung aufrufen (`project-sync.ts`s
 *  `remoteAnwenden`) — `kurzform` ist ein knapper, menschenlesbarer Hinweis
 *  fürs Warntoast (z. B. Anzahl geänderter Entities). */
export function meldeFremdAenderung(kurzform: string): void {
  letzteFremdeFolge = ++zaehler;
  letzteFremdeKurz = kurzform;
}

/**
 * `null`, solange die letzte lokale Aktion die jüngste war (der normale
 * Fall — «Rückgängig» trifft, was man erwartet). Sonst der Kurzform-Text
 * der jüngeren Fremdänderung, die «Rückgängig» NICHT treffen wird — der
 * Aufrufer (`project-store.ts`s `undo()`) meldet ihn als Warnung, BEVOR der
 * eigentliche Undo-Schritt läuft (der selbst unverändert bleibt).
 */
export function rueckgaengigTraefeNichtDieLetzteSichtbareAenderung(): string | null {
  return letzteFremdeFolge > letzteLokaleFolge ? letzteFremdeKurz : null;
}

/** Nur für Tests: setzt Zähler und Merker zurück. */
export function _resetFuerTests(): void {
  zaehler = 0;
  letzteLokaleFolge = 0;
  letzteFremdeFolge = 0;
  letzteFremdeKurz = '';
}
