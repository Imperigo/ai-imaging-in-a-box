import type { VisGraph, VisNode } from '@kosmo/kernel';
import { nodeBreite, ruhendeNodeHoehe } from './NodeCanvas';

/**
 * **Gesicherte Graphen beim Laden einmal sanft entzerren** (Owner-Befund am Mac, 20.10.2026:
 * im Modell-Knoten mit 3D-Fenster lag die Auto-Kamera über seinem unteren Rand).
 *
 * Ursache: Der Modell-Knoten ist mit dem 3D-Fenster (F1, Entscheid 109 A) um 162 px gewachsen.
 * Ein Graph, der **vorher** gesichert wurde, trägt die Lagen von damals — die Auto-Kamera steht
 * dort, wo der kürzere Knoten endete. Der fertige Anfang selbst rechnet mit der echten Höhe
 * (`startGraphLage` über `groessteNodeHoehe`) und überlappt nicht.
 *
 * Regel: **Nur wenn sich Knoten wirklich überlappen**, rückt der untere so weit nach unten,
 * bis er frei steht (Abstand `ENTZERREN_ABSTAND`); das schiebt, was darunter liegt, mit. Nichts
 * rückt nach oben oder zur Seite, und ein Graph ohne Überlappung bleibt Pixel für Pixel, wie er
 * ist. Gerechnet wird mit der Höhe in Ruhe (`ruhendeNodeHoehe`) — ein aufgeklappter Text oder
 * ein laufender Render wächst nur für den Augenblick.
 *
 * Wer es aufruft: der Wirt, der gesicherte Graphen beim Öffnen ins Dokument legt (Visbox,
 * `graph-sichern.ts`). KosmoOrbit ruft es **nicht** von selbst — dort ist ein Graph Teil eines
 * geteilten, gespeicherten Projekts, und blosses Öffnen soll es nicht ändern (Begründung wie
 * beim fertigen Anfang, `start-graph.ts`).
 */

/** Abstand zwischen zwei Knoten, die beim Entzerren untereinander gerückt werden. */
export const ENTZERREN_ABSTAND = 32;

type Lage = Pick<VisNode, 'id' | 'x' | 'y' | 'typ' | 'collapsed'>;

/**
 * Neue Lagen für überlappende Knoten — `Map` von Knoten-Kennung auf neues `y`. Leer, wenn
 * nichts überlappt. Rein: Höhe und Breite kommen als Funktion (Vorgabe `ruhendeNodeHoehe` und
 * `nodeBreite` — seit Entscheid 119 ist der Render-Knoten breiter als die anderen).
 */
export function entzerreLagen(
  knoten: readonly Lage[],
  hoehe: (n: Lage) => number = ruhendeNodeHoehe,
  breite: (n: Lage) => number = (n) => nodeBreite(n.typ),
  abstand = ENTZERREN_ABSTAND,
): Map<string, number> {
  const reihe = [...knoten].sort((a, b) => a.y - b.y || a.x - b.x);
  const gesetzt: { x: number; y: number; h: number; b: number }[] = [];
  const neu = new Map<string, number>();
  for (const n of reihe) {
    const h = hoehe(n);
    const b = breite(n);
    let y = n.y;
    // Höchstens so oft, wie Knoten da sind: jeder Durchgang rückt unter einen weiteren.
    for (let runde = 0; runde <= gesetzt.length; runde++) {
      const im = gesetzt.find((p) => n.x < p.x + p.b && p.x < n.x + b && y < p.y + p.h && p.y < y + h);
      if (!im) break;
      y = im.y + im.h + abstand;
    }
    if (y !== n.y) neu.set(n.id, y);
    gesetzt.push({ x: n.x, y, h, b });
  }
  return neu;
}

/** Ein Graph mit entzerrten Lagen — derselbe Gegenstand, wenn nichts überlappt. */
export function entzerreGraph(g: VisGraph, hoehe?: (n: Lage) => number): VisGraph {
  const neu = entzerreLagen(g.nodes, hoehe);
  if (neu.size === 0) return g;
  return { ...g, nodes: g.nodes.map((n) => (neu.has(n.id) ? { ...n, y: neu.get(n.id)! } : n)) };
}
