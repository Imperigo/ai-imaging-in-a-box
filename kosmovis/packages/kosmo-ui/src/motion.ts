/**
 * Systemanimationen (v0.6.6 MOTION-KONZEPT-066 §4) — `mitUebergang()`
 * kapselt `document.startViewTransition` mit Feature-Detection: fehlt die
 * API ODER verlangt `prefers-reduced-motion: reduce` einen Verzicht, läuft
 * `wechsel()` direkt aus (No-op-Übergang) — sonst über eine echte View
 * Transition (altes Blatt weicht sofort, neues setzt mit `--k-feder`, die
 * eigentliche Choreografie lebt in CSS `::view-transition-*`-Regeln je
 * Konsument, nicht hier).
 *
 * Bewusst synchron aufrufbar (kein Promise-Rückgabewert nötig für die
 * Aufrufer in App.tsx) — wer auf den Abschluss warten will, kann künftig
 * `document.startViewTransition` selbst direkt nutzen; dieser Baustein
 * deckt den 0.6.6-Bedarf (Stationswechsel-Trigger) ab.
 */
export function mitUebergang(wechsel: () => void): void {
  const doc = typeof document === 'undefined' ? undefined : document;
  const reduziert =
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!doc || typeof doc.startViewTransition !== 'function' || reduziert) {
    wechsel();
    return;
  }
  doc.startViewTransition(() => {
    wechsel();
  });
}
