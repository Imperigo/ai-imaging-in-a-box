/**
 * SKIZZE VOM IPAD — die Skizzen-Quelle, die der WIRT bereitstellt (Owner-Entscheide 95/95a der
 * Visbox, 14.10.2026, Blatt 25).
 *
 * Anlass: Die Knotenansicht ist in beiden Programmen die Arbeitsfläche zum Rendern
 * (Entscheid 94). Die Skizzen, die man am iPad zeichnet und «In die Mappe legt», standen bisher
 * nur auf der alten Visbox-Seite. Der Knoten «Skizze vom iPad» holt sie in die Knotenansicht:
 * von selbst die neueste, eine ältere am Knoten wählbar.
 *
 * Das Vis-Werkzeug läuft in zwei Programmen, und nur eines hat eine Mappe mit Skizzen:
 *
 * - **In Visbox** meldet der Wirt die Quelle an (`registriereSkizzenQuelle`): die Liste aus der
 *   Mappe am Heim-PC, die Bilder vom selben Server.
 * - **In KosmoOrbit** meldet niemand etwas an. Der Knoten steht trotzdem im Katalog — wie der
 *   Modell-Knoten, der ohne Lade-Fähigkeit seine eine Zeile zeigt (`modell-laden.ts`) — und
 *   sagt ruhig, dass es Skizzen vom iPad in Visbox gibt. Ausgeblendet wird er nicht: Ein Graph,
 *   der in Visbox entstand, bliebe sonst mit einem Knoten stehen, den die Palette nicht kennt.
 *
 * Darum steht hier kein Weg zu einem Server: Den weiss nur der Wirt. Ohne React-Abhängigkeit —
 * ein kleiner Speicher mit Hörern, den Knoten und Canvas über `useSyncExternalStore` lesen.
 */

/** Typ des Knotens im Katalog (`derive/visgraph.ts`). */
export const SKIZZE_IPAD_TYP = 'skizzeIpad' as const;

/** Wert des Parameters `skizze`, wenn der Knoten von selbst die neueste nimmt (Vorgabe). */
export const SKIZZE_NEUESTE = 'neueste';

/** Ohne Wirt (KosmoOrbit). */
export const SKIZZE_OHNE_WIRT_SATZ = 'Skizzen vom iPad gibt es in Visbox.';

/** Mit Wirt, aber die Mappe hat keine Skizze. */
export const SKIZZE_LEER_SATZ = 'Noch keine Skizze in der Mappe — am iPad zeichnen und «In die Mappe legen».';

/** Beschriftung des Bilds auf einem Blatt (Pflicht-Beschriftung, `platziereBildAufsBlatt`). */
export const SKIZZE_BESCHRIFTUNG = 'Skizze (iPad)';

/** Eine Skizze der Mappe, wie der Wirt sie meldet — die neueste zuerst. */
export interface Skizze {
  /** Dateiname in der Mappe; zugleich der gespeicherte Wert, wenn sie gewählt ist. */
  name: string;
  titel?: string | null;
  /** Zeitpunkt (ISO), zu dem sie in die Mappe gelegt wurde. */
  erzeugt?: string | null;
  /** Worüber gezeichnet wurde (ein Bild der Mappe), wenn überhaupt. */
  ueber?: string | null;
  /** Zustand in der Mappe (verworfene meldet der Wirt nicht). */
  stand?: string | null;
  /**
   * Entscheid 96a (Owner, 15.10.2026): die Bemerkung, die beim Zeichnen an der Skizze stand — sie
   * ist die Anweisung, wenn die Skizze am Render-Knoten hängt. `null` oder leer: keine geschrieben
   * (dann wird nichts gesendet). Fehlt das Feld ganz (ein Wirt, der es nicht meldet), ist sie
   * unbekannt, und die Bildseite entscheidet.
   */
  bemerkung?: string | null;
  /**
   * Entscheid 96b (Owner, 15.10.2026): von wo das Bild aus dieser Skizze entsteht, wie es die
   * Bibliothek der Visbox sagt (`projekt.standpunkt_fuer_skizze`): `'bild'` — vom Standpunkt
   * des Bildes, auf das gezeichnet wurde (`ueber`); `'mappe'` — vom Standpunkt der Mappe (keine
   * Unterlage, oder von ihr ist der Standpunkt nicht bekannt). Fehlt das Feld, wird aus `ueber`
   * geschlossen.
   */
  standpunkt?: 'bild' | 'mappe' | null;
}

