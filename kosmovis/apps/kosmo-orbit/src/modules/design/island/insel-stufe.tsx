import { createContext, useContext } from 'react';

/**
 * E-10 · «In einer Insel wird nicht gescrollt»
 * (`docs/design/GESTALTUNGS-ENTSCHEIDE-2026-08-10.md`, Owner-Befund O-12 vom
 * 11.08.2026: «insel ui so gestalten dass nicht in der insel selbst
 * gescrollt werden kann — **niemals** scrollbare Menüs in den Inseln
 * selbst»).
 *
 * Dieses Modul liefert das EINE Mittel für E-10s **Antwort (a)**: Inhalt,
 * dessen Länge das PROJEKT bestimmt (Dokumente, Blätter, Import-Ergebnisse),
 * zeigt in Stufe 2 nur den Kopf der Liste und nennt den Rest ehrlich; die
 * vollständige Liste lebt in Stufe 3 — der einen sanktionierten
 * Scrollfläche der Insel-UI (`.isl-fenster`, s. `island.css`).
 *
 * **Warum ein Context und nicht ein Prop:** die Stations-Registries
 * registrieren fast überall DIESELBE Komponente für Stufe 2 und Stufe 3
 * (`registriere('blatt', { Stufe2: BlattListeStufe2, Stufe3:
 * BlattListeStufe2 })` — publish/prepare/vis durchgehend). Ein Prop müsste
 * durch jede dieser Registrierungen gefädelt werden und jede Registry-
 * Signatur ändern; der Context stellt dieselbe Auskunft ohne einen einzigen
 * Aufrufer anzufassen. `IslandShell.tsx` legt ihn genau um die zwei
 * gerenderten Inhaltsflächen (Popup/Fenster).
 *
 * **Default `'fenster'`:** eine Insel-Inhaltskomponente, die AUSSERHALB der
 * Shell gerendert wird (Unit-Tests, künftige Einbettungen), zeigt lieber
 * alles als versehentlich zu wenig — Kappung ist eine Platzregel der engen
 * Stufe 2, kein Datenschutz.
 */

/** Die zwei Inhaltsstufen einer Insel (Stufe 0/1 tragen keinen Inhalt). */
export type InselInhaltsStufe = 'popup' | 'fenster';

export const InselStufeContext = createContext<InselInhaltsStufe>('fenster');

/** In welcher Stufe rendert der aufrufende Insel-Inhalt gerade? */
export function useInselStufe(): InselInhaltsStufe {
  return useContext(InselStufeContext);
}

/**
 * E-10 Antwort (a): so viele Einträge zeigt eine projektlange Liste in
 * Stufe 2. Fünf, weil die bestehende Präzedenz (`spez/island/inhalte/
 * befund.tsx`s `slice(0, 3)`, `wissen.tsx`s `searchKnowledge(q, 6)`) genau
 * dieses Band aufspannt — und weil fünf Zeilen à ~26px plus Restzeile die
 * Stufe-2-Fläche auch auf einem 768px-Fenster nicht über die Insel hinaus
 * wachsen lassen.
 */
export const STUFE2_LISTEN_KAPPUNG = 5;

export interface ListenKappung<T> {
  /** Die tatsächlich zu rendernden Einträge. */
  readonly sichtbar: readonly T[];
  /** Wie viele Einträge die Kappung zurückhält (0 = nichts verborgen). */
  readonly verborgen: number;
}

/**
 * Reine Funktion hinter `useListenKappung` — ohne React testbar (Muster
 * `findeOffScaleBreakpoints` im Breakpoint-Wächter).
 *
 * `behalten` ist die Regel für AUSWAHL-Listen (Blätter, Varianten): eine
 * Kappung darf nie den gerade gewählten Eintrag verstecken, sonst weiss der
 * Nutzer nicht mehr, worauf er schaut. Liegt der gewählte Eintrag ausserhalb
 * des Listenkopfs, tritt er an die Stelle des letzten Kopf-Eintrags — die
 * Liste bleibt gleich lang, zeigt aber immer, wo man steht.
 */
export function kappeListe<T>(
  eintraege: readonly T[],
  stufe: InselInhaltsStufe,
  behalten?: (eintrag: T) => boolean,
): ListenKappung<T> {
  if (stufe !== 'popup' || eintraege.length <= STUFE2_LISTEN_KAPPUNG) {
    return { sichtbar: eintraege, verborgen: 0 };
  }
  const kopf = eintraege.slice(0, STUFE2_LISTEN_KAPPUNG);
  const gewaehlt = behalten ? eintraege.find(behalten) : undefined;
  const sichtbar =
    gewaehlt !== undefined && !kopf.includes(gewaehlt)
      ? [...kopf.slice(0, STUFE2_LISTEN_KAPPUNG - 1), gewaehlt]
      : kopf;
  return { sichtbar, verborgen: eintraege.length - sichtbar.length };
}

/** Kappt eine Liste gemäss E-10 (a) auf die aktuelle Insel-Stufe. */
export function useListenKappung<T>(
  eintraege: readonly T[],
  behalten?: (eintrag: T) => boolean,
): ListenKappung<T> {
  return kappeListe(eintraege, useInselStufe(), behalten);
}

/**
 * Die ehrliche Restzeile unter einer gekappten Liste — sie nennt die Zahl
 * der zurückgehaltenen Einträge UND den Weg zu ihnen (nochmals auf das
 * Werkzeug klicken eskaliert Stufe 2 → Stufe 3, s. `IslandShell.tsx`s
 * `aufWerkzeugKlick`). Rendert nichts, wenn nichts verborgen ist — der
 * Aufrufer braucht keine eigene Bedingung.
 */
export function ListenRest({ anzahl, testid }: { anzahl: number; testid?: string }) {
  if (anzahl <= 0) return null;
  return (
    <p
      className="isl-listen-rest"
      {...(testid ? { 'data-testid': testid } : { 'data-testid': 'island-listen-rest' })}
    >
      + {anzahl} {anzahl === 1 ? 'weiterer Eintrag' : 'weitere'} — nochmals klicken zeigt alle
    </p>
  );
}
