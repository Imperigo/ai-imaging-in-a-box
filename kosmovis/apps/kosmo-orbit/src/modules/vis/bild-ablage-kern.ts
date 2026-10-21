import { create } from 'zustand';
import * as kern from '@kosmo/kernel';
import { abgelegtesBild, bildFeldRechteck, druckaufloesung, druckaufloesungSatz, getCommand, type AnyPatch, type ImageAsset, type SheetImage } from '@kosmo/kernel';
import { ohneVerlauf, useProject } from '../../state/project-store';
import type { NodeLauf } from './vis-runtime';

/**
 * Video-Befunde L4-16, L3-A4, L3-A5 (Demolauf 16.10.2026; Blatt «Bild aufs Blatt») — der Kern
 * der Bildablage, ohne Netz und ohne React.
 *
 * Der Befund: «Aufs Blatt» nahm nur den aktuellen Lauf, und der war abgebrochen und leer; die
 * Grossansicht hatte keinen Export, die Bilder lagen nur am Heim-PC; am Ende stand ein
 * Bildschirmausschnitt von 369 × 228 px hochgezogen auf dem A0. Daraus:
 *
 *  - jedes fertige Bild kommt in VOLLER AUFLOESUNG ins Projekt (`vis.bildSichern`, ein
 *    `ImageAsset` mit `visHerkunft`) — ohne Rueckgaengig-Schritt (`ohneVerlauf`), weil es kein
 *    Handgriff des Architekten ist;
 *  - «Aufs Blatt» setzt dieses Projektbild per `assetId` (`publish.bildFuellen`), statt es ein
 *    zweites Mal als Text durch den Werkzeugkanal zu schicken;
 *  - beim Platzieren wird die Druckaufloesung am Platz geprueft (`druckWarnung`, dieselbe Rechnung wie Publish) und gewarnt;
 *  - ein Lauf ohne fertiges Bild ist nicht waehlbar und sagt, warum (`laufNichtWaehlbar`).
 *
 * Die Netzseite (Bild holen, Export) und das Nachholen fuer den Verlauf liegen in
 * `bild-ablage.ts`; diese Datei importiert nichts aus `vis-jobs.ts`, damit `vis-jobs.ts` sie
 * benutzen kann, ohne einen Kreis zu schliessen.
 */

/**
 * Bis zu dieser Groesse (Bytes des Bildes, 5 MB) kommt ein Bild unveraendert ins Projekt. Die harte Grenze liegt beim
 * Abgleich: der Sync-Server deckelt EINE Nachricht auf 8 MiB (`KOSMO_SYNC_MAX_BYTES`), darueber bricht die Verbindung
 * mit 1009 still ab; Base64 macht aus 5 MB rund 6,36 MiB (Prepare gemessen, Integrator entschieden 21.10.2026).
 * Darueber: `fuerDenAbgleich` (JPEG, dann verkleinern, sonst mit Satz abgelehnt).
 */
export const ABLAGE_GRENZE_BYTES = 5_000_000;

/** So klein wird hoechstens verkleinert (lange Seite); darunter wird abgelehnt — ein Plakatbild braucht mehr. */
export const VERKLEINERN_MIN_PX = 1200;

/** Unter dieser Aufloesung am Platz warnt das Platzieren — dieselbe Schwelle wie Publish. */
export const DRUCK_DPI_MIN = kern.DRUCK_DPI_MIN;

export interface BildMasse {
  width: number;
  height: number;
}

/** Schluessel eines Bildes: Auftrag und Datei. */
export function ablageSchluessel(jobId: string, bild: string): string {
  return `${jobId}/${bild}`;
}

/** Bytes → «4,2 MB» (wie die Meldungen sonst: eine Nachkommastelle, Komma). */
export function mbText(bytes: number): string {
  return (bytes / 1_000_000).toFixed(1).replace('.', ',');
}

/**
 * Breite und Hoehe aus dem Dateikopf — PNG (IHDR) und JPEG (SOF), ohne das Bild zu dekodieren
 * (laeuft auch ohne DOM). Andere Formate oder ein kaputter Kopf: `null`, dann wird die
 * Druckaufloesung nicht behauptet.
 */
