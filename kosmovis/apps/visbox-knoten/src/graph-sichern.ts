/**
 * Der Graph der Knotenansicht übersteht das Neuladen (Visbox-eigen, 15.10.2026).
 *
 * Anlass (HomeStation, auf-20261015-286): In Visbox lebt das Dokument nur in dieser Seite — kein
 * Tresor, keine Mitarbeitenden. Nach dem Neuladen war der Graph weg. Der Wirt sichert darum die
 * Render-Graphen (Einträge der Art `visgraph`) je Mappe auf dem Heim-PC (`./graph`, siehe
 * `oberflaeche/server.py` WEG_KNOTEN_GRAPH und `aiimaging.knotenweg.schreibe_graph`) und legt sie
 * beim Öffnen wieder ins Dokument — VOR dem ersten Bild, damit der fertige Anfang (Entscheid 91)
 * nicht zusätzlich angelegt wird.
 *
 * Beim Legen wird ein Graph **einmal sanft entzerrt, nur wenn Knoten sich überlappen**
 * (Owner-Befund am Mac, 20.10.2026: die Auto-Kamera lag über dem unteren Rand des Modell-Knotens,
 * seit der mit dem 3D-Fenster gewachsen ist — der Graph war vorher gesichert). Ohne Überlappung
 * bleibt jede Lage, wie sie gesichert ist (`entzerreGraph` in `knoten-entzerren.ts`). Der Wirt
 * hat die Lade-Fähigkeit zu diesem Zeitpunkt schon gemeldet (`main.tsx`), die Höhe des
 * Modell-Knotens stimmt also.
 *
 * Seit den Kopfteilen (Entscheide 115/116, 20.10.2026) meldet das Sichern seine Lage an den
 * Speichern-Kreis (wortgleich aus KosmoOrbit): «sichert …», «Gesichert · zuletzt HH:MM» oder
 * «NICHT gesichert» mit Grund — auch dann, wenn der Heim-PC mit einem Fehler antwortet, statt dass
 * die Anzeige still «gesichert» sagt (Fund F7 dort).
 */
import type { VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import type { AutosaveLage } from '../../kosmo-orbit/src/state/project-vault';
import { entzerreGraph } from '../../kosmo-orbit/src/modules/vis/knoten-entzerren';

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
  doc.apply(graphen.filter((g) => !doc.get(g.id)).map((g) => ({ id: g.id, before: null, after: entzerreGraph(g) })));
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
  melde: (lage: AutosaveLage) => void = () => {},
): () => void {
  let zuletzt = JSON.stringify({ graphen: renderGraphen() });
  let uhr: ReturnType<typeof setTimeout> | null = null;
  let gesichertUm: string | null = null;
  const abmelden = useProject.subscribe((s, vorher) => {
    if (s.revision === vorher.revision) return;
    if (uhr) clearTimeout(uhr);
    uhr = setTimeout(() => {
      uhr = null;
      const rumpf = JSON.stringify({ graphen: renderGraphen() });
      if (rumpf === zuletzt) return;
      zuletzt = rumpf;
      melde({ stand: 'sichert', iso: gesichertUm });
      void senden(rumpf)
        .then(async (antwort) => {
          const grund = await abgewiesen(antwort);
          if (grund !== null) throw new Error(grund);
          gesichertUm = new Date().toISOString();
          melde({ stand: 'gesichert', iso: gesichertUm });
        })
        .catch((fehler: unknown) => {
          zuletzt = ''; // beim nächsten Mal noch einmal versuchen
          melde({ stand: 'fehler', iso: gesichertUm, grund: fehler instanceof Error ? fehler.message : String(fehler) });
        });
    }, nachMs);
  });
  return () => {
    if (uhr) clearTimeout(uhr);
    abmelden();
  };
}

/** Der Grund, wenn der Heim-PC das Sichern abwies (eine Antwort mit `ok: false`), sonst `null`. */
async function abgewiesen(antwort: unknown): Promise<string | null> {
  const a = antwort as { ok?: unknown; status?: unknown; text?: () => Promise<string> } | null;
  if (!a || typeof a !== 'object' || a.ok !== false) return null;
  let satz = '';
  try {
    satz = typeof a.text === 'function' ? (await a.text()).trim() : '';
  } catch {
    satz = '';
  }
  // Ein kurzer Satz (wie der der App ohne Heim-PC) wird gezeigt, eine Fehlerseite nicht.
  return satz && satz.length <= 200 && !satz.startsWith('<') ? satz : `Der Heim-PC hat nicht gesichert (Antwort ${String(a.status)}).`;
}
