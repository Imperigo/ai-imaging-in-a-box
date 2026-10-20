import { LOGO_FUER_HAUPTWERKZEUG, LOGO_FUER_STATION, type LogoId, type ModuleId } from '@kosmo/ui';
import { ORBIT_HAUPTWERKZEUGE, type HauptwerkzeugId } from '../orbit-werkzeuge';

/**
 * B/C · die Palette am Kosmo-Logo — die reine Rechnung, ohne Oberflaeche
 * (Entwurf `docs/entwuerfe/palette-und-speichern/`, Entwurfsflaeche
 * «KosmoOrbit Logo-Sammlung», Blatt «Palette»; **U4, v0.1.7: Entwurf A
 * «zweiter Bogen»**, Owner 01.10.2026).
 *
 * **Welche Werkzeuge** (Owner 30.09.2026): «alle stationen auf die palette» —
 * und gleich danach: «das ganze abteil Kosmo, das brauchen wir nicht, das
 * sind hintergrundtools die nicht aktiv aufgeschaltet werden». Die Palette
 * zeigt darum die Hauptwerkzeuge KosmoDesign und KosmoData (Owner, zuletzt:
 * «bitte keine spez sondern nur data und design symbole») und, wenn man eines
 * antippt, dessen Stationen — die man wirklich oeffnen kann (nichts
 * «kommend»), ohne die gerade offene. KosmoSpez, Kosmos Werkstaetten (Speak,
 * Sketch, Train, Dev, Doc, Trust, Package) und KosmoOffice stehen nicht darauf.
 *
 * **Zwei Bogen** (U4): innen die Hauptwerkzeuge, aussen die Unterwerkzeuge
 * des angetippten — je in der Farbe ihrer Station.
 */

/** Die Hauptwerkzeuge auf dem inneren Bogen, in dieser Reihenfolge. */
const HAUPT_REIHE: readonly HauptwerkzeugId[] = ['design', 'data'];

/**
 * Welche Station ein zweites Antippen des Hauptwerkzeugs oeffnet: bei
 * KosmoDesign die Zeichenflaeche (KosmoDraw), bei KosmoData der Datenraum
 * (KosmoReference) — dieselben Stationen, die ihre Untertools mit gleicher
 * `moduleId` oeffnen.
 */
const HAUPT_STATION: Readonly<Record<string, ModuleId>> = { design: 'design', data: 'data' };

export interface PalettenWerkzeug {
  readonly id: string;
  readonly moduleId: ModuleId;
  /** Zu welchem Hauptwerkzeug es gehoert — dessen Antippen faechert es auf (in KosmoOrbit eine `HauptwerkzeugId`). */
  readonly gruppe: string;
  /** Kurz, als Beschriftung am Tupfer («Prepare»). */
  readonly kurz: string;
  /** Voller Name fuer Vorlesen («KosmoPrepare»). */
  readonly titel: string;
  /** Das Logo aus der Sammlung (`@kosmo/ui` `StationLogo`). */
  readonly logo: LogoId;
}

export interface PalettenGruppe {
  /** In KosmoOrbit eine `HauptwerkzeugId`; ein zweiter Wirt (`registrierePalettenQuelle`) nennt eigene. */
  readonly id: string;
  /** «KosmoDesign» */
  readonly titel: string;
  /** «Design» */
  readonly kurz: string;
  readonly logo: LogoId;
  /** Die Station, die ein zweites Antippen oeffnet. */
  readonly station: ModuleId;
  /** Seine Unterwerkzeuge, ohne die gerade offene Station. */
  readonly werkzeuge: readonly PalettenWerkzeug[];
  /**
   * Nur bei einem zweiten Wirt: ein Ziel ausserhalb der Stationen (Visbox: «visbox-seite»). Die
   * Palette ruft dann `onZielOeffnen` statt `onStationOeffnen`. KosmoOrbit setzt es nie.
   */
  readonly ziel?: string;
}

/**
 * NAHTSTELLE FUER EINEN ZWEITEN WIRT (Visbox-Entscheide 115/116, 20.10.2026), nach dem Muster
 * `registriereModellLaden` (`modules/vis/modell-laden.ts`): Visbox zeigt dieselbe Palette am
 * Logo, aber mit seinen eigenen Zielen («Knoten», «Visbox-Seite») statt der Stationen von
 * KosmoOrbit. Die Datei geht dafuer wortgleich hinueber; nur der Wirt meldet hier seine
 * Gruppen an. **In KosmoOrbit ruft das niemand** — dann gilt die Rechnung unten unveraendert.
 */
export type PalettenQuelle = (aktivesModul: string) => PalettenGruppe[];

let palettenQuelle: PalettenQuelle | null = null;