export function bildMasseAusBytes(b: Uint8Array): BildMasse | null {
  if (b.length >= 24 && b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47) {
    const width = ((b[16]! << 24) | (b[17]! << 16) | (b[18]! << 8) | b[19]!) >>> 0;
    const height = ((b[20]! << 24) | (b[21]! << 16) | (b[22]! << 8) | b[23]!) >>> 0;
    return width > 0 && height > 0 ? { width, height } : null;
  }
  if (b.length >= 4 && b[0] === 0xff && b[1] === 0xd8) {
    let i = 2;
    while (i + 9 < b.length) {
      if (b[i] !== 0xff) return null;
      const marke = b[i + 1]!;
      // SOF0..SOF15 ausser DHT (C4), JPG (C8) und DAC (CC)
      if (marke >= 0xc0 && marke <= 0xcf && marke !== 0xc4 && marke !== 0xc8 && marke !== 0xcc) {
        const height = (b[i + 5]! << 8) | b[i + 6]!;
        const width = (b[i + 7]! << 8) | b[i + 8]!;
        return width > 0 && height > 0 ? { width, height } : null;
      }
      const laenge = (b[i + 2]! << 8) | b[i + 3]!;
      if (laenge < 2) return null;
      i += 2 + laenge;
    }
  }
  return null;
}

/** Base64 → Bytes, hoechstens `max` Bytes (fuer den Dateikopf genuegt der Anfang). */
function base64Anfang(b64: string, max: number): Uint8Array {
  const zeichen = Math.min(b64.length, Math.ceil(max / 3) * 4);
  const roh = atob(b64.slice(0, zeichen - (zeichen % 4)));
  const out = new Uint8Array(roh.length);
  for (let i = 0; i < roh.length; i++) out[i] = roh.charCodeAt(i);
  return out;
}

/** Masse einer `data:image/…;base64,…`-Adresse (s. `bildMasseAusBytes`). */
export function bildMasseAusDataUrl(dataUrl: string): BildMasse | null {
  const komma = dataUrl.indexOf(',');
  if (komma < 0) return null;
  try {
    return bildMasseAusBytes(base64Anfang(dataUrl.slice(komma + 1), 256 * 1024));
  } catch {
    return null;
  }
}

/**
 * Druckaufloesung am Platz — EINE Rechnung mit Publish (Prepare, `derive/sheet.ts` `druckaufloesung`,
 * `druckaufloesungSatz`, `bildFeldRechteck`). Gibt den Warnsatz zurueck, wenn es unter 150 dpi liegt, sonst `null`.
 */
export function druckWarnung(
  asset: Pick<ImageAsset, 'width' | 'height' | 'data'> | undefined,
  feld: Pick<SheetImage, 'x' | 'y' | 'w' | 'verhaeltnis'>,
): string | null {
  const d = druckaufloesung(asset, bildFeldRechteck(feld, asset));
  if (!d || d.dpi >= DRUCK_DPI_MIN) return null;
  return druckaufloesungSatz(d).replace(/^ · /, '');
}

/**
 * Warum ein Lauf nicht aufs Blatt und nicht zum Export kann — `null`, wenn er ein fertiges Bild
 * hat. Dieselbe Bedingung wie `laufMitBild` (`vis-runtime.ts`), nur mit Grund.
 */
export function laufNichtWaehlbar(lauf: Pick<NodeLauf, 'status' | 'jobId' | 'bild' | 'fehler' | 'teilbild'> | undefined): string | null {
  if (!lauf) return 'Noch kein Lauf — erst rendern.';
  switch (lauf.status) {
    case 'fertig':
      return lauf.jobId && lauf.bild ? null : 'Der Lauf ist fertig, hat aber kein Bild geliefert.';
    case 'abgebrochen':
      return lauf.teilbild
        ? 'Der Lauf wurde abgebrochen — sein Teilbild ist unvollständig und geht nicht aufs Blatt.'
        : 'Der Lauf wurde abgebrochen und hat kein Bild.';
    case 'fehler':
      return `Der Lauf ist gescheitert${lauf.fehler ? `: ${lauf.fehler}` : ''} — kein Bild.`;
    case 'zeitueberschreitung':
      return 'Der Lauf hat zu lange gebraucht und wurde aufgegeben — kein Bild.';
    default:
      return 'Der Lauf rechnet noch — das Bild kommt, wenn er fertig ist.';
  }
}

