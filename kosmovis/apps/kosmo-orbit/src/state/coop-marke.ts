/**
 * B2 «Wer hat was geändert» (Teil B, Entwurfsfläche «KosmoOrbit Coop-Modus»,
 * Owner-Entscheid 07.10.2026): ein neuer Coop-Schritt von Claude oder Kosmo
 * leuchtet drei Sekunden in der Farbe seines Urhebers auf, mit einem Schild
 * «Claude · Fenster gesetzt». Danach ist es ein normales Bauteil; wer es
 * geändert hat, steht weiter im Verlauf.
 *
 * Diese Datei ist die EINE Quelle dafür: welcher Schritt gerade leuchtet,
 * von wem, welche Bauteile. Das Schild unten links liest sie
 * (`shell/kosmo-maus/KosmoCoop.tsx`); Grundriss und 3D (KosmoDraw, `3d/**`,
 * `PlanView.tsx`) färben die Bauteile über `useCoopMarke((z) => z.marke)`
 * ein — sie müssen dafür nichts über den Coop wissen.
 *
 * Bei weniger Bewegung gilt dasselbe Zeitfenster; die Darstellung entscheidet,
 * ob sie leuchtet oder still einfärbt.
 */

import { create } from 'zustand';
import { isSettingsPatch, type AnyPatch, type Entity } from '@kosmo/kernel';
import { kennungenVon, useKosmoCoop, type CoopGruppe } from './kosmo-coop';
import type { Urheber } from './kosmo-maus-freigabe';

/** So lange leuchtet ein neuer Coop-Schritt (Entwurf B2: 3 s). */
export const COOP_MARKE_MS = 3000;

export interface CoopMarke {
  /** Kennung des Coop-Schritts (`coop-<n>`). */
  kennung: string;
  urheber: Urheber;
  zusammenfassung: string;
  /** Kennungen der Bauteile, die der Schritt berührt hat. */
  bauteile: string[];
  /**
   * Nr. 55 (Demolauf 16.10., Entwurf «Claude im Bild»): je Bauteil, ob es neu ist,
   * geändert oder gelöscht — mit dem Stand davor, damit Grundriss und 3D die
   * Geisterlinie (geändert) und den Umriss (gelöscht) zeichnen können.
   */
  aenderungen: MarkeAenderung[];
  /** Zeitpunkt (ms), bis zu dem die Marke steht. */
  bis: number;
}

export interface MarkeAenderung {
  id: string;
  art: 'neu' | 'geaendert' | 'geloescht';
  /** Stand vor dem Schritt (`null` bei neuen Bauteilen). */
  vorher: Entity | null;
}

/** Ein Bauteil je Kennung: erster Vorher-Stand, letzter Nachher-Stand. */
export function aenderungenAus(patches: readonly AnyPatch[]): MarkeAenderung[] {
  const je = new Map<string, { vorher: Entity | null; nachher: Entity | null }>();
  for (const p of patches) {
    if (isSettingsPatch(p)) continue;
    const alt = je.get(p.id);
    je.set(p.id, { vorher: alt ? alt.vorher : (p.before as Entity | null), nachher: p.after as Entity | null });
  }
  const raus: MarkeAenderung[] = [];
  for (const [id, { vorher, nachher }] of je) {
    if (vorher === null && nachher === null) continue; // angelegt und im selben Schritt wieder gelöscht
    raus.push({ id, art: vorher === null ? 'neu' : nachher === null ? 'geloescht' : 'geaendert', vorher });
  }
  return raus;
}

export const useCoopMarke = create<{ marke: CoopMarke | null }>(() => ({ marke: null }));

let zuletztGesehen: string | null = null;
let uhr: ReturnType<typeof setTimeout> | null = null;

function neuesterSchritt(gruppen: readonly CoopGruppe[]): CoopGruppe | null {
  return gruppen.length > 0 ? gruppen[gruppen.length - 1]! : null;
}

/** Setzt die Marke für einen neuen Schritt und räumt sie nach `COOP_MARKE_MS` weg. */
export function markiereSchritt(
  g: Pick<CoopGruppe, 'kennung' | 'urheber' | 'zusammenfassung' | 'patches'>,
  jetzt: number = Date.now(),
): void {
  if (uhr) clearTimeout(uhr);
  useCoopMarke.setState({
    marke: {
      kennung: g.kennung,
      urheber: g.urheber,
      zusammenfassung: g.zusammenfassung,
      bauteile: kennungenVon(g),
      aenderungen: aenderungenAus(g.patches),
      bis: jetzt + COOP_MARKE_MS,
    },
  });
  uhr = setTimeout(() => {
    uhr = null;
    if (useCoopMarke.getState().marke?.kennung === g.kennung) useCoopMarke.setState({ marke: null });
  }, COOP_MARKE_MS);
}

/**
 * Hört auf neue Coop-Schritte. Gibt die Abmeldung zurück. Ein Schritt, der
 * schon beim Start da war, leuchtet nicht nach; ein zurückgenommener Schritt
 * löscht seine Marke sofort.
 */
export function beobachteCoopMarken(): () => void {
  zuletztGesehen = neuesterSchritt(useKosmoCoop.getState().gruppen)?.kennung ?? null;
  const ab = useKosmoCoop.subscribe((z) => {
    const neu = neuesterSchritt(z.gruppen);
    const marke = useCoopMarke.getState().marke;
    if (marke && z.gruppen.find((g) => g.kennung === marke.kennung)?.zurueckgenommen) useCoopMarke.setState({ marke: null });
    if (!neu || neu.kennung === zuletztGesehen) return;
    zuletztGesehen = neu.kennung;
    if (!neu.zurueckgenommen) markiereSchritt(neu);
  });
  return () => {
    ab();
    if (uhr) clearTimeout(uhr);
    uhr = null;
  };
}

/** Nur für Proben. */
export function setzeCoopMarkeZurueck(): void {
  if (uhr) clearTimeout(uhr);
  uhr = null;
  zuletztGesehen = null;
  useCoopMarke.setState({ marke: null });
}
