/**
 * FLIP-Utility (v0.7.2 W2-C, `docs/V072-VISUELLES-UPDATE-SPEZ.md` §4) — First/
 * Last/Invert/Play für Reihenfolge-/Grössen-Umbrüche (OrbitStart-Hub: Rang-
 * Umsortierung der Untertool-Kreise). Bewusst UNABHÄNGIG von `mitUebergang()`
 * (`motion.ts`, `document.startViewTransition`): FLIP animiert einzelne,
 * bereits vorhandene DOM-Knoten, die NUR Position/Grösse wechseln (keine
 * Ein-/Ausblendung), `startViewTransition` eignet sich dafür nicht gut
 * (ganze-Seite-Snapshot).
 *
 * Eigener `matchMedia`-Wächter (Spec §0 Regel 4: JS-Animationen prüfen
 * `prefers-reduced-motion` SELBST) — der globale CSS-Riegel in `aura.css`
 * greift nur für reine CSS-`animation`/`transition`, nicht für per-`rAF`
 * gesetzte Inline-Transforms wie hier.
 */

/** `element.getBoundingClientRect()`, eingefroren auf die vier Werte, die
 *  FLIP tatsächlich braucht — kleinere Signatur als `DOMRect` (leichter zu
 *  mocken in Tests ohne echtes DOM-Layout). */
export interface FlipRechteck {
  left: number;
  top: number;
  width: number;
  height: number;
}

export function reduzierteBewegungAktiv(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );
}

/** «First»: Position/Grösse VOR der DOM-/Style-Änderung einsammeln. Reiner
 *  Lese-Zugriff, kein Seiteneffekt. */
export function flipFirst(el: Element): FlipRechteck {
  const r = el.getBoundingClientRect();
  return { left: r.left, top: r.top, width: r.width, height: r.height };
}

/**
 * «Last→Invert→Play»: nach der DOM-/Style-Änderung aufrufen. Berechnet die
 * Differenz zur `first`-Messung, setzt sie SOFORT als (unsichtbaren) inversen
 * `transform` — dann, einen Frame später (`requestAnimationFrame`), eine CSS-
 * Transition zurück auf `transform: none`, was optisch als sanfter Übergang
 * vom alten an den neuen Platz erscheint.
 *
 * `prefers-reduced-motion`: setzt NICHTS (kein Transform, keine Transition) —
 * das Element springt direkt an seine neue, bereits im DOM stehende Position.
 */
export function flipPlay(
  el: HTMLElement,
  first: FlipRechteck,
  opts: { dauerMs?: number; easing?: string } = {},
): void {
  if (reduzierteBewegungAktiv()) return;
  const dauerMs = opts.dauerMs ?? 320;
  const easing = opts.easing ?? 'var(--k-ease-standard, cubic-bezier(0.4,0,0.2,1))';

  const last = el.getBoundingClientRect();
  const dx = first.left - last.left;
  const dy = first.top - last.top;
  const sx = last.width > 0 ? first.width / last.width : 1;
  const sy = last.height > 0 ? first.height / last.height : 1;

  // Keine messbare Verschiebung/Skalierung — nichts zu animieren (vermeidet
  // eine No-op-Transition, die trotzdem `transitionend` feuern würde).
  if (Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5 && Math.abs(sx - 1) < 0.01 && Math.abs(sy - 1) < 0.01) return;

  const vorher = el.style.transition;
  el.style.transition = 'none';
  el.style.transformOrigin = 'top left';
  el.style.transform = `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})`;

  requestAnimationFrame(() => {
    el.style.transition = `transform ${dauerMs}ms ${easing}`;
    el.style.transform = 'none';
    const aufraeumen = () => {
      el.style.transition = vorher;
      el.style.transformOrigin = '';
      el.removeEventListener('transitionend', aufraeumen);
    };
    el.addEventListener('transitionend', aufraeumen);
  });
}
