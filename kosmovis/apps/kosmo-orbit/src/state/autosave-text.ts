import type { AutosaveLage } from './project-vault';

/**
 * Der Text der Autosave-Anzeige — **eine** Formel für beide Wege.
 *
 * Fund **F7** (`docs/UI-UX-2026-09-08-FEHLER-DATENVERLUST.md`): die Anzeige
 * kannte genau zwei Zustände, `'Auto-Save aktiv'` und
 * `Auto-gesichert <Uhrzeit>`. Einen dritten gab es nicht — schlug der
 * Schreibvorgang fehl, blieb die Uhrzeit des letzten **geglückten**
 * Speicherns stehen. Die Anzeige sagte «gesichert», während nichts gesichert
 * wurde.
 *
 * **Und sie stand zweimal da:** einmal inline in `App.tsx`, einmal als
 * eigene Funktion in `InselKopf.tsx` — zwei Kopien derselben Formel, die
 * beide denselben Fehler trugen. Darum liegt sie jetzt hier, an einer
 * Stelle, und beide Wege lesen von hier.
 *
 * **Warum der Grund im Fehlertext steht:** eine Anzeige, die nur «Fehler»
 * sagt, verschiebt die Frage bloss. `QuotaExceededError` sagt dem
 * Architekten, dass sein Speicher voll ist — das kann er beheben.
 */
export function autosaveText(lage: AutosaveLage): string {
  if (lage.stand === 'fehler') {
    return lage.grund ? `NICHT gesichert — ${lage.grund}` : 'NICHT gesichert (Grund unbekannt, s. Konsole)';
  }
  if (lage.stand === 'sichert') return 'sichert …';
  if (lage.iso === null) return 'Auto-Save aktiv';
  return `Auto-gesichert ${new Date(lage.iso).toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' })}`;
}
