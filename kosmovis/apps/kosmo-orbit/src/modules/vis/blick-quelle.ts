import { kameraArtAusParams, kameraBlickAusParams, kameraBlickId, kameraBlickName, type KosmoDoc, type VisNode } from '@kosmo/kernel';

/**
 * **GESICHERTE BLICKE FÜR DEN KNOTEN «KAMERA»** (Video-Befund L4-4, 21.10.2026, Blatt «Blick zur
 * Kamera»).
 *
 * Befund: Ein im Entwurf gesicherter Fussgänger-Blick kam nicht im Kamera-Knoten an. Der einzige Weg
 * war «Kamera aus 3D-Ansicht», und der verlangt eine offene 3D-Ansicht; der Knoten blieb
 * unverbunden. Jetzt bietet der Knoten «Kamera» die gesicherten Blicke als Auswahl an (Reiter
 * «Blick») — ohne 3D-Ansicht. Ein gewählter Blick wird zur Kamera der Grundlage (eine Grundlage, nur
 * die Stimmung variiert).
 *
 * EINE LISTE, ZWEI QUELLEN:
 *  - **Entwurf** (KosmoOrbit): `doc.settings.gespeicherteBlicke` — dieselbe Liste, die die
 *    BLICKE-Leiste der 3D-Ansicht zeigt und `design.blickSichern` schreibt. Niemand registriert
 *    etwas; gelesen wird das Dokument.
 *  - **Wirt** (Visbox): die Standpunkte der offenen Mappe, die der Wirt hier anmeldet
 *    (`registriereBlickQuelle`, Muster `registriereModellLaden`). Visbox hat keinen Entwurf.
 *
 * KENNUNG STATT NAME (Wunsch von KosmoDraw, v0.1.10): Blicke sind umbenennbar
 * (`design.blickUmbenennen`). Der Knoten hält darum die Kennung (`blickId`) fest und liest den
 * Namen jedes Mal neu; ein umbenannter Blick bleibt gültig, ohne Satz. Zwei Blicke dürfen gleich
 * heissen — die Auswahl unterscheidet sie an der Kennung, ein Aufruf nur mit Namen wird dann
 * abgewiesen.
 *
 * Kein React im Kern: ein kleiner Speicher mit Hörern wie `heim-standpunkte.ts`.
 */

/** Ein Blick, wie der Knoten ihn anbietet — glTF-Achsen (Y oben), Meter, waagrechter Bildwinkel. */
export interface WaehlbarerBlick {
  /** Stabil über Umbenennen: `GespeicherterBlick.id`, beim Wirt seine eigene (Visbox: `bild:<Bild>`). */
  id: string;
  name: string;
  /** Woher: «Entwurf» (gesichert in der 3D-Ansicht) oder was der Wirt nennt («Mappe» …). */
  herkunft: string;
  position: [number, number, number];
  target: [number, number, number];
  fov: number;
}

/** Was der Wirt meldet: seine Blicke und der Satz, wenn er keine hat. */
export interface BlickQuelle {
  blicke: WaehlbarerBlick[];
  /** Steht am Knoten, wenn die Liste leer ist — statt `KEIN_BLICK_SATZ`. */
  leerSatz?: string;
}

/** Am Knoten, wenn es keinen gesicherten Blick gibt (KosmoOrbit). */
export const KEIN_BLICK_SATZ =
  'Noch kein Blick gesichert — in der 3D-Ansicht «Blick sichern»; er steht danach hier, ohne dass die 3D-Ansicht offen sein muss.';

/** Am Knoten und beim Senden, wenn «Blick» gewählt, aber kein Blick da ist. */
export const KAMERA_BLICK_FEHLT_HINWEIS = 'Der Knoten «Kamera» steht auf «Blick», aber es ist kein Blick gewählt — erst einen Blick wählen.';

let quelle: BlickQuelle | null = null;
const hoerer = new Set<() => void>();
let fassung = 0;

