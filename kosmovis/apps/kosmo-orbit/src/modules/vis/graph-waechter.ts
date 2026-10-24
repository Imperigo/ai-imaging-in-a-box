import type { VisGraph } from '@kosmo/kernel';
import { useProject } from '../../state/project-store';
import {
  aktuellesProjekt,
  GRAPH_ENTFERNT_SATZ,
  laufZugehoerigkeit,
  OFFENE_LAUF_STATUS,
  useVisRuntime,
} from './vis-runtime';

/**
 * KosmoVis-Entscheid 2, Nachzug nach der Geraeteprobe R62: «Graph entfernt» darf nicht an der
 * Knotenansicht haengen. Nimmt Strg+Z den einzigen Graphen zurueck, verschwindet die Ansicht und mit
 * ihr der Abfrage-Takt; ein spaeteres Wiederholen holte das Bild dann doch ab und legte es ab. Dieser
 * Waechter schliesst einen offenen Lauf sofort, sobald sein Graph im eigenen Projekt fehlt — bei jeder
 * Aenderung am Projekt, ob die Knotenansicht offen ist oder nicht. Ein Lauf eines anderen Projekts
 * bleibt offen (Entscheid 1); ohne Projekt-Leser (Visbox) tut der Waechter nichts.
 */
export function schliesseLaeufeOhneGraph(): string[] {
  const doc = useProject.getState().doc;
  const hatGraph = (id: string) => doc.get<VisGraph>(id)?.kind === 'visgraph';
  const projekt = aktuellesProjekt();
  const { laeufe, patchLauf } = useVisRuntime.getState();
  const geschlossen: string[] = [];
  for (const [nodeId, l] of Object.entries(laeufe)) {
    if (!(OFFENE_LAUF_STATUS as readonly string[]).includes(l.status)) continue;
    if (laufZugehoerigkeit(l, hatGraph, projekt) !== 'graph-entfernt') continue;
    patchLauf(nodeId, { status: 'abgebrochen', fehler: GRAPH_ENTFERNT_SATZ });
    geschlossen.push(nodeId);
  }
  return geschlossen;
}

/** Meldet den Waechter am Projekt an (App: einmal beim Start). Gibt die Abmeldung zurueck. */
export function starteGraphWaechter(): () => void {
  return useProject.subscribe((s, vorher) => {
    if (s.doc === vorher.doc && s.revision === vorher.revision) return;
    schliesseLaeufeOhneGraph();
  });
}
