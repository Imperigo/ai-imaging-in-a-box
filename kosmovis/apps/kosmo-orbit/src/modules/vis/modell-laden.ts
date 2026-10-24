/**
 * MODELL LADEN — die Lade-Fähigkeit des Modell-Knotens, die der WIRT bereitstellt.
 *
 * Anlass (Owner-Entscheid 90 der Visbox, 14.10.2026, Blatt 21): Der Modell-Knoten
 * bekommt «Datei laden …». Das Vis-Werkzeug läuft aber in zwei Programmen:
 *
 * - **In KosmoOrbit** kommt das Gebäude aus dem Entwurf — es wird dort gebaut, und
 *   `exportGlb` macht daraus das glb. Eine Datei zu laden gehört hier nicht zum
 *   Modell-Knoten. **Niemand registriert etwas, und der Knoten zeigt wie bisher nur
 *   «Szene: N Bauteile (GLB)».**
 * - **In Visbox** kommt das Gebäude aus einer Mappe am Heim-PC. Visbox registriert hier
 *   einen Wirt, der eine Datei an seinen Server schickt (dort wird umgewandelt und die
 *   Mappe angelegt); der Knoten zeigt dann Knopf, Formate, Fortschritt und Ergebnis.
 *
 * Darum steht hier **kein** Weg zu einem Server und kein Format: Beides weiss nur der Wirt.
 * Derselbe Knoten-Code läuft in beiden Programmen; was sich unterscheidet, ist allein, ob
 * jemand `registriereModellLaden` gerufen hat.
 *
 * Ohne React-Abhängigkeit im Kern: ein kleiner Speicher mit Hörern, den der Knoten über
 * `useSyncExternalStore` liest (`ModellKnoten.tsx`).
 */

import { mitZahl } from './einzahl';

/** Was der Modell-Knoten gerade zeigt — die vier Zustände von Blatt 21. */
export type ModellLadeZustand =
  /** (1) Noch kein Modell — Knopf «Datei laden …» und darunter die Formate. */
  | { stand: 'leer'; satz?: string }
  /** (2) Wird umgewandelt. `anteil` 0…1 nur, wenn der Wirt echten Fortschritt kennt. */
  | { stand: 'laeuft'; datei: string; satz: string; anteil?: number }
  /** (3) Geladen: «Szene: N Bauteile (aus IFC)», die Mappe, Knopf «Andere Datei …». */
  | {
      stand: 'geladen';
      bauteile: number;
      /** Woraus das Modell kam, für einen Menschen («IFC», «glb», «OBJ» …). */
      herkunft: string;
      /** Name der Mappe, in der das Modell jetzt liegt. */
      mappe: string;
      /** Die wievielte Fassung des Modells in dieser Mappe (1 beim ersten Laden). */
      fassung?: number;
      satz?: string;
    }
  /** (4) Nicht lesbar — mit dem Satz, warum, und was stattdessen zu tun ist. `noch`: das
   *  Modell, das davor geladen war und weiter gilt (KV-STARTGRAPH, Visbox-Plan «Modell laden
   *  im Knoten»): eine unlesbare zweite Datei nimmt das erste Modell nicht weg, und der
   *  Knoten soll das sagen, statt nur den Fehler zu zeigen. */
  | { stand: 'fehler'; satz: string; datei?: string; noch?: GeladenesModell };

/** Was von einem geladenen Modell genannt wird, wenn danach eine Datei nicht lesbar war. */
export interface GeladenesModell {
  bauteile: number;
  herkunft: string;
  mappe: string;
  fassung?: number;
}

/** Was der Wirt bereitstellt. */
export interface ModellLadeWirt {
  /** Die Formate zum Anzeigen unter dem Knopf, in der Reihenfolge des Wirts. */
  formate: readonly string[];
  /** Für `<input type="file" accept>` — Endungen mit Punkt, durch Komma getrennt. */
  annehmen: string;
  /**
   * Lädt die Datei. `melde` darf beliebig oft einen Zwischenstand liefern (in der Regel
   * `laeuft`); das Ergebnis ist der Endzustand (`geladen` oder `fehler`). Wirft der Wirt,
   * zeigt der Knoten den Fehlertext als Zustand `fehler`.
   */
  laden(datei: File, melde: (zustand: ModellLadeZustand) => void): Promise<ModellLadeZustand>;
}

