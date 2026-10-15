/**
 * Der Graph der Knotenansicht übersteht das Neuladen (Visbox-eigen, 15.10.2026).
 *
 * Anlass (HomeStation, auf-20261015-286): In Visbox lebt das Dokument nur in dieser Seite — kein
 * Tresor, keine Mitarbeitenden. Nach dem Neuladen war der Graph weg. Der Wirt sichert darum die
 * Render-Graphen (Einträge der Art `visgraph`) je Mappe auf dem Heim-PC (`./graph`, siehe
 * `oberflaeche/server.py` WEG_KNOTEN_GRAPH und `aiimaging.knotenweg.schreibe_graph`) und legt sie
 * beim Öffnen wieder ins Dokument — VOR dem ersten Bild, damit der fertige Anfang (Entscheid 91)
 * nicht zusätzlich angelegt wird.
 */
import type { VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';

/** Wie lange nach der letzten Änderung gesichert wird. */
export const SICHERN_NACH_MS = 1000;

/** Die Render-Graphen des Dokuments. */
export function renderGraphen(): VisGraph[] {
  return useProject.getState().doc.byKind<VisGraph>('visgraph');
}

/** Legt gesicherte Graphen ins Dokument (ohne Rückgängig-Schritt: Es ist der Stand beim Öffnen). */
export function legeGraphen(graphen: VisGraph[]): number {
  if (graphen.length === 0) return 0;
  const { doc } = useProject.getState();
  doc.apply(graphen.filter((g) => !doc.get(g.id)).map((g) => ({ id: g.id, before: null, after: g })));
  useProject.setState((s) => ({ revision: s.revision + 1 }));
  return graphen.length;
}

/** Holt den gesicherten Graph vom Heim-PC und legt ihn ins Dokument. Gibt die Zahl zurück. */
export async function ladeGesichertenGraph(holen: typeof fetch = fetch): Promise<number> {
  try {
    const antwort = await holen('./graph');
    if (!antwort.ok) return 0;
    const sicht = (await antwort.json()) as { graphen?: VisGraph[] };
    return legeGraphen(Array.isArray(sicht.graphen) ? sicht.graphen : []);
  } catch {
    return 0; // Ohne Antwort beginnt die Ansicht wie bisher — mit dem fertigen Anfang.
  }
}

/**
 * Sichert die Graphen nach jeder Änderung (mit Verzögerung, und nur, wenn sich etwas
 * geändert hat). Gibt eine Abmeldung zurück.
 */
export function sichereBeiAenderung(
  senden: (rumpf: string) => Promise<unknown> = (rumpf) =>
    fetch('./graph', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: rumpf }),
  nachMs: number = SICHERN_NACH_MS,
): () => void {
  let zuletzt = JSON.stringify({ graphen: renderGraphen() });
  let uhr: ReturnType<typeof setTimeout> | null = null;
  const abmelden = useProject.subscribe((s, vorher) => {
    if (s.revision === vorher.revision) return;
    if (uhr) clearTimeout(uhr);
    uhr = setTimeout(() => {
      uhr = null;
      const rumpf = JSON.stringify({ graphen: renderGraphen() });
      if (rumpf === zuletzt) return;
      zuletzt = rumpf;
      void senden(rumpf).catch(() => {
        zuletzt = ''; // beim nächsten Mal noch einmal versuchen
      });
    }, nachMs);
  });
  return () => {
    if (uhr) clearTimeout(uhr);
    abmelden();
  };
}