export type AblageStand =
  | { zustand: 'sichert' }
  | { zustand: 'gesichert'; assetId: string; masse: BildMasse | null; satz?: string }
  | { zustand: 'zu-gross'; bytes: number; satz: string }
  | { zustand: 'fehler'; grund: string; um: number };

interface BildAblageZustand {
  stand: Record<string, AblageStand>;
}

/** Was mit jedem Bild geschehen ist — fuer die Zeile in der Grossansicht und das Nachholen. */
export const useBildAblage = create<BildAblageZustand>(() => ({ stand: {} }));

export function setzeAblageStand(schluessel: string, stand: AblageStand): void {
  useBildAblage.setState((s) => ({ stand: { ...s.stand, [schluessel]: stand } }));
}

/** Der Satz zum Stand, wie er in der Grossansicht steht. */
export function ablageSatz(stand: AblageStand | undefined, masse?: BildMasse | null): string {
  if (!stand) return 'Noch nicht im Projekt — «Aufs Blatt» oder «Exportieren» holt es vom Heim-PC.';
  switch (stand.zustand) {
    case 'sichert':
      return 'Wird in voller Auflösung ins Projekt gesichert …';
    case 'gesichert': {
      const m = stand.masse ?? masse;
      const kopf = m ? `${m.width} × ${m.height} px · im Projekt gesichert` : 'Im Projekt gesichert';
      return stand.satz ? `${kopf} — ${stand.satz}` : kopf;
    }
    case 'zu-gross':
      return stand.satz;
    case 'fehler':
      return `Noch nicht im Projekt: ${stand.grund}`;
  }
}

/**
 * NAHT MIT PREPARE (21.10.2026): abgelegt wird ueber `publish.bildAblegen({ name, dataUrl, herkunft? })` →
 * «Bild-Id <id>» (Prepare, `claude/kosmo-pubprep-bild-ablegen`); gleiches `jobId + bild + guete` legt nichts neu an.
 * Wiedergefunden wird mit `abgelegtesBild(doc, { jobId, bild, guete })`; die Zuordnung der Sitzung ist nur Rueckfall.
 * Ohne `bildAblegen` (Visbox) wird nicht abgelegt. Der Kern lehnt ueber 5 MiB selbst ab (zweite Sicherung); sein Satz
 * wird durchgereicht.
 */
export const ABLEGEN_BEFEHL = 'publish.bildAblegen';

const zuordnung = new Map<string, string>();

export function ablegenDa(): boolean {
  return !!getCommand(ABLEGEN_BEFEHL);
}

/**
 * Das Projektbild dieses Laufs, wenn es im Projekt liegt (und noch da ist) — ueber die Herkunft am Asset
 * (`abgelegtesBild`, Prepare), also auch nach dem Neuladen. Ohne bekannte Guete gilt jedes Bild desselben Laufs und
 * derselben Datei (ein Aufrufer ohne Lauf soll es nicht ein zweites Mal ablegen).
 */
export function projektBild(jobId: string, bild: string, guete?: 'vorschau' | 'voll'): ImageAsset | undefined {
  const doc = useProject.getState().doc;
  const genau = abgelegtesBild(doc, { jobId, bild, guete });
  if (genau) return genau;
  if (guete === undefined) {
    const irgendeins = doc.byKind<ImageAsset>('imageasset').find((a) => a.herkunft?.jobId === jobId && a.herkunft.bild === bild);
    if (irgendeins) return irgendeins;
  }
  const id = zuordnung.get(ablageSchluessel(jobId, bild));
  const a = id ? doc.get<ImageAsset>(id) : undefined;
  return a && a.kind === 'imageasset' ? a : undefined;
}

/** Nur fuer Proben: die Zuordnung der Sitzung leeren. */
export function vergissZuordnung(): void {
  zuordnung.clear();
}

