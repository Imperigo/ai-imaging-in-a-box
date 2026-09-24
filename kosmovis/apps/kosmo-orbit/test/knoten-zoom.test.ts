import { describe, expect, it } from 'vitest';
import { zoomAmZeiger, type KnotenAnsicht } from '../src/modules/vis/knoten-zoom';

/**
 * **P-KNOTEN-ZOOM — das Rad zoomte zur Mitte, nicht zum Zeiger.**
 *
 * Der Befund aus der Bestandsaufnahme: der Knotengraph aenderte beim Radzoom
 * nur den Massstab und liess den Mittelpunkt stehen. Wer einen Knoten am Rand
 * vergroessern wollte, schob ihn damit aus dem Bild und musste hinterherziehen.
 * Die Plansicht macht es seit Langem richtig — der Knotengraph war die
 * Ausnahme.
 *
 * **Die Zusage, an der alles haengt:** der Weltpunkt unter dem Zeiger bleibt
 * unter dem Zeiger. Genau das wird hier geprueft, und zwar als Rechnung
 * (Weltpunkt vorher = Weltpunkt nachher), nicht als Vergleich mit einer von
 * Hand ausgerechneten Zahl — eine Zahl koennte ich falsch abschreiben, die
 * Gleichung nicht.
 */

const GRENZEN = { min: 0.2, max: 4 };

/** Weltpunkt unter einem Bildschirmpunkt `d` Pixel neben der Flaechenmitte. */
function weltX(v: KnotenAnsicht, dx: number): number {
  return v.cx + dx / v.scale;
}
function weltY(v: KnotenAnsicht, dy: number): number {
  return v.cy + dy / v.scale;
}

describe('zoomAmZeiger — der Punkt unter dem Zeiger bleibt liegen', () => {
  const start: KnotenAnsicht = { cx: 560, cy: 300, scale: 1 };

  it('beim Hineinzoomen bleibt der Weltpunkt unter dem Zeiger derselbe', () => {
    const dx = 400;
    const dy = -180;
    const vorher = { x: weltX(start, dx), y: weltY(start, dy) };
    const nachher = zoomAmZeiger(start, 1.6, dx, dy, GRENZEN);
    expect(weltX(nachher, dx)).toBeCloseTo(vorher.x, 9);
    expect(weltY(nachher, dy)).toBeCloseTo(vorher.y, 9);
    expect(nachher.scale).toBeCloseTo(1.6, 9);
  });

  it('beim Herauszoomen ebenso — und der Ausschnitt wandert in die ANDERE Richtung', () => {
    const dx = 400;
    const vorher = weltX(start, dx);
    const nachher = zoomAmZeiger(start, 0.5, dx, 0, GRENZEN);
    expect(weltX(nachher, dx)).toBeCloseTo(vorher, 9);
    // Gegenrichtung: beim Hineinzoomen wandert die Mitte ZUM Zeiger, beim
    // Herauszoomen von ihm weg. Ohne diesen Fall waere auch eine Fassung
    // gruen, die das Vorzeichen verdreht und beim Herauszoomen zufaellig
    // wieder passt.
    const hinein = zoomAmZeiger(start, 2, dx, 0, GRENZEN);
    expect(hinein.cx).toBeGreaterThan(start.cx);
    expect(nachher.cx).toBeLessThan(start.cx);
  });

  it('KONTROLLFALL: mit dem Zeiger GENAU in der Mitte aendert sich nur der Massstab', () => {
    // Das ist der Knopf-Fall (`+`/`-`) und zugleich der Beweis, dass die
    // Funktion nicht einfach immer verschiebt.
    const nachher = zoomAmZeiger(start, 2, 0, 0, GRENZEN);
    expect(nachher.cx).toBe(start.cx);
    expect(nachher.cy).toBe(start.cy);
    expect(nachher.scale).toBe(2);
  });

  it('senkrecht und waagrecht gleich orientiert — kein geerbtes Vorzeichen aus der Plansicht', () => {
    // Die Plansicht rechnet mit UMGEKEHRTER y-Achse. Waere ihre Formel
    // uebernommen worden, verfolgte der Zoom den Zeiger senkrecht
    // spiegelverkehrt — und genau das faellt hier durch.
    const nurY = zoomAmZeiger(start, 2, 0, 250, GRENZEN);
    expect(nurY.cy, 'die Mitte wandert nach oben statt nach unten').toBeGreaterThan(start.cy);
    expect(weltY(nurY, 250)).toBeCloseTo(weltY(start, 250), 9);
  });

  it('an der oberen Grenze bleibt die Ansicht UNVERAENDERT — nicht bloss der Massstab', () => {
    // Sonst wanderte der Ausschnitt am Anschlag weiter, obwohl sichtbar
    // nichts passiert: das Bild ruckelt, ohne zu zoomen.
    const amAnschlag: KnotenAnsicht = { cx: 100, cy: 50, scale: GRENZEN.max };
    const nachher = zoomAmZeiger(amAnschlag, 2, 300, 300, GRENZEN);
    expect(nachher).toBe(amAnschlag);
  });

  it('an der unteren Grenze ebenso', () => {
    const amAnschlag: KnotenAnsicht = { cx: 100, cy: 50, scale: GRENZEN.min };
    const nachher = zoomAmZeiger(amAnschlag, 0.5, 300, 300, GRENZEN);
    expect(nachher).toBe(amAnschlag);
  });

  it('ein Zoom, der ueber die Grenze hinausschiesst, wird geklemmt und verankert trotzdem', () => {
    // Der Fall, der bei einer naiven Umsetzung falsch wird: geklemmt wird der
    // Massstab, gerechnet wird aber mit dem UNGEKLEMMTEN — dann verrutscht
    // der Zeigerpunkt genau dort, wo das Rad am haertesten gedreht wird.
    const dx = 500;
    const vorher = weltX(start, dx);
    const nachher = zoomAmZeiger(start, 99, dx, 0, GRENZEN);
    expect(nachher.scale).toBe(GRENZEN.max);
    expect(weltX(nachher, dx)).toBeCloseTo(vorher, 9);
  });
});
