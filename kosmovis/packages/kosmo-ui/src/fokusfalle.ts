import { useEffect, type RefObject } from 'react';

/**
 * `useFokusFalle` (v0.6.5-Restpunkt, im Zug von v0.6.6 in `overlay.tsx`
 * entstanden, hier mit P-g / Tastatur-Rückgrat aus `overlay.tsx:31`
 * herausgezogen) — solange `aktiv`, zykliert Tab/Shift+Tab innerhalb von
 * `containerRef` statt den Fokus aus dem Overlay hinauswandern zu lassen.
 *
 * Dies ist ein reiner Umzug, keine Verbesserung: der Hook existierte bereits
 * fertig und generisch in `overlay.tsx`, war dort aber NIE exportiert — von
 * aussen unerreichbar, obwohl seine Signatur (`RefObject`, `boolean`) schon
 * lange konsumierbar war. Genau denselben Weg ist zuvor `useOverlaySchliessen`
 * gegangen (`overlay-schliessen.ts:4-8` sagt es wörtlich) — dieselbe
 * Begründung gilt hier: ein künftiges Overlay soll die Falle importieren
 * können, ohne `overlay.tsx` anzufassen oder die Logik neu abzuschreiben.
 *
 * ## API
 *
 * ```ts
 * useFokusFalle(containerRef, aktiv);
 * ```
 *
 * `containerRef` ist der Container, dessen fokussierbare Nachfahren
 * (`FOKUSIERBAR_AUSWAHL` unten) den Zyklus bilden — bei `KDialog` die
 * Dialog-Box, bei `KMenu` das `role=menu`-Element. Ist `aktiv` falsch, oder
 * hat der Container keine fokussierbaren Nachfahren, tut der Hook nichts.
 *
 * Verhalten IDENTISCH zum Original in `overlay.tsx`: Tab am letzten
 * fokussierbaren Element (oder wenn der Fokus den Container verlassen hat)
 * springt zum ersten; Shift+Tab am ersten (oder ausserhalb) springt zum
 * letzten. `e.preventDefault()` nur in diesen beiden Fällen — normales
 * Tab-Wandern INNERHALB des Containers bleibt unangetastet.
 *
 * ## Verhältnis zu `rollfokus.ts`
 *
 * Zwei verschiedene Tastatur-Verträge, die einander ergänzen, nicht
 * ersetzen: `useFokusFalle` hält den Fokus INNERHALB eines Overlays fest
 * (Tab-Reihenfolge des Browsers, ein Container), `useRollfokus`
 * (`rollfokus.ts`) steuert die BEWEGUNG INNERHALB einer Gruppe
 * gleichrangiger Elemente (Pfeiltasten, `tabIndex`-Rotation) — ein `KMenu`
 * könnte künftig beide zugleich tragen: die Falle hält den Fokus im Menü,
 * der Rollfokus bewegt ihn zwischen den Einträgen.
 *
 * ## SSR-/jsdom-Sicherheit
 *
 * Der Effect fasst `document` nur innerhalb seines Bodies an (React führt
 * Effects nie während SSR/`renderToString` aus); `containerRef.current ===
 * null` lässt ihn früh und geräuschlos aussteigen (Element noch nicht
 * gemountet oder bereits unmountet).
 *
 * ## Bestehende Konsumenten (unverändert, nur der Importpfad wechselt)
 *
 * `KMenu` und `KDialog` in `overlay.tsx` — Verhalten byte-gleich, belegt
 * durch Rot-vor-Grün gegen die unveränderten Bestandstests
 * `test/komponenten.test.tsx` (Fokus-Trap-Suiten) und
 * `test/overlay-schliessen.test.tsx`.
 *
 * `KSelect` (`select.tsx:37-38`) verzichtet BEWUSST auf diese Falle — es
 * hält den Fokus auf dem Trigger und steuert die Auswahl per
 * `aria-activedescendant` statt echtem DOM-Fokuswechsel. Daran ändert
 * dieser Umzug nichts.
 */
const FOKUSIERBAR_AUSWAHL =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Fokus-Falle: solange `aktiv`, zykliert Tab/Shift+Tab innerhalb von
 * `containerRef`. Siehe Datei-Kopfkommentar für die volle Doku.
 */
export function useFokusFalle(containerRef: RefObject<HTMLElement | null>, aktiv: boolean): void {
  useEffect(() => {
    if (!aktiv) return undefined;
    const behandleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      const container = containerRef.current;
      if (!container) return;
      const fokussierbare = Array.from(container.querySelectorAll<HTMLElement>(FOKUSIERBAR_AUSWAHL));
      if (fokussierbare.length === 0) return;
      const erster = fokussierbare[0]!;
      const letzter = fokussierbare[fokussierbare.length - 1]!;
      const aktives = document.activeElement as HTMLElement | null;
      const innerhalb = aktives !== null && container.contains(aktives);
      if (e.shiftKey) {
        if (!innerhalb || aktives === erster) {
          e.preventDefault();
          letzter.focus();
        }
      } else if (!innerhalb || aktives === letzter) {
        e.preventDefault();
        erster.focus();
      }
    };
    document.addEventListener('keydown', behandleTab);
    return () => document.removeEventListener('keydown', behandleTab);
  }, [aktiv, containerRef]);
}