/** Der Wirt meldet die Blicke seiner offenen Mappe an — `null`: keine (KosmoOrbit). */
export function registriereBlickQuelle(neu: BlickQuelle | null): void {
  quelle = neu;
  fassung++;
  for (const h of hoerer) h();
}

export function blickQuelleFassung(): number {
  return fassung;
}

export function abonniereBlickQuelle(h: () => void): () => void {
  hoerer.add(h);
  return () => {
    hoerer.delete(h);
  };
}

function rund(x: number, stellen = 3): number {
  const f = 10 ** stellen;
  return Math.round(x * f) / f;
}

/**
 * Alle wählbaren Blicke, in fester Reihenfolge: zuerst die des Entwurfs, dann die des Wirts. Jede
 * Kennung steht einmal; gleiche Namen bleiben stehen (die Auswahl zeigt dann die Herkunft dazu).
 */
export function waehlbareBlicke(doc: KosmoDoc): WaehlbarerBlick[] {
  const out: WaehlbarerBlick[] = [];
  const belegt = new Set<string>();
  for (const b of doc.settings.gespeicherteBlicke ?? []) {
    if (belegt.has(b.id)) continue;
    belegt.add(b.id);
    out.push({
      id: b.id,
      name: b.name,
      herkunft: 'Entwurf',
      position: [b.position[0], b.position[1], b.position[2]],
      target: [b.ziel[0], b.ziel[1], b.ziel[2]],
      fov: b.fovGrad,
    });
  }
  for (const b of quelle?.blicke ?? []) {
    if (belegt.has(b.id)) continue;
    belegt.add(b.id);
    out.push({ ...b });
  }
  return out;
}

/** Der Eintrag in der Auswahl: der Name, bei gleichen Namen mit der Herkunft (und Nummer) dazu. */
export function blickBeschriftung(b: WaehlbarerBlick, liste: readonly WaehlbarerBlick[]): string {
  const gleich = liste.filter((x) => x.name === b.name);
  if (gleich.length < 2) return b.name;
  const gleicheHerkunft = gleich.filter((x) => x.herkunft === b.herkunft);
  return gleicheHerkunft.length < 2 ? `${b.name} (${b.herkunft})` : `${b.name} (${b.herkunft} ${gleicheHerkunft.indexOf(b) + 1})`;
}

/** Der gewählte Blick des Knotens in der Liste: über die Kennung, ohne sie über den einzigen gleichen Namen. */
export function gewaehlterBlick(params: VisNode['params'], liste: readonly WaehlbarerBlick[]): WaehlbarerBlick | undefined {
  const id = kameraBlickId(params ?? {});
  if (id) return liste.find((x) => x.id === id);
  const name = kameraBlickName(params ?? {});
  const gleich = name ? liste.filter((x) => x.name === name) : [];
  return gleich.length === 1 ? gleich[0] : undefined;
}

/** Der Name, der am Knoten steht: der heutige des Blicks, sonst der beim Wählen festgehaltene. */
export function blickAnzeigeName(params: VisNode['params'], liste: readonly WaehlbarerBlick[]): string {
  return gewaehlterBlick(params, liste)?.name ?? kameraBlickName(params ?? {});
}

/** Der Satz für die leere Liste: der des Wirts, sonst `KEIN_BLICK_SATZ`. */
export function leerSatzBlicke(): string {
  return quelle?.leerSatz ?? KEIN_BLICK_SATZ;
}

/** Die Parameter, die eine Wahl schreibt: Name und die festgehaltene Kamera (ein Befehl). */
export function blickParams(b: WaehlbarerBlick): Record<string, string> {
  return {
    art: 'blick',
    blickId: b.id,
    blick: b.name,
    blickKamera: JSON.stringify({ position: b.position.map((v) => rund(v)), target: b.target.map((v) => rund(v)), fov: rund(b.fov) }),
  };
}

