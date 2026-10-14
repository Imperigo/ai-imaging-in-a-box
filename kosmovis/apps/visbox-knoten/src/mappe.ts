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
 * 3. Seit Entscheid 90 (14.10.2026, Blatt 21) die **Lade-Fähigkeit des Modell-Knotens**
 *    (`ladeWirt`, registriert in `main.tsx`): «Datei laden …» schickt die Datei an
 *    `POST ./modell-laden`; der Server legt daneben eine Mappe an (oder eine neue Fassung in
 *    derselben) und wandelt im Hintergrund um. Hier wird nachgefragt, bis es fertig ist, und
 *    danach die neue Mappe geladen — sie ist am Server jetzt die zuletzt geöffnete.
 *
 * Und die Brücke: Auf dieser Seite ist der Visbox-Server die Brücke. `vis-jobs.ts` liest ihre
 * Adresse aus `localStorage['kosmo.bridge']`; sie wird hier auf `/bruecke` desselben Servers
 * gesetzt. Andere Adressen gehören zu KosmoOrbit und haben in diesem Ursprung nichts zu tun.
 */
import { newId, setzeModellGlb, type FreeMesh, type Storey } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import {
  setzeModellLadeZustand,
  type ModellLadeWirt,
  type ModellLadeZustand,
} from '../../kosmo-orbit/src/modules/vis/modell-laden';

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
  /** Entscheid 90: Name des Mappen-Ordners, Herkunft («IFC», «glb» …), Fassung, Teile mit
   *  Geometrie in der glb (`null`: nicht gelesen). */
  mappe?: string;
  herkunft?: string | null;
  fassung?: number;
  bauteile?: number | null;
}

/** Der Stand des Ladens, wie `GET ./modell-laden` ihn meldet (`oberflaeche/server.py`). */
export interface LadeStand {
  kennung: string;
  stand: 'laeuft' | 'geladen' | 'fehler';
  datei: string;
  satz: string;
  schritt: string | null;
  seit_s: number;
  mappe?: string | null;
  herkunft?: string | null;
  fassung?: number | null;
  bauteile?: number | null;
  ersetzt?: boolean;
}

