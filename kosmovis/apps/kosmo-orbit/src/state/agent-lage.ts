/**
 * STELLVERTRETER (Visbox) (KI-Bedienung Stufe 6, 21.10.2026) fuer `state/agent-lage.ts` von
 * KosmoOrbit: die Zeile «MODUS» in KosmoBlick — welche Karten-Regel JETZT fuer den Agenten gilt.
 *
 * Dort nennt der Satz KosmoOrbits Ausnahmen (Pakete, Datei ausgeben, Projekt anlegen,
 * KosmoPrepare-Kontext, Veroeffentlichen). In Visbox gilt die Regel des Werkzeugsatzes
 * (`modules/vis/ki-werkzeuge.ts`, `brauchtKarte`; Entscheide 106b, 106c, 108): Loeschen ist in jedem
 * Modus eine Karte; Rendern in Karte und Coop auch, in Voll ohne Karte mit den Grenzen von Entscheid
 * 146 (`VOLL_BILDER`). Ein woertlicher
 * Satz von dort waere hier eine Falschauskunft an das Modell. Namen und Form wie dort.
 */
import { useKosmoCoop } from './kosmo-coop';
import { bedienZustandText, URHEBER_NAME, useKosmoMaus, type Urheber } from './kosmo-maus-freigabe';

function uhrzeit(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

/** Was in jedem Modus eine Karte bleibt — die Regel von `brauchtKarte`, in einem Satz. */
export const KARTE_BLEIBT = 'Löschen und Rendern bleiben in jedem Modus eine Karte; «Freigeben» (Grafikkarte) drückt nur der Architekt';

/**
 * In «Voll» (Owner-Entscheid 146, 24.10.2026): Bilder ueber die Werkzeuge rechnen ohne Karte und ohne
 * Freigabe-Klick, mit den Grenzen; Loeschen und die Maus bleiben bei der Karte.
 */
export const VOLL_BILDER =
  'Bilder über vis_render, vis_varianten und vis_grundlage rechnen ohne Karte und ohne Freigabe-Klick (höchstens 5 je Stunde, nie ein Bildmodell mit offener Lizenz — sonst eine Karte); Löschen und Bestellen über die Maus bleiben eine Karte';

/** Die Karten-Regel, die JETZT für diesen Agenten gilt, in einem Satz. */
export function modusText(urheber: Urheber): string {
  const c = useKosmoCoop.getState();
  if (c.vollautomatik) {
    const seit = uhrzeit(c.vollautomatikSeit);
    return (
      `Modus: Voll${seit ? ` (seit ${seit})` : ''} — Änderungen am Render-Graph (Werkzeuge, Maus) wendet Visbox ohne Karte an, ` +
      `im Verlauf zurücknehmbar; ${VOLL_BILDER}. Arbeite selbständig weiter.`
    );
  }
  if (c.an[urheber]) {
    const seit = uhrzeit(c.seit[urheber]);
    return (
      `Modus: Coop für ${URHEBER_NAME[urheber]}${seit ? ` (seit ${seit})` : ''} — einzelne Änderungen am Render-Graph ohne Karte, ` +
      `im Verlauf zurücknehmbar; ${KARTE_BLEIBT}.`
    );
  }
  return `Modus: Karte — jede Änderung am Render-Graph wird eine Vorschlagskarte; erst «Anwenden» des Architekten ändert ihn. ${KARTE_BLEIBT}.`;
}

/** Lage in einer Zeile: Modus · Bedienen · Mitschauen. */
export function agentLage(urheber: Urheber): string {
  const mitschauen = useKosmoMaus.getState().freigaben[urheber].mitschauen;
  return `${modusText(urheber)} ${bedienZustandText(urheber)}. Mitschauen: ${mitschauen ? 'an' : 'aus'}.`;
}
