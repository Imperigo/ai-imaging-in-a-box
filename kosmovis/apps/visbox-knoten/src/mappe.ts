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
 * 4. Seit Entscheid 92 (14.10.2026, Blatt 23) die **Standpunkte des Heim-PCs** für die
 *    Auto-Kamera (`registriereHeimStandpunkte`): dieselben drei Richtungen, die der Abholer ohne
 *    mitgeschickte Kameras rechnet, als Vorschau — der Auftrag bleibt `cameras: 'auto'`.
 *
 * 5. Seit Entscheiden 95/95a (14.10.2026, Blatt 25) die **Skizzen-Quelle** für den Knoten «Skizze
 *    vom iPad» (`skizzenQuelleDerMappe`, registriert in `main.tsx`): die Liste aus `GET ./mappe`
 *    (Feld `skizzen`, die neueste zuerst, `knotenweg.skizzen_der_mappe`), das Bild aus
 *    `GET ./skizze?name=…` — beides für die Mappe dieser Seite (`?ordner=`, sonst die zuletzt
 *    geöffnete). Nach jedem Laden einer Mappe wird die Liste neu gelesen.
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
import { registriereHeimStandpunkte, type HeimStandpunkte } from '../../kosmo-orbit/src/modules/vis/heim-standpunkte';
import {
  aktualisiereSkizzen,
  type Skizze,
  type SkizzenQuelle,
} from '../../kosmo-orbit/src/modules/vis/skizze-quelle';

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
  /** Entscheid 92: die drei Standpunkte, die der Heim-PC ohne mitgeschickte Kameras rechnet
   *  (`knotenweg.heim_standpunkte`) — `null` ohne Modell. */
  standpunkte?: HeimStandpunkte | null;
  /** Entscheide 95/95a: die Skizzen der Mappe, die neueste zuerst (ohne verworfene). */
  skizzen?: Skizze[];
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

/** Läuft die Seite auf dem Visbox-Server (unter `/knoten/`) bzw. in der Mac-App
 *  (`visbox://app/knoten/`, derselbe Pfad) — oder im Entwicklungsserver? */
export function aufDemVisboxServer(pfad: string = location.pathname): boolean {
  return pfad === '/knoten' || pfad.startsWith('/knoten/');
}

/**
 * Die Adresse der Brücke: `/bruecke` am selben Ort wie die Seite. **Aus der Adresse der Seite
 * gebaut, nicht aus `location.origin`** («Visbox eigenständig», Schritt 1, 20.10.2026): In der
 * Mac-App kommt die Seite über ein eigenes Adressschema (`visbox://app/knoten/`), und für ein
 * solches Schema darf ein Browser den Ursprung «null» nennen — `null/bruecke` wäre keine
 * Adresse. Am Heim-PC ergibt beides dasselbe (`https://…:8443/bruecke`).
 */
export function brueckenAdresse(seite: string = location.href): string {
  return new URL('/bruecke', seite).href;
}

/** Das eigene Adressschema der Mac-App (`Kern/Knotenwege.swift`, `schema`). */
export const EIGENES_SCHEMA = 'visbox:';

export function imEigenenSchema(protokoll: string = location.protocol): boolean {
  return protokoll === EIGENES_SCHEMA;
}

/**
 * Schritt 1 von «Visbox eigenständig»: Im eigenen Adressschema reicht die Mac-App jede Anfrage
 * selbst an den Heim-PC weiter. WebKit gibt ihr den Rumpf aber nur **als fertige Bytes** sicher
 * mit — ein Formular mit Datei-Teil (das Modell beim Bestellen, die Datei bei «Datei laden …»)
 * kann unterwegs leer werden. Darum macht dieser Umschlag aus jedem Rumpf, der keine Bytes und
 * kein Text ist, vorher Bytes: mit demselben `Content-Type` (samt `boundary`), den der Browser
 * dem Formular gegeben hätte. Am Heim-PC (https) wird er nicht eingesetzt.
 */
