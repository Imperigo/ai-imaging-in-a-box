import { create } from 'zustand';
import { getCommand, gesichertesVisBild, type AnyPatch, type ImageAsset } from '@kosmo/kernel';
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
 *  - beim Platzieren wird die Druckaufloesung am Platz geprueft (`druckPruefung`) und gewarnt;
 *  - ein Lauf ohne fertiges Bild ist nicht waehlbar und sagt, warum (`laufNichtWaehlbar`).
 *
 * Die Netzseite (Bild holen, Export) und das Nachholen fuer den Verlauf liegen in
 * `bild-ablage.ts`; diese Datei importiert nichts aus `vis-jobs.ts`, damit `vis-jobs.ts` sie
 * benutzen kann, ohne einen Kreis zu schliessen.
 */

/**
 * Bis zu dieser Groesse (Bytes des Bildes) kommt ein Bild ins Projekt. Die harte Grenze liegt
 * beim Abgleich: der Sync-Server deckelt EINE Nachricht auf 8 MiB (`KOSMO_SYNC_MAX_BYTES`), und
 * Base64 macht aus 5 MiB rund 6,7 MiB — darueber risse die Verbindung, statt zu melden. Ein
 * groesseres Bild bleibt am Heim-PC; «Aufs Blatt» bettet es dann wie bisher direkt ein, und
 * «Exportieren» holt es von dort.
 */
export const ABLAGE_GRENZE_BYTES = 5 * 1024 * 1024;

/** Unter dieser Aufloesung am Platz warnt das Platzieren (Druck, gesperrt wird nichts). */
export const DRUCK_DPI_MIN = 150;

const MM_JE_ZOLL = 25.4;

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
  return (bytes / 1_048_576).toFixed(1).replace('.', ',');
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
 * Die Druckaufloesung am Platz: Pixel gegen die Breite des Felds auf dem Papier. Hat das Feld ein
 * festes Seitenverhaeltnis (`verhaeltnis`, Breite/Hoehe), fuellt das Bild es (`slice`) — dann
 * zaehlt die knappere Richtung. Ohne Verhaeltnis folgt die Hoehe dem Bild, es zaehlt die Breite.
 */
export function druckDpi(px: BildMasse, breiteMm: number, verhaeltnis?: number): number {
  const jeBreite = (px.width * MM_JE_ZOLL) / breiteMm;
  if (verhaeltnis === undefined || !(verhaeltnis > 0)) return jeBreite;
  const hoeheMm = breiteMm / verhaeltnis;
  return Math.min(jeBreite, (px.height * MM_JE_ZOLL) / hoeheMm);
}

export interface DruckPruefung {
  /** Reicht es fuer den Druck (≥ `DRUCK_DPI_MIN`)? `null`: Masse unbekannt, nichts behauptet. */
  ok: boolean | null;
  dpi?: number;
  /** Die groesste Breite in mm, bei der es noch reicht (nur wenn es nicht reicht). */
  hoechstensMm?: number;
  satz: string;
}

/**
 * VORLAEUFIG bis Prepare `derive/bildgroesse.ts` (`druckaufloesung`, `druckaufloesungSatz`, Zweig
 * `claude/kosmo-pubprep-bild-druckaufloesung`) eingespielt ist — dann rufen die zwei Stellen in `vis-jobs.ts` jene
 * Funktion, und diese faellt weg (Naht mit Prepare, 21.10.2026). Rechteck wie `imagePaperBounds`.
 *
 * Der Satz zum Platzieren. Reicht es nicht, sagt er Pixel, Breite, dpi und die groesste Breite,
 * bei der es noch reicht — ein kleines Bild wird nicht hochgerechnet, nur benannt.
 */
export function druckPruefung(px: BildMasse | null | undefined, breiteMm: number, verhaeltnis?: number): DruckPruefung {
  if (!px) return { ok: null, satz: 'Grösse des Bildes unbekannt — die Druckauflösung ist nicht geprüft.' };
  const dpi = druckDpi(px, breiteMm, verhaeltnis);
  const mm = Math.round(breiteMm);
  if (dpi >= DRUCK_DPI_MIN) {
    return { ok: true, dpi, satz: `${Math.round(dpi)} dpi bei ${mm} mm Breite — druckfähig.` };
  }
  const hoechstensMm = Math.floor((breiteMm * dpi) / DRUCK_DPI_MIN);
  return {
    ok: false,
    dpi,
    hoechstensMm,
    satz:
      `Zu grob für den Druck: ${px.width} × ${px.height} px auf ${mm} mm sind ${Math.round(dpi)} dpi, ` +
      `nötig sind ${DRUCK_DPI_MIN}. Höchstens ${hoechstensMm} mm breit setzen oder grösser rendern.`,
  };
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
  | { zustand: 'gesichert'; assetId: string; masse: BildMasse | null }
  | { zustand: 'zu-gross'; bytes: number }
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
      return m ? `${m.width} × ${m.height} px · im Projekt gesichert` : 'Im Projekt gesichert';
    }
    case 'zu-gross':
      return `Nicht im Projekt gesichert: ${mbText(stand.bytes)} MB, Grenze ${mbText(ABLAGE_GRENZE_BYTES)} MB. Es liegt weiter am Heim-PC.`;
    case 'fehler':
      return `Noch nicht im Projekt: ${stand.grund}`;
  }
}