/** Eine Zeile über einen Blick: Herkunft, Bildwinkel, Augenhöhe (glTF y). */
export function blickZeile(b: { herkunft?: string; position: readonly number[]; fov: number }): string {
  const teile = [b.herkunft ? `aus ${b.herkunft === 'Entwurf' ? 'dem Entwurf' : `der ${b.herkunft}`}` : '', `Bildwinkel ${Math.round(b.fov)}°`, `Auge ${b.position[1]!.toFixed(1).replace('.', ',')} m`];
  return teile.filter(Boolean).join(' · ');
}

/**
 * Wie der Blick am Knoten zur Liste steht: `gleich` (der gewählte ist so gesichert), `geaendert`
 * (gleicher Name, andere Werte — die Kamera bleibt, wie übernommen), `fehlt` (nicht mehr in der
 * Liste), `ohne` (keiner gewählt).
 */
export function blickStand(params: VisNode['params'], liste: readonly WaehlbarerBlick[]): 'gleich' | 'geaendert' | 'fehlt' | 'ohne' {
  if (!kameraBlickId(params ?? {}) && !kameraBlickName(params ?? {})) return 'ohne';
  // Umbenannt zählt nicht: verglichen wird über die Kennung, und nur die Pose.
  const b = gewaehlterBlick(params, liste);
  if (!b) return 'fehlt';
  const k = kameraBlickAusParams(params ?? {});
  if (!k) return 'gleich';
  const nah = (a: readonly number[], c: readonly number[]) => a.every((v, i) => Math.abs(v - c[i]!) < 1e-3);
  return nah(k.position, b.position) && nah(k.target, b.target) && Math.abs(k.fov - b.fov) < 1e-3 ? 'gleich' : 'geaendert';
}

/** Der Zusatz im Knotenkopf: « · Ecke SO/SW» am Knoten «Kamera» mit gewähltem Blick, sonst leer. */
export function kameraKopfZusatz(node: Pick<VisNode, 'typ' | 'params'>, doc: KosmoDoc): string {
  if (node.typ !== 'kamera' || kameraArtAusParams(node.params ?? {}) !== 'blick') return '';
  const name = blickAnzeigeName(node.params, waehlbareBlicke(doc));
  if (!name) return '';
  return ` · ${name.length > 18 ? `${name.slice(0, 17)}…` : name}`;
}

/**
 * Für Aufrufe von aussen (Claude, Assistent): `{ art: 'blick', blick: 'Name' }` oder
 * `{ art: 'blick', blickId: '…' }` ohne festgehaltene Kamera wird ergänzt — Kennung, Name und
 * Kamera aus derselben Liste, die der Knoten zeigt (also auch mit den Blicken des Wirts, die der
 * Kern nicht kennt). Der Name wird beim Setzen auf die Kennung aufgelöst. Unbekannt oder (nur mit
 * Namen) mehrdeutig: wirft mit der Liste der gesicherten. Alles andere bleibt, wie es ist.
 */
export function blickAufrufErgaenzen(
  doc: KosmoDoc,
  params: Record<string, string | number | boolean>,
): Record<string, string | number | boolean> {
  const name = typeof params['blick'] === 'string' ? params['blick'].trim() : '';
  const id = typeof params['blickId'] === 'string' ? params['blickId'].trim() : '';
  if (!name && !id) return params;
  if (typeof params['blickKamera'] === 'string' && params['blickKamera'].trim() !== '') return params;
  const liste = waehlbareBlicke(doc);
  const aufzaehlung = liste.map((x) => `«${x.name}» (blickId ${x.id})`).join(', ');
  const treffer = id ? liste.filter((x) => x.id === id) : liste.filter((x) => x.name === name);
  if (treffer.length > 1) {
    throw new Error(`Blick «${name}» ist mehrdeutig — ${treffer.length} heissen so; mit blickId wählen: ${aufzaehlung}.`);
  }
  const b = treffer[0];
  if (!b) {
    const wer = id ? `blickId «${id}»` : `Blick «${name}»`;
    throw new Error(liste.length > 0 ? `${wer} gibt es nicht — gesichert sind: ${aufzaehlung}.` : `${wer} gibt es nicht — es ist noch kein Blick gesichert.`);
  }
  return { ...params, ...blickParams(b) };
}
