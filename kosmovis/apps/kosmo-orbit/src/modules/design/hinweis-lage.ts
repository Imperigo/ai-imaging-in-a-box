/**
 * Gerätebefund LW, Nachprobe Runde 17 (Punkt 1): die schwebenden Hinweise (`.dw-hinweise`, etwa das
 * Bestand-Angebot nach einem IFC-Import) standen mittig oben über der ganzen Arbeitsfläche. In der 3D-Ansicht
 * liegen dort aber Ansichtswürfel und Schnitt-Regler (KosmoDraw) — sie deckten den Text zu.
 *
 * Die Hinweise weichen aus, ohne die Bedienteile anzufassen (die gehören KosmoDraw): `hinweisLage` sucht in
 * der Höhe des Hinweises die breiteste freie Strecke neben den Hindernissen und setzt ihn dort hin, so nah
 * an die Mitte wie möglich. Reicht keine Strecke für `MIN_BREITE`, rückt er unter die Hindernisse.
 * Reine Rechnung, ohne DOM — der Haken `useHinweisLage` misst und setzt.
 */
import { useLayoutEffect, type RefObject } from 'react';

export interface Kasten {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

export const WUNSCH_BREITE = 720;
export const MIN_BREITE = 320;
const RAND = 16;
const LUFT = 8;

/** Lage relativ zum Feld: linker Rand, Breite, oberer Rand. */
export function hinweisLage(feld: Kasten, obenWunsch: number, hoehe: number, hindernisse: readonly Kasten[]): { left: number; width: number; top: number } {
  const innen = { von: feld.left + RAND, bis: feld.right - RAND };
  const mitte = (feld.left + feld.right) / 2;
  let oben = feld.top + obenWunsch;
  for (let versuch = 0; versuch < 4; versuch++) {
    const imBand = hindernisse.filter((h) => h.top < oben + hoehe + LUFT && h.bottom > oben - LUFT && h.right > innen.von && h.left < innen.bis);
    const strecken: { von: number; bis: number }[] = [];
    let von = innen.von;
    for (const h of [...imBand].sort((a, b) => a.left - b.left)) {
      if (h.left - LUFT > von) strecken.push({ von, bis: h.left - LUFT });
      von = Math.max(von, h.right + LUFT);
    }
    if (innen.bis > von) strecken.push({ von, bis: innen.bis });
    const beste = strecken.reduce<{ von: number; bis: number } | null>((a, s) => (!a || s.bis - s.von > a.bis - a.von ? s : a), null);
    if (beste && beste.bis - beste.von >= Math.min(MIN_BREITE, innen.bis - innen.von)) {
      const breite = Math.min(WUNSCH_BREITE, beste.bis - beste.von);
      const links = Math.min(Math.max(mitte - breite / 2, beste.von), beste.bis - breite);
      return { left: links - feld.left, width: breite, top: oben - feld.top };
    }
    // Keine Strecke reicht: unter die Hindernisse dieses Bandes.
    oben = Math.max(...imBand.map((h) => h.bottom)) + LUFT;
  }
  const breite = Math.min(WUNSCH_BREITE, innen.bis - innen.von);
  return { left: mitte - breite / 2 - feld.left, width: breite, top: oben - feld.top };
}

/** Die Bedienteile, denen die Hinweise ausweichen (Kennungen von KosmoDraw, nur gelesen). */
export const HINWEIS_HINDERNISSE = ['[data-testid="c1-wuerfel"]', '[data-testid="d5-schnitt-regler"]'];

function kasten(el: Element): Kasten {
  const r = el.getBoundingClientRect();
  return { left: r.left, right: r.right, top: r.top, bottom: r.bottom };
}

/**
 * Misst Feld, Hinweis und Hindernisse und setzt `left/width/top` des Hinweisstapels. Läuft bei jeder
 * Grössenänderung und wenn Bedienteile kommen oder gehen (Ansichtswechsel).
 */
export function useHinweisLage(stapelRef: RefObject<HTMLElement | null>, obenWunsch: number, aktiv: boolean): void {
  useLayoutEffect(() => {
    const stapel = stapelRef.current;
    const feldEl = stapel?.offsetParent as HTMLElement | null;
    if (!aktiv || !stapel || !feldEl) return undefined;
    let geplant = 0;
    const lege = () => {
      geplant = 0;
      const feld = kasten(feldEl);
      const hindernisse = HINWEIS_HINDERNISSE.flatMap((s) => Array.from(feldEl.querySelectorAll(s)))
        .filter((el) => getComputedStyle(el).visibility !== 'hidden')
        .map(kasten)
        .filter((k) => k.right > k.left);
      const l = hinweisLage(feld, obenWunsch, stapel.offsetHeight, hindernisse);
      stapel.style.left = `${Math.round(l.left)}px`;
      stapel.style.width = `${Math.round(l.width)}px`;
      stapel.style.top = `${Math.round(l.top)}px`;
      stapel.style.transform = 'none';
    };
    const plane = () => {
      if (!geplant) geplant = requestAnimationFrame(lege);
    };
    lege();
    const ro = typeof ResizeObserver === 'function' ? new ResizeObserver(plane) : null;
    ro?.observe(feldEl);
    ro?.observe(stapel);
    // Kommen/gehen Bedienteile (childList) oder verrücken sie nur (Würfel und Regler setzen ihre Lage als
    // `style`, etwa beim Wechsel 3D ↔ geteilt) — beides verschiebt die freie Strecke.
    // Die eigenen Lage-Schreibungen (und alles im Stapel) zählen nicht — sonst nährte sich die Schleife selbst.
    const mo = new MutationObserver((eintraege) => {
      if (eintraege.some((e) => !stapel.contains(e.target))) plane();
    });
    mo.observe(feldEl, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'class'] });
    window.addEventListener('resize', plane);
    return () => {
      if (geplant) cancelAnimationFrame(geplant);
      ro?.disconnect();
      mo.disconnect();
      window.removeEventListener('resize', plane);
      stapel.style.removeProperty('left');
      stapel.style.removeProperty('width');
      stapel.style.removeProperty('top');
      stapel.style.removeProperty('transform');
    };
  }, [stapelRef, obenWunsch, aktiv]);
}
