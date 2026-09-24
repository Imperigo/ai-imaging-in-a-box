/**
 * Visbox-eigen — das Gebäude der offenen Mappe in die Knotenansicht (E26, 24.09.2026).
 *
 * In KosmoOrbit baut man das Gebäude im Entwurf, und das Vis-Werkzeug exportiert es als glb.
 * In Visbox kommt es fertig aus der Mappe. Diese Datei holt es vom Visbox-Server und legt es
 * an die zwei Stellen, an denen das kopierte Werkzeug danach fragt:
 *
 * 1. `setzeModellGlb` — der Stellvertreter `exportGlb` gibt diese Bytes weiter, wenn ein
 *    Render bestellt wird. Das Modell geht also **unverändert** an die Rechnung.
 * 2. Ein Geschoss und ein Bauteil «Hüllbox des Modells aus der Mappe» im Dokument. Das
 *    Werkzeug sperrt den Render, solange das Dokument 0 Bauteile hat (`szeneBauteileAnzahl`),
 *    und das zu Recht. Die Hüllbox ist kein erfundenes Bauteil, sondern der gemessene Umriss
 *    des Gebäudes (`aiimaging.glbbox.bauwerksbox`); gerendert wird sie nicht — gerendert
 *    wird das glb aus Punkt 1.
 *
 * Und die Brücke: Auf dieser Seite ist der Visbox-Server die Brücke. `vis-jobs.ts` liest ihre
 * Adresse aus `localStorage['kosmo.bridge']`; sie wird hier auf `/bruecke` desselben Servers
 * gesetzt. Andere Adressen gehören zu KosmoOrbit und haben in diesem Ursprung nichts zu tun.
 */
import { newId, setzeModellGlb, type FreeMesh, type Storey } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';

export interface MappeAntwort {
  name: string | null;
  glb: boolean;
  /** Welt, Meter, Z oben: [[xmin, ymin, zmin], [xmax, ymax, zmax]]. */
  huellbox_m: [[number, number, number], [number, number, number]] | null;
  hochachse: string | null;
  /** Warum etwas fehlt — für einen Menschen; leer, wenn nichts fehlt. */
  grund: string;
  /** Fachvermerk der Hüllbox (welche Regel das Gelände getrennt hat) — nicht zum Anzeigen. */
  huellbox_vermerk: string;
}

/** Läuft die Seite auf dem Visbox-Server (unter `/knoten/`) — oder im Entwicklungsserver? */
export function aufDemVisboxServer(pfad: string = location.pathname): boolean {
  return pfad === '/knoten' || pfad.startsWith('/knoten/');
}

export function brueckeAufDiesenServer(): void {
  try {
    localStorage.setItem('kosmo.bridge', `${location.origin}/bruecke`);
  } catch {
    // Ohne Speicher bleibt die Vorgabe der Kopie (localhost:8600) — der Render-Knoten sagt
    // dann selbst, dass keine Brücke antwortet.
  }
}

/** Die acht Ecken und zwölf Dreiecke eines Quaders — Millimeter, ganzzahlig, nach aussen. */
export function huellboxAlsNetz(box: [[number, number, number], [number, number, number]]): {
  positions: number[];
  faces: number[];
} {
  const [[x0, y0, z0], [x1, y1, z1]] = box.map((p) => p.map((m) => Math.round(m * 1000))) as [
    [number, number, number],
    [number, number, number],
  ];
  const positions = [
    x0, y0, z0, x1, y0, z0, x1, y1, z0, x0, y1, z0,
    x0, y0, z1, x1, y0, z1, x1, y1, z1, x0, y1, z1,
  ];
  const faces = [
    0, 2, 1, 0, 3, 2, // unten
    4, 5, 6, 4, 6, 7, // oben
    0, 1, 5, 0, 5, 4,
    1, 2, 6, 1, 6, 5,
    2, 3, 7, 2, 7, 6,
    3, 0, 4, 3, 4, 7,
  ];
  return { positions, faces };
}

/** Holt die Mappe und legt das Modell an. Gibt den Satz zurück, der dem Menschen sagt, was ist. */
export async function ladeMappe(): Promise<string> {
  // Die Mappe, die auf der Visbox-Seite offen war (`?ordner=`), sonst die vom Serverstart.
  const antwort = await fetch(`./mappe${location.search}`);
  if (!antwort.ok) {
    const text = await antwort.text();
    try {
      return (JSON.parse(text) as { fehler?: string }).fehler ?? text;
    } catch {
      return text;
    }
  }
  const mappe = (await antwort.json()) as MappeAntwort;
  if (!mappe.glb) return mappe.grund || 'Die Mappe hat noch kein Modell.';

  const modell = await fetch(`./modell.glb${location.search}`);
  if (!modell.ok) return 'Das Modell der Mappe liess sich nicht laden.';
  setzeModellGlb(await modell.arrayBuffer());

  if (!mappe.huellbox_m) {
    return `Modell «${mappe.name ?? 'ohne Namen'}» geladen, aber ohne Umriss: ${mappe.grund}`;
  }
  const { doc } = useProject.getState();
  const geschoss: Storey = {
    id: newId('st'),
    kind: 'storey',
    name: 'Mappe',
    index: 0,
    elevation: 0,
    height: Math.max(1, Math.round((mappe.huellbox_m[1][2] - mappe.huellbox_m[0][2]) * 1000)),
    cutHeight: 1100,
  };
  const huelle: FreeMesh = {
    id: newId('fm'),
    kind: 'freemesh',
    storeyId: geschoss.id,
    name: `Hüllbox des Modells aus der Mappe «${mappe.name ?? ''}»`,
    ...huellboxAlsNetz(mappe.huellbox_m),
  };
  doc.apply([
    { id: geschoss.id, before: null, after: geschoss },
    { id: huelle.id, before: null, after: huelle },
  ]);
  useProject.setState((s) => ({ revision: s.revision + 1, activeStoreyId: geschoss.id }));
  return `Modell «${mappe.name ?? 'ohne Namen'}» aus der Mappe geladen.`;
}