interface Stand {
  wirt: ModellLadeWirt | null;
  zustand: ModellLadeZustand;
}

let stand: Stand = { wirt: null, zustand: { stand: 'leer' } };
const hoerer = new Set<() => void>();

function setze(neu: Partial<Stand>): void {
  stand = { ...stand, ...neu };
  for (const h of hoerer) h();
}

/**
 * Der Wirt stellt die Lade-Fähigkeit bereit — oder nimmt sie mit `null` zurück. Darf
 * mehrfach gerufen werden (etwa wenn die Formate erst nach einer Anfrage feststehen).
 */
export function registriereModellLaden(wirt: ModellLadeWirt | null): void {
  setze({ wirt, ...(wirt ? {} : { zustand: { stand: 'leer' } as ModellLadeZustand }) });
}

/** Der registrierte Wirt, oder `null` (KosmoOrbit: es gibt keinen). */
export function modellLadenWirt(): ModellLadeWirt | null {
  return stand.wirt;
}

/** Der Wirt setzt den Zustand von aussen — etwa, wenn beim Start schon ein Modell da ist. */
export function setzeModellLadeZustand(zustand: ModellLadeZustand): void {
  setze({ zustand });
}

export function modellLadeStand(): Stand {
  return stand;
}

export function abonniereModellLaden(h: () => void): () => void {
  hoerer.add(h);
  return () => {
    hoerer.delete(h);
  };
}

/**
 * Eine Datei laden: Zustand `laeuft`, dann der Endzustand des Wirts. Läuft schon eine
 * Datei, wird die zweite **nicht** angenommen — zwei Umwandlungen, die beide in dieselbe
 * Mappe schreiben wollen, gäben zwei Stände, und der zweite überschriebe den ersten.
 *
 * @returns der Endzustand, oder `null`, wenn nichts geschah (kein Wirt, schon am Laden).
 */
export async function ladeModellDatei(datei: File): Promise<ModellLadeZustand | null> {
  const wirt = stand.wirt;
  if (!wirt || stand.zustand.stand === 'laeuft') return null;
  // Was jetzt gilt — bleibt es nach einem Fehler, nennt der Knoten es weiter.
  const vorher = geltendesModell(stand.zustand);
  setze({ zustand: { stand: 'laeuft', datei: datei.name, satz: `«${datei.name}» wird geladen …` } });
  let ende: ModellLadeZustand;
  try {
    ende = await wirt.laden(datei, (zwischen) => setze({ zustand: zwischen }));
  } catch (fehler) {
    ende = {
      stand: 'fehler',
      datei: datei.name,
      satz: fehler instanceof Error ? fehler.message : String(fehler),
    };
  }
  if (ende.stand === 'fehler' && vorher && !ende.noch) ende = { ...ende, noch: vorher };
  setze({ zustand: ende });
  return ende;
}

/** Das Modell, das in diesem Zustand gilt: das geladene, oder nach einem Fehler das davor. */
export function geltendesModell(z: ModellLadeZustand): GeladenesModell | undefined {
  if (z.stand === 'geladen') {
    return { bauteile: z.bauteile, herkunft: z.herkunft, mappe: z.mappe, ...(z.fassung ? { fassung: z.fassung } : {}) };
  }
  if (z.stand === 'fehler') return z.noch;
  return undefined;
}

/** Die Zeile «Szene: N Bauteile (aus IFC)» eines geladenen Modells — eine Stelle für
 *  Knoten und Proben. (Ohne Wirt bleibt die bisherige Zeile «Szene: N Bauteile (GLB)», s. `szeneZeileGlb`.) */
export function szeneZeile(bauteile: number, herkunft: string): string {
  return `Szene: ${mitZahl(bauteile, 'Bauteil', 'Bauteile')} (aus ${herkunft})`;
}

/** Die Zeile ohne Wirt, «Szene: N Bauteile (GLB)» — bei einem Bauteil «Szene: 1 Bauteil (GLB)». */
export function szeneZeileGlb(bauteile: number): string {
  return `Szene: ${mitZahl(bauteile, 'Bauteil', 'Bauteile')} (GLB)`;
}
