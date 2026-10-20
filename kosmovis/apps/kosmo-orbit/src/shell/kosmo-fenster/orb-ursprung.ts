/**
 * **Der Ursprung des Kosmo-Fensters: der Orb in der Ecke** (U1 «der Orb wird
 * zum Fensterkopf», Owner-Entscheid 01.10.2026; Visbox-Regel 4 «ein
 * Gegenstand, ein Weg»).
 *
 * Das Fenster waechst aus dem Orb und zieht sich beim Schliessen in ihn
 * zurueck. Dafuer muss bekannt sein, WO der Orb steht — und genau in dem
 * Moment, in dem das Fenster erscheint, ist er schon weg: die App blendet den
 * Eck-Orb aus, solange das Seitenfenster steht (`app.css`, `.keo-wurzel`). Eine
 * Messung des Orbs im Moment des Oeffnens fiele daher ins Leere.
 *
 * Darum merkt sich jeder Orb seine Mitte, solange er sichtbar ist
 * (`merkeOrbPunkt`), und das Fenster liest sie beim Oeffnen (`orbPunkt`). Das
 * ist dieselbe Idee wie `useHerkunft` (`@kosmo/ui`, «Fenster waechst aus dem
 * Knopf»), nur dass hier der Ausloeser nicht mehr da ist, wenn das Fenster
 * misst — und dass es auch stimmt, wenn das Panel schon laenger gemountet ist
 * (Auftrag im Hintergrund, «Kosmo fragen»): `useHerkunft` haelt den Punkt vom
 * ersten Rendern der Komponente fest und waere dann veraltet.
 *
 * Ohne gemerkten Orb (Zentrale, erste Messung vor dem ersten Orb) gilt die
 * Ecke: dort steht der Orb in jeder Station — 16 px vom Rand, 44 px gross.
 */

export interface OrbPunkt {
  x: number;
  y: number;
}

let gemerkt: OrbPunkt | null = null;

/** Abstand der Orb-Mitte von rechtem und unterem Rand in Ruhe (16 + 22 px). */
export const ORB_ECKE_ABSTAND = 38;

/** Merkt die Mitte eines sichtbaren Orb-Elements. Unsichtbare (Breite 0) werden ignoriert. */
export function merkeOrbPunkt(el: Element | null): void {
  if (!el) return;
  const r = el.getBoundingClientRect();
  if (r.width === 0 || r.height === 0) return;
  gemerkt = { x: r.left + r.width / 2, y: r.top + r.height / 2 };
}

/** Die Mitte des Orbs; ohne gemerkten Wert die Ecke unten rechts. */
export function orbPunkt(): OrbPunkt {
  if (gemerkt && typeof window !== 'undefined') {
    // Ein gemerkter Punkt ausserhalb des Fensters (Fenster wurde kleiner)
    // taugt nicht — dann gilt die Ecke.
    if (gemerkt.x <= window.innerWidth && gemerkt.y <= window.innerHeight) return gemerkt;
  }
  const b = typeof window !== 'undefined' ? window.innerWidth : 1280;
  const h = typeof window !== 'undefined' ? window.innerHeight : 800;
  return { x: b - ORB_ECKE_ABSTAND, y: h - ORB_ECKE_ABSTAND };
}

/** Nur fuer Proben: vergisst den gemerkten Orb. */
export function vergissOrbPunkt(): void {
  gemerkt = null;
}

/**
 * Setzt Ursprung und Verschiebung an einem Fenster, das aus dem Orb waechst.
 *
 * - `box`: das Fenster (`.kp-panel`).
 * - `kopfOrb`: der Orb im Fensterkopf (oder `null`); er fliegt von der Ecke
 *   an seinen Platz — `--kp-orb-dx/dy` sind seine Verschiebung dorthin zurueck.
 *
 * Gemessen wird OHNE laufende Bewegung (`animation: none`): sonst misst der
 * Browser die schon verkleinerte Box, und der Ursprung laege daneben
 * (derselbe Kniff wie in `useHerkunft`).
 */
export function setzeUrsprung(box: HTMLElement, kopfOrb: HTMLElement | null): OrbPunkt {
  const p = orbPunkt();
  // Beides wird gemessen, waehrend die Bewegung des Fensters AUS ist: der Kopf-Orb
  // liegt im Fenster, und ein schon auf 92 % verkleinertes Fenster verschobe
  // seine Mitte.
  const boxAnim = box.style.animation;
  const kopfAnim = kopfOrb?.style.animation ?? '';
  box.style.animation = 'none';
  if (kopfOrb) kopfOrb.style.animation = 'none';
  const r = box.getBoundingClientRect();
  const o = kopfOrb?.getBoundingClientRect() ?? null;
  box.style.animation = boxAnim;
  if (kopfOrb) kopfOrb.style.animation = kopfAnim;
  box.style.transformOrigin = `${Math.round(p.x - r.left)}px ${Math.round(p.y - r.top)}px`;
  if (kopfOrb && o) {
    // Die Verschiebung des Kopf-Orbs zur Ecke hin: Differenz der beiden Mitten.
    kopfOrb.style.setProperty('--kp-orb-dx', `${Math.round(p.x - (o.left + o.width / 2))}px`);
    kopfOrb.style.setProperty('--kp-orb-dy', `${Math.round(p.y - (o.top + o.height / 2))}px`);
  }
  return p;
}
