/**
 * v0.1.10 (HomeStation R53/v0.1.9): Claude startete per KosmoMaus einen Bibliothekslauf. Schritt 1 lief
 * noch im Nachlauf des Klicks, wurde von der Befehls-Wache abgefangen und blieb als Karte m-1 stehen —
 * die übrigen 83 Schritte liefen danach durch. Ein Lauf ist mit «Lauf starten» als Ganzes freigegeben;
 * seine Schritte fängt die Wache darum nicht einzeln ab. Eigenes kleines Modul, damit `kosmo-maus.ts`
 * die Lauf-Runtime nicht einbinden muss.
 */
let tiefe = 0;

export function alsLaufSchritt<T>(fn: () => T): T {
  tiefe += 1;
  try {
    return fn();
  } finally {
    tiefe -= 1;
  }
}

export function laufSchrittLaeuft(): boolean {
  return tiefe > 0;
}