/** Was der Wirt bereitstellt. */
export interface SkizzenQuelle {
  /** Die Skizzen der Mappe, die neueste zuerst. */
  liste(): Promise<Skizze[]>;
  /** Adresse des Bilds einer Skizze (für `<img>` und zum Holen). */
  bildUrl(name: string): string;
}

export interface SkizzenStand {
  quelle: SkizzenQuelle | null;
  /** `null`: noch nicht gelesen. */
  liste: readonly Skizze[] | null;
  laedt: boolean;
  /** Satz, wenn das Lesen der Liste scheiterte. */
  fehler: string | null;
  /** Geholte Bilder als data:-Adresse, je Name — für Vergleich und Blatt. */
  bilder: Readonly<Record<string, string>>;
}

const LEER: SkizzenStand = { quelle: null, liste: null, laedt: false, fehler: null, bilder: {} };
let stand: SkizzenStand = LEER;
const hoerer = new Set<() => void>();
let laufendeListe: Promise<void> | null = null;
const laufendeBilder = new Map<string, Promise<string | null>>();

function setze(neu: Partial<SkizzenStand>): void {
  stand = { ...stand, ...neu };
  for (const h of hoerer) h();
}

/**
 * Der Wirt stellt die Skizzen-Quelle bereit — oder nimmt sie mit `null` zurück. Danach wird die
 * Liste neu gelesen; Gelesenes einer früheren Quelle fällt weg.
 */
export function registriereSkizzenQuelle(quelle: SkizzenQuelle | null): void {
  laufendeListe = null;
  laufendeBilder.clear();
  stand = { ...LEER, quelle };
  for (const h of hoerer) h();
  if (quelle) void aktualisiereSkizzen();
}

/** Die angemeldete Quelle, oder `null` (KosmoOrbit: es gibt keine). */
export function skizzenQuelle(): SkizzenQuelle | null {
  return stand.quelle;
}

export function skizzenStand(): SkizzenStand {
  return stand;
}

export function abonniereSkizzen(h: () => void): () => void {
  hoerer.add(h);
  return () => {
    hoerer.delete(h);
  };
}

/**
 * Liest die Liste neu. Läuft schon ein Lesen, wird keines daneben begonnen. Ein Fehler steht
 * danach als Satz im Stand; die zuletzt gelesene Liste bleibt stehen.
 */
export function aktualisiereSkizzen(): Promise<void> {
  const quelle = stand.quelle;
  if (!quelle) return Promise.resolve();
  if (laufendeListe) return laufendeListe;
  setze({ laedt: true });
  const lauf = liesListe(quelle).finally(() => {
    if (laufendeListe === lauf) laufendeListe = null;
  });
  laufendeListe = lauf;
  return lauf;
}

async function liesListe(quelle: SkizzenQuelle): Promise<void> {
  try {
    const liste = await quelle.liste();
    if (stand.quelle !== quelle) return;
    setze({ liste: [...liste], laedt: false, fehler: null });
  } catch (fehler) {
    if (stand.quelle !== quelle) return;
    setze({
      laedt: false,
      fehler: `Die Skizzen liessen sich nicht lesen: ${fehler instanceof Error ? fehler.message : String(fehler)}`,
    });
  }
}

/** Der gespeicherte Wert des Knotens — «neueste», wenn nichts (oder Leeres) gespeichert ist. */
export function skizzenWahl(params: Readonly<Record<string, unknown>> | undefined): string {
  const roh = params?.['skizze'];
  return typeof roh === 'string' && roh.trim() ? roh : SKIZZE_NEUESTE;
}

/** Welche Skizze gilt: «neueste» → die erste der Liste; ein Name → genau diese, sonst `null`. */
export function waehleSkizze(liste: readonly Skizze[] | null, wahl: string): Skizze | null {
  if (!liste || liste.length === 0) return null;
  if (wahl === SKIZZE_NEUESTE) return liste[0] ?? null;
  return liste.find((s) => s.name === wahl) ?? null;
}

