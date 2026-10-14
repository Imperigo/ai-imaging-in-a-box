import { useLayoutEffect, useState, type RefObject } from 'react';

/**
 * **Herkunft — ein Fenster wächst aus dem Auslöser** (U19, Owner C5,
 * 01.10.2026; Visbox-Regel 4 «ein Gegenstand, ein Weg»).
 *
 * `useHerkunft(boxRef)` legt den `transform-origin` der Box auf die Mitte des
 * Elements, das sie geöffnet hat. Zusammen mit `.k-aus-ausloeser`
 * (`bewegung.css`) wächst das Fenster sichtbar aus dem Knopf, statt
 * irgendwo aufzutauchen.
 *
 * **Woher der Auslöser kommt:**
 *  - Zuerst der letzte Zeigerdruck (Maus, Finger, Stift) der letzten Sekunde.
 *    Safari fokussiert Knöpfe beim Klick nicht, darum reicht der Fokus allein
 *    nicht.
 *  - Sonst das fokussierte Element beim Öffnen (Tastatur).
 *  - Gibt es keinen, bleibt der Ursprung in der Mitte, wie bisher.
 *
 * Der Wert wird gemessen, bevor der Browser das erste Bild zeichnet; die
 * Animation startet also schon mit dem richtigen Ursprung.
 */

const FRISCH_MS = 1000;
let letzterDruck: { x: number; y: number; zeit: number } | null = null;
let horchtSchon = false;

function horche(): void {
  if (horchtSchon || typeof window === 'undefined') return;
  horchtSchon = true;
  window.addEventListener(
    'pointerdown',
    (e) => {
      letzterDruck = { x: e.clientX, y: e.clientY, zeit: Date.now() };
    },
    { capture: true, passive: true },
  );
}

function ausloeserPunkt(): { x: number; y: number } | null {
  if (letzterDruck && Date.now() - letzterDruck.zeit < FRISCH_MS) return { x: letzterDruck.x, y: letzterDruck.y };
  // Ohne DOM (Node, Server-Rendern) gibt es weder Fokus noch HTMLElement.
  if (typeof document === 'undefined' || typeof HTMLElement === 'undefined') return null;
  const el = document.activeElement;
  if (!(el instanceof HTMLElement) || el === document.body) return null;
  const r = el.getBoundingClientRect();
  return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
}

export function useHerkunft(boxRef: RefObject<HTMLElement | null>): void {
  horche();
  // Beim ersten Rendern festhalten — bevor eine Fokusfalle den Fokus in das
  // Fenster zieht und der Auslöser nicht mehr zu erkennen ist.
  const [punkt] = useState(ausloeserPunkt);
  useLayoutEffect(() => {
    const box = boxRef.current;
    if (!box || !punkt) return;
    // Die Lage OHNE laufende Bewegung messen: die Animation hat in diesem
    // Moment schon begonnen (scale 0.92), und `getBoundingClientRect` misst
    // die verkleinerte Box — der Ursprung laege dann daneben. Kurz aus- und
    // wieder einschalten startet sie neu, noch vor dem ersten Bild.
    const vorher = box.style.animation;
    box.style.animation = 'none';
    const r = box.getBoundingClientRect();
    box.style.animation = vorher;
    box.style.transformOrigin = `${Math.round(punkt.x - r.left)}px ${Math.round(punkt.y - r.top)}px`;
  }, [boxRef, punkt]);
}
