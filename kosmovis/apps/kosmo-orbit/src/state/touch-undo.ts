/**
 * Zwei-Finger-Doppeltipp-Undo — Einstellung (v0.8.3 P8/E10 §10.2, `docs/
 * V083-SPEZ.md`). Reiner localStorage-Spiegel nach dem BESTEHENDEN Muster
 * `kosmo.texturen`/`kosmo.abspielen`/`kosmo.eigencursor` (state/texturen.ts,
 * state/abspiel-ebene.ts, state/cursor-zustand.ts) — kein Store, keine
 * Reaktivität über Zustand/Yjs nötig, `IslandShell.tsx`s Gesten-Handler liest
 * den Wert nur beim tatsächlichen Zwei-Finger-Doppeltipp neu.
 *
 * **Default AUS** (anders als `kosmo.abspielen`, das Default AN ist) — die
 * Geste ist ein Vorschlag, kein Owner-Entscheid: `docs/ISLAND-UI-SPEZ.md` §8
 * Punkt 1 («Undo/Redo aufs iPad») steht dort wörtlich als «Ungeklärt» und
 * bleibt es — dieser Schalter nimmt die Owner-Frage NICHT vorweg, er bietet
 * nur einen ausdrücklich abschaltbaren (und default-abgeschalteten) Weg an.
 */
const KEY = 'kosmo.touch-undo-geste';

/** Ist die Geste aktiv? Default `false` — nur `'1'` schaltet sie ein. */
export function touchUndoGesteAktiv(): boolean {
  try {
    return typeof localStorage !== 'undefined' && localStorage.getItem(KEY) === '1';
  } catch {
    return false;
  }
}

/** Schreibt `kosmo.touch-undo-geste` (Einstellungen.tsx, Schalter
 *  `einstellung-touch-undo-geste`). */
export function setTouchUndoGesteEingestellt(an: boolean): void {
  try {
    if (typeof localStorage !== 'undefined') localStorage.setItem(KEY, an ? '1' : '0');
  } catch {
    /* localStorage kann in seltenen Umgebungen werfen — Einstellung ist optional */
  }
}