export interface LadeSicht {
  formate: string[];
  annehmen: string;
  hoechstens_mb: number;
  laden: LadeStand | null;
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

/** Was `ladeMappe` ins Dokument gelegt hat — damit eine neue Mappe es ersetzt, statt eine
 *  zweite Hüllbox daneben zu stellen. */
let gelegt: { geschoss: Storey; huelle: FreeMesh } | null = null;

function raeumeGelegtes(): void {
  if (!gelegt) return;
  const { doc } = useProject.getState();
  doc.apply([
    { id: gelegt.huelle.id, before: gelegt.huelle, after: null },
    { id: gelegt.geschoss.id, before: gelegt.geschoss, after: null },
  ]);
  gelegt = null;
}

/** Der Zustand des Modell-Knotens aus der Antwort von `./mappe` (Entscheid 90). */
export function zustandAusMappe(mappe: MappeAntwort): ModellLadeZustand {
  if (!mappe.glb) return { stand: 'leer', ...(mappe.grund ? { satz: mappe.grund } : {}) };
  return {
    stand: 'geladen',
    bauteile: mappe.bauteile ?? 0,
    herkunft: mappe.herkunft ?? 'glb',
    mappe: mappe.mappe ?? mappe.name ?? '',
    ...(mappe.fassung ? { fassung: mappe.fassung } : {}),
  };
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
  raeumeGelegtes();
  setzeModellLadeZustand(zustandAusMappe(mappe));
  if (!mappe.glb) {
    setzeModellGlb(null);
    useProject.setState((s) => ({ revision: s.revision + 1 }));
    return mappe.grund || 'Die Mappe hat noch kein Modell.';
  }

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
  gelegt = { geschoss, huelle };
  useProject.setState((s) => ({ revision: s.revision + 1, activeStoreyId: geschoss.id }));
  return `Modell «${mappe.name ?? 'ohne Namen'}» aus der Mappe geladen.`;
}

/** Wie oft nachgefragt wird, solange eine Datei geladen wird. */
export const NACHFRAGE_MS = 800;
/** Wie lange höchstens: eine grosse IFC braucht Minuten (Umwandlung und Raumleser haben am
 *  Heim-PC je eigene Fristen); danach sagt der Knoten, dass der Heim-PC nicht mehr meldet. */
export const NACHFRAGE_HOECHSTENS_MS = 30 * 60 * 1000;

async function fehlerSatz(antwort: Response): Promise<string> {
  const text = await antwort.text();
  try {
    return (JSON.parse(text) as { fehler?: string }).fehler ?? text;
  } catch {
    return text || `Der Heim-PC antwortet mit ${antwort.status}.`;
  }
}

/** Ein Satz für «läuft», mit der Zeit seit Beginn. */
export function laeuftSatz(stand: Pick<LadeStand, 'satz' | 'seit_s'>): string {
  const s = Math.max(0, Math.round(stand.seit_s));
  const zeit = s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, '0')} s`;
  return `${stand.satz} (${zeit})`;
}

const warte = (ms: number) => new Promise((fertig) => setTimeout(fertig, ms));

/**
 * Die Lade-Fähigkeit für den Modell-Knoten (Entscheid 90). `formate`/`annehmen` kommen vom
 * Server (`GET ./modell-laden`, also aus `importeur.WEGE`) — bis die Antwort da ist, stehen
 * sie leer bzw. auf der Liste, die der Server zuletzt hatte.
 */
export function ladeWirt(sicht?: Pick<LadeSicht, 'formate' | 'annehmen'>): ModellLadeWirt {
  return {
    formate: sicht?.formate ?? [],
    annehmen: sicht?.annehmen ?? '',
    async laden(datei, melde) {
      const formular = new FormData();
      formular.append('datei', datei, datei.name);
      const antwort = await fetch('./modell-laden', { method: 'POST', body: formular });
      if (!antwort.ok) return { stand: 'fehler', datei: datei.name, satz: await fehlerSatz(antwort) };
      const begonnen = ((await antwort.json()) as LadeSicht).laden;
      if (!begonnen) return { stand: 'fehler', datei: datei.name, satz: 'Der Heim-PC hat das Laden nicht begonnen.' };
      return verfolge(begonnen, melde);
    },
  };
}

/** Fragt nach, bis das Laden nicht mehr läuft, und lädt dann die (neue) Mappe. */
export async function verfolge(
  stand: LadeStand,
  melde: (z: ModellLadeZustand) => void,
): Promise<ModellLadeZustand> {
  const ende = Date.now() + NACHFRAGE_HOECHSTENS_MS;
  let jetzt: LadeStand = stand;
  let fehlversuche = 0;
  while (jetzt.stand === 'laeuft') {
    melde({ stand: 'laeuft', datei: jetzt.datei, satz: laeuftSatz(jetzt) });
    if (Date.now() > ende) {
      return { stand: 'fehler', datei: jetzt.datei, satz: 'Der Heim-PC meldet seit einer halben Stunde nichts Neues. Die Visbox-Seite zeigt, ob die Mappe angekommen ist.' };
    }
    await warte(NACHFRAGE_MS);
    try {
      const antwort = await fetch('./modell-laden');
      if (!antwort.ok) throw new Error(await fehlerSatz(antwort));
      const neu = ((await antwort.json()) as LadeSicht).laden;
      if (!neu || neu.kennung !== stand.kennung) {
        return { stand: 'fehler', datei: stand.datei, satz: 'Der Heim-PC weiss von diesem Laden nichts mehr — vermutlich wurde er neu gestartet.' };
      }
      jetzt = neu;
      fehlversuche = 0;
    } catch (fehler) {
      fehlversuche += 1;
      if (fehlversuche >= 5) {
        return { stand: 'fehler', datei: stand.datei, satz: `Der Heim-PC antwortet nicht: ${String(fehler)}` };
      }
    }
  }
  if (jetzt.stand === 'fehler') return { stand: 'fehler', datei: jetzt.datei, satz: jetzt.satz };

  // GELADEN: Die neue Mappe ist am Server jetzt die zuletzt geoeffnete. Ein `?ordner=` in der
  // Adresse zeigte weiter auf die alte — er faellt weg, dann laedt `ladeMappe` die neue.
  if (location.search) history.replaceState(null, '', location.pathname);
  await ladeMappe();
  return {
    stand: 'geladen',
    bauteile: jetzt.bauteile ?? 0,
    herkunft: jetzt.herkunft ?? 'glb',
    mappe: jetzt.mappe ?? '',
    ...(jetzt.fassung ? { fassung: jetzt.fassung } : {}),
    satz: jetzt.satz,
  };
}
