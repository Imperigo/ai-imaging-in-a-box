/**
 * research-Profil (v0.9.28 P-AUF Posten 3) — der EINE Ort, an dem diese App
 * entscheidet, ob ein Render-Auftrag als Forschungslauf bestellt werden darf.
 *
 * ## Warum es das gibt
 *
 * Die Modell-Lizenz-Sanierung vom 11.08.2026 hat drei Riegel gesetzt
 * (`docs/CLOUD-WORKER-REMEDIATION.md`, Phase 2): der HomeStation-Worker lädt
 * gesperrte Checkpoints nur mit `--research-only`, der Vertrag
 * (`RenderScene`, `kosmo-contracts`) verlangt für den Non-Commercial-Backbone
 * `research_only: true`, und `postRenderJob` wirft schon vor dem Senden.
 * Offen blieb Punkt 5 der Restliste: `vis.render` reicht kein research-Flag
 * durch — ein Kosmo-Auftrag mit `backbone: 'flux-krea'` endete deshalb
 * IMMER als Node-Fehler, auch beim Owner, der genau einen Vergleichslauf
 * fahren wollte.
 *
 * ## Warum das Gate dadurch nicht weicher wird — nachgelesen, nicht vermutet
 *
 *  1. **Erzwungen wird auf der HomeStation, nicht hier.** Das
 *     `research_only`-Feld des Vertrags «dokumentiert die Bestellung, das
 *     Worker-Flag erzwingt das Laden» (Wortlaut `render-scene.ts`). Der
 *     Worker liest sein `research_only` AUS SEINEM EIGENEN CLI-Flag/der
 *     Umgebungsvariablen (`kosmo_worker_comfyui.py`: `pruefe_faehigkeit(...,
 *     research_only=args.research_only)`), NIE aus der Job-Nutzlast. Nichts,
 *     was diese App sendet, kann dort einen gesperrten Checkpoint aufsperren.
 *  2. **Die Zustimmung ist menschlich und ausdrücklich.** Der Schalter steht
 *     in den Einstellungen mit dem Lizenz-Grund im Klartext, Vorgabe AUS.
 *     Ohne ihn bleibt jeder Job byte-identisch zum Stand vor P-AUF.
 *  3. **Das Modell kann sie nicht selbst geben.** Bewusst KEIN
 *     `research_only` im `vis.render`-Schema: eine Lizenz-Entscheidung
 *     gehört dem Menschen am Gerät, nicht einem erzeugten Werkzeug-Aufruf.
 *     Das Modell darf `flux-krea` weiter WÜNSCHEN — ob der Wunsch bestellbar
 *     ist, beantwortet allein dieser Schalter.
 *  4. **Geräte-lokal, nicht im Doc.** Deshalb `localStorage` und nicht
 *     `DocSettings`/`visRenderAuftrag`: ein Projekt wandert über Yjs und
 *     `.kosmo`-Pakete zu anderen Menschen und Rechnern. Eine im Dokument
 *     mitreisende Forschungs-Zustimmung wäre die Zustimmung von jemand
 *     anderem — genau die Aufweichung, die hier nicht passieren darf.
 *     Dieselbe Ablage-Logik wie `kosmo.bridge` (Gerät ≠ Doc, CLAUDE.md).
 *
 * Muster und Fehlertoleranz folgen `state/sounds.ts` (`kosmo.sounds`): lesen
 * ist immer frisch, ein werfender `localStorage` bedeutet AUS — im Zweifel
 * gilt das Produktprofil.
 */

const SCHLUESSEL = 'kosmo.researchProfil';

/**
 * true, wenn der Mensch das research-Profil ausdrücklich eingeschaltet hat.
 * Vorgabe AUS — und jeder unlesbare/unerwartete Wert zählt als AUS.
 */
export function researchProfilAktiv(): boolean {
  try {
    return typeof localStorage !== 'undefined' && localStorage.getItem(SCHLUESSEL) === '1';
  } catch {
    return false;
  }
}

/** Schreibt den Schalter (`Einstellungen.tsx`, `einstellung-research-profil`). */
export function setResearchProfilAktiv(an: boolean): void {
  try {
    if (typeof localStorage !== 'undefined') localStorage.setItem(SCHLUESSEL, an ? '1' : '0');
  } catch {
    /* localStorage kann in seltenen Umgebungen werfen — dann bleibt es AUS */
  }
}