/** «14.10. 09:12» aus einem ISO-Zeitpunkt — leer, wenn er sich nicht lesen lässt. */
export function skizzenZeit(erzeugt: string | null | undefined): string {
  if (!erzeugt) return '';
  const t = new Date(erzeugt);
  if (Number.isNaN(t.getTime())) return '';
  const zwei = (n: number) => String(n).padStart(2, '0');
  return `${zwei(t.getDate())}.${zwei(t.getMonth() + 1)}. ${zwei(t.getHours())}:${zwei(t.getMinutes())}`;
}

/** Wie eine Skizze in der Auswahl heisst: ihr Titel (sonst der Dateiname), dahinter die Zeit. */
export function skizzenName(s: Skizze): string {
  const titel = (s.titel ?? '').trim() || s.name;
  const zeit = skizzenZeit(s.erzeugt);
  return zeit ? `${titel} · ${zeit}` : titel;
}

function alsDataUrl(blob: Blob): Promise<string> {
  return new Promise((fertig, fehlschlag) => {
    const leser = new FileReader();
    leser.onload = () => fertig(String(leser.result));
    leser.onerror = () => fehlschlag(leser.error ?? new Error('Bild nicht lesbar'));
    leser.readAsDataURL(blob);
  });
}

/**
 * Holt das Bild einer Skizze als data:-Adresse (einmal je Name). Vergleich und Blatt brauchen
 * das Bild selbst, nicht nur seine Adresse — ein Blatt trägt seine Bilder im Dokument.
 *
 * @returns die data:-Adresse, oder `null` (keine Quelle, nicht erreichbar).
 */
export function holeSkizzenBild(name: string): Promise<string | null> {
  const quelle = stand.quelle;
  if (!quelle) return Promise.resolve(null);
  const schon = stand.bilder[name];
  if (schon) return Promise.resolve(schon);
  const laeuft = laufendeBilder.get(name);
  if (laeuft) return laeuft;
  const lauf = (async () => {
    try {
      const antwort = await fetch(quelle.bildUrl(name));
      if (!antwort.ok) return null;
      const url = await alsDataUrl(await antwort.blob());
      if (stand.quelle !== quelle) return null;
      setze({ bilder: { ...stand.bilder, [name]: url } });
      return url;
    } catch {
      return null;
    } finally {
      laufendeBilder.delete(name);
    }
  })();
  laufendeBilder.set(name, lauf);
  return lauf;
}

/**
 * Das Bild am Ausgang eines Skizzen-Knotens, für den Bild-Eingang eines anderen Knotens
 * (`bildQuelle` im Canvas). Ist es noch nicht geholt, wird es angestossen und es gibt vorerst
 * nichts — der Speicher meldet sich, sobald es da ist.
 */
export function skizzeAlsBildQuelle(
  params: Readonly<Record<string, unknown>> | undefined,
): { dataUrl: string; beschriftung: string } | null {
  const gewaehlt = waehleSkizze(stand.liste, skizzenWahl(params));
  if (!gewaehlt) return null;
  const url = stand.bilder[gewaehlt.name];
  if (!url) {
    void holeSkizzenBild(gewaehlt.name);
    return null;
  }
  return { dataUrl: url, beschriftung: SKIZZE_BESCHRIFTUNG };
}

/* ------------------------------------------------------------------ *
 * Owner-Entscheid 96 (Visbox, 15.10.2026): DIE SKIZZE FUEHRT DAS BILD.
 * ------------------------------------------------------------------ */

/** Was die Bestellung über die Skizze trägt (`RenderScene.skizze` ohne `quelle`). */
export interface SkizzeDerBestellung {
  /** Der Dateiname der Skizze in der Mappe — «neueste» ist hier schon aufgelöst. */
  name: string;
  /**
   * Was sich am Bild ändern soll; fehlt sie, nimmt die Bildseite die Bemerkung der Skizze. Die
   * Knotenansicht setzt sie seit Entscheid 96a nur als RÜCKFALL (96c): den Prompt, wenn die Skizze
   * keine Bemerkung hat (`skizzeZurBestellung`) — der Vertrag kennt
   * das Feld für andere Besteller.
   */
  anweisung?: string;
}

