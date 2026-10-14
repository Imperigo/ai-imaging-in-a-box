/**
 * Strg+Z / ⌘Z (rückgängig) und Strg+Y / ⇧⌘Z (wiederholen) in der Visbox-Knotenansicht.
 *
 * Visbox-eigen (14.10.2026, auf-20261014-284 D5): In KosmoOrbit hängt das Kürzel am Hauptprogramm
 * (`App.tsx`, `VerlaufKurztasten`), und das ist nicht Teil der Kopie — in Visbox wirkte Strg+Z
 * darum nicht, obwohl der fertige Anfang und jedes Verschieben einen Rückgängig-Schritt anlegen.
 * Dieselbe Wache wie dort: In einem Textfeld bleibt das Rückgängig des Browsers zuständig.
 */

const KEIN_TEXT_INPUT = new Set([
  'checkbox', 'radio', 'range', 'button', 'submit', 'reset', 'color', 'file', 'image',
]);

/** Wie `istTextEingabe` in KosmoOrbits `App.tsx`: Nur wo der Browser Text bearbeitet. */
export function istTextEingabe(ziel: { tagName?: string; isContentEditable?: boolean; type?: string } | null): boolean {
  if (!ziel) return false;
  if (ziel.isContentEditable || ziel.tagName === 'TEXTAREA') return true;
  if (ziel.tagName !== 'INPUT') return false;
  return !KEIN_TEXT_INPUT.has(String(ziel.type ?? 'text'));
}

export type Verlaufsschritt = 'rueckgaengig' | 'wiederholen' | null;

/** Welcher Schritt eine Taste ist — oder `null`, wenn sie nicht gemeint ist. */
export function verlaufsschritt(e: {
  key: string; ctrlKey: boolean; metaKey: boolean; altKey: boolean; shiftKey: boolean;
  target: unknown;
}): Verlaufsschritt {
  if (!(e.ctrlKey || e.metaKey) || e.altKey) return null;
  const taste = e.key.toLowerCase();
  if (taste !== 'z' && taste !== 'y') return null;
  if (istTextEingabe(e.target as never)) return null;
  return taste === 'y' || e.shiftKey ? 'wiederholen' : 'rueckgaengig';
}

/** Hängt die Kürzel an `ziel` (das Fenster) und gibt eine Abmeldung zurück. */
export function haengeVerlaufKurztastenAn(
  ziel: Pick<Window, 'addEventListener' | 'removeEventListener'>,
  verlauf: { undo(): unknown; redo(): unknown },
): () => void {
  const hoerer = (e: KeyboardEvent) => {
    const schritt = verlaufsschritt(e);
    if (!schritt) return;
    e.preventDefault();
    if (schritt === 'wiederholen') verlauf.redo();
    else verlauf.undo();
  };
  ziel.addEventListener('keydown', hoerer as EventListener);
  return () => ziel.removeEventListener('keydown', hoerer as EventListener);
}
