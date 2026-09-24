/**
 * `cssVar()` (v0.8.8 / PA4, `docs/V088-SPEZ.md` §2 D7/§3, Token-Brücke Vis)
 * — kanonisierter Helfer für Stellen, die einen ECHTEN Hex-/Farbwert
 * brauchen statt einen `var(--k-…)`-String (2D-`CanvasRenderingContext2D`,
 * Farbrechnung), gemäss dem bestehenden Muster in `Viewport3D.tsx:811`
 * (`cssVar`, dort lokal, NICHT konsolidiert — Sanktion 6/§4: Viewport3D ist
 * PA4 tabu, die Konsolidierung des dortigen Helfers auf DIESEN hier bleibt
 * ein späterer Fable-Nachzug).
 *
 * Liest den aktuellen, berechneten Wert einer CSS-Custom-Property vom
 * Dokument-Wurzelelement (`getComputedStyle(document.documentElement)`) —
 * damit folgt der gelesene Wert IMMER dem gerade aktiven Theme/Akzent
 * (`[data-theme]`/`[data-akzent]` sitzen beide auf `<html>` bzw. werden von
 * dort vererbt), ohne dass der Aufrufer selbst auf Theme-Wechsel lauschen
 * muss — ein Neuzeichnen (z.B. nach einem Redraw-Trigger) genügt.
 */
export function cssVar(name: string, fallback: string): string {
  if (typeof document === 'undefined') return fallback;
  const wert = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return wert || fallback;
}