/**
 * NAHT MIT PREPARE (21.10.2026): abgelegt wird ueber `publish.bildAblegen({ name, dataUrl }) → Asset-Kennung`
 * (Prepare, Zweig `claude/kosmo-pubprep-bild-ablegen`, Ziel v0.1.10, noch nicht eingespielt). Solange es den Befehl
 * nicht gibt, springt der STELLVERTRETER `vis.bildSichern` ein (Kern-Vorschlag dieses Zweigs) — er faellt weg, sobald
 * `bildAblegen` da ist. Welcher Weg gilt, entscheidet allein `getCommand('publish.bildAblegen')`.
 */
export const ABLEGEN_BEFEHL = 'publish.bildAblegen';
export const ABLEGEN_STELLVERTRETER = 'vis.bildSichern';

/**
 * Welcher Lauf welches Projektbild hat. `bildAblegen` traegt (noch) keine Herkunft am Asset — darum merkt KosmoVis sich
 * die Zuordnung hier (fuer diese Sitzung). Der Stellvertreter schreibt sie zusaetzlich als `visHerkunft` ans Asset.
 * Bitte an Prepare: `bildAblegen` mit optionaler Herkunft, dann haelt sie auch ueber das Neuladen.
 */
const zuordnung = new Map<string, string>();

export function ablegenWeg(): 'bildAblegen' | 'stellvertreter' {
  return getCommand(ABLEGEN_BEFEHL) ? 'bildAblegen' : 'stellvertreter';
}

/** Das Projektbild dieses Laufs, wenn es im Projekt liegt (und noch da ist). */
export function projektBild(jobId: string, bild: string): ImageAsset | undefined {
  const doc = useProject.getState().doc;
  const mitHerkunft = gesichertesVisBild(doc, jobId, bild);
  if (mitHerkunft) return mitHerkunft;
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

/**
 * Ob gesichert wird (Nahtstelle des Wirts). In KosmoOrbit immer; Visbox hat kein Blatt und kein
 * Projekt, in dem das Bild bliebe (die Mappe sichert nur Graphen) — dort schaltet der Wirt es
 * ab, und «Aufs Blatt» faellt in der Grossansicht weg (UI_AUSNAHMEN, Entscheid 115).
 */
let blattDa = true;
export function setzeBlattDa(da: boolean): void {
  blattDa = da;
}
export function istBlattDa(): boolean {
  return blattDa;
}

/**
 * Ein geholtes Bild ins Projekt: liegt es schon dort, bleibt es; ist es zu gross, bleibt es am
 * Heim-PC (Stand `zu-gross`). Ohne Rueckgaengig-Schritt. Gibt den Stand zurueck.
 */
export function sichereImProjekt(
  jobId: string,
  bild: string,
  name: string,
  dataUrl: string,
  zusatz: { guete?: 'vorschau' | 'voll' | undefined; lizenzOffen?: { modell?: string; lizenz?: string } | undefined } = {},
): AblageStand {
  const schluessel = ablageSchluessel(jobId, bild);
  const vorhanden = projektBild(jobId, bild);
  if (vorhanden) {
    const stand: AblageStand = { zustand: 'gesichert', assetId: vorhanden.id, masse: masseVon(vorhanden) };
    setzeAblageStand(schluessel, stand);
    return stand;
  }
  const komma = dataUrl.indexOf(',');
  const b64 = komma >= 0 ? dataUrl.slice(komma + 1) : dataUrl;
  const fuellung = b64.endsWith('==') ? 2 : b64.endsWith('=') ? 1 : 0;
  const bytes = Math.max(0, Math.floor((b64.length * 3) / 4) - fuellung);
  if (bytes > ABLAGE_GRENZE_BYTES) {
    const stand: AblageStand = { zustand: 'zu-gross', bytes };
    setzeAblageStand(schluessel, stand);
    return stand;
  }
  const masse = bildMasseAusDataUrl(dataUrl);
  try {
    const r = ohneVerlauf(() =>
      ablegenWeg() === 'bildAblegen'
        ? useProject.getState().runCommand(ABLEGEN_BEFEHL, { name, dataUrl })
        : useProject.getState().runCommand(ABLEGEN_STELLVERTRETER, {
            jobId,
            bild,
            name,
            dataUrl,
            ...(masse ? { width: masse.width, height: masse.height } : {}),
            ...(zusatz.guete ? { guete: zusatz.guete } : {}),
            ...(zusatz.lizenzOffen ? { lizenzOffen: zusatz.lizenzOffen } : {}),
          }),
    );
    const id = neuesAsset(r.patches);
    if (id) zuordnung.set(schluessel, id);
  } catch (err) {
    const stand: AblageStand = { zustand: 'fehler', grund: err instanceof Error ? err.message : String(err), um: Date.now() };
    setzeAblageStand(schluessel, stand);
    return stand;
  }
  const neu = projektBild(jobId, bild);
  const stand: AblageStand = neu
    ? { zustand: 'gesichert', assetId: neu.id, masse }
    : { zustand: 'fehler', grund: 'Das Projekt hat das Bild nicht angenommen.', um: Date.now() };
  setzeAblageStand(schluessel, stand);
  return stand;
}

export function masseVon(a: Pick<ImageAsset, 'width' | 'height'>): BildMasse | null {
  return a.width && a.height ? { width: a.width, height: a.height } : null;
}