function neuesAsset(patches: readonly AnyPatch[]): string | undefined {
  for (const p of patches) {
    const nach = (p as { after?: unknown }).after as { kind?: string; id?: string } | null | undefined;
    if (nach && nach.kind === 'imageasset' && nach.id) return nach.id;
  }
  return undefined;
}

function bytesVon(dataUrl: string): number {
  const komma = dataUrl.indexOf(',');
  const b64 = komma >= 0 ? dataUrl.slice(komma + 1) : dataUrl;
  const fuellung = b64.endsWith('==') ? 2 : b64.endsWith('=') ? 1 : 0;
  return Math.max(0, Math.floor((b64.length * 3) / 4) - fuellung);
}

/**
 * Umkodieren fuer den Abgleich (Nahtstelle, in Proben ersetzbar): das Bild als JPEG mit `qualitaet`, die lange Seite
 * hoechstens `langeSeite` px. `null`, wenn es hier nicht geht (kein Canvas).
 */
export type Umkodierer = (dataUrl: string, o: { qualitaet: number; langeSeite?: number }) => Promise<string | null>;

const canvasUmkodierer: Umkodierer = async (dataUrl, o) => {
  if (typeof document === 'undefined' || typeof Image === 'undefined') return null;
  const img = new Image();
  const geladen = new Promise<boolean>((ok) => {
    img.onload = () => ok(true);
    img.onerror = () => ok(false);
  });
  img.src = dataUrl;
  if (!(await geladen) || !img.naturalWidth) return null;
  const lang = Math.max(img.naturalWidth, img.naturalHeight);
  const f = o.langeSeite && lang > o.langeSeite ? o.langeSeite / lang : 1;
  const c = document.createElement('canvas');
  c.width = Math.max(1, Math.round(img.naturalWidth * f));
  c.height = Math.max(1, Math.round(img.naturalHeight * f));
  const g = c.getContext('2d');
  if (!g) return null;
  g.drawImage(img, 0, 0, c.width, c.height);
  const url = c.toDataURL('image/jpeg', o.qualitaet);
  return url.startsWith('data:image/jpeg') ? url : null;
};

let umkodierer: Umkodierer = canvasUmkodierer;
export function setzeUmkodierer(u: Umkodierer | null): void {
  umkodierer = u ?? canvasUmkodierer;
}

/**
 * Vor dem Ablegen (Integrator/Prepare 21.10.2026): der Abgleich deckelt eine Nachricht auf 8 MiB, Base64 ×1,33 —
 * ueber 5 MB Rohbild riss die Verbindung still. Darum: unter der Grenze bleibt das Bild, wie es ist; darueber als JPEG
 * (Qualitaet 0,9); reicht das nicht, verkleinert (lange Seite in Stufen, nie unter 1200 px); geht auch das nicht,
 * abgelehnt — immer mit Satz, nie still. Das Original bleibt ueber «Exportieren» erhaeltlich.
 */
export async function fuerDenAbgleich(
  dataUrl: string,
): Promise<{ dataUrl: string; satz?: string } | { abgelehnt: string }> {
  const roh = bytesVon(dataUrl);
  if (roh <= ABLAGE_GRENZE_BYTES) return { dataUrl };
  const grenze = `${mbText(ABLAGE_GRENZE_BYTES)} MB`;
  const masse = bildMasseAusDataUrl(dataUrl);
  const jpeg = await umkodierer(dataUrl, { qualitaet: 0.9 });
  if (jpeg && bytesVon(jpeg) <= ABLAGE_GRENZE_BYTES) {
    return { dataUrl: jpeg, satz: `${mbText(roh)} MB über der Grenze von ${grenze} — als JPEG (Qualität 90 %) abgelegt, ${mbText(bytesVon(jpeg))} MB, gleiche Auflösung. Das Original gibt «Exportieren».` };
  }
  if (jpeg && masse) {
    let lang = Math.max(masse.width, masse.height);
    while (lang * 0.75 >= VERKLEINERN_MIN_PX) {
      lang = Math.round(lang * 0.75);
      const klein = await umkodierer(dataUrl, { qualitaet: 0.9, langeSeite: lang });
      if (klein && bytesVon(klein) <= ABLAGE_GRENZE_BYTES) {
        const m = bildMasseAusDataUrl(klein);
        return {
          dataUrl: klein,
          satz: `${mbText(roh)} MB über der Grenze von ${grenze} — als JPEG verkleinert auf ${m ? `${m.width} × ${m.height}` : `${lang} px`} abgelegt, ${mbText(bytesVon(klein))} MB. Das Original gibt «Exportieren».`,
        };
      }
    }
  }
  return {
    abgelehnt:
      `Nicht im Projekt abgelegt: ${mbText(roh)} MB, und auch als JPEG${masse ? ' und verkleinert bis 1200 px' : ''} nicht unter ${grenze} — ` +
      `der Abgleich trüge es nicht. Das Original gibt «Exportieren».`,
  };
}

