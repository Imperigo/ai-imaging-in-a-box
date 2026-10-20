/**
 * R37 (K3-Befund aus der Werkzeug-Vollprobe, UI-Aufklaerung 20.10.2026): eine
 * Skizze, die Kosmo oder Claude PER WERKZEUG anlegt, ist kein «Weisungs-Strich
 * vom iPad» (P1, v0.9.60, Entscheid C). Die Weisungswache im Panel deutete
 * bisher JEDE ungedeutete Skizze und stellte dazu eine neue Karte «Weisung vom
 * iPad: Wand …» — die KI schickte sich damit selbst eine Weisung, falsch
 * beschriftet, und die naechste Karte verdeckte die eigentliche.
 *
 * Hier merkt sich die App (Laufzeit, nicht im Doc), welche Skizzen ein Agent
 * angelegt hat; gefuellt in `project-store.ts#runCommand`, gelesen von der
 * Weisungswache (`KosmoPanel.tsx`). Ein Strich vom iPad laeuft ohne Agenten-
 * Urheber und bleibt Weisung wie bisher.
 */
const agentSkizzen = new Set<string>();

export function merkeAgentSkizzen(ids: readonly string[]): void {
  for (const id of ids) agentSkizzen.add(id);
}

export function istAgentSkizze(id: string): boolean {
  return agentSkizzen.has(id);
}

/** Nur fuer Proben. */
export function vergissAgentSkizzen(): void {
  agentSkizzen.clear();
}