export function koerperAlsBytes(roh: typeof fetch): typeof fetch {
  return async (eingabe: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const rumpf = init?.body;
    if (rumpf == null || typeof rumpf === 'string' || rumpf instanceof ArrayBuffer || ArrayBuffer.isView(rumpf)) {
      return roh(eingabe, init);
    }
    const verpackt = new Response(rumpf as BodyInit);
    const typ = verpackt.headers.get('content-type');
    const bytes = await verpackt.arrayBuffer();
    const koepfe = new Headers(init?.headers);
    if (typ && !koepfe.has('content-type')) koepfe.set('content-type', typ);
    return roh(eingabe, { ...init, headers: koepfe, body: bytes });
  };
}

/**
 * Schritt 2 von «Visbox eigenständig» (Entscheid 103b, 20.10.2026): **ohne Rechner ein Satz am
 * Render-Knoten, keine Zahl.** Ohne Heim-PC antwortet die Mac-App auf die Render-Wege der Brücke
 * sofort mit 503 (kein Heim-PC eingerichtet) bzw. 502 (nicht erreicht) und einem Satz in der Form
 * des Servers (`{"fehler": satz}`, `Kern/Knotenwege.swift`). Der wörtlich übernommene Render-Weg
 * (`vis-jobs.ts`) liest bei einer solchen Antwort nur die Zahl, und am Knoten stünde «Bridge
 * antwortet mit: 503».
 *
 * Statt die Kopie anzufassen, macht dieser Umschlag aus **genau dieser** Antwort einen Fehler mit
 * dem Satz. `bridgeBescheid` gibt einen Fehler ohne Status und ohne Netzfehler wörtlich weiter
 * (Art `roh`) — so steht der Satz der App am Knoten und in der Meldung. Eng gefasst: nur im
 * eigenen Schema (`main.tsx`), nur auf `/bruecke/jobs…` (Bestellen, Abfragen, Freigeben,
 * Abbrechen, Bilder), nur 502/503, nur mit lesbarem Satz. Alles andere — auch 401/403, die
 * `bridgeBescheid` selbst deutet — geht unverändert durch.
 */
export const BRUECKE_SATZ_STATUS: readonly number[] = [502, 503];
export const BRUECKE_SATZ_PFAD = '/bruecke/jobs';

export function brueckeSagtDenSatz(roh: typeof fetch, seite: () => string = () => location.href): typeof fetch {
  return async (eingabe: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const antwort = await roh(eingabe, init);
    if (!BRUECKE_SATZ_STATUS.includes(antwort.status)) return antwort;
    const adresse = typeof eingabe === 'string' || eingabe instanceof URL ? String(eingabe) : eingabe.url;
    let pfad: string;
    try {
      pfad = new URL(adresse, seite()).pathname;
    } catch {
      return antwort;
    }
    if (pfad !== BRUECKE_SATZ_PFAD && !pfad.startsWith(`${BRUECKE_SATZ_PFAD}/`)) return antwort;
    let satz: unknown;
    try {
      satz = (JSON.parse(await antwort.clone().text()) as { fehler?: unknown }).fehler;
    } catch {
      return antwort;
    }
    if (typeof satz !== 'string' || satz.trim() === '') return antwort;
    throw new Error(satz);
  };
}