/**
 * Ein geholtes Bild ins Projekt (je Bild ein eigener `bildAblegen`-Aufruf), ohne Rueckgaengig-Schritt (Prepare: ok,
 * Ablegen legt nur das Asset an; Setzen ist ein eigener Schritt). Gibt den Stand zurueck.
 */
export async function sichereImProjekt(
  jobId: string,
  bild: string,
  name: string,
  dataUrl: string,
  zusatz: { guete?: 'vorschau' | 'voll' | undefined; lizenzOffen?: { modell?: string; lizenz?: string } | undefined } = {},
): Promise<AblageStand> {
  const schluessel = ablageSchluessel(jobId, bild);
  const setze = (st: AblageStand): AblageStand => {
    setzeAblageStand(schluessel, st);
    return st;
  };
  const vorhanden = projektBild(jobId, bild, zusatz.guete);
  if (vorhanden) return setze({ zustand: 'gesichert', assetId: vorhanden.id, masse: masseVon(vorhanden) });
  if (!ablegenDa()) return setze({ zustand: 'fehler', grund: 'Ablegen ins Projekt gibt es hier nicht.', um: Date.now() });
  const vorbereitet = await fuerDenAbgleich(dataUrl);
  if ('abgelehnt' in vorbereitet) return setze({ zustand: 'zu-gross', bytes: bytesVon(dataUrl), satz: vorbereitet.abgelehnt });
  const herkunft = {
    jobId,
    bild,
    ...(zusatz.guete ? { guete: zusatz.guete } : {}),
    ...(zusatz.lizenzOffen ? { lizenzOffen: zusatz.lizenzOffen } : {}),
  };
  try {
    const r = ohneVerlauf(() => useProject.getState().runCommand(ABLEGEN_BEFEHL, { name, dataUrl: vorbereitet.dataUrl, herkunft }));
    const id = neuesAsset(r.patches) ?? projektBild(jobId, bild, zusatz.guete)?.id;
    if (!id) return setze({ zustand: 'fehler', grund: 'Das Projekt hat das Bild nicht angenommen.', um: Date.now() });
    zuordnung.set(schluessel, id);
    const a = useProject.getState().doc.get<ImageAsset>(id);
    return setze({
      zustand: 'gesichert',
      assetId: id,
      masse: a ? masseVon(a) : bildMasseAusDataUrl(vorbereitet.dataUrl),
      ...(vorbereitet.satz ? { satz: vorbereitet.satz } : {}),
    });
  } catch (err) {
    return setze({ zustand: 'fehler', grund: err instanceof Error ? err.message : String(err), um: Date.now() });
  }
}

export function masseVon(a: Pick<ImageAsset, 'width' | 'height'>): BildMasse | null {
  return a.width && a.height ? { width: a.width, height: a.height } : null;
}

/**
 * Ob es ein Blatt gibt (Nahtstelle des Wirts). In KosmoOrbit immer; Visbox hat kein Blatt und kein Projekt, in dem das
 * Bild bliebe (die Mappe sichert nur Graphen) — dort schaltet der Wirt es ab: kein Ablegen, und «Aufs Blatt» faellt in
 * der Grossansicht weg (UI_AUSNAHMEN, Entscheid 115).
 */
let blattDa = true;
export function setzeBlattDa(da: boolean): void {
  blattDa = da;
}
export function istBlattDa(): boolean {
  return blattDa;
}
