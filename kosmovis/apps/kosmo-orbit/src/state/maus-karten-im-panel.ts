/**
 * Gerätebefund LW, Nachprobe Runde 17 (Punkt 3): Kosmos eigene KosmoMaus-Vorschläge (Kennung «m-…»)
 * schwebten unten rechts über allem — bei offenem Kosmo-Panel genau auf dessen Eingabe, aber nicht IM
 * Panel, wo Kosmos Vorschläge sonst stehen. Gesucht wurde die Karte dort; sie war nur im Bildschirmfoto
 * (kosmo_blick) zu finden.
 *
 * Solange ein Kosmo-Panel sichtbar ist, stehen Kosmos Maus-Karten darum in dessen Vorschlagszone, und die
 * schwebende Ablage zeigt nur noch die übrigen (Claudes). Dieser Merker sagt der Ablage, ob gerade ein
 * Panel sie übernimmt. Gezählt, nicht geschaltet: zwei Panel-Instanzen (Zentrale und Blase) sind nie
 * zugleich sichtbar, aber ein Wechsel darf den Merker nicht kurz falsch stehen lassen.
 */
import { create } from 'zustand';

export const useMausKartenImPanel = create<{ panels: number }>(() => ({ panels: 0 }));

/** Ein sichtbares Kosmo-Panel meldet sich an; Rückgabe: abmelden. */
export function panelZeigtMausKarten(): () => void {
  useMausKartenImPanel.setState((z) => ({ panels: z.panels + 1 }));
  let ab = false;
  return () => {
    if (ab) return;
    ab = true;
    useMausKartenImPanel.setState((z) => ({ panels: Math.max(0, z.panels - 1) }));
  };
}