/** Meldet die Gruppen eines zweiten Wirts an (`null` meldet sie ab). */
export function registrierePalettenQuelle(quelle: PalettenQuelle | null): void {
  palettenQuelle = quelle;
}

/** Die Hauptwerkzeuge samt ihren Unterwerkzeugen — das, was die Palette zeigt. */
export function palettenGruppen(aktivesModul: string): PalettenGruppe[] {
  if (palettenQuelle) return palettenQuelle(aktivesModul);
  const gesehen = new Set<string>();
  const raus: PalettenGruppe[] = [];
  for (const hid of HAUPT_REIHE) {
    const h = ORBIT_HAUPTWERKZEUGE.find((x) => x.id === hid);
    if (!h) continue;
    const werkzeuge: PalettenWerkzeug[] = [];
    for (const u of h.untertools) {
      if (!u.moduleId || u.kommend || u.moduleId === aktivesModul || gesehen.has(u.moduleId)) continue;
      gesehen.add(u.moduleId);
      werkzeuge.push({
        id: u.id,
        moduleId: u.moduleId,
        gruppe: hid,
        kurz: u.titel.replace(/^Kosmo/, ''),
        titel: u.titel,
        logo: LOGO_FUER_STATION[u.moduleId] ?? 'orbit',
      });
    }
    raus.push({
      id: hid,
      titel: h.titel,
      kurz: h.titel.replace(/^Kosmo/, ''),
      logo: LOGO_FUER_HAUPTWERKZEUG[hid] ?? 'orbit',
      station: HAUPT_STATION[hid] ?? 'design',
      werkzeuge,
    });
  }
  return raus;
}

/** Alle Unterwerkzeuge in Palettenreihenfolge (Design zuerst, dann Data). */
export function palettenWerkzeuge(aktivesModul: string): PalettenWerkzeug[] {
  return palettenGruppen(aktivesModul).flatMap((g) => g.werkzeuge);
}

/**
 * Die Farbe eines Logos als Token der Stationsfarben (`--k-mod-<id>`,
 * `aura.css`). Werkzeuge ohne eigenes Token erben das ihrer Gruppe:
 * KosmoReference steht in der Farbe von KosmoData (`LOGO_FARBE.reference`).
 */
export function farbTokenFuer(logo: LogoId): string {
  const gruppenFarbe: Partial<Record<LogoId, string>> = { reference: 'data', climate: 'spez', energy: 'spez', ing: 'spez' };
  return `--k-mod-${gruppenFarbe[logo] ?? logo}`;
}

/** Abstand der Bogen vom Logo-Mittelpunkt, in px: innen die Hauptwerkzeuge, aussen ihre Unterwerkzeuge. */
export const PALETTE_BAHNEN: readonly [number, number] = [110, 196];
/** Winkelabstand zweier Tupfer auf demselben Bogen (Grad): innen weiter, aussen enger, damit drei auf einen Viertelkreis passen. */
export const PALETTE_SCHRITT_GRAD: readonly [number, number] = [40, 37];
/**
 * Die Mitte je Bogen, in Grad unter der Waagrechten (Logo oben links, die Tupfer
 * liegen rechts unter ihm). Der innere Bogen sitzt steiler (52°): bei 45° stuende
 * der Tupfer von KosmoDesign (Gemessen am Bild, 1024 x 768) auf dem Insel-Knopf
 * «3D · PLAN» neben dem Logo und auf dem Hinweis darunter.
 */
export const PALETTE_MITTE_GRAD: readonly [number, number] = [52, 45];

export interface PalettenLage {
  /** 0 = innerer Bogen (Hauptwerkzeuge), 1 = aeusserer (Unterwerkzeuge). */
  readonly bahn: 0 | 1;
  readonly winkel: number;
  readonly x: number;
  readonly y: number;
}

/**
 * `anzahl` Tupfer auf dem Bogen `bahn`, mit festem Winkelabstand um die Mitte
 * des Viertelbogens: drei Tupfer fuellen den Bogen, zwei und einer rutschen
 * zur Mitte zusammen (statt auseinanderzurutschen).
 */
export function bogenLagen(anzahl: number, bahn: 0 | 1): PalettenLage[] {
  const r = PALETTE_BAHNEN[bahn];
  const schritt = PALETTE_SCHRITT_GRAD[bahn];
  return Array.from({ length: anzahl }, (_, i) => {
    const winkel = PALETTE_MITTE_GRAD[bahn] + (i - (anzahl - 1) / 2) * schritt;
    const rad = (winkel * Math.PI) / 180;
    return { bahn, winkel, x: r * Math.cos(rad), y: r * Math.sin(rad) };
  });
}