export function brueckeAufDiesenServer(): void {
  try {
    localStorage.setItem('kosmo.bridge', brueckenAdresse());
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
  // F1 (Entscheid 109 A): «geladen» erst, wenn die glb bereitliegt — das 3D-Fenster im
  // Modell-Knoten holt sie mit `exportGlb`, sobald der Zustand umspringt.
  const zustand = zustandAusMappe(mappe);
  // Entscheid 92 (Blatt 23): die Auto-Kamera zeigt, was der Heim-PC rechnen wird — vor dem
  // Hochzaehlen der Revision unten, damit der Knoten gleich in seiner Hoehe steht.
  registriereHeimStandpunkte(mappe.glb && mappe.standpunkte ? mappe.standpunkte : null);
  // Entscheide 95/95a: eine andere Mappe hat andere Skizzen — der Knoten liest sie neu.
  void aktualisiereSkizzen();
  if (!mappe.glb) {
    setzeModellGlb(null);
    setzeModellLadeZustand(zustand);
    useProject.setState((s) => ({ revision: s.revision + 1 }));
    return mappe.grund || 'Die Mappe hat noch kein Modell.';
  }

  const modell = await fetch(`./modell.glb${location.search}`);
  if (!modell.ok) {
    // Die glb der vorigen Mappe gilt nicht mehr: das 3D-Fenster sagt «Modell nicht lesbar».
    setzeModellGlb(null);
    setzeModellLadeZustand(zustand);
    return 'Das Modell der Mappe liess sich nicht laden.';
  }
  setzeModellGlb(await modell.arrayBuffer());

  if (!mappe.huellbox_m) {
    setzeModellLadeZustand(zustand);
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
  setzeModellLadeZustand(zustand);
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

  // SCHRITT 3 (21.10.2026): IN DER MAC-APP MIT MAPPE AM MAC kommt das Modell in DIESE Mappe —
  // die App holt es von der neuen Mappe am Heim-PC (`holeInDieMappeAmMac`).
  const nichtGeholt = await holeInDieMappeAmMac(jetzt.mappe);
  if (nichtGeholt) return { stand: 'fehler', datei: jetzt.datei, satz: nichtGeholt };

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

/** Der Weg der Mac-App nach «Datei laden …» (`Mappenkern.wegModellHolen`) — nur dort bekannt. */
export const WEG_MODELL_HOLEN = './mappe-holen';

/**
 * «Visbox eigenständig», Schritt 3 (21.10.2026, Blatt 36): Die Mappe liegt am Mac. «Datei laden …»
 * wandelt die Datei weiter am Heim-PC (IfcOpenShell liegt dort, hinter der Prozessgrenze) und legt
 * dort eine Mappe an; danach holt die App deren Modell **in die offene Mappe am Mac**. Gibt `null`
 * zurück, wenn alles da ist oder nichts zu tun war (nicht in der App, oder keine Mappe am Mac
 * offen: dann antwortet die App 404 und es bleibt wie bis 0.3.14), sonst den Satz der App.
 */
export async function holeInDieMappeAmMac(
  mappe: string | null | undefined,
  holen: typeof fetch = (e, i) => fetch(e, i),
  protokoll: string = location.protocol,
): Promise<string | null> {
  if (!imEigenenSchema(protokoll) || !mappe) return null;
  const antwort = await holen(WEG_MODELL_HOLEN, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mappe }),
  });
  if (antwort.ok || antwort.status === 404) return null;
  return fehlerSatz(antwort);
}

/** Die Anfrage an den Server für die Mappe dieser Seite, mit `name` dazu (`?ordner=` bleibt). */
function mappenFrage(zusatz: Record<string, string> = {}): string {
  const frage = new URLSearchParams(location.search);
  for (const [k, v] of Object.entries(zusatz)) frage.set(k, v);
  const text = frage.toString();
  return text ? `?${text}` : '';
}

/**
 * Die Skizzen-Quelle für den Knoten «Skizze vom iPad» (Entscheide 95/95a). Liest die Adresse der
 * Seite bei jedem Ruf neu: Nach dem Laden einer Datei fällt `?ordner=` weg (`verfolge`), dann
 * gilt die zuletzt geöffnete Mappe.
 */
export function skizzenQuelleDerMappe(): SkizzenQuelle {
  return {
    async liste() {
      const antwort = await fetch(`./mappe${mappenFrage()}`);
      if (!antwort.ok) throw new Error(await fehlerSatz(antwort));
      const mappe = (await antwort.json()) as MappeAntwort;
      return Array.isArray(mappe.skizzen) ? mappe.skizzen.filter((s) => typeof s?.name === 'string' && s.name) : [];
    },
    bildUrl: (name) => `./skizze${mappenFrage({ name })}`,
  };
}
