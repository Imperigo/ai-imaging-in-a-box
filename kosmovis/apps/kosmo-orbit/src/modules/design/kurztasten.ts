/**
 * STELLVERTRETER für `apps/kosmo-orbit/src/modules/design/kurztasten.ts` (KosmoOrbit, 329 Zeilen).
 *
 * Runde 26 (14.10.2026): Die Insel-Bühne (`IslandShell.tsx`) fragt hier nur zwei Dinge:
 * liegt der Fokus in einem Eingabefeld, und öffnet die Taste das Kreismenü (Q). Beide
 * Funktionen sind wörtlich. Die Kurztasten der Zeichenwerkzeuge und die Maus im 2D-Plan
 * hängen am Grundriss (`plan-hit-test.ts`) und bleiben drüben.
 */

export function istEingabefeld(el: { tagName?: string; isContentEditable?: boolean } | null): boolean {
  if (!el) return false;
  return el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.isContentEditable === true;
}

export function istKreismenueTaste(
  event: Pick<KeyboardEvent, 'key' | 'repeat' | 'metaKey' | 'ctrlKey' | 'altKey'>,
  fokusImEingabefeld: boolean,
): boolean {
  if (event.repeat || event.metaKey || event.ctrlKey || event.altKey || fokusImEingabefeld) return false;
  return event.key.toLowerCase() === 'q';
}