/** Hängt eine Skizze am Render-Knoten, aber hier gibt es keine Mappe (KosmoOrbit). */
export const SKIZZE_NUR_IN_VISBOX_SATZ =
  'Die Skizze am Render-Knoten kommt nur in Visbox an — bestellt ist das Bild aus dem Modell.';

/** Die gewählte Skizze steht nicht (mehr) in der Mappe. */
export const SKIZZE_FEHLT_SATZ =
  'Die gewählte Skizze steht nicht (mehr) in der Mappe — nichts gesendet. Am Skizzen-Knoten eine andere wählen.';

/** Entscheid 96a: die gewählte Skizze hat keine Bemerkung — und die ist mit Skizze die Anweisung. */
export const SKIZZE_OHNE_BEMERKUNG_SATZ = 'Die Skizze hat keine Bemerkung, und am Render-Knoten hängt kein Prompt — eines von beiden braucht es.';

/**
 * Entscheid 96a: hat die Skizze eine Bemerkung? `true`/`false`, oder `null`, wenn der Wirt das Feld
 * nicht meldet (dann entscheidet die Bildseite, und sie weist ohne Bemerkung mit Satz ab).
 */
export function skizzeHatBemerkung(s: Skizze): boolean | null {
  if (s.bemerkung === undefined) return null;
  return typeof s.bemerkung === 'string' && s.bemerkung.trim() !== '';
}

/**
 * Die Skizze für eine Bestellung — aus der Wahl am Skizzen-Knoten («neueste» oder ein Dateiname).
 *
 * **Entscheid 96a (Owner, 15.10.2026):** Hängt eine Skizze am Render-Knoten, gilt die BEMERKUNG
 * DER SKIZZE als Anweisung; die Stimmung (der Prompt des Knotens) tritt zurück. Darum geht KEINE
 * `anweisung` mit — die Bildseite nimmt die Bemerkung, wie `rechne_skizze` ohne Anweisung. Hat die
 * Skizze keine Bemerkung, wird nichts gesendet: Die Bildseite wiese sie ohnehin ab, aber erst nach
 * dem Freigeben am Heim-PC.
 *
 * Vor dem Auflösen wird die Liste der Mappe NEU gelesen: «neueste» heisst die neueste zum Zeitpunkt
 * des Klicks, nicht die beim letzten Blick auf den Knoten.
 *
 * @returns die Skizze; `undefined`, wenn es keinen Wirt gibt (KosmoOrbit: das Bild kommt aus dem
 *   Modell, und der Aufrufer sagt das). Wirft mit Satz, wenn der Wirt die Skizze nicht (mehr) kennt,
 *   die Liste sich nicht lesen liess oder die Skizze keine Bemerkung hat — dann wird nichts gesendet.
 */
export async function skizzeZurBestellung(wahl: string, prompt = ''): Promise<SkizzeDerBestellung | undefined> {
  if (!stand.quelle) return undefined;
  await aktualisiereSkizzen();
  if (stand.fehler) throw new Error(`${stand.fehler} — nichts gesendet.`);
  if (!stand.liste || stand.liste.length === 0) throw new Error(`${SKIZZE_LEER_SATZ} Nichts gesendet.`);
  const skizze = waehleSkizze(stand.liste, wahl);
  if (!skizze) throw new Error(SKIZZE_FEHLT_SATZ);
  // RUECKFALL (Owner, 15.10.2026, Entscheid 96c): Am iPad gibt es noch kein Feld fuer die
  // Bemerkung. Ohne Bemerkung gilt darum der Prompt des Render-Knotens als Anweisung; erst wenn
  // auch der leer ist, wird nichts gesendet.
  if (skizzeHatBemerkung(skizze) === false) {
    const anweisung = prompt.trim();
    if (!anweisung) throw new Error(`${SKIZZE_OHNE_BEMERKUNG_SATZ} Nichts gesendet.`);
    return { name: skizze.name, anweisung };
  }
  return { name: skizze.name };
}
