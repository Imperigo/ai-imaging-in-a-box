/**
 * L51 (Vorprobe R24, Punkt b): Die offene AUSTAUSCH-Leiste am unteren Rand lag über den Zoomleisten der Ansichten
 * (`navi-insel-3d`/`-2d`) und deckte deren Vollbild-Knopf. Gemessen am 14.10.2026 (Demohaus, 3D und Plan
 * nebeneinander): bei 1280 × 800 deckt die Leiste 70 px der 3D-Leiste, bei 1024 × 768 dazu den Rand der Plan-Leiste.
 *
 * Die Leiste weicht aus, die Zoomleisten bleiben, wo sie sind (sie gehören KosmoDraw, hier nur gelesen):
 *  1. **Zur Seite**, wenn sie zwischen die Hindernisse passt und dabei ihre Pille noch deckt. Sie öffnet sich beim
 *     Darüberfahren; rückte sie unter dem Zeiger weg, klappte sie zu und gleich wieder auf.
 *  2. **Sonst darüber.** Dann bleibt zwischen Leiste und Pillen-Platz eine unsichtbare Brücke (`--isl-steg-hoehe`), so
 *     breit wie die Pille. Die Pille liegt nie über einer Zoomleiste, die Brücke darum auch nicht.
 */
import { useLayoutEffect, type RefObject } from 'react';
import type { Kasten } from '../hinweis-lage';

/** Die Bedienteile, denen die untere Leiste ausweicht (Kennungen von KosmoDraw, nur gelesen). */
export const LEISTE_HINDERNISSE = '[data-testid^="navi-insel-"]';
/** Breite der Pille (`.isl-pill`, lange Achse), auf der die Leiste aufgeht. */
export const PILLE_BREITE = 88;
const LUFT = 8;
const RAND = 8;

const schneidet = (a: Kasten, b: Kasten) => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;

/**
 * Versatz der Leiste (`leiste`, Lage OHNE Ausweichen) und Höhe der Brücke darunter. `steg` ist 0, solange die Leiste
 * auf ihrer Zeile bleibt. Reine Rechnung.
 */
export function leisteAusweichen(leiste: Kasten, hindernisse: readonly Kasten[], feldBreite: number): { dx: number; dy: number; steg: number } {
  const im = hindernisse.filter((h) => schneidet(leiste, h));
  if (im.length === 0) return { dx: 0, dy: 0, steg: 0 };

  // 1. Zur Seite: die Lücken zwischen allen Hindernissen auf der Höhe der Leiste.
  const breite = leiste.right - leiste.left;
  const spielraum = (breite - PILLE_BREITE) / 2;
  const zeile = hindernisse
    .filter((h) => h.top < leiste.bottom && h.bottom > leiste.top)
    .sort((a, b) => a.left - b.left);
  const kanten = [RAND - LUFT, ...zeile.flatMap((h) => [h.left, h.right]), feldBreite - RAND + LUFT];
  let besterDx: number | null = null;
  for (let i = 0; i + 1 < kanten.length; i += 2) {
    const links = kanten[i]! + LUFT;
    const rechts = kanten[i + 1]! - LUFT;
    if (rechts - links < breite) continue;
    const dx = Math.min(Math.max(0, links - leiste.left), rechts - leiste.right);
    if (Math.abs(dx) <= spielraum && (besterDx === null || Math.abs(dx) < Math.abs(besterDx))) besterDx = dx;
  }
  if (besterDx !== null) return { dx: Math.round(besterDx), dy: 0, steg: 0 };

  // 2. Darüber, mit Brücke zum Platz der Pille.
  const dy = Math.min(...im.map((h) => h.top)) - LUFT - leiste.bottom;
  return { dx: 0, dy: Math.round(dy), steg: Math.round(-dy) };
}

function kasten(el: Element): Kasten {
  const r = el.getBoundingClientRect();
  return { left: r.left, right: r.right, top: r.top, bottom: r.bottom };
}

/**
 * Setzt `--isl-ausweich-x/-y` und `--isl-steg-hoehe` auf die Insel-Wurzel, solange `aktiv` (Leiste offen, unterer
 * Rand). Die Rechnung läuft gegen die Lage ohne eigenen Versatz.
 */
export function useLeisteAusweichen(wurzel: RefObject<HTMLElement | null>, aktiv: boolean): void {
  useLayoutEffect(() => {
    const el = wurzel.current;
    if (!el) return undefined;
    const setze = (a: { dx: number; dy: number; steg: number }) => {
      el.style.setProperty('--isl-ausweich-x', `${a.dx}px`);
      el.style.setProperty('--isl-ausweich-y', `${a.dy}px`);
      el.style.setProperty('--isl-steg-hoehe', `${a.steg}px`);
    };
    if (!aktiv) {
      setze({ dx: 0, dy: 0, steg: 0 });
      return undefined;
    }
    let jetzt = { dx: 0, dy: 0, steg: 0 };
    let geplant = 0;
    const lege = () => {
      geplant = 0;
      const leiste = el.querySelector('.isl-leiste') ?? el;
      const r = kasten(leiste);
      const ohne = { left: r.left - jetzt.dx, right: r.right - jetzt.dx, top: r.top - jetzt.dy, bottom: r.bottom - jetzt.dy };
      const hindernisse = Array.from(document.querySelectorAll(LEISTE_HINDERNISSE))
        .filter((h) => !el.contains(h) && getComputedStyle(h).visibility !== 'hidden')
        .map(kasten)
        .filter((k) => k.right > k.left && k.bottom > k.top);
      const neu = leisteAusweichen(ohne, hindernisse, window.innerWidth);
      if (neu.dx !== jetzt.dx || neu.dy !== jetzt.dy || neu.steg !== jetzt.steg) {
        jetzt = neu;
        setze(neu);
      }
    };
    const plane = () => {
      if (!geplant) geplant = requestAnimationFrame(lege);
    };
    lege();
    // Die Zoomleisten kommen und gehen mit dem Ansichtswechsel. Eigene Änderungen zählen nicht.
    const mo = new MutationObserver((eintraege) => {
      if (eintraege.some((e) => !el.contains(e.target) && e.target !== el)) plane();
    });
    mo.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'class'] });
    window.addEventListener('resize', plane);
    // Die Leiste geht mit einer Bewegung auf (Grösse und Skalierung); erst danach stimmt ihr Kasten. Ein Beobachter
    // für die Grösse und das Ende jeder Bewegung rechnen nach.
    const ro = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(plane);
    ro?.observe(el);
    el.addEventListener('animationend', plane);
    el.addEventListener('transitionend', plane);
    return () => {
      if (geplant) cancelAnimationFrame(geplant);
      mo.disconnect();
      ro?.disconnect();
      el.removeEventListener('animationend', plane);
      el.removeEventListener('transitionend', plane);
      window.removeEventListener('resize', plane);
      setze({ dx: 0, dy: 0, steg: 0 });
    };
  }, [wurzel, aktiv]);
}
